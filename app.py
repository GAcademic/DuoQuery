import json
from collections import Counter
import streamlit as st
import pandas as pd
from db import run_query, run_explain, is_select

st.set_page_config(page_title="DuoQuery", layout="wide")

def extract_plan_summary(plan_json):
    root = plan_json[0]["Plan"]
    nodes = []
    counter = Counter()
    alerts = []

    def walk(node, depth=0):
        node_type = node.get("Node Type", "Unknown")
        actual_rows = node.get("Actual Rows")
        actual_time = node.get("Actual Total Time")
        plan_rows = node.get("Plan Rows")
        loops = node.get("Actual Loops", node.get("Loops"))
        shared_hit = node.get("Shared Hit Blocks")
        shared_read = node.get("Shared Read Blocks")

        nodes.append({
            "Depth": depth,
            "Node Type": node_type,
            "Actual Rows": actual_rows,
            "Plan Rows": plan_rows,
            "Actual Total Time": actual_time,
            "Loops": loops,
            "Shared Hit Blocks": shared_hit,
            "Shared Read Blocks": shared_read,
        })
        counter[node_type] += 1

        if node_type == "Seq Scan":
            alerts.append("Se detectó un Seq Scan.")
        if node_type == "Nested Loop":
            alerts.append("Se detectó un Nested Loop.")

        for child in node.get("Plans", []):
            walk(child, depth + 1)

    walk(root)

    total_time = root.get("Actual Total Time")
    total_rows = root.get("Actual Rows")
    return {
        "nodes": nodes,
        "counter": counter,
        "alerts": sorted(set(alerts)),
        "total_time": total_time,
        "total_rows": total_rows,
        "root_type": root.get("Node Type", "Unknown"),
    }

st.title("DuoQuery")
st.write("Herramienta didáctica para analizar y optimizar consultas SQL en PostgreSQL.")

modo = st.selectbox(
    "Selecciona el modo",
    ["Ejecutar consulta", "Ver plan de ejecución"]
)

query = st.text_area(
    "Consulta SQL",
    "SELECT film_id, title, release_year FROM film LIMIT 10;"
)

col1, col2 = st.columns([1, 3])
with col1:
    ejecutar = st.button("Ejecutar")

with col2:
    st.caption("Solo se permiten sentencias SELECT.")

if ejecutar:
    try:
        if not is_select(query):
            st.error("Solo se permiten sentencias SELECT.")
        elif modo == "Ejecutar consulta":
            result = run_query(query)

            if result is None:
                st.success("Consulta ejecutada correctamente, pero no devolvió filas.")
            else:
                columns, rows = result
                df = pd.DataFrame(rows, columns=columns)
                st.dataframe(df, use_container_width=True)
                st.write(f"Filas devueltas: {len(df)}")
        else:
            plan = run_explain(query)
            summary = extract_plan_summary(plan)

            m1, m2, m3 = st.columns(3)
            m1.metric("Nodo raíz", summary["root_type"])
            m2.metric("Filas reales", summary["total_rows"] if summary["total_rows"] is not None else "N/D")
            m3.metric("Tiempo total", f'{summary["total_time"]:.3f} ms' if summary["total_time"] is not None else "N/D")

            if summary["alerts"]:
                st.warning(" | ".join(summary["alerts"]))

            st.subheader("Resumen de nodos")
            df_nodes = pd.DataFrame(summary["nodes"])
            st.dataframe(df_nodes, use_container_width=True)

            st.subheader("Tipos de nodo detectados")
            df_counts = pd.DataFrame(
                [{"Node Type": k, "Count": v} for k, v in summary["counter"].items()]
            ).sort_values("Count", ascending=False)
            st.dataframe(df_counts, use_container_width=True)

            with st.expander("Ver JSON completo del plan"):
                st.json(plan)

    except Exception as e:
        st.error(f"Error: {e}")
