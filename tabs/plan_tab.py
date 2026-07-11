import pandas as pd
import streamlit as st
from collections import Counter

from db import is_select, run_explain

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
            "Relation Name": node.get("Relation Name"),
            "Index Name": node.get("Index Name"),
            "Startup Cost": node.get("Startup Cost"),
            "Total Cost": node.get("Total Cost"),
            "Plan Rows": node.get("Plan Rows"),
            "Plan Width": node.get("Plan Width"),
            "Actual Startup Time": node.get("Actual Startup Time"),
            "Actual Total Time": node.get("Actual Total Time"),
            "Actual Rows": node.get("Actual Rows"),
            "Actual Loops": node.get("Actual Loops", node.get("Loops")),
            "Filter": node.get("Filter"),
            "Index Cond": node.get("Index Cond"),
            "Join Filter": node.get("Join Filter"),
        })
        counter[node_type] += 1

        if node_type == "Seq Scan":
            alerts.append("Se detectó un Seq Scan.")
        if node_type == "Nested Loop":
            alerts.append("Se detectó un Nested Loop.")
        if node_type == "Hash Join":
            alerts.append("Se detectó un Hash Join.")
        if node_type == "Merge Join":
            alerts.append("Se detectó un Merge Join.")

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

def render_plan_tab():
    st.subheader("Plan de ejecución")
    st.caption("EXPLAIN muestra el plan estimado. EXPLAIN ANALYZE ejecuta la consulta y añade tiempos y filas reales.")

    query_plan = st.text_area(
        "Consulta para analizar",
        "SELECT film_id, title, release_year FROM film LIMIT 10;",
        height=180,
        key="query_plan",
    )

    modo_plan = st.selectbox(
        "Tipo de plan",
        ["EXPLAIN", "EXPLAIN ANALYZE"],
        key="modo_plan",
    )

    ejecutar_plan = st.button("Analizar plan", key="run_plan")

    if ejecutar_plan:
        try:
            if not is_select(query_plan):
                st.error("Solo se permiten sentencias SELECT.")
            else:
                plan = run_explain(
                    query_plan,
                    analyze=(modo_plan == "EXPLAIN ANALYZE"),
                    buffers=True,
                    verbose=True,
                    format_json=True,
                )
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

                if modo_plan == "EXPLAIN":
                    st.info("EXPLAIN muestra el plan previsto por PostgreSQL sin ejecutar la consulta.")
                else:
                    st.info("EXPLAIN ANALYZE ejecuta la consulta y añade métricas reales del recorrido.")

                if summary["row_diff"] is not None:
                    extra = f" | Ratio real/estimado: {summary['row_ratio']:.2f}" if summary["row_ratio"] is not None else ""
                    st.warning(f"Diferencia entre filas reales y estimadas: {summary['row_diff']}{extra}")

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

