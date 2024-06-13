import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import requests
import pandas as pd
import re
import plotly.graph_objs as go
from urllib3.util import Retry
from requests.adapters import HTTPAdapter
import os
from dotenv import load_dotenv
load_dotenv()

# Obtener los datos de pedidos desde el backend
urlPedido = 'https://restaurant-modern-backend-c4j8.vercel.app/pedido'
proxies = {
    "http": None,
    "https": None,
}

# Configurar retries y timeout
session = requests.Session()
retry = Retry(
    total=5,
    read=5,
    connect=5,
    backoff_factor=0.3,
    status_forcelist=(500, 502, 504)
)
adapter = HTTPAdapter(max_retries=retry)
session.mount('http://', adapter)
session.mount('https://', adapter)
# Obtener los datos de pedidos desde el backend
urlPedido = 'https://restaurant-modern-backend-c4j8.vercel.app/pedido'
responsePedido = requests.get(urlPedido)
dataPedido = responsePedido.json()

dfPedido = pd.DataFrame(dataPedido)

pattern = r'(\d+)/(\d+)/(\d+)'

def convert_date(date_str):
    match = re.match(pattern, date_str)
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3))
        if month >= 1 and month <= 12:
            return pd.Timestamp(year, month, day)
        else:
            return None
    else:
        return None

dfPedido['fecha'] = dfPedido['fecha'].apply(convert_date)

# Crear el gráfico de barras para pedidos
figPedido = px.histogram(dfPedido, x='fecha', title='Cantidad de Pedidos por Fecha')

urlFacturas = 'https://restaurant-modern-23.fly.dev/graphql'
query = """
    query Facturas {
        facturas {
            nro
            total
            fecha
        }
    }
"""
query2 = """
    query Facturas {
    facturas {
        nro
        total
        fecha
        pedido {
            nro_pedido
            id_mesero
            nro_mesa
            nombre_comensal
            fecha
            hora
            estado
            plato {
                cantidad
                nombre
            }
            bebida {
                cantidad
                nombre
            }
        }
    }
}
"""
responseFacturas = requests.post(urlFacturas, json={'query': query})
dataFacturas = responseFacturas.json()['data']['facturas']

responseFacturasPedido = requests.post(urlFacturas, json={'query': query2})
dataFacturasPedido = responseFacturasPedido.json()['data']['facturas']

dfFacturas = pd.DataFrame(dataFacturas)
dfFacturas = dfFacturas.groupby('fecha').sum().reset_index()

# Crear el gráfico circular para facturas
figFacturas = go.Figure(data=[go.Scatter(x=dfFacturas['fecha'], y=dfFacturas['total'], mode='lines+markers')])
figFacturas.update_layout(title='Total de Facturas por Fecha', xaxis_title='Fecha', yaxis_title='Total')

platos = []
for factura in dataFacturasPedido:
    pedido = factura['pedido']
    for plato in pedido['plato']:
        platos.append(plato)

dfPlatos = pd.DataFrame(platos)
dfPlatos = dfPlatos.groupby('nombre').sum().reset_index()
# Crear el gráfico circular para platos
figPlatos = px.pie(dfPlatos, values='cantidad', names='nombre', title='Cantidad Total de Platos')

bebidas = []
for factura in dataFacturasPedido:
    pedido = factura['pedido']
    for bebida in pedido['bebida']:
        bebidas.append(bebida)

dfBebidas = pd.DataFrame(bebidas)
dfBebidas = dfBebidas.groupby('nombre').sum().reset_index()
# Crear el gráfico circular para bebidas
figBebidas = px.pie(dfBebidas, values='cantidad', names='nombre', title='Cantidad Total de Bebidas')

# Inicialización de la aplicación Dash
app = dash.Dash(__name__)

# Layout de la aplicación Dash
app.layout = html.Div([
    html.H1(children='Dashboard de Pedidos y Facturas'),

    html.Div([
        dcc.DatePickerRange(
            id='date-picker-pedido',
            min_date_allowed=dfPedido['fecha'].min(),
            max_date_allowed=dfPedido['fecha'].max(),
            start_date=dfPedido['fecha'].min(),
            end_date=dfPedido['fecha'].max(),
            display_format='D/M/YYYY'
        ),
        dcc.Graph(
            id='graph-pedido',
            figure=figPedido
        )
    ]),

    html.Div([
        dcc.DatePickerRange(
            id='date-picker-factura',
            min_date_allowed=dfFacturas['fecha'].min(),
            max_date_allowed=dfFacturas['fecha'].max(),
            start_date=dfFacturas['fecha'].min(),
            end_date=dfFacturas['fecha'].max(),
            display_format='D/M/YYYY'
        ),
        dcc.Graph(
            id='graph-facturas',
            figure=figFacturas
        )
    ]),

    html.Div([
        dcc.Graph(
            id='graph-platos',
            figure=figPlatos
        )
    ]),

    html.Div([
        dcc.Graph(
            id='graph-bebidas',
            figure=figBebidas
        )
    ])
])

# Callback para actualizar el gráfico de pedidos
@app.callback(
    Output('graph-pedido', 'figure'),
    [Input('date-picker-pedido', 'start_date'),
     Input('date-picker-pedido', 'end_date')]
)
def update_graph_pedido(start_date, end_date):
    filtered_df = dfPedido[(dfPedido['fecha'] >= start_date) & (dfPedido['fecha'] <= end_date)]
    fig = px.histogram(filtered_df, x='fecha', title='Cantidad de Pedidos por Fecha')
    fig.update_layout(bargap=0.5)  # Ajustar el ancho de las barras
    return fig

# Callback para actualizar el gráfico de facturas
@app.callback(
    Output('graph-facturas', 'figure'),
    [Input('date-picker-factura', 'start_date'),
     Input('date-picker-factura', 'end_date')]
)
def update_graph_factura(start_date_factura, end_date_factura):
    filtered_df = dfFacturas[(dfFacturas['fecha'] >= start_date_factura) & (dfFacturas['fecha'] <= end_date_factura)]
    
    figFacturas = go.Figure(data=[go.Scatter(x=filtered_df['fecha'], y=filtered_df['total'], mode='lines+markers')])
    figFacturas.update_layout(title='Total de Facturas por Fecha', xaxis_title='Fecha', yaxis_title='Total')
    return figFacturas

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8050))
    app.run_server(host='0.0.0.0', port=port, debug=True)
