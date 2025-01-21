import pandas as pd
import geopandas as gpd
import requests
import zipfile
import tempfile
import os
from io import BytesIO
import streamlit as st
import folium
from streamlit.components.v1 import html  # Para exibir o mapa como HTML
from shapely.geometry import Point

# Configurações da página
st.set_page_config(
    page_title="Vazão Outorgável",
    page_icon=":droplet:",
    layout="wide",
    initial_sidebar_state='collapsed'
)

# Limites aproximados de latitude e longitude do Rio Grande do Sul
LAT_MIN = -33.75  # Latitude mínima (ajustada)
LAT_MAX = -27.5   # Latitude máxima (ajustada)
LON_MIN = -54.5   # Longitude mínima
LON_MAX = -49.0   # Longitude máxima

# Função para validar se as coordenadas estão dentro dos limites do Rio Grande do Sul
def valida_coordenadas(latitude, longitude):
    if LAT_MIN <= latitude <= LAT_MAX and LON_MIN <= longitude <= LON_MAX:
        return True
    else:
        return False

col1, col2, col3 = st.columns([1, 4, 1], vertical_alignment="center")

col2.markdown("<h1 style='text-align: center;'>Consulta da Vazão Outorgável</h1>", unsafe_allow_html=True)
col2.subheader("Insira as Coordenadas e a Área:")

# Campos para inserir coordenadas e área
latitude = col2.number_input("Latitude", min_value=-90.0, max_value=90.0, step=0.0001, format="%.4f", value=None)
longitude = col2.number_input("Longitude", min_value=-180.0, max_value=180.0, step=0.0001, format="%.4f", value=None)
area = col2.number_input("Área (em km²)", min_value=0.0, step=0.1, format="%.1f", value=None)

# Botão para enviar as coordenadas e a área
enviar = col2.button("Enviar")

# Coordenadas iniciais do centro do Rio Grande do Sul
default_latitude = -30.0
default_longitude = -53.5

# URL do arquivo .zip hospedado no GitHub
zip_url = "https://github.com/barbara-pietoso/balanco-hidrico/raw/main/arquivos_shape.zip"

# Inicializar o mapa padrão com as coordenadas centrais do Rio Grande do Sul
mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)

# Inicializar uma variável para armazenar o texto a ser exibido
informacao_upg = ""
qout = None

# Função para calcular Qout
def calcular_qout(qesp, area, perc_out):
    return qesp * area * perc_out

if enviar:
    if latitude is not None and longitude is not None and area is not None:
        if valida_coordenadas(latitude, longitude):
            col2.write(f"Coordenadas inseridas: {latitude}, {longitude}")
            col2.write(f"Área inserida: {area} km²")

            # Criar o mapa usando Folium com as coordenadas inseridas
            mapa = folium.Map(location=[latitude, longitude], zoom_start=12)

            try:
                # Baixar e extrair o arquivo shapefile do GitHub
                zip_file = requests.get(zip_url).content
                with tempfile.TemporaryDirectory() as temp_dir:
                    # Salvar o arquivo ZIP temporariamente
                    zip_path = os.path.join(temp_dir, "shapefile.zip")
                    with open(zip_path, "wb") as f:
                        f.write(zip_file)

                    # Extrair o conteúdo do ZIP
                    with zipfile.ZipFile(zip_path, "r") as zip_ref:
                        zip_ref.extractall(temp_dir)

                    # Caminho para o shapefile extraído
                    shp_file_path = os.path.join(temp_dir, "UNIDADES_BH_RS_NOVO.shp")

                    # Carregar o shapefile como GeoDataFrame
                    gdf = gpd.read_file(shp_file_path)

                    # Certificar-se de que o shapefile está em WGS84
                    if gdf.crs.to_string() != "EPSG:4326":
                        gdf = gdf.to_crs("EPSG:4326")

                    # Criar um ponto com as coordenadas inseridas
                    ponto = Point(longitude, latitude)

                    # Verificar em qual polígono o ponto está
                    for _, row in gdf.iterrows():
                        if row['geometry'].contains(ponto):
                            informacao_upg = f"UPG: {row['UPG']}"  # Substitua 'UPG' pela coluna correta
                            # Adicionar o polígono correspondente ao mapa
                            folium.GeoJson(row['geometry'].__geo_interface__,
                                           style_function=lambda x: {'fillColor': 'blue', 'color': 'blue'}).add_to(mapa)
                            break
                    else:
                        informacao_upg = "O ponto inserido não está dentro de nenhuma unidade."

            except Exception as e:
                informacao_upg = f"Erro ao processar o shapefile: {e}"
        else:
            informacao_upg = "As coordenadas inseridas estão fora dos limites do Rio Grande do Sul."
    else:
        informacao_upg = "Por favor, insira as coordenadas e a área corretamente."

# Exibir as informações
col2.write(informacao_upg)

# Salvar o mapa como HTML e exibi-lo no Streamlit
mapa_html = mapa._repr_html_()
html(mapa_html, height=500)

