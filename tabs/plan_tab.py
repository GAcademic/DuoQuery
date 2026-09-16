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


import pandas as pd
import streamlit as st
from collections import Counter

from db import is_select, run_explain


# Colores de fondo por tipo de nodo del plan de ejecución (EXPLAIN).
# Es un diccionario (Tipo de nodo -> color) 
NODE_TYPE_COLORS = {
    "Seq Scan": "#ffdddd",          # rojo suave: escaneo secuencial (posible anti-patron)
    "Index Scan": "#ddffdd",        # verde: escaneo por índice
    "Index Only Scan": "#ddffdd",   # verde: variante de escaneo por índice
    "Bitmap Heap Scan": "#ddffdd",  # verde: también se apoya en un índice
    "Nested Loop": "#fff4cc",       # amarillo: join anidado
    "Hash Join": "#ddeeff",         # azul: join por hash
    "Merge Join": "#eee0ff",        # morado: join por mezcla (merge)
}


def highlight_node_types(row):
    """
    Devuelve el estilo CSS para colorear la fila completa de la tabla de nodos
    según su Node Type, usando NODE_TYPE_COLORS. Permite detectar de un
    vistazo escaneos costosos o el tipo de join sin leer cada fila.
    """
    color = NODE_TYPE_COLORS.get(row["Node Type"], "")
    style = f"background-color: {color}" if color else ""
    return [style] * len(row)


def render_node_legend():
    """
    Construye la leyenda de colores del plan a partir de NODE_TYPE_COLORS,
    para que solo haya un sitio (el diccionario) donde tocar los colores.
    Agrupa los tipos de nodo que comparten color en una misma línea.
    """
    color_to_labels = {}
    for node_type, color in NODE_TYPE_COLORS.items():
        color_to_labels.setdefault(color, []).append(node_type)

    lines = []
    for color, labels in color_to_labels.items():
        label = " / ".join(labels)
        lines.append(
            f'<span style="background-color:{color};padding:2px 10px;">&nbsp;</span> {label}'
        )

    st.markdown("<br>".join(lines), unsafe_allow_html=True)


# Mensajes de ayuda por tipo de nodo 
# Explican el tipo de nodo y lo que implica cada uno.
# Se usa dentro de walk().
NODE_ALERTS = {
    "Seq Scan": "Se detectó un Seq Scan. PostgreSQL recorre la tabla secuencialmente; en tablas grandes sin un filtro selectivo o un LIMIT que lo detenga, puede leerla entera.",
    "Nested Loop": "Se detectó un Nested Loop. Puede ser eficiente con pocas filas, pero costoso con conjuntos de datos grandes.",
    "Hash Join": "Se detectó un Hash Join. PostgreSQL crea una tabla hash para realizar la unión.",
    "Merge Join": "Se detectó un Merge Join. PostgreSQL une resultados previamente ordenados.",
}


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
            "Actual Rows": node.get("Actual Rows"),
            "Actual Total Time": node.get("Actual Total Time"),
            "Actual Loops": node.get("Actual Loops", node.get("Loops")),
            "Filter": node.get("Filter"),
            "Index Cond": node.get("Index Cond"),
            "Join Filter": node.get("Join Filter"),
        })
        counter[node_type] += 1

        message = NODE_ALERTS.get(node_type)
        if message:
            alerts.append(message)

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
    st.markdown(
        """
**EXPLAIN** muestra el plan que PostgreSQL cree que va a usar, sin ejecutar la consulta.  
**EXPLAIN ANALYZE** ejecuta la consulta y añade tiempos y filas reales.
        """
    )

    modo_plan = st.selectbox(
        "Tipo de plan",
        ["EXPLAIN", "EXPLAIN ANALYZE"],
        key="modo_plan",
    )

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
                render_node_legend()
                nodes_df = pd.DataFrame(summary["nodes"])
                st.dataframe(
                    nodes_df.style.apply(highlight_node_types, axis=1),
                    use_container_width=True,
                )


                st.markdown("### Tipos de nodo detectados")
                df_counts = pd.DataFrame(
                    [{"Node Type": k, "Count": v} for k, v in summary["counter"].items()]
                ).sort_values("Count", ascending=False)
                st.dataframe(df_counts, use_container_width=True)

                with st.expander("Ver JSON completo del plan"):
                    st.json(plan)

        except Exception as e:
            st.error(f"Error analizando el plan: {e}")
