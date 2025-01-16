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

col1, col2, col3 = st.columns([1, 5, 1], vertical_alignment="center")

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
zip_url = "https://github.com/barbara-pietoso/balanco-hidrico/raw/main/Unidades_BH_RS.zip"

# Inicializar o mapa padrão com as coordenadas centrais do Rio Grande do Sul
mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)

# Inicializar uma variável para armazenar o texto a ser exibido
informacao_upg = ""
qout = None

# Função para calcular Qout
def calcular_qout(qesp, area, perc_out):
    return qesp * area * perc_out

# Atualizar o mapa com as coordenadas inseridas
if enviar:
    if latitude is not None and longitude is not None and area is not None:
        if valida_coordenadas(latitude, longitude):
            col2.write(f"Coordenadas inseridas: {latitude}, {longitude}")
            col2.write(f"Área inserida: {area} km²")
            
            # Criar o mapa usando o Folium com as coordenadas inseridas
            mapa = folium.Map(location=[latitude, longitude], zoom_start=12)

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

                        # Verificar se a coluna 'ID_balanco' existe no shapefile
                        if 'ID_balanco' not in gdf.columns:
                            col2.write("A coluna 'ID_Balanco' não foi encontrada no shapefile.")
                        else:
                            # Adicionar o arquivo GeoDataFrame ao mapa
                            folium.GeoJson(gdf.__geo_interface__).add_to(mapa)

                            # Criar um ponto com as coordenadas inseridas
                            ponto = Point(longitude, latitude)

                            # Verificar se o ponto está dentro de algum polígono
                            for _, row in gdf.iterrows():
                                if row['geometry'].contains(ponto):  # Verifica se o ponto está dentro do polígono
                                    informacao_upg = f"UPG: {row['UPG']}"
                                    id_balanco = row['ID_Balanco']  # Pega o ID_balanco
                                    break
                            else:
                                informacao_upg = "O ponto inserido não está dentro de nenhuma unidade."
                                id_balanco = None

                            # Se o ID_balanco for encontrado, buscar as informações na tabela_dados
                            if id_balanco:
                                # Supondo que a tabela_dados seja um DataFrame que já foi carregado
                                tabela_dados = pd.read_csv("tabela_dados.csv")  # Carregar a tabela_dados

                                # Filtrar os dados pela ID_balanco
                                dados_filtrados = tabela_dados[tabela_dados['ID_balanco'] == id_balanco]

                                if not dados_filtrados.empty:
                                    qesp = dados_filtrados.iloc[0]['Qesp']
                                    perc_out = dados_filtrados.iloc[0]['perc_out']

                                    # Calcular Qout
                                    qout = calcular_qout(qesp, area, perc_out)
                                    informacao_upg += f"\nQesp: {qesp}\nPerc Out: {perc_out}\nQout: {qout}"
                                else:
                                    informacao_upg += "\nNão foram encontrados dados para o ID_Balanco."

            except requests.exceptions.RequestException as e:
                col2.write(f"Erro ao carregar o arquivo SHP: {e}")
            except Exception as e:
                col2.write(f"Erro ao baixar ou extrair os arquivos: {e}")
        else:
            col2.write("As coordenadas inseridas estão fora dos limites do Rio Grande do Sul.")
            # Criar o mapa padrão quando as coordenadas não são válidas
            mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)
            col2.write("Mapa centralizado no Rio Grande do Sul.")
            # Adicionar um marcador no mapa
            folium.Marker([default_latitude, default_longitude], popup="Centro do Rio Grande do Sul").add_to(mapa)
    else:
        col2.write("Por favor, insira as coordenadas e a área corretamente.")
        # Criar o mapa padrão
        mapa = folium.Map(location=[default_latitude, default_longitude], zoom_start=7)
        # Adicionar um marcador no mapa
        folium.Marker([default_latitude, default_longitude], popup="Centro do Rio Grande do Sul").add_to(mapa)

# Exibir a informação da coluna 'UPG' e o cálculo de Qout
col2.write(informacao_upg)

# Salvar o mapa como HTML e exibi-lo no Streamlit
mapa_html = mapa._repr_html_()
html(mapa_html, height=500)



