import os
import time
import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
import pandas as pd 
# import mysql.connector

app = dash.Dash(__name__)

# Função para aguardar o banco de dados estar pronto
# def wait_for_db():
#     max_attempts = 10
#     attempts = 0
#     while attempts < max_attempts:
#         try:
#             # Tenta conectar ao banco de dados
#             mydb = mysql.connector.connect(
#                 host=os.environ.get('MYSQL_HOST'),
#                 user=os.environ.get('MYSQL_USER'),
#                 password=os.environ.get('MYSQL_ROOT_PASSWORD'),
#                 database=os.environ.get('MYSQL_DATABASE')
#             )
#             mydb.close()
#             break  # Conexão bem-sucedida, sai do loop
#         except mysql.connector.Error as err:
#             print(f"Erro ao conectar ao banco de dados: {err}")
#             attempts += 1
#             time.sleep(10)  # Aguarda 5 segundos antes de tentar novamente
#     else:
#         # Caso atinja o limite de tentativas, exibe uma mensagem de erro
#         print("Não foi possível conectar ao banco de dados após várias tentativas.")

# wait_for_db()

# mydb = mysql.connector.connect(
#     host=os.environ.get('MYSQL_HOST'),
#     user=os.environ.get('MYSQL_USER'),
#     password=os.environ.get('MYSQL_ROOT_PASSWORD'),
#     database=os.environ.get('MYSQL_DATABASE')
# )

# cursor = mydb.cursor()

# cursor.execute("SELECT title FROM IMDB_Movies")
# movie_titles = cursor.fetchall()

# cursor.execute("SELECT title FROM IMDB_Series")
# series_titles = cursor.fetchall()

# # Define the dropdown options
# dropdown_options = {'Movies':
#                     [{'label': title, 'value': title} for title in movie_titles], 
#                     'Series':
#                     [{'label': title, 'value': title} for title in series_titles]
# }

dropdown_options = {'Movies':
                    [
                        {'label': 'O poderoso chefão', 'value': 'O poderoso chefão'},
                        {'label': 'Miranha', 'value': 'Miranha'},
                        {'label': 'Flash', 'value': 'Flash'}
                    ], 'Series':
                    [
                        {'label': 'breaking bad', 'value': 'breaking bad'},
                        {'label': 'sucession', 'value': 'sucession'},
                        {'label': 'sla', 'value': 'sla'}
                    ]
                    }


app.layout = html.Div(
    children=[
        html.H1("IMDB reviews classifications", style = {"text-align": "center", "margin":"20px 0px 20px 0px"}),
        html.Div(
            children = [
                html.P("In this website you are able to select a title that is currently in the top 250 movies or top 250 series in IMDB and check for the overall classification of the reviews from this title in the same page. For this project, we use a BERT based model with finetuning in goemotions dataset (but with resampled set of labels)")
            ],
            style = {"background":"#fafafa", "width":"80%", "margin": "auto auto", "padding":"40px 40px 40px 40px", "boder-radius": "5px"}
        ),
        html.Div(
            id = 'container-options',
            children=[
                dcc.RadioItems(id='check_options', options=[
                               'Movies', 'Series'], value='Movies', inline=True),
                dcc.Dropdown(
                    id="dropdown",
                    options=dropdown_options['Movies'],
                    value='filme1',  # Default selected option
                    style = {"width":"80%"}
                ),
                html.Button("Select", id="send-button", n_clicks=0, style={"width": "100px"}),
            ],
            style = {"display": "flex", "flex-direction": "row", "width": "80%", "justify-content": "space-evenly", "background": "#ffffff", "margin": "40px auto 40px auto", "gap": "10px", "align-items": "stretch"}
        ),
        html.Div(id='output'),  # Output div to display the selected option
        dcc.Graph(id='plot', figure={})
    ],
    style = {"font-family": "Courier New"}
)

@app.callback(
    dash.dependencies.Output('dropdown', 'options'),
    dash.dependencies.Output('dropdown', 'value'),
    dash.dependencies.Input('check_options', 'value')
)
def change_dropdown_options(check_option):
    return dropdown_options[check_option], dropdown_options[check_option][0]['value']

@app.callback(
    dash.dependencies.Output('output', 'children'),
    dash.dependencies.Output('plot', 'figure'),
    dash.dependencies.Input('send-button', 'n_clicks'),
    dash.dependencies.State('dropdown', 'value'),
    dash.dependencies.State('check_options', 'value')
)
def update_output(n_clicks, selected_option, type_option):
    fig = go.Figure(data=go.Scatterpolar(r=[1,5,2,2,3], theta=['Joy','Awful','Bad','Surprise', 'Excitement'], fill='toself'))
    
    # cursor.execute(f'SELECT * FROM IMDB_Revies_{type_option}_Predictions P JOIN IMDB_Reviews_{type_option} R ON R.id=P.id JOIN IMDB_{type_option} T ON R.id_title=T.id_title')
    
    return f"Filme selecionado: {selected_option}. Button clicked {n_clicks} times.", fig

if __name__ == "__main__":
    app.run_server(debug=True)
