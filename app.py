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
                            area_qesp_rio = unidade_data['area_qesp_rio'].values[0]

                            if pd.isna(area_qesp_rio):
                                # Se a coluna "area_qesp_rio" estiver em branco
                                if area > 10:
                                    qesp_valor = unidade_data['Qesp_maior10'].values[0]
                                else:
                                    qesp_valor = unidade_data['Qesp_menor10'].values[0]
                                col1.success(f"O valor da Qesp para a sua localidade é: {qesp_valor}")
                            else:
                                # Se a coluna "area_qesp_rio" não estiver em branco
                                if area > area_qesp_rio:
                                    # Se a área inserida for maior que a área da unidade
                                    qesp_valor = unidade_data['Qesp_rio'].values[0]
                                    col1.success(f"O valor de Qesp para sua área é: {qesp_valor}")
                                else:
                                    # Se a área inserida for menor ou igual à área da unidade
                                    if area > 10:
                                        qesp_valor = unidade_data['Qesp_maior10'].values[0]
                                    else:
                                        qesp_valor = unidade_data['Qesp_menor10'].values[0]
                                    col1.success(f"O valor da Qesp para a sua localidade é: {qesp_valor}")
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

