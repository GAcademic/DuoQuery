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


"""
parser.py - Extracción de métricas del plan de ejecución.

Convierte el JSON de EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) en un diccionario
de métricas. No accede a la base de datos: recibe el JSON ya obtenido, para
poder probarse de forma aislada.
"""


def extract_metrics(plan_json):
    """
    Extrae del plan las métricas que necesita el modelo energético.

    Parámetros
    ----------
    plan_json : list
        Lo que devuelve EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON): una lista cuyo
        primer elemento tiene "Execution Time" y "Plan" (el nodo raíz).

    Devuelve
    --------
    dict con:
        tiempo_s          tiempo de ejecución de la consulta (s)
        bloques_cache     Shared Hit Blocks (memoria)
        bloques_leidos    Shared Read Blocks (disco)
        bloques_escritos  Shared Written Blocks (disco)
        bloques_temp      Temp Read + Temp Written Blocks (disco temporal)
        bloques_disco     total de disco (leidos + escritos + temporales)
        filas_devueltas   Actual Rows del nodo raíz
        filas_descartadas filas eliminadas por filtros en todo el plan
        ancho_fila        Plan Width del nodo raíz (bytes/fila ESTIMADOS por el
                          planner para la tupla de salida; NO es una medida real)
    """
    raiz_json = plan_json[0]
    root = raiz_json["Plan"]

    # Tiempo: "Execution Time" que reporta EXPLAIN ANALYZE (ms -> s).
    # Si no estuviera, se usa el Actual Total Time del nodo raíz como respaldo.
    tiempo_ms = raiz_json.get("Execution Time", root.get("Actual Total Time", 0.0))
    tiempo_s = tiempo_ms / 1000.0

    # Buffers: se leen del nodo raíz, que ya acumula los de sus hijos.
    bloques_cache = root.get("Shared Hit Blocks", 0)
    bloques_leidos = root.get("Shared Read Blocks", 0)
    bloques_escritos = root.get("Shared Written Blocks", 0)
    bloques_temp = root.get("Temp Read Blocks", 0) + root.get("Temp Written Blocks", 0)
    bloques_disco = bloques_leidos + bloques_escritos + bloques_temp

    filas_devueltas = root.get("Actual Rows", 0)
    filas_descartadas = _contar_filas_descartadas(root)

    # Plan Width: ancho medio de la fila de SALIDA (tupla proyectada), en bytes.
    # A diferencia de los bloques, este valor SÍ cambia entre 'SELECT *' y una
    # proyección explícita. Es una estimación del planner (a partir de
    # estadisticas), no un valor observado: bajo EXPLAIN ANALYZE no hay
    # transferencia real al cliente que medir.
    ancho_fila = root.get("Plan Width", 0)

    return {
        "tiempo_s": tiempo_s,
        "bloques_cache": bloques_cache,
        "bloques_leidos": bloques_leidos,
        "bloques_escritos": bloques_escritos,
        "bloques_temp": bloques_temp,
        "bloques_disco": bloques_disco,
        "filas_devueltas": filas_devueltas,
        "filas_descartadas": filas_descartadas,
        "ancho_fila": ancho_fila,
    }


def _contar_filas_descartadas(root):
    """
    Suma las filas eliminadas por filtros en todo el plan
    ("Rows Removed by Filter" y "Rows Removed by Join Filter").

    Cada valor se multiplica por "Actual Loops", porque el plan lo reporta
    por iteración: en un nodo dentro de un nested loop que se repite N veces,
    el total real de filas descartadas es el valor mostrado x N.
    """
    total = 0

    def walk(node):
        nonlocal total
        loops = node.get("Actual Loops", 1) or 1
        filtro = node.get("Rows Removed by Filter", 0) or 0
        join_filtro = node.get("Rows Removed by Join Filter", 0) or 0
        total += (filtro + join_filtro) * loops
        for child in node.get("Plans", []):
            walk(child)

    walk(root)
    return total
