import streamlit as st
import folium
import geopandas as gpd
from shapely.geometry import Point
import requests
import zipfile
import os
import tempfile
from streamlit.components.v1 import html

# Configurações da página
st.set_page_config(
    page_title="Consulta de Unidades",
    page_icon=":world_map:",
    layout="wide"
)

# Limites aproximados de latitude e longitude do Rio Grande do Sul
LAT_MIN = -33.75  # Latitude mínima
LAT_MAX = -27.5   # Latitude máxima
LON_MIN = -54.5   # Longitude mínima
LON_MAX = -49.0   # Longitude máxima

# URL do arquivo .zip hospedado no GitHub
zip_url = "https://github.com/barbara-pietoso/balanco-hidrico/raw/main/arquivos_shape.zip"

# Função para validar se as coordenadas estão dentro dos limites do Rio Grande do Sul
def valida_coordenadas(latitude, longitude):
    return LAT_MIN <= latitude <= LAT_MAX and LON_MIN <= longitude <= LON_MAX

# Layout de colunas
col1, col2, col3 = st.columns([1, 4, 1])

# Título
col2.markdown("<h1 style='text-align: center;'>Consulta de Unidades</h1>", unsafe_allow_html=True)

# Layout de colunas ajustado
col1, col2 = st.columns([1, 3])

# Entradas de latitude e longitude no lado esquerdo
with col1:
    latitude_input = st.text_input("Latitude", placeholder="Insira uma latitude")
    longitude_input = st.text_input("Longitude", placeholder="Insira uma longitude")
    enviar = st.button("Exibir no Mapa")

# Inicializar o mapa centralizado no Rio Grande do Sul
mapa = folium.Map(location=[-30.0, -53.5], zoom_start=7)

# Lógica para exibição do mapa
if enviar:
    try:
        # Tentar converter os valores inseridos para float
        latitude = float(latitude_input)
        longitude = float(longitude_input)

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

                    # Destacar a unidade que contém o ponto
                    for _, row in gdf.iterrows():
                        if row['geometry'].contains(ponto):
                            folium.GeoJson(
                                row['geometry'].__geo_interface__,
                                style_function=lambda x: {'fillColor': 'blue', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.5}
                            ).add_to(mapa)
                            break

            except Exception as e:
                col1.error(f"Erro ao carregar o shapefile: {e}")
        else:
            col1.warning("As coordenadas estão fora dos limites do Rio Grande do Sul.")

    except ValueError:
        col1.error("Por favor, insira valores numéricos válidos para latitude e longitude.")

# Renderizar o mapa no Streamlit
mapa_html = mapa._repr_html_()
html(mapa_html, height=600)

