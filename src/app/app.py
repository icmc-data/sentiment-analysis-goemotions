import os
import time
import dash
from dash import dcc, html
import plotly.graph_objects as go
import pandas as pd 
import psycopg2
import numpy

app = dash.Dash(__name__)

columns = ['admiration','amusement','anger','annoyance','approval','caring','confusion','curiosity','desire','disappointment','disapproval','disgust','embarrassment','excitement','fear','gratitude','grief','joy','love','nervousness','optimism','pride','realization','relief','remorse','sadness','surprise','neutral']

def dict_to_markdown(titles_list: dict, n_titles: int = 3) -> str:
    md = ''''''
    for i in range(n_titles):
        elem = titles_list[i]
        md += f'**{elem[0]}**: {elem[1]:.2f}  \n\n'

    return md
    



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

def cosine_similarity(a, b):
    return numpy.dot(a, b)/(numpy.linalg.norm(a)*numpy.linalg.norm(b))

def get_titles_vec(cursor):
    title_dict = {}
    cursor.execute(
        f'SELECT title FROM IMDB_Titles'
    )
    all_titles = list(cursor.fetchall())

    for title in all_titles:
        cursor.execute(
            f'select p.emotion, avg(p.review_value) + avg(p.title_value) as value from imdb_titles as t join imdb_reviews as r \
            on t.title_id = r.title_id join imdb_reviews_predictions as p on \
            r.review_id = p.review_id where title = \'{title[0]}\' group by \
            p.emotion order by p.emotion')
        prob_vec = [review_value for _, review_value in cursor.fetchall()]
        title_dict[title[0]] = prob_vec
    return title_dict

def get_title_distance(original_title, title_dict):
    distances = {}
    original_vec = title_dict[original_title]
    for title in title_dict:
        if title == original_title:
            continue
        distance = cosine_similarity(original_vec, title_dict[title])
        distances[title] = distance
    return distances

mydb = wait_for_db()

cursor = mydb.cursor()

cursor.execute("SELECT title FROM IMDB_Titles")
titles = cursor.fetchall()
titles_dict = get_titles_vec(cursor)


# Define the dropdown options
dropdown_options = {'Titles':
                    [{'label': title[0], 'value': title[0]} for title in titles]
}

app.layout = html.Div(
    children=[
        html.H1("Cinema Recommendation based on IMDB", style = {"text-align": "center", "margin":"20px 0px 20px 0px"}),
        html.Div(
            children = [
                html.P("In this website you are able to select a title and check for recomendations based on similarity. The titles were vectorized according to IMDB Reviews sentiment analysis."),
                html.Img(src='data.jpg')
            ],
            style = {"background":"#fafafa", "width":"80%", "margin": "auto auto", "padding":"40px 40px 40px 40px", "boder-radius": "5px"}
        ),
        html.Div(
            id = 'container-options',
            children=[
                dcc.Dropdown(
                    id="dropdown-1",
                    options=dropdown_options['Titles'],
                    value=dropdown_options['Titles'][0]['value'],  # Default selected option
                    style = {"width":"80%"}
                ),
                html.Button("Select", id="send-button", n_clicks=0, style={"width": "100px"})
            ],

            style = {"display": "flex", "flex-direction": "row", "width": "80%", "justify-content": "space-evenly", "background": "#ffffff", "margin": "40px auto 40px auto", "gap": "10px", "align-items": "stretch"}
        ),
        html.H2("Results", style = {"text-align": "center", "margin":"20px 0px 20px 0px"}),
        dcc.Markdown(id='output')
        # html.Div(id='output')  # Output div to display the selected option
        
    ],
    style = {"font-family": "Courier New"}
)

@app.callback(
    dash.dependencies.Output('dropdown-1', 'options'),
    dash.dependencies.Output('dropdown-1', 'value'),
    dash.dependencies.Input('send-button', 'value')
)
def change_dropdown_options(check_option):
    return dropdown_options[check_option], dropdown_options[check_option][0]['value']

@app.callback(
    dash.dependencies.Output('output', 'children'),
    dash.dependencies.Input('send-button', 'n_clicks'),
    dash.dependencies.State('dropdown-1', 'value'),
)
def update_output(n_clicks, selected_first_title):
    distances = get_title_distance(selected_first_title, titles_dict)
    
    distance_list = []
    for title in distances:
        distance_list.append((title, 100 * float(distances[title])))

    distance_list.sort(reverse=True, key=lambda a: a[1])

    return dict_to_markdown(distance_list)
    # return f"{distances}"

if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050, use_reloader=False)
