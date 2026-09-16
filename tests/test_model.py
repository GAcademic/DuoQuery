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
Tests de energy/model.py (estimate_energy, wasted_work).

Criterio de comparación: los enteros y recuentos se comparan con ==; los valores
decimales calculados (kWh, CO2e, porcentajes) con pytest.approx, porque los
floats se almacenan en binario de forma aproximada.
"""

import pytest

from energy.model import (
    estimate_energy,
    wasted_work,
    CPU_POWER_W,
    JOULES_PER_KWH,
)


# --- estimate_energy --------------------------------------------------------

def test_formula_con_parametros_explicitos():
    """
    Se pasan parámetros inventados y redondos en lugar de las constantes reales:
    así se prueba la FÓRMULA, no el valor de la constante. Si cambia
    CPU_POWER_W, este test debe seguir pasando.

    De paso verifica que los parámetros sobreescribibles surten efecto.
    """
    metrics = {"tiempo_s": 2.0, "bloques_cache": 10, "bloques_disco": 5}

    energia = estimate_energy(
        metrics,
        cpu_power_w=10.0,
        e_hit=2.0,
        e_io=3.0,
        emission_factor=0.5,
    )

    # cpu     = 10 * 2.0 = 20
    # memoria =  2 * 10  = 20
    # disco   =  3 * 5   = 15
    # total              = 55
    assert energia["energia_cpu_j"] == pytest.approx(20.0)
    assert energia["energia_memoria_j"] == pytest.approx(20.0)
    assert energia["energia_disco_j"] == pytest.approx(15.0)
    assert energia["energia_total_j"] == pytest.approx(55.0)
    assert energia["energia_kwh"] == pytest.approx(55.0 / JOULES_PER_KWH)
    assert energia["co2e_kg"] == pytest.approx(55.0 / JOULES_PER_KWH * 0.5)


def test_valores_por_defecto_fijan_el_modelo_real():
    """
    Red de seguridad: si alguien cambia una constante del modelo sin querer,
    este test salta.
    """
    metrics = {"tiempo_s": 1.0, "bloques_cache": 0, "bloques_disco": 0}

    energia = estimate_energy(metrics)

    assert energia["energia_cpu_j"] == pytest.approx(CPU_POWER_W)
    assert energia["energia_memoria_j"] == pytest.approx(0.0)
    assert energia["energia_disco_j"] == pytest.approx(0.0)
    assert energia["energia_total_j"] == pytest.approx(CPU_POWER_W)


def test_energia_total_es_la_suma_de_los_tres_terminos():
    metrics = {"tiempo_s": 0.5, "bloques_cache": 40, "bloques_disco": 7}

    energia = estimate_energy(metrics)

    esperado = (
        energia["energia_cpu_j"]
        + energia["energia_memoria_j"]
        + energia["energia_disco_j"]
    )

    assert energia["energia_total_j"] == pytest.approx(esperado)


# --- wasted_work ------------------------------------------------------------

def test_porcentaje_de_desperdicio():
    w = wasted_work({"filas_devueltas": 39, "filas_descartadas": 961})

    assert w["filas_devueltas"] == 39
    assert w["filas_descartadas"] == 961
    assert w["porcentaje_desperdicio"] == pytest.approx(96.1)


def test_sin_filas_no_divide_por_cero():
    # Rama del else: total == 0
    w = wasted_work({"filas_devueltas": 0, "filas_descartadas": 0})

    assert w["porcentaje_desperdicio"] == 0.0


def test_sin_descartes_el_desperdicio_es_cero():
    w = wasted_work({"filas_devueltas": 200, "filas_descartadas": 0})

    assert w["porcentaje_desperdicio"] == pytest.approx(0.0)
