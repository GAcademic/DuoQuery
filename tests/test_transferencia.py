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
Test del indicador estimado de coste de transferencia.

Es la comprobación que en su día se hizo a mano al incorporar Plan Width:
bytes = ancho de fila estimado x filas devueltas.
"""

import pytest

from energy.model import bytes_transferencia


@pytest.mark.parametrize("ancho, filas, esperado", [
    (13,  200,      2_600),         # proyección explícita sobre actor
    (25,  200,      5_000),         # SELECT * sobre actor
    (13,  1_000_000, 13_000_000),   # proyección sobre actor_wide
    (645, 1_000_000, 645_000_000),  # SELECT * sobre actor_wide
])
def test_bytes_transferencia(ancho, filas, esperado):
    assert bytes_transferencia(ancho, filas) == esperado


def test_sin_filas_no_hay_transferencia():
    assert bytes_transferencia(645, 0) == 0


def test_sin_ancho_no_hay_transferencia():
    # Caso del fallback: si el plan no trae Plan Width, ancho_fila vale 0.
    assert bytes_transferencia(0, 1_000_000) == 0
