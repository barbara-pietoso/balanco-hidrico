import pandas as pd 
import geopandas as gpd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import requests
import folium
from streamlit_folium import st_folium, folium_static
import altair as alt
from unidecode import unidecode
import textwrap
import extra_streamlit_components as stx
from streamlit_echarts import st_echarts
import math

from io import BytesIO

# Limites aproximados de latitude e longitude do Rio Grande do Sul
LAT_MIN = -34.0  # Latitude mínima
LAT_MAX = -28.0  # Latitude máxima
LON_MIN = -54.5  # Longitude mínima
LON_MAX = -49.0  # Longitude máxima

# Função para validar se as coordenadas estão dentro dos limites do Rio Grande do Sul
def valida_coordenadas(latitude, longitude):
    if LAT_MIN <= latitude <= LAT_MAX and LON_MIN <= longitude <= LON_MAX:
        return True
    else:
        return False

# Configurações da página
st.set_page_config(
    page_title="Vazão Outorgável",
    page_icon=":droplet:",
    layout="wide",
    initial_sidebar_state='collapsed'
)

col1, col2, col3 = st.columns([1, 5, 1], vertical_alignment="center")

col2.markdown("<h1 style='text-align: center;'>Consulta da Vazão Outorgável</h1>", unsafe_allow_html=True)
col2.subheader("Insira as Coordenadas:")

# Campos para inserir coordenadas, inicialmente vazios
latitude = col2.number_input("Latitude", min_value=-90.0, max_value=90.0, step=0.0001, format="%.4f", value=None)
longitude = col2.number_input("Longitude", min_value=-180.0, max_value=180.0, step=0.0001, format="%.4f", value=None)

# Botão para enviar as coordenadas
enviar = col2.button("Enviar")

# Coordenadas iniciais do centro do Rio Grande do Sul
default_latitude = -30.0
default_longitude = -53.5

# Criar mapa centralizado no centro do Rio Grande do Sul (sem coordenadas inseridas)
if not enviar:
    mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)
else:
    if latitude is not None and longitude is not None:
        if valida_coordenadas(latitude, longitude):
            col2.write(f"Coordenadas inseridas: {latitude}, {longitude}")
            
            # Criar mapa centrado nas coordenadas inseridas
            mapa = folium.Map(location=[latitude, longitude], zoom_start=12)

            # URL do arquivo .shp hospedado no GitHub (precisa dos arquivos .shp, .shx, .dbf)
            shp_url = "https://raw.githubusercontent.com/barbara-pietoso/balanco-hidrico/main/Unidades_BH_RS.shp"
            shx_url = "https://raw.githubusercontent.com/barbara-pietoso/balanco-hidrico/main/Unidades_BH_RS.shx"
            dbf_url = "https://raw.githubusercontent.com/barbara-pietoso/balanco-hidrico/main/Unidades_BH_RS.dbf"

            try:
                # Baixar os arquivos .shp, .shx e .dbf
                shp_file = requests.get(shp_url).content
                shx_file = requests.get(shx_url).content
                dbf_file = requests.get(dbf_url).content

                # Carregar o shapefile no Geopandas a partir dos bytes
                with BytesIO(shp_file) as shp, BytesIO(shx_file) as shx, BytesIO(dbf_file) as dbf:
                    gdf = gpd.read_file(f"zip://{shp.filename},{shx.filename},{dbf.filename}")

                # Adicionar o arquivo GeoDataFrame ao mapa
                folium.GeoJson(gdf.__geo_interface__).add_to(mapa)

                # Adicionar um marcador no mapa
                folium.Marker([latitude, longitude], popup="Coordenadas Inseridas").add_to(mapa)

            except requests.exceptions.RequestException as e:
                col2.write(f"Erro ao carregar o arquivo SHP: {e}")
        else:
            col2.write("As coordenadas inseridas estão fora dos limites do Rio Grande do Sul.")
            # Criar mapa centralizado no centro do Rio Grande do Sul em caso de erro
            mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)
            col2.write("Mapa centralizado no Rio Grande do Sul.")
    else:
        col2.write("Por favor, insira as coordenadas corretamente.")
        mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)

# Exibir o mapa no Streamlit
st_folium(mapa, width=700, height=500)
