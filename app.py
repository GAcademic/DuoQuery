import streamlit as st
import pandas as pd
from db import get_conn

st.title("DuoQuery")
st.write("Versión mínima funcional con PostgreSQL y Streamlit.")

query = st.text_area("Consulta SQL", "SELECT 1;")

if st.button("Ejecutar"):
    try:
        conn = get_conn()
        df = pd.read_sql_query(query, conn)
        st.dataframe(df)
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")
