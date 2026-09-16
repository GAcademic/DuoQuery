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
Tests de db.is_select().

Los casos son variantes del mismo patrón, así que se agrupan con parametrize:
pytest ejecuta la función una vez por tupla y cuenta cada una como un test
independiente. Se corresponden con el contrato descrito en el docstring de
is_select().
"""

import pytest

from db import is_select


@pytest.mark.parametrize("consulta, esperado", [
    # Lecturas validas
    ("SELECT * FROM actor",                              True),
    ("SELECT first_name, last_name FROM actor",          True),
    ("WITH t AS (SELECT 1) SELECT * FROM t",             True),

    # Varias sentencias apiladas
    ("SELECT 1; DROP TABLE film;",                       False),

    # Sentencias que no son de lectura
    ("UPDATE actor SET first_name = 'x'",                False),
    ("DELETE FROM actor",                                False),
    ("DROP TABLE film",                                  False),

    # No-SELECT precedida de comentario
    ("-- comentario\nDROP TABLE film;",                  False),

    # Entradas vacias o sin sentencia
    ("",                                                 False),
    ("   ",                                              False),
])
def test_is_select(consulta, esperado):
    assert is_select(consulta) == esperado
