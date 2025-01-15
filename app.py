import pandas as pd 
import geopandas as gpd
import requests
import zipfile
import tempfile
import os
from io import BytesIO
import streamlit as st
import pydeck as pdk

# Configurações da página
st.set_page_config(
    page_title="Vazão Outorgável",
    page_icon=":droplet:",
    layout="wide",
    initial_sidebar_state='collapsed'
)

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

# URL do arquivo .zip hospedado no GitHub
zip_url = "https://github.com/barbara-pietoso/balanco-hidrico/raw/main/Unidades_BH_RS.zip"

# Atualizar o mapa com as coordenadas inseridas
if enviar:
    if latitude is not None and longitude is not None:
        if valida_coordenadas(latitude, longitude):
            col2.write(f"Coordenadas inseridas: {latitude}, {longitude}")
            
            # Atualizar o mapa para centralizar nas coordenadas inseridas
            view_state = pdk.ViewState(latitude=latitude, longitude=longitude, zoom=12)

            try:
                # Baixar o arquivo .zip
                zip_file = requests.get(zip_url).content

                # Criar um arquivo ZIP em memória
                with BytesIO() as zip_buffer:
                    zip_buffer.write(zip_file)

                    # Salvar o arquivo zip em um arquivo temporário
                    with tempfile.TemporaryDirectory() as temp_dir:
                        temp_zip_path = os.path.join(temp_dir, "Unidades_BH_RS.zip")
                        
                        # Escrever o conteúdo do arquivo ZIP em um diretório temporário
                        with open(temp_zip_path, "wb") as f:
                            f.write(zip_buffer.getvalue())

                        # Extrair o arquivo ZIP
                        with zipfile.ZipFile(temp_zip_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)

                        # Agora vamos tentar ler o arquivo .shp diretamente do diretório temporário
                        shp_file_path = os.path.join(temp_dir, 'Unidades_BH_RS.shp')

                        # Ler o arquivo shapefile usando geopandas
                        gdf = gpd.read_file(shp_file_path)

                        # Convertendo os dados do GeoDataFrame para um formato utilizável pelo Deck.gl
                        geojson_data = gdf.to_json()

                        # Criar o mapa do OpenStreetMap usando o pydeck
                        layer = pdk.Layer(
                            "GeoJsonLayer",
                            geojson_data,
                            get_fill_color=[255, 0, 0, 160],  # Cor do preenchimento
                            get_line_color=[0, 0, 0],         # Cor da linha
                            get_line_width=1,
                            pickable=True
                        )

                        # Adicionar a camada ao mapa
                        r = pdk.Deck(layers=[layer], initial_view_state=view_state, map_style="mapbox://styles/mapbox/light-v10", mapbox_key=None)

                        # Exibir o mapa no Streamlit
                        st.pydeck_chart(r)

            except requests.exceptions.RequestException as e:
                col2.write(f"Erro ao carregar o arquivo SHP: {e}")
            except Exception as e:
                col2.write(f"Erro ao baixar ou extrair os arquivos: {e}")
        else:
            col2.write("As coordenadas inseridas estão fora dos limites do Rio Grande do Sul.")
            # Manter o mapa padrão quando as coordenadas não são válidas
            view_state = pdk.ViewState(latitude=default_latitude, longitude=default_longitude, zoom=7)
            col2.write("Mapa centralizado no Rio Grande do Sul.")
            # Exibir o mapa do OpenStreetMap
            r = pdk.Deck(layers=[], initial_view_state=view_state, map_style="mapbox://styles/mapbox/light-v10", mapbox_key=None)
            st.pydeck_chart(r)
    else:
        col2.write("Por favor, insira as coordenadas corretamente.")
        # Manter o mapa padrão
        view_state = pdk.ViewState(latitude=default_latitude, longitude=default_longitude, zoom=7)
        # Exibir o mapa do OpenStreetMap
        r = pdk.Deck(layers=[], initial_view_state=view_state, map_style="mapbox://styles/mapbox/light-v10", mapbox_key=None)
        st.pydeck_chart(r)
