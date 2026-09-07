import streamlit as st

from db import is_select
from estimation import estimar_consulta
from energy.model import FACTORES_EMISION, PAIS_POR_DEFECTO
from validation.benchmark_queries import PAREJAS_DIDACTICAS, QUERIES_POR_ID


def render_comparison_tab():
    st.subheader("Comparativa de consultas")
    st.markdown(
        "Compara el impacto energético, las emisiones de CO₂e, el tráfico de "
        "datos estimado y el trabajo desperdiciado entre dos consultas SQL."
    )

    # Factor de emisión según el país.
    paises = sorted(FACTORES_EMISION.keys())
    pais = st.selectbox(
        "País (factor de emisión de la red eléctrica)",
        paises,
        index=paises.index(PAIS_POR_DEFECTO),
        key="pais_comp",
    )
    factor_emision, fuente = FACTORES_EMISION[pais]
    st.caption(f"Factor seleccionado: {factor_emision} kg CO₂e/kWh · Fuente: {fuente}")

    modo = st.radio(
        "Modo",
        ["Didáctico", "Libre"],
        horizontal=True,
        key="modo_comp",
    )

    explicacion = None

    if modo == "Didáctico":
        indices = list(range(len(PAREJAS_DIDACTICAS)))
        idx = st.selectbox(
            "Pareja de consultas",
            indices,
            format_func=lambda i: PAREJAS_DIDACTICAS[i]["concepto"],
            key="pareja_comp",
        )
        pareja = PAREJAS_DIDACTICAS[idx]
        sql_a = QUERIES_POR_ID[pareja["a"]]["sql"].strip()
        sql_b = QUERIES_POR_ID[pareja["b"]]["sql"].strip()
        explicacion = pareja["explicacion"]
        titulo_a = f'Consulta A ({pareja["etiqueta_a"]})'
        titulo_b = f'Consulta B ({pareja["etiqueta_b"]})'

        col_a, col_b = st.columns(2)
        col_a.code(sql_a, language="sql")
        col_b.code(sql_b, language="sql")
    else:
        titulo_a = "Consulta A"
        titulo_b = "Consulta B"

        col_a, col_b = st.columns(2)
        sql_a = col_a.text_area(
            "Consulta A",
            "SELECT * FROM actor;",
            height=160,
            key="sql_a_comp",
        )
        sql_b = col_b.text_area(
            "Consulta B",
            "SELECT first_name, last_name FROM actor;",
            height=160,
            key="sql_b_comp",
        )

    if st.button("Comparar", key="run_comp"):
        if not is_select(sql_a) or not is_select(sql_b):
            st.error("Ambas consultas deben ser sentencias SELECT.")
        else:
            try:
                res_a = estimar_consulta(sql_a, factor_emision)
                res_b = estimar_consulta(sql_b, factor_emision)

                res_col_a, res_col_b = st.columns(2)
                _render_columna(res_col_a, titulo_a, res_a)
                _render_columna(res_col_b, titulo_b, res_b)

                _render_veredicto(res_a, res_b)

                if explicacion:
                    st.info(f"**Análisis técnico del consumo**\n\n{explicacion}")
            except Exception as e:
                st.error(f"Error en la comparación: {e}")


def _render_columna(col, titulo, resultado):
    """
    Pinta los resultados de una consulta en una columna. Se usa dos veces (A y B),
    por eso es un helper: mismo formato para ambos lados.
    """
    energia = resultado["energia"]
    desperdicio = resultado["desperdicio"]

    col.markdown(f"### {titulo}")
    col.metric("Energía total", f'{energia["energia_total_j"]:.4f} J')
    col.metric("Emisiones", f'{energia["co2e_kg"]:.3e} kg CO₂e')
    col.metric("Transferencia estimada", f'{resultado["bytes_transferencia"]:,} B')
    col.write(
        f'Trabajo desperdiciado: {desperdicio["porcentaje_desperdicio"]:.1f}% '
        f'({desperdicio["filas_descartadas"]} filas descartadas)'
    )


def _render_veredicto(res_a, res_b):
    """
    Lectura rápida calculada en vivo a partir de las dos estimaciones:
    diferencias de energía y de transferencia. Es la parte que cambia en cada
    ejecución;la explicación conceptual (fija) la aporta la pareja didáctica.
    """
    ea = res_a["energia"]["energia_total_j"]
    eb = res_b["energia"]["energia_total_j"]
    ba = res_a["bytes_transferencia"]
    bb = res_b["bytes_transferencia"]

    st.markdown("### Lectura rápida")
    st.write(_linea_energia(ea, eb))
    st.write(_linea_transferencia(ba, bb))


def _fmt_julios(j):
    """Energía en julios con cifras significativas (legible para valores grandes
    y muy pequeños)."""
    return f"{j:.3g} J"


def _fmt_bytes(b):
    """Bytes en unidades legibles (base 1000): B, KB, MB, GB."""
    if b < 1_000:
        return f"{b} B"
    if b < 1_000_000:
        return f"{b / 1_000:.1f} KB"
    if b < 1_000_000_000:
        return f"{b / 1_000_000:.1f} MB"
    return f"{b / 1_000_000_000:.2f} GB"


def _linea_energia(ea, eb):
    if min(ea, eb) <= 0:
        return "Energía: no se puede comparar (algún valor es cero)."
    ratio = max(ea, eb) / min(ea, eb)
    if ratio < 1.10:
        return (
            f"Energía: prácticamente igual en ambas consultas "
            f"({_fmt_julios(ea)} frente a {_fmt_julios(eb)})."
        )
    mayor, v_may, v_men = ("A", ea, eb) if ea > eb else ("B", eb, ea)
    return (
        f"Energía: la Consulta {mayor} requiere {ratio:.1f}× más energía "
        f"({_fmt_julios(v_may)} frente a {_fmt_julios(v_men)})."
    )


def _linea_transferencia(ba, bb):
    if ba == bb:
        return f"Red (estimada): transferencia igual en ambas ({_fmt_bytes(ba)})."
    if min(ba, bb) <= 0:
        mayor, v_may = ("A", ba) if ba > bb else ("B", bb)
        return (
            f"Red (estimada): la Consulta {mayor} transferiría {_fmt_bytes(v_may)} "
            f"al cliente, mientras que la otra no devuelve filas."
        )
    ratio = max(ba, bb) / min(ba, bb)
    mayor, v_may, v_men = ("A", ba, bb) if ba > bb else ("B", bb, ba)
    if ratio < 1.10:
        return (
            f"Red (estimada): transferencia similar "
            f"({_fmt_bytes(v_may)} frente a {_fmt_bytes(v_men)})."
        )
    return (
        f"Red (estimada): la Consulta {mayor} transferiría {ratio:.1f}× más datos "
        f"al cliente ({_fmt_bytes(v_may)} frente a {_fmt_bytes(v_men)})."
    )
