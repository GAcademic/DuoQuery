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
conftest.py - Fixtures compartidas por los tests.

pytest carga este fichero automáticamente (el nombre es obligatorio) y pone sus
fixtures a disposición de todos los tests, sin necesidad de importarlos.
"""

import pytest


@pytest.fixture
def make_plan():
    """
    Factory fixture: devuelve una función que fabrica planes de ejecución
    sintñeticos con la forma que produce EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON).

    Evita repetir el diccionario anidado en cada test: se parte de unos valores
    por defecto y cada test sobreescribe únicamente el campo que le interesa.

    Se recibe un diccionario (y no argumentos sueltos) porque las claves del plan
    llevan espacios y mayúsculas ("Plan Width"), que no son identificadores
    válidos de Python.

    Ejemplo:
        make_plan({"Plan Width": 25, "Actual Rows": 200})
    """

    def _make(root=None, execution_time=10.0):
        base = {
            "Actual Rows": 0,
            "Plan Width": 0,
            "Shared Hit Blocks": 0,
        }

        if root:
            base.update(root)

        return [{"Execution Time": execution_time, "Plan": base}]

    return _make
