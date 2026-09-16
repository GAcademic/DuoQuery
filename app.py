# DuoQuery - Estimación energética de consultas SQL
# Copyright (C) 2026  Eva Molina Jiménez
#
# Trabajo Fin de Estudios - Grado en Ingeniería Informática
# Universidad Internacional de La Rioja (UNIR)
#
# Este archivo forma parte de DuoQuery.
#
# DuoQuery es software libre: puede redistribuirlo y/o modificarlo
# bajo los términos de la GNU Affero General Public License publicada
# por la Free Software Foundation, ya sea la versión 3 de la licencia
# o (a su elección) cualquier versión posterior.
#
# DuoQuery se distribuye con la esperanza de que resulte útil, pero
# SIN NINGUNA GARANTÍA; ni siquiera la garantía implícita de
# COMERCIABILIDAD o IDONEIDAD PARA UN PROPÓSITO PARTICULAR. Consulte
# la GNU Affero General Public License para más detalles.
#
# Debería haber recibido una copia de la GNU Affero General Public
# License junto con DuoQuery. Si no, véase <https://www.gnu.org/licenses/>.


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

