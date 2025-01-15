import pandas as pd
import geopandas as gpd
import folium
import requests
import zipfile
import tempfile
from io import BytesIO
import streamlit as st
from streamlit_folium import st_folium

# Limites aproximados de latitude e longitude do Rio Grande do Sul
LAT_MIN = -34.0  # Latitude mínima
LAT_MAX = -28.0  # Latitude máxima
LON_MIN = -54.5  # Longitude mínima
LON_MAX = -49.0  # Longitude máxima

# Função para validar se as coordenadas estão dentro dos limites do Rio Grande do Sul
def valida_coordenadas(latitude, longitude):
    return LAT_MIN <= latitude <= LAT_MAX and LON_MIN <= longitude <= LON_MAX

# Função para baixar e extrair arquivos ZIP
def download_and_extract_zip(url):
    try:
        # Baixar o arquivo
        st.write(f"Baixando o arquivo de {url}...")
        response = requests.get(url)
        response.raise_for_status()  # Garante que a resposta seja bem-sucedida (status 200)
        
        # Salvar o arquivo em uma pasta temporária
        temp_dir = tempfile.mkdtemp()
        zip_path = temp_dir + "/shapefile.zip"
        
        with open(zip_path, 'wb') as f:
            f.write(response.content)
        
        st.write(f"Arquivo baixado com sucesso para {zip_path}")

        # Extrair o arquivo ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(temp_dir)

        # Retornar o caminho da pasta onde os arquivos foram extraídos
        return temp_dir
    
    except requests.exceptions.RequestException as e:
        st.error(f"Erro ao baixar o arquivo: {e}")
        return None

# URL do arquivo shapefile zipado
shp_url = "https://github.com/barbara-pietoso/balanco-hidrico/raw/main/Unidades_BH_RS.zip"

# Função principal
def main():
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

                # Baixar e extrair o shapefile
                shapefile_dir = download_and_extract_zip(shp_url)

                if shapefile_dir:
                    # Caminho do shapefile extraído
                    shapefile_path = shapefile_dir + "/Unidades_BH_RS.shp"
                    
                    try:
                        # Ler o shapefile com Geopandas
                        gdf = gpd.read_file(shapefile_path)
                        
                        # Adicionar o arquivo GeoDataFrame ao mapa
                        folium.GeoJson(gdf.__geo_interface__).add_to(mapa)

                        # Adicionar um marcador no mapa
                        folium.Marker([latitude, longitude], popup="Coordenadas Inseridas").add_to(mapa)
                    except Exception as e:
                        col2.write(f"Erro ao processar o arquivo SHP: {e}")
                else:
                    col2.write("Erro ao baixar ou extrair os arquivos.")
            else:
                col2.write("As coordenadas inseridas estão fora dos limites do Rio Grande do Sul.")
                # Criar mapa centralizado no centro do Rio Grande do Sul em caso de erro
                mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)
        else:
            col2.write("Por favor, insira as coordenadas corretamente.")
            mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)

    # Exibir o mapa no Streamlit
    st_folium(mapa, width=700, height=500)

if __name__ == "__main__":
    main()
