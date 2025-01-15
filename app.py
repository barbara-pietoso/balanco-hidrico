import pandas as pd 
import geopandas as gpd
import plotly.express as px
import streamlit as st
import plotly.graph_objects as go
import requests
import folium
from streamlit_folium import st_folium, folium_static
import altair as alt
from unidecode import unidecode
import textwrap
import extra_streamlit_components as stx
from streamlit_echarts import st_echarts
import math

# Configurações da página
st.set_page_config(
    page_title="Consulta de balanço hídrico",
    page_icon="	:droplet:",
    layout="wide",
    initial_sidebar_state='collapsed'
)

col1, col2, col3 = st.columns([1,5,1], vertical_alignment="center")
