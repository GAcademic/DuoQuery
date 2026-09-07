"""
Tests de energy/parser.py (extract_metrics).

Se usan planes sintéticos: construidos a mano y con valores controlados, para
poder calcular el resultado esperado de forma independiente de la función.
"""

import pytest

from energy.parser import extract_metrics


# --- Tiempo -----------------------------------------------------------------

def test_convierte_el_tiempo_de_ms_a_segundos(make_plan):
    m = extract_metrics(make_plan(execution_time=168.0))
    assert m["tiempo_s"] == pytest.approx(0.168)


def test_usa_actual_total_time_si_falta_execution_time():
    # Plan sin "Execution Time": debe recurrir al respaldo del nodo raiz.
    plan = [{"Plan": {"Actual Rows": 0, "Actual Total Time": 250.0}}]

    m = extract_metrics(plan)

    assert m["tiempo_s"] == pytest.approx(0.25)


# --- Buffers ----------------------------------------------------------------

def test_suma_los_bloques_de_disco_y_separa_los_de_cache(make_plan):
    m = extract_metrics(make_plan({
        "Shared Hit Blocks": 100,
        "Shared Read Blocks": 10,
        "Shared Written Blocks": 5,
        "Temp Read Blocks": 2,
        "Temp Written Blocks": 3,
    }))

    assert m["bloques_cache"] == 100
    assert m["bloques_leidos"] == 10
    assert m["bloques_escritos"] == 5
    assert m["bloques_temp"] == 5          # 2 + 3
    assert m["bloques_disco"] == 20        # 10 + 5 + 5


# --- Filas y ancho ----------------------------------------------------------

def test_filas_devueltas_del_nodo_raiz(make_plan):
    m = extract_metrics(make_plan({"Actual Rows": 1000}))
    assert m["filas_devueltas"] == 1000


@pytest.mark.parametrize("ancho", [13, 25, 645])
def test_ancho_fila_recoge_plan_width(make_plan, ancho):
    m = extract_metrics(make_plan({"Plan Width": ancho}))
    assert m["ancho_fila"] == ancho


def test_ancho_fila_es_cero_si_no_hay_plan_width():
    # Rama distinta: el valor por defecto del .get()
    plan = [{"Execution Time": 1.0, "Plan": {"Actual Rows": 10}}]

    m = extract_metrics(plan)

    assert m["ancho_fila"] == 0


# --- Filas descartadas ------------------------------------------------------

def test_filas_descartadas_en_un_nodo_simple(make_plan):
    m = extract_metrics(make_plan({"Rows Removed by Filter": 199}))
    assert m["filas_descartadas"] == 199


def test_filas_descartadas_se_multiplican_por_los_loops(make_plan):
    m = extract_metrics(make_plan({
        "Rows Removed by Filter": 10,
        "Actual Loops": 5,
    }))

    assert m["filas_descartadas"] == 50


def test_filas_descartadas_recorre_el_arbol(make_plan):
    """
    Cubre a la vez: recursión sobre "Plans", multiplicación por "Actual Loops"
    en varios niveles, y que se cuentan los dos tipos de filtro.
    """
    plan = make_plan({
        "Rows Removed by Filter": 100,          # nodo raiz
        "Actual Loops": 1,
        "Plans": [
            {
                "Rows Removed by Join Filter": 30,
                "Actual Loops": 2,
                "Plans": [
                    {"Rows Removed by Filter": 5, "Actual Loops": 1}
                ],
            }
        ],
    })

    m = extract_metrics(plan)

    # raiz:  100 x 1 = 100
    # hijo:   30 x 2 =  60
    # nieto:   5 x 1 =   5
    assert m["filas_descartadas"] == 165


def test_sin_filtros_no_hay_filas_descartadas(make_plan):
    m = extract_metrics(make_plan({"Actual Rows": 200}))
    assert m["filas_descartadas"] == 0
