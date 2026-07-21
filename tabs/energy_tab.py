import streamlit as st

from db import is_select, run_explain
from energy.parser import extract_metrics
from energy.model import (
    estimate_energy, wasted_work,
    FACTORES_EMISION, PAIS_POR_DEFECTO,
    CPU_POWER_W, E_IO, E_HIT,
)


def render_energy_tab():
    st.subheader("Estimación energética")
    st.markdown(
        """
Estima la energía y las emisiones de una consulta a partir de su plan de ejecución
(`EXPLAIN ANALYZE, BUFFERS`). Es una **estimación comparativa**, no una medición física exacta.
        """
    )

    # Factor de emision segun el pais (unico parametro seleccionable).
    paises = sorted(FACTORES_EMISION.keys())
    pais = st.selectbox(
        "País (factor de emisión de la red eléctrica)",
        paises,
        index=paises.index(PAIS_POR_DEFECTO),
        key="pais_energy",
    )
    factor_emision, fuente = FACTORES_EMISION[pais]
    st.caption(f"Factor seleccionado: {factor_emision} kg CO₂e/kWh · Fuente: {fuente}")

    # Parametros fijos del modelo (informativos, no editables).
    with st.expander("Parámetros del modelo (fijos)"):
        st.write(f"- Potencia de CPU: {CPU_POWER_W} W (Intel Core Ultra 7 155H)")
        st.write(f"- Energía por bloque de disco: {E_IO} J (SSD Samsung PM9A1)")
        st.write(f"- Energía por bloque de caché: {E_HIT} J (e_io / 100)")

    query = st.text_area(
        "Consulta a analizar",
        "SELECT film_id, title, release_year FROM film LIMIT 10;",
        height=180,
        key="query_energy",
    )

    if st.button("Estimar energía", key="run_energy"):
        try:
            if not is_select(query):
                st.error("Solo se permiten sentencias SELECT.")
            else:
                plan = run_explain(query, analyze=True, buffers=True,
                                   verbose=False, format_json=True)
                metrics = extract_metrics(plan)
                energia = estimate_energy(metrics, emission_factor=factor_emision)
                desperdicio = wasted_work(metrics)

                c1, c2, c3 = st.columns(3)
                c1.metric("Energía total", f'{energia["energia_total_j"]:.4f} J')
                c2.metric("Consumo", f'{energia["energia_kwh"]:.3e} kWh')
                c3.metric("Emisiones", f'{energia["co2e_kg"]:.3e} kg CO₂e')

                st.markdown("### Desglose de energía")
                st.write(f'- CPU: {energia["energia_cpu_j"]:.4f} J (tiempo {metrics["tiempo_s"]*1000:.3f} ms)')
                st.write(f'- Memoria (caché): {energia["energia_memoria_j"]:.6f} J ({metrics["bloques_cache"]} bloques)')
                st.write(f'- Disco: {energia["energia_disco_j"]:.6f} J ({metrics["bloques_disco"]} bloques)')

                st.markdown("### Detalle de bloques de disco")
                st.write(
                    f'- Leídos: {metrics["bloques_leidos"]} | '
                    f'Escritos: {metrics["bloques_escritos"]} | '
                    f'Temporales: {metrics["bloques_temp"]}'
                )

                st.markdown("### Trabajo desperdiciado")
                if desperdicio["filas_descartadas"] > 0:
                    total_leidas = desperdicio["filas_devueltas"] + desperdicio["filas_descartadas"]
                    st.warning(
                        f'Se procesaron {total_leidas} filas y se descartaron '
                        f'{desperdicio["filas_descartadas"]} por filtros '
                        f'({desperdicio["porcentaje_desperdicio"]:.1f}% desperdiciado). '
                        f'Un índice o un filtro más selectivo reduciría el consumo.'
                    )
                else:
                    st.success("No se descartaron filas por filtros: la consulta no desperdicia lecturas.")
        except Exception as e:
            st.error(f"Error estimando la energía: {e}")
