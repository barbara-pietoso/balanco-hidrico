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

# Coordenadas iniciais do centro do Rio Grande do Sul
default_latitude = -30.0
default_longitude = -53.5

latitude = col2.number_input("Latitude", min_value=-90.0, max_value=90.0, step=0.0001, format="%.4f")
longitude = col2.number_input("Longitude", min_value=-180.0, max_value=180.0, step=0.0001, format="%.4f")


# Exibir as coordenadas inseridas
if latitude and longitude:
    col2.write(f"Coordenadas inseridas: {latitude}, {longitude}")

    # Criar mapa centrado nas coordenadas inseridas
    mapa = folium.Map(location=[latitude, longitude], zoom_start=12)

    # Carregar o arquivo GeoJSON diretamente da URL
    file_url = "https://drive.google.com/uc?export=download&id=1--laLHmabXElImR5RT-j-c4FajYICPqJ"
    
    try:
        # Carregar o arquivo GeoJSON diretamente da URL
        response = requests.get(file_url)
        response.raise_for_status()  # Verifica se houve algum erro na requisição
        geojson_data = response.json()

        # Adicionar o arquivo GeoJSON ao mapa
        folium.GeoJson(geojson_data).add_to(mapa)

        # Adicionar um marcador no mapa
        folium.Marker([latitude, longitude], popup="Coordenadas Inseridas").add_to(mapa)

        # Exibir o mapa no Streamlit
        st_folium(mapa, width=700, height=500)

    except requests.exceptions.RequestException as e:
        col2.write(f"Erro ao carregar o arquivo GeoJSON: {e}")

else:
    # Criar mapa centralizado no centro do Rio Grande do Sul (sem coordenadas inseridas)
    mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)

    # Carregar o arquivo GeoJSON diretamente da URL
    file_url = "https://drive.google.com/uc?export=download&id=1--laLHmabXElImR5RT-j-c4FajYICPqJ"
    
    try:
        # Carregar o arquivo GeoJSON diretamente da URL
        response = requests.get(file_url)
        response.raise_for_status()  # Verifica se houve algum erro na requisição
        geojson_data = response.json()

        # Adicionar o arquivo GeoJSON ao mapa
        folium.GeoJson(geojson_data).add_to(mapa)

        # Exibir o mapa no Streamlit
        st_folium(mapa, width=700, height=500)

    except requests.exceptions.RequestException as e:
        col2.write(f"Erro ao carregar o arquivo GeoJSON: {e}")
