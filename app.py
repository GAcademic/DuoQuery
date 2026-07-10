
import pandas as pd
import streamlit as st
from collections import Counter

from db import run_query, run_explain, is_select
from schema import get_schema_summary, get_table_names, get_table_detail

st.set_page_config(page_title="DuoQuery", layout="wide")
st.title("DuoQuery")
st.write("Herramienta didáctica para ejecutar consultas SQL, analizar planes y explorar el esquema.")

def extract_plan_summary(plan_json):
    root = plan_json[0]["Plan"]
    nodes = []
    counter = Counter()
    alerts = []

    def walk(node, depth=0):
        node_type = node.get("Node Type", "Unknown")
        nodes.append({
            "Depth": depth,
            "Node Type": node_type,
            "Plan Rows": node.get("Plan Rows"),
            "Actual Rows": node.get("Actual Rows"),
            "Actual Total Time": node.get("Actual Total Time"),
            "Actual Loops": node.get("Actual Loops", node.get("Loops")),
            "Shared Hit Blocks": node.get("Shared Hit Blocks"),
            "Shared Read Blocks": node.get("Shared Read Blocks"),
        })
        counter[node_type] += 1

        if node_type == "Seq Scan":
            alerts.append("Se detectó un Seq Scan.")
        if node_type == "Nested Loop":
            alerts.append("Se detectó un Nested Loop.")

        for child in node.get("Plans", []):
            walk(child, depth + 1)

    walk(root)

    estimated_rows = root.get("Plan Rows")
    actual_rows = root.get("Actual Rows")
    row_diff = None
    row_ratio = None
    if estimated_rows is not None and actual_rows is not None:
        row_diff = actual_rows - estimated_rows
        row_ratio = (actual_rows / estimated_rows) if estimated_rows else None

    return {
        "nodes": nodes,
        "counter": counter,
        "alerts": sorted(set(alerts)),
        "root_type": root.get("Node Type", "Unknown"),
        "total_time": root.get("Actual Total Time"),
        "estimated_rows": estimated_rows,
        "actual_rows": actual_rows,
        "row_diff": row_diff,
        "row_ratio": row_ratio,
    }

tab_query, tab_plan, tab_schema = st.tabs(["Consulta", "Plan", "Esquema"])

with tab_query:
    st.subheader("Ejecutar consulta")
    query = st.text_area(
        "Consulta SQL",
        "SELECT film_id, title, release_year FROM film LIMIT 10;",
        height=180,
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

with tab_plan:
    st.subheader("Plan de ejecución")
    query_plan = st.text_area(
        "Consulta para analizar",
        "SELECT film_id, title, release_year FROM film LIMIT 10;",
        height=180,
        key="query_plan",
    )
    ejecutar_plan = st.button("Analizar plan", key="run_plan")

    if ejecutar_plan:
        try:
            if not is_select(query_plan):
                st.error("Solo se permiten sentencias SELECT.")
            else:
                plan = run_explain(query_plan)
                summary = extract_plan_summary(plan)

                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Nodo raíz", summary["root_type"])
                c2.metric(
                    "Tiempo total",
                    f'{summary["total_time"]:.3f} ms' if summary["total_time"] is not None else "N/D",
                )
                c3.metric(
                    "Filas estimadas",
                    summary["estimated_rows"] if summary["estimated_rows"] is not None else "N/D",
                )
                c4.metric(
                    "Filas reales",
                    summary["actual_rows"] if summary["actual_rows"] is not None else "N/D",
                )

                if summary["row_diff"] is not None:
                    extra = f" | Ratio real/estimado: {summary['row_ratio']:.2f}" if summary["row_ratio"] is not None else ""
                    st.info(f"Diferencia entre filas reales y estimadas: {summary['row_diff']}{extra}")

                if summary["alerts"]:
                    st.warning(" | ".join(summary["alerts"]))

                st.markdown("### Resumen de nodos")
                st.dataframe(pd.DataFrame(summary["nodes"]), use_container_width=True)

                st.markdown("### Tipos de nodo detectados")
                df_counts = pd.DataFrame(
                    [{"Node Type": k, "Count": v} for k, v in summary["counter"].items()]
                ).sort_values("Count", ascending=False)
                st.dataframe(df_counts, use_container_width=True)

                with st.expander("Ver JSON completo del plan"):
                    st.json(plan)
        except Exception as e:
            st.error(f"Error analizando el plan: {e}")

with tab_schema:
    st.subheader("Esquema de la base de datos")
    st.caption("Vista básica: tabla, clave primaria, columnas y claves foráneas.")

    summary_df = get_schema_summary()
    if summary_df is not None and not summary_df.empty:
        st.markdown("### Resumen del esquema")
        st.dataframe(summary_df, use_container_width=True)

    st.markdown("### Tablas")
    table_names = get_table_names()

    for table_name in table_names:
        detail = get_table_detail(table_name)

        with st.expander(table_name, expanded=False):
            st.markdown("**Clave primaria**")
            pk = detail.get("primary_key")
            if pk:
                st.write(f"{pk['constraint_name']}: {', '.join(pk['columns'])}")
            else:
                st.write("No definida")

            st.markdown("**Columnas y tipo**")
            cols = detail.get("columns", [])
            if cols:
                cols_df = pd.DataFrame(cols)[["column_name", "data_type"]]
                cols_df.columns = ["column_name", "data_type"]
                st.dataframe(cols_df, use_container_width=True, hide_index=True)
            else:
                st.write("Sin columnas.")

            st.markdown("**Claves foráneas**")
            fks = detail.get("foreign_keys", [])
            if fks:
                fk_rows = []
                for fk in fks:
                    for item in fk["columns"]:
                        fk_rows.append({
                            "constraint_name": fk["constraint_name"],
                            "column_name": item["column_name"],
                            "referenced_table": item["referenced_table"],
                            "referenced_column": item["referenced_column"],
                        })
                fk_df = pd.DataFrame(fk_rows)
                st.dataframe(fk_df, use_container_width=True, hide_index=True)
            else:
                st.write("No definidas.")

