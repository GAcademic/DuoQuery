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
