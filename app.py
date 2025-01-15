from google.colab import drive
import geopandas as gpd
import pyogrio  # ou 'fiona'
from shapely.geometry import Point
import glob
import dask.dataframe as dd
from dask import delayed
import geopandas as gpd
from shapely.geometry import Point
import pandas as pd
import matplotlib.pyplot as plt
import pyogrio
import matplotlib.patches as mpatches
import warnings
import zipfile
import os

# Configurações da página
st.set_page_config(
    page_title="Consulta de balanço hídrico",
    page_icon="	:droplet:",
    layout="wide",
    initial_sidebar_state='collapsed'
)

col1, col2, col3 = st.columns([1,5,1], vertical_alignment="center")
