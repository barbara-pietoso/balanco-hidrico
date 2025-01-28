import streamlit as st
import folium
import geopandas as gpd
from shapely.geometry import Point
import requests
import zipfile
import os
import tempfile
import pandas as pd
from streamlit.components.v1 import html

# Configurações da página
st.set_page_config(
    page_title="Consulta de disponibilidade hídrica",
    page_icon=":droplet:",
    layout="wide"
)

col1, col2, col3 = st.columns([1,3,1])

col3.image('https://github.com/barbara-pietoso/disponibilidade-hidrica-rs/blob/main/Bras%C3%A3o---RS---Sema%20(2).png?raw=true', width=300)
col2.title('Disponibilidade Hídrica no Rio Grande do Sul')
col1.image('https://github.com/barbara-pietoso/disponibilidade-hidrica-rs/blob/main/drhslogo.png?raw=true', width=150)


# Limites aproximados de latitude e longitude do Rio Grande do Sul
LAT_MIN = -33.75  # Latitude mínima
LAT_MAX = -27.5   # Latitude máxima
LON_MIN = -54.5   # Longitude mínima
LON_MAX = -49.0   # Longitude máxima

# URL do arquivo .zip hospedado no GitHub
zip_url = "https://github.com/barbara-pietoso/balanco-hidrico/raw/main/arquivos_shape_upg.zip"

# Função para validar se as coordenadas estão dentro dos limites do Rio Grande do Sul
def valida_coordenadas(latitude, longitude):
    return LAT_MIN <= latitude <= LAT_MAX and LON_MIN <= longitude <= LON_MAX

# Layout do título no topo
#st.markdown("<h1 style='text-align: center;'>Disponibilidade Hídrica para Outorga</h1>", unsafe_allow_html=True)

# Layout de colunas para as entradas (latitude e longitude) à esquerda e o mapa à direita
col4, col5, col6 = st.columns([1,1,1])  # A primeira coluna (1) para as entradas e a segunda (2) para o mapa

# Entradas de latitude, longitude e área
with col4:
    latitude_input = st.text_input("Latitude", placeholder="Digite a latitude. Ex: -32.000")
with col5:
    longitude_input = st.text_input("Longitude", placeholder="Digite a longitude. Ex: -50.000")
with col6:
    area_input = st.text_input("Área (em km²)", placeholder="Digite a área em km²")
    
enviar = st.button("Consultar disponibilidade hídrica")

col8, col9, col10 = st.columns([1,1,1])

# Inicializar o mapa centralizado no Rio Grande do Sul
with col10:
    mapa = folium.Map(location=[-30.0, -52.5], zoom_start=5)

# Lógica para exibição do mapa e consulta dos dados
if enviar:
    try:
        # Tentar converter os valores inseridos para float
        latitude = float(latitude_input)
        longitude = float(longitude_input)
        area = float(area_input)

        if valida_coordenadas(latitude, longitude):
            try:
                # Baixar e extrair o shapefile do GitHub
                zip_file = requests.get(zip_url).content
                with tempfile.TemporaryDirectory() as temp_dir:
                    zip_path = os.path.join(temp_dir, "shapefile.zip")
                    with open(zip_path, "wb") as f:
                        f.write(zip_file)

                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)

                    shp_file_path = os.path.join(temp_dir, "UNIDADES_BH_RS_NOVO.shp")
                    gdf = gpd.read_file(shp_file_path)

                    # Certificar-se de que o shapefile está em WGS84
                    if gdf.crs.to_string() != "EPSG:4326":
                        gdf = gdf.to_crs("EPSG:4326")

                    # Adicionar todas as unidades ao mapa em uma única cor
                    folium.GeoJson(
                        gdf,
                        style_function=lambda x: {'fillColor': 'gray', 'color': 'black', 'weight': 1, 'fillOpacity': 0.3}
                    ).add_to(mapa)

                    # Criar um ponto para as coordenadas inseridas
                    ponto = Point(longitude, latitude)

                    # Adicionar o ponto ao mapa
                    folium.Marker([latitude, longitude], popup="Coordenadas Inseridas").add_to(mapa)

                    # **Centralizar o mapa no ponto e ajustar o zoom**
                    mapa.location = [latitude, longitude]
                    mapa.zoom_start = 12  # Ajuste o zoom conforme necessário

                    # Destacar a unidade que contém o ponto e exibir a UPG
                    unidade_encontrada = None
                    for _, row in gdf.iterrows():
                        if row['geometry'].contains(ponto):
                            # Destacar a unidade
                            folium.GeoJson(
                                row['geometry'].__geo_interface__,
                                style_function=lambda x: {'fillColor': 'babyblue', 'color': 'babyblue', 'weight': 2, 'fillOpacity': 0.2}
                            ).add_to(mapa)
                            unidade_encontrada = row['ID_Balanco']  # Armazenar o ID_Balanco
                            break

                    # (resto do código permanece igual)
                    
            except Exception as e:
                col4.error(f"Erro ao carregar o shapefile: {e}")
        else:
            col4.warning("As coordenadas estão fora dos limites do Rio Grande do Sul.")
    except ValueError:
        col4.error("Por favor, insira valores numéricos válidos para latitude, longitude e área.")

# Renderizar o mapa no Streamlit
mapa_html = mapa._repr_html_()
with col10:
    html(mapa_html, width=600, height=700)  # Renderiza o mapa na segunda coluna
