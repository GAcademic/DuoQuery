"""
conftest.py - Fixtures compartidas por los tests.

pytest carga este fichero automaticamente (el nombre es obligatorio) y pone sus
fixtures a disposicion de todos los tests, sin necesidad de importarlos.
"""

import pytest


@pytest.fixture
def make_plan():
    """
    Factory fixture: devuelve una funcion que fabrica planes de ejecucion
    sinteticos con la forma que produce EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON).

    Evita repetir el diccionario anidado en cada test: se parte de unos valores
    por defecto y cada test sobreescribe unicamente el campo que le interesa.

    Se recibe un diccionario (y no argumentos sueltos) porque las claves del plan
    llevan espacios y mayusculas ("Plan Width"), que no son identificadores
    validos de Python.

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
