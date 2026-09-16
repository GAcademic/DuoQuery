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

from db import is_select
from estimation import estimar_consulta
from energy.model import (
    FACTORES_EMISION, PAIS_POR_DEFECTO,
    CPU_POWER_W, E_IO, E_HIT,
)


def _fmt_j(x):
    """Formatea una energía en julios; usa notación científica si es muy pequeña."""
    if x == 0:
        return "0 J"
    if abs(x) < 1e-3:
        return f"{x:.2e} J"
    return f"{x:.4f} J"


def _bloques(n):
    return f'{n} bloque{"s" if n != 1 else ""}'


def render_energy_tab():
    st.subheader("Estimación energética")
    st.markdown(
        """
Estima la energía y las emisiones de una consulta a partir de su plan de ejecución
(`EXPLAIN ANALYZE, BUFFERS`). Es una **estimación comparativa**, no una medición física exacta.
        """
    )

    # Factor de emisión según el país (único parámetro seleccionable).
    paises = sorted(FACTORES_EMISION.keys())
    pais = st.selectbox(
        "País (factor de emisión de la red eléctrica)",
        paises,
        index=paises.index(PAIS_POR_DEFECTO),
        key="pais_energy",
    )
    factor_emision, fuente = FACTORES_EMISION[pais]
    st.caption(f"Factor seleccionado: {factor_emision} kg CO₂e/kWh · Fuente: {fuente}")

    # Parámetros fijos del modelo (informativos, no editables).
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
                resultado = estimar_consulta(query, factor_emision)
                metrics = resultado["metrics"]
                energia = resultado["energia"]
                desperdicio = resultado["desperdicio"]

                c1, c2, c3 = st.columns(3)
                c1.metric("Energía total", f'{energia["energia_total_j"]:.4f} J')
                c2.metric("Consumo", f'{energia["energia_kwh"]:.3e} kWh')
                c3.metric("Emisiones", f'{energia["co2e_kg"]:.3e} kg CO₂e')

                st.markdown("### Desglose de energía")
                st.write(f'- CPU: {_fmt_j(energia["energia_cpu_j"])} (tiempo {metrics["tiempo_s"]*1000:.3f} ms)')
                st.write(f'- Memoria (caché): {_fmt_j(energia["energia_memoria_j"])} ({_bloques(metrics["bloques_cache"])})')
                st.write(f'- Disco: {_fmt_j(energia["energia_disco_j"])} ({_bloques(metrics["bloques_disco"])})')

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
