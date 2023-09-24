import os
import time
import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
import pandas as pd 
import psycopg2

app = dash.Dash(__name__)

# Função para aguardar o banco de dados estar pronto
def wait_for_db():
    max_attempts = 10
    attempts = 0
    while attempts < max_attempts:
        try:
            # Tenta conectar ao banco de dados
            mydb = psycopg2.connect(
                host=os.environ.get('POSTGRES_HOST'),
                user=os.environ.get('POSTGRES_USER'),
                password=os.environ.get('POSTGRES_PASSWORD'),
                database=os.environ.get('POSTGRES_NAME'),
                port=os.environ.get('POSTGRES_PORT')
            )
            return mydb
        except Exception as err:
            print(f"Erro ao conectar ao banco de dados: {err}")
            attempts += 1
            time.sleep(5)  # Aguarda 5 segundos antes de tentar novamente
    else:
        print("Não foi possível conectar ao banco de dados após várias tentativas.")
        # Caso atinja o limite de tentativas, exibe uma mensagem de erro

mydb = wait_for_db()

cursor = mydb.cursor()

cursor.execute("SELECT title FROM IMDB_Movies")
movie_titles = cursor.fetchall()

cursor.execute("SELECT title FROM IMDB_Series")
series_titles = cursor.fetchall()

# Define the dropdown options
dropdown_options = {'Movies':
                    [{'label': title, 'value': title} for title in movie_titles], 
                    'Series':
                    [{'label': title, 'value': title} for title in series_titles]
}

# app.layout = html.Div(
#     children=[
#         html.H1("IMDB reviews classifications", style = {"text-align": "center", "margin":"20px 0px 20px 0px"}),
#         html.Div(
#             children = [
#                 html.P("In this website you are able to select a title that is currently in the top 250 movies or top 250 series in IMDB and check for the overall classification of the reviews from this title in the same page. For this project, we use a BERT based model with finetuning in goemotions dataset (but with resampled set of labels)")
#             ],
#             style = {"background":"#fafafa", "width":"80%", "margin": "auto auto", "padding":"40px 40px 40px 40px", "boder-radius": "5px"}
#         ),
#         html.Div(
#             id = 'container-options',
#             children=[
#                 dcc.RadioItems(id='check_options', options=[
#                                'Movies', 'Series'], value='Movies', inline=True),
#                 dcc.Dropdown(
#                     id="dropdown-1",
#                     options=dropdown_options['Movies'],
#                     value=dropdown_options['Movies'][0]['value'],  # Default selected option
#                     style = {"width":"80%"}
#                 ),
#                 dcc.Dropdown(
#                     id="dropdown-2",
#                     options=dropdown_options['Movies'],
#                     value=dropdown_options['Movies'][1]['value'],  # Default selected option
#                     style = {"width":"80%"}
#                 ),
#                 html.Button("Select", id="send-button", n_clicks=0, style={"width": "100px"}),
#             ],
#             style = {"display": "flex", "flex-direction": "row", "width": "80%", "justify-content": "space-evenly", "background": "#ffffff", "margin": "40px auto 40px auto", "gap": "10px", "align-items": "stretch"}
#         ),
#         html.Div(id='output'),  # Output div to display the selected option
#         dcc.Graph(id='plot', figure={})
#     ],
#     style = {"font-family": "Courier New"}
# )

@app.callback(
    dash.dependencies.Output('dropdown-1', 'options'),
    dash.dependencies.Output('dropdown-1', 'value'),
    dash.dependencies.Output('dropdown-2', 'options'),
    dash.dependencies.Output('dropdown-2', 'value'),
    dash.dependencies.Input('check_options', 'value')
)
def change_dropdown_options(check_option):
    return dropdown_options[check_option], dropdown_options[check_option][0]['value'], dropdown_options[check_option], dropdown_options[check_option][1]['value']

@app.callback(
    dash.dependencies.Output('output', 'children'),
    dash.dependencies.Output('plot', 'figure'),
    dash.dependencies.Input('send-button', 'n_clicks'),
    dash.dependencies.State('dropdown-1', 'value'),
    dash.dependencies.State('dropdown-2', 'value'),
    dash.dependencies.State('check_options', 'value')
)
def update_output(n_clicks, selected_first_title, selected_second_title, type_option):
    columns = ['admiration','amusement','anger','annoyance','approval','caring','confusion','curiosity','desire','disappointment','disapproval','disgust','embarrassment','excitement','fear','gratitude','grief','joy','love','nervousness','optimism','pride','realization','relief','remorse','sadness','surprise','neutral']

    with db.connect() as conn:
        print(f'SELECT {",".join(columns)} FROM IMDB_Reviews_{type_option}_Predictions AS P JOIN IMDB_Reviews_{type_option} AS R ON R.id = P.id JOIN IMDB_{type_option} T ON T.id_title = R.id_title WHERE T.title = \'{selected_first_title}\'')
        first_title_predictions = list(conn.execute(f'SELECT {",".join(columns)} FROM IMDB_Reviews_{type_option}_Predictions AS P JOIN IMDB_Reviews_{type_option} AS R ON R.id = P.id JOIN IMDB_{type_option} T ON T.id_title = R.id_title WHERE T.title = \'{selected_first_title}\''))
        second_title_predictions = list(conn.execute(f'SELECT {",".join(columns)} FROM IMDB_Reviews_{type_option}_Predictions AS P JOIN IMDB_Reviews_{type_option} AS R ON R.id = P.id JOIN IMDB_{type_option} T ON T.id_title = R.id_title WHERE T.title = \'{selected_second_title}\''))

    first_title_pred_df = pd.DataFrame(first_title_predictions, columns=columns)
    second_title_pred_df = pd.DataFrame(second_title_predictions, columns=columns)
    
    first_title_pred_mean = first_title_pred_df[columns].mean()
    second_title_pred_mean = second_title_pred_df[columns].mean()

    print(first_title_pred_mean)
    print(second_title_pred_mean)

    fig = go.Figure(data=[go.Scatterpolar(r=first_title_pred_mean.to_list(), theta=columns, fill='toself'), 
                          go.Scatterpolar(r=second_title_pred_mean.to_list(), theta=columns, fill='toself')])
    
    
    return f"Titles selected: {selected_first_title} e {selected_second_title}. Button clicked {n_clicks} times.", fig

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050, use_reloader=False)
