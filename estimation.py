"""
estimation.py - Orquestador de la estimación de una consulta.

Reúne en un solo sitio el cálculo que necesitan las pestanas de Energía y de
Comparativa: ejecuta el plan, extrae las métricas y aplica el modelo. No importa
Streamlit (no pinta nada) y no vive dentro de energy/ porque toca la base de
datos; así energy/ se mantiene puro y testeable.

La validación de que la consulta es un SELECT (is_select) se hace en la capa de
pestaña, no aquí: mostrar el error es responsabilidad de la interfaz. Esta
función asume que recibe un SELECT válido.
"""

from db import run_explain
from energy.parser import extract_metrics
from energy.model import estimate_energy, wasted_work, bytes_transferencia


def estimar_consulta(query, factor_emision):
    """
    Estima el coste de una consulta a partir de su plan de ejecución.

    Parámetros
    ----------
    query : str
        Sentencia SELECT ya validada.
    factor_emision : float
        Factor de emisión (kg CO2e / kWh) del país seleccionado.

    Devuelve
    --------
    dict con:
        metrics              métricas extraídas del plan (parser.extract_metrics)
        energia              resultado del modelo energético (estimate_energy)
        desperdicio          indicador de trabajo desperdiciado (wasted_work)
        bytes_transferencia  coste estimado de transferencia (indicador didáctico)
    """
    plan = run_explain(query, analyze=True, buffers=True,
                       verbose=False, format_json=True)
    metrics = extract_metrics(plan)

    return {
        "metrics": metrics,
        "energia": estimate_energy(metrics, emission_factor=factor_emision),
        "desperdicio": wasted_work(metrics),
        "bytes_transferencia": bytes_transferencia(
            metrics["ancho_fila"], metrics["filas_devueltas"]),
    }
