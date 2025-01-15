import geopandas as gpd
import dask.dataframe as dd
from dask import delayed
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import warnings
import streamlit as st

# Configurações da página
st.set_page_config(
    page_title="Consulta de balanço hídrico",
    page_icon="	:droplet:",
    layout="wide",
    initial_sidebar_state='collapsed'
)

col1, col2, col3 = st.columns([1,5,1], vertical_alignment="center")
