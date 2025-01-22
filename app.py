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
    page_title="Disponibilidade Hídrica para Outórga",
    page_icon=":world_map:",
    layout="wide"
)

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
st.markdown("<h1 style='text-align: center;'>Disponibilidade Hídrica para Outórga</h1>", unsafe_allow_html=True)

# Layout de colunas para as entradas (latitude e longitude) à esquerda e o mapa à direita
col1, col2 = st.columns([1, 2])  # A primeira coluna (1) para as entradas e a segunda (2) para o mapa

# Entradas de latitude, longitude e área
with col1:
    latitude_input = st.text_input("Latitude", placeholder="Insira uma latitude")
    longitude_input = st.text_input("Longitude", placeholder="Insira uma longitude")
    area_input = st.text_input("Área (em km²)", placeholder="Insira a área em km²")
    enviar = st.button("Exibir no Mapa")

# Inicializar o mapa centralizado no Rio Grande do Sul
mapa = folium.Map(location=[-30.0, -52.5], zoom_start=6.5)

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

                    # Destacar a unidade que contém o ponto e exibir a UPG
                    unidade_encontrada = None
                    for _, row in gdf.iterrows():
                        if row['geometry'].contains(ponto):
                            # Destacar a unidade
                            folium.GeoJson(
                                row['geometry'].__geo_interface__,
                                style_function=lambda x: {'fillColor': 'blue', 'color': 'blue', 'weight': 2, 'fillOpacity': 0.5}
                            ).add_to(mapa)
                            unidade_encontrada = row['ID_Balanco']  # Armazenar o ID_Balanco
                            break

                    if unidade_encontrada:
                        # Carregar a planilha para fazer o cruzamento com a coluna ID_Balanco
                        tabela_path = "tabela_id_balanco.xlsx"  # Caminho para a planilha
                        tabela_df = pd.read_excel(tabela_path)

                        # Procurar o valor correspondente à unidade
                        unidade_data = tabela_df[tabela_df['ID_Balanco'] == unidade_encontrada]

                            if not unidade_data.empty:
                                try:
                                    area_qesp_rio = unidade_data.get('area_qesp_rio', pd.NA).values[0]
                                    area_drenagem = unidade_data.get('Área de drenagem (km²)', pd.NA).values[0]
    
                                # Validar se área de drenagem está presente
                                if pd.isna(area_drenagem):
                                    col1.error("Área de drenagem não disponível para essa unidade.")
                                else:
                                    # Tratamento para quando area_qesp_rio for NaN
                                    if pd.isna(area_qesp_rio):
                                        if area > 10:
                                            qesp_valor = unidade_data.get('Qesp_maior10', pd.NA).values[0]
                                        else:
                                            qesp_valor = unidade_data.get('Qesp_menor10', pd.NA).values[0]
                                    else:
                                        if area > area_qesp_rio:
                                            qesp_valor = unidade_data.get('Qesp_rio', pd.NA).values[0]
                                        else:
                                            if area > 10:
                                                qesp_valor = unidade_data.get('Qesp_maior10', pd.NA).values[0]
                                            else:
                                                qesp_valor = unidade_data.get('Qesp_menor10', pd.NA).values[0]
                        
                                    # Verificar se o valor da Qesp foi calculado corretamente
                                    if pd.isna(qesp_valor):
                                        col1.error("Valor da Qesp não disponível para essa unidade.")
                                    else:
                                        # Calcular valor multiplicado pela área de drenagem
                                        valor_m3_s = qesp_valor * area_drenagem
                                        col1.success(f"A UPG da sua localidade é {unidade_encontrada}")
                                        col1.success(f"A Vazão de referência para sua localidade é: {valor_m3_s:.10f} m³/s")
                            except Exception as e:
                                col1.error(f"Erro no cálculo dos valores: {e}")
                    else:
                        col1.warning("Nenhum dado encontrado para o ID_Balanco.")

                            if pd.isna(area_qesp_rio):
                                # Se a coluna "area_qesp_rio" estiver em branco
                                if area > 10:
                                    qesp_valor = unidade_data['Qesp_maior10'].values[0]
                                else:
                                    qesp_valor = unidade_data['Qesp_menor10'].values[0]
                            else:
                                # Se a coluna "area_qesp_rio" não estiver em branco
                                if area > area_qesp_rio:
                                    qesp_valor = unidade_data['Qesp_rio'].values[0]
                                else:
                                    if area > 10:
                                        qesp_valor = unidade_data['Qesp_maior10'].values[0]
                                    else:
                                        qesp_valor = unidade_data['Qesp_menor10'].values[0]

                            # Cálculo do valor em m³/s
                            valor_m3_s = qesp_valor * area_drenagem

                            # Retornar o valor calculado
                            col1.success(f"A Vazão de referência para a sua localidade é: {valor_m3_s:.8f} m³/s")
                        else:
                            col1.warning("ID_Balanco não encontrado na planilha.")
                    else:
                        col1.warning("Não foi possível encontrar uma unidade correspondente à coordenada inserida.")
            except Exception as e:
                col1.error(f"Erro ao carregar o shapefile: {e}")
        else:
            col1.warning("As coordenadas estão fora dos limites do Rio Grande do Sul.")
    except ValueError:
        col1.error("Por favor, insira valores numéricos válidos para latitude, longitude e área.")

# Renderizar o mapa no Streamlit
mapa_html = mapa._repr_html_()
with col2:
    html(mapa_html, width=1000, height=600)  # Renderiza o mapa na segunda coluna


