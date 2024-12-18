# Caminho do arquivo de grandes bacias
caminho_arquivo = '/content/drive/MyDrive/bacias/bacias/Bacia_Hidrografica.shp'

# Carregar o shapefile das grandes bacias
bacias = gpd.read_file(caminho_arquivo)
bacias = bacias.to_crs(epsg=4326)  # Reprojetar para EPSG:4326

# Função para encontrar a grande bacia
def encontrar_bacia(lat, lon):
    ponto = Point(lon, lat)  # Criar ponto
    for index, bacia in bacias.iterrows():
        if bacia['geometry'].contains(ponto):
            return bacia['nome']  # Substituir pela coluna desejada
    return 'Ponto fora das bacias definidas'

# Coordenadas do ponto
latitude = -29.9673
longitude = -51.1704

# Encontrar a grande bacia
bacia = encontrar_bacia(latitude, longitude)
print(f'A grande bacia para as coordenadas ({latitude}, {longitude}) é: {bacia}')

# Dicionário das grandes bacias e caminhos para as mini bacias
dic_cod_bacia = {
    'gravataí': "/content/drive/MyDrive/bacias/mini_bacias/G010_mini_19_02.shp",
    'sinos': "/content/drive/MyDrive/bacias/mini_bacias/G020_mini_19_02.shp",
    # Adicionar todas as bacias conforme necessário...
}

# Inicializar variáveis
bacia_encontrada = None
numero_mini_bacia = None

# Identificar grande bacia e verificar mini bacias
for nome_bacia, caminho_bacia in dic_cod_bacia.items():
    try:
        bacia_gdf = gpd.read_file(caminho_bacia)
        if bacia_gdf.geometry.contains(Point(longitude, latitude)).any():
            bacia_encontrada = nome_bacia
            break
    except Exception as e:
        print(f"Erro ao carregar a bacia {nome_bacia}: {e}")

# Encontrar mini bacia dentro da grande bacia
if bacia_encontrada:
    print(f"O ponto está dentro da grande bacia: {bacia_encontrada}")
    try:
        bacia_grande = gpd.read_file(dic_cod_bacia[bacia_encontrada])
        mini_bacias = bacia_grande[bacia_grande.geometry.contains(Point(longitude, latitude))]
        if not mini_bacias.empty:
            numero_mini_bacia = mini_bacias.iloc[0]['Mini']  # Ajuste conforme o nome da coluna
            print(f"O ponto está dentro da mini bacia com o número: {numero_mini_bacia}.")
        else:
            print("O ponto não está dentro de nenhuma mini bacia dessa grande bacia.")
    except Exception as e:
        print(f"Erro ao carregar a grande bacia {bacia_encontrada}: {e}")
else:
    print("O ponto não está dentro de nenhuma grande bacia.")

# Função recursiva para buscar as bacias a montante
relacionamento_bacias = []

def buscar_montante(numero_mini_bacia):
    try:
        bacia_grande = gpd.read_file(dic_cod_bacia[bacia_encontrada])
        mini_bacias_montante = bacia_grande[bacia_grande['MiniJus'] == numero_mini_bacia]
        if not mini_bacias_montante.empty:
            for _, row in mini_bacias_montante.iterrows():
                mini_bacia_montante = row['Mini']
                relacionamento_bacias.append((numero_mini_bacia, mini_bacia_montante))
                buscar_montante(mini_bacia_montante)
    except Exception as e:
        print(f"Erro ao buscar montante para a mini bacia {numero_mini_bacia}: {e}")

# Buscar a montante para a mini bacia inicial
if numero_mini_bacia:
    buscar_montante(numero_mini_bacia)

# Criar DataFrame com as relações
df_relacionamento = pd.DataFrame(relacionamento_bacias, columns=['Mini Bacia Atual', 'Mini Bacia Montante'])
print(df_relacionamento)
