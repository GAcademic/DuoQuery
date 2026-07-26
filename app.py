import streamlit as st

from tabs.query_tab import render_query_tab
from tabs.plan_tab import render_plan_tab
from tabs.energy_tab import render_energy_tab
from tabs.comparison_tab import render_comparison_tab
from tabs.schema_tab import render_schema_tab

st.set_page_config(page_title="DuoQuery", layout="wide")
st.title("DuoQuery")
st.write("Herramienta didáctica para ejecutar consultas SQL, analizar planes y explorar el esquema.")

tab_query, tab_plan, tab_energy, tab_comparison, tab_schema = st.tabs(
    ["Consulta", "Plan", "Energía", "Comparativa", "Esquema"]
)

with tab_query:
    render_query_tab()

with tab_plan:
    render_plan_tab()

with tab_energy:
    render_energy_tab()

with tab_comparison:
    render_comparison_tab()

with tab_schema:
    render_schema_tab()

