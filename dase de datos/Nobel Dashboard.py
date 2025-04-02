from dash import Dash, html, dcc, Input, Output, State
from pymongo import MongoClient
import pandas as pd
import plotly.express as px
import datetime

# Conexión con MongoDB
client = MongoClient("mongodb://localhost:27017/")
db = client['nobel']
collection = db['nobel_prizes']

# Función para obtener datos de MongoDB
def fetch_data():
    data = list(collection.find())
    return data

# Inicializar la aplicación Dash
app = Dash(__name__)

# Estilos globales con tonos lila
colors = {
    'background': '#EDE7F6',  # Lila claro
    'text': '#5E35B1',        # Morado profundo
    'accent': '#BA68C8'       # Lila pastel
}

# Diseño de la aplicación
app.layout = html.Div(
    style={'backgroundColor': colors['background'], 'fontFamily': 'Arial, sans-serif', 'padding': '20px'},
    children=[
        html.H1(
            "Nobel Prize Dashboard",
            style={'textAlign': 'center', 'color': colors['text'], 'marginBottom': '20px'}
        ),
        dcc.RangeSlider(
            id='year-slider',
            min=1900,
            max=2025,
            value=[1900, 2025],
            marks={i: str(i) for i in range(1900, 2026, 10)},
            tooltip={'placement': 'bottom', 'always_visible': True},
            className='range-slider'
        ),
        html.Div([
            dcc.Dropdown(
                id='cat-dropdown',
                options=[
                    {'label': 'Physics', 'value': 'Physics'},
                    {'label': 'Chemistry', 'value': 'Chemistry'},
                    {'label': 'Literature', 'value': 'Literature'},
                    {'label': 'Peace', 'value': 'Peace'},
                    {'label': 'Medicine', 'value': 'Medicine'},
                    {'label': 'Economics', 'value': 'Economics'},
                ],
                placeholder="Select a category",
                style={'backgroundColor': colors['background'], 'color': colors['text']}
            )
        ], style={'marginBottom': '20px'}),
        dcc.Graph(id='map-graph', style={'backgroundColor': colors['background']}),
        dcc.Graph(id='scatter-graph', style={'backgroundColor': colors['background']}),
        html.Div([
            html.H4("Gestionar datos en tiempo real", style={'color': colors['text']}),
            html.Div("Año:", style={'marginTop': '10px', 'color': colors['text']}),
            dcc.Input(id='input-year', type='number', placeholder='Año', step=1, min=1900, max=2025),
            html.Div("Categoría:", style={'marginTop': '10px', 'color': colors['text']}),
            dcc.Dropdown(
                id='input-category',
                options=[
                    {'label': 'Physics', 'value': 'Physics'},
                    {'label': 'Chemistry', 'value': 'Chemistry'},
                    {'label': 'Literature', 'value': 'Literature'},
                    {'label': 'Peace', 'value': 'Peace'},
                    {'label': 'Medicine', 'value': 'Medicine'},
                    {'label': 'Economics', 'value': 'Economics'},
                ],
                placeholder="Categoría",
                style={'backgroundColor': colors['background'], 'color': colors['text']}
            ),
            html.Div("Género:", style={'marginTop': '10px', 'color': colors['text']}),
            dcc.Dropdown(
                id='input-gender',
                options=[
                    {'label': 'Male', 'value': 'male'},
                    {'label': 'Female', 'value': 'female'},
                ],
                placeholder="Género",
                style={'backgroundColor': colors['background'], 'color': colors['text']}
            ),
            html.Div("País de nacimiento:", style={'marginTop': '10px', 'color': colors['text']}),
            dcc.Input(id='input-country', type='text', placeholder='País de nacimiento'),
            html.Div([
                html.Button('Agregar Datos', id='submit-button', n_clicks=0, 
                            style={'backgroundColor': colors['accent'], 'color': 'white', 'margin': '5px'}),
                html.Button('Editar Datos', id='edit-button', n_clicks=0, 
                            style={'backgroundColor': colors['accent'], 'color': 'white', 'margin': '5px'}),
                html.Button('Eliminar Datos', id='delete-button', n_clicks=0, 
                            style={'backgroundColor': colors['accent'], 'color': 'white', 'margin': '5px'}),
            ], style={'marginTop': '20px'})
        ], style={'marginTop': '20px'}),
    ]
)

@app.callback(
    Output('map-graph', 'figure'),
    Output('scatter-graph', 'figure'),
    Input('submit-button', 'n_clicks'),
    Input('edit-button', 'n_clicks'),
    Input('delete-button', 'n_clicks'),
    State('input-year', 'value'),
    State('input-category', 'value'),
    State('input-gender', 'value'),
    State('input-country', 'value'),
    Input('year-slider', 'value'),
    Input('cat-dropdown', 'value')
)
def update_dashboard(add_clicks, edit_clicks, delete_clicks, year, category, gender, country, selected_years, selected_category):
    # Insertar datos nuevos
    if add_clicks and add_clicks > 0 and year and category and gender and country:
        new_data = {
            'year': year,
            'category': category,
            'gender': gender,
            'bornCountry': country,
            'born': datetime.datetime(year, 1, 1),
            'age': year - 1900
        }
        collection.insert_one(new_data)

    # Editar datos existentes
    if edit_clicks and edit_clicks > 0 and year and category and (gender or country):
        query = {'year': year, 'category': category}
        update_fields = {}
        if gender:
            update_fields['gender'] = gender
        if country:
            update_fields['bornCountry'] = country
        if update_fields:
            updated_data = {"$set": update_fields}
            result = collection.update_one(query, updated_data)
            if result.matched_count == 0:
                print("No se encontraron registros para editar.")

    # Eliminar datos existentes
    if delete_clicks and delete_clicks > 0 and year and category:
        query = {'year': year, 'category': category}
        result = collection.delete_one(query)
        if result.deleted_count == 0:
            print("No se encontraron registros para eliminar.")

    # Obtener datos actualizados desde MongoDB
    fetched_data = fetch_data()
    df = pd.DataFrame(fetched_data)

    # Filtrar datos por los controles seleccionados
    df['year'] = pd.to_numeric(df['year'], errors='coerce')
    filtered_data = df[
        (df['year'] >= selected_years[0]) &
        (df['year'] <= selected_years[1])
    ]
    if selected_category:
        filtered_data = filtered_data[filtered_data['category'] == selected_category]

    # Visualización en el mapa
    if 'bornCountry' in filtered_data.columns:
        country_counts = filtered_data['bornCountry'].value_counts().reset_index()
        country_counts.columns = ['Country', 'Count']
        map_fig = px.choropleth(
            country_counts,
            locations='Country',
            locationmode='country names',
            color='Count',
            color_continuous_scale=px.colors.sequential.Purples,
            title='Number of Nobel Prize Winners by Country'
        )
    else:
        map_fig = {}

    # Gráfica de dispersión
    if 'year' in filtered_data.columns and 'age' in filtered_data.columns:
        scatter_fig = px.scatter(
            filtered_data,
            x='year',
            y='age',
            title='Age of Nobel Prize Winners by Year',
            opacity=0.65,
            trendline='ols',
            color_discrete_sequence=[colors['accent']]
        )
    else:
        scatter_fig = {}

    return map_fig, scatter_fig

# Ejecutar la app
if __name__ == '__main__':
    app.run(debug=True)