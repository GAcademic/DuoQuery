import pandas as pd
import streamlit as st

from db import is_select, run_query

def render_query_tab():
    st.subheader("Ejecutar consulta")

    query = st.text_area(
        "Consulta SQL",
        "SELECT film_id, title, release_year FROM film LIMIT 10;",
        height=180,
        key="query_sql",
    )

    ejecutar = st.button("Ejecutar consulta", key="run_query")

    if ejecutar:
        try:
            if not is_select(query):
                st.error("Solo se permiten sentencias SELECT.")
            else:
                result = run_query(query)

                if result is None:
                    st.success("Consulta ejecutada correctamente, pero no devolvió filas.")
                else:
                    columns, rows = result
                    df = pd.DataFrame(rows, columns=columns)
                    st.dataframe(df, use_container_width=True)
                    st.metric("Filas devueltas", len(df))
        except Exception as e:
            st.error(f"Error ejecutando la consulta: {e}")

