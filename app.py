import dash
from dash import dcc
from dash import html
import plotly.graph_objects as go
import pandas as pd 

app = dash.Dash(__name__)

# Define the dropdown options
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
    dash.dependencies.State('dropdown', 'value')
)
def update_output(n_clicks, selected_option):
    fig = go.Figure(data=go.Scatterpolar(r=[1,5,2,2,3], theta=['Joy','Awful','Bad','Surprise', 'Excitement'], fill='toself'))
    return f"Filme selecionado: {selected_option}. Button clicked {n_clicks} times.", fig


if __name__ == "__main__":
    app.run_server(debug=True)
