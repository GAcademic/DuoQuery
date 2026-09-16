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
model.py - Modelo energético.

Aplica la fórmula de estimación energética a las métricas extraídas del plan
(ver parser.py) y devuelve la energía en julios, kWh y las emisiones en CO2e.

Modelo (estimación en unidades físicas):
    E_total(J) = E_CPU + E_memoria + E_disco
        E_CPU     = CPU_POWER_W * tiempo_s
        E_memoria = E_HIT * bloques_cache
        E_disco   = E_IO  * bloques_disco
    kWh  = E_total / 3_600_000
    CO2e = kWh * EMISSION_FACTOR

Los parámetros se derivan del hardware de referencia (equipo anfitrion) y de una
relación de proporcionalidad para el coste de memoria frente a disco.
"""

# --- Parámetros del modelo (hardware de referencia; ver memoria) ---

# Potencia efectiva de CPU, en vatios.
# Intel Core Ultra 7 155H, Processor Base Power (ficha de Intel).
CPU_POWER_W = 28.0

# Energía por bloque de 8 KB de E/S a disco, en julios.
# Derivado del SSD Samsung PM9A1: 6,2 W (potencia activa de lectura, dato oficial
# de la ficha del 980 PRO equivalente) / 7,0e9 B/s (lectura secuencial)
# * 8192 B ~= 7,3e-6 J/bloque.
E_IO = 7.3e-6

# Energía por bloque de 8 KB servido desde cache (memoria).
# Eleccion de modelado: el acceso a memoria es mas barato que el de disco.
E_HIT = E_IO / 100

# Factor de emisión de la red eléctrica, kg de CO2e por kWh.
# MITECO, mix electrico nacional 2025.
EMISSION_FACTOR = 0.258

# Factores de emisión por país (kg CO2e por kWh) y su fuente.
# Fuente internacional: Our World in Data / Ember (2026), intensidad de ciclo de
# vida de la electricidad, año 2025. Para España se incluye también el factor
# oficial de MITECO (mix nacional 2025).
FACTORES_EMISION = {
    "Noruega": (0.028, "Ember / Our World in Data"),
    "Francia": (0.041, "Ember / Our World in Data"),
    "España (Ember)": (0.154, "Ember / Our World in Data"),
    "Reino Unido": (0.217, "Ember / Our World in Data"),
    "España (MITECO oficial)": (0.258, "MITECO"),
    "Alemania": (0.330, "Ember / Our World in Data"),
    "Estados Unidos": (0.384, "Ember / Our World in Data"),
    "China": (0.525, "Ember / Our World in Data"),
    "Polonia": (0.589, "Ember / Our World in Data"),
    "India": (0.670, "Ember / Our World in Data"),
    "Sudáfrica": (0.699, "Ember / Our World in Data"),
}

PAIS_POR_DEFECTO = "España (MITECO oficial)"

JOULES_PER_KWH = 3_600_000


def estimate_energy(metrics, cpu_power_w=CPU_POWER_W, e_io=E_IO,
                    e_hit=E_HIT, emission_factor=EMISSION_FACTOR):
    """
    Aplica el modelo energético a las métricas del plan.

    Parámetros
    ----------
    metrics : dict
        Salida de parser.extract_metrics(): usa tiempo_s, bloques_cache y bloques_disco.

    Devuelve
    --------
    dict con:
        energia_cpu_j, energia_memoria_j, energia_disco_j, energia_total_j (julios)
        energia_kwh
        co2e_kg
    """
    energia_cpu_j = cpu_power_w * metrics["tiempo_s"]
    energia_memoria_j = e_hit * metrics["bloques_cache"]
    energia_disco_j = e_io * metrics["bloques_disco"]
    energia_total_j = energia_cpu_j + energia_memoria_j + energia_disco_j

    energia_kwh = energia_total_j / JOULES_PER_KWH
    co2e_kg = energia_kwh * emission_factor

    return {
        "energia_cpu_j": energia_cpu_j,
        "energia_memoria_j": energia_memoria_j,
        "energia_disco_j": energia_disco_j,
        "energia_total_j": energia_total_j,
        "energia_kwh": energia_kwh,
        "co2e_kg": co2e_kg,
    }


def wasted_work(metrics):
    """
    Indicador didáctico de 'trabajo desperdiciado' (NO es energía): hace visible
    que parte del trabajo realizado por PostgreSQL queda asociada a filas que no
    forman parte del resultado final (leídas y descartadas por filtros), frente a
    las filas devueltas. Es reducible con un mejor acceso (índice o filtro más
    selectivo).

    Devuelve dict con filas_devueltas, filas_descartadas y porcentaje_desperdicio.
    """
    devueltas = metrics["filas_devueltas"]
    descartadas = metrics["filas_descartadas"]
    total = devueltas + descartadas
    porcentaje = (descartadas / total * 100.0) if total > 0 else 0.0
    return {
        "filas_devueltas": devueltas,
        "filas_descartadas": descartadas,
        "porcentaje_desperdicio": porcentaje,
    }


def bytes_transferencia(ancho_fila, filas):
    """
    Indicador didáctico de coste estimado de transferencia, en bytes.

    Es el ancho medio de la fila de salida (Plan Width, estimado por el planner)
    multiplicado por el número de filas devueltas.

    IMPORTANTE: NO es energía y NO es una medida observada. Bajo EXPLAIN ANALYZE
    la salida se descarta y no se transfiere nada al cliente, por lo que no
    existen bytes reales que medir. Se mantiene separado del modelo energético,
    igual que wasted_work.
    """

    return ancho_fila * filas
