"""
estimation.py - Orquestador de la estimacion de una consulta.

Reune en un solo sitio el calculo que necesitan las pestanas de Energia y de
Comparativa: ejecuta el plan, extrae las metricas y aplica el modelo. No importa
Streamlit (no pinta nada) y no vive dentro de energy/ porque toca la base de
datos; asi energy/ se mantiene puro y testeable.

La validacion de que la consulta es un SELECT (is_select) se hace en la capa de
pestana, no aqui: mostrar el error es responsabilidad de la interfaz. Esta
funcion asume que recibe un SELECT valido.
"""

from db import run_explain
from energy.parser import extract_metrics
from energy.model import estimate_energy, wasted_work, bytes_transferencia


def estimar_consulta(query, factor_emision):
    """
    Estima el coste de una consulta a partir de su plan de ejecucion.

    Parametros
    ----------
    query : str
        Sentencia SELECT ya validada.
    factor_emision : float
        Factor de emision (kg CO2e / kWh) del pais seleccionado.

    Devuelve
    --------
    dict con:
        metrics              metricas extraidas del plan (parser.extract_metrics)
        energia              resultado del modelo energetico (estimate_energy)
        desperdicio          indicador de trabajo desperdiciado (wasted_work)
        bytes_transferencia  coste estimado de transferencia (indicador didactico)
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
