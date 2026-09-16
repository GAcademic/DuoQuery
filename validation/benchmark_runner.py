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
benchmark_runner.py

Ejecuta el benchmark de validación de DuoQuery y genera:

- results_energy.csv
- results_efficiency.csv

Cada consulta se ejecuta múltiples veces y se almacenan
estadísticos descriptivos para reducir el efecto de la
variabilidad entre ejecuciones.
"""

import csv
import statistics

from pathlib import Path

from db import get_connection

from validation.benchmark_queries import ALL_QUERIES

from energy.parser import extract_metrics
from energy.model import estimate_energy, wasted_work, bytes_transferencia


N_RUNS = 100

OUTPUT_DIR = Path(__file__).parent


def get_explain_json(cursor, sql):
    """
    Ejecuta EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
    y devuelve el JSON resultante.
    """

    explain_sql = f"""
    EXPLAIN (
        ANALYZE,
        BUFFERS,
        FORMAT JSON
    )
    {sql}
    """

    cursor.execute(explain_sql)

    return cursor.fetchone()[0]


def save_csv(filename, rows):

    if not rows:
        return

    output_file = OUTPUT_DIR / filename

    with open(
        output_file,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=rows[0].keys()
        )

        writer.writeheader()
        writer.writerows(rows)


def std(values):
    """
    Desviación estándar.
    """

    if len(values) < 2:
        return 0.0

    return statistics.stdev(values)


def run_benchmark():

    conn = get_connection()
    cursor = conn.cursor()

    energy_results = []
    efficiency_results = []

    try:

        for query in ALL_QUERIES:

            print(
                f"Ejecutando {query['id']} "
                f"({N_RUNS} repeticiones)..."
            )

            times = []

            energy_cpu = []
            energy_memory = []
            energy_disk = []
            energy_total = []

            energy_kwh = []
            co2e = []

            waste_sample = None
            ancho_fila_sample = None

            for _ in range(N_RUNS):

                plan_json = get_explain_json(
                    cursor,
                    query["sql"]
                )

                metrics = extract_metrics(plan_json)

                energy = estimate_energy(metrics)

                if waste_sample is None:
                    waste_sample = wasted_work(metrics)

                # Plan Width es una estimación del planner: constante entre
                # ejecuciones, basta con muestrearla una vez.
                if ancho_fila_sample is None:
                    ancho_fila_sample = metrics["ancho_fila"]

                times.append(metrics["tiempo_s"])

                energy_cpu.append(
                    energy["energia_cpu_j"]
                )

                energy_memory.append(
                    energy["energia_memoria_j"]
                )

                energy_disk.append(
                    energy["energia_disco_j"]
                )

                energy_total.append(
                    energy["energia_total_j"]
                )

                energy_kwh.append(
                    energy["energia_kwh"]
                )

                co2e.append(
                    energy["co2e_kg"]
                )

            energy_results.append({

                "query_id": query["id"],
                "group": query["group"],
                "runs": N_RUNS,

                "mean_time_s":
                    statistics.mean(times),

                "min_time_s":
                    min(times),

                "max_time_s":
                    max(times),

                "std_time_s":
                    std(times),

                "mean_energy_cpu_j":
                    statistics.mean(energy_cpu),

                "std_energy_cpu_j":
                    std(energy_cpu),

                "mean_energy_memory_j":
                    statistics.mean(energy_memory),

                "std_energy_memory_j":
                    std(energy_memory),

                "mean_energy_disk_j":
                    statistics.mean(energy_disk),

                "std_energy_disk_j":
                    std(energy_disk),

                "mean_energy_total_j":
                    statistics.mean(energy_total),

                "std_energy_total_j":
                    std(energy_total),

                "mean_energy_kwh":
                    statistics.mean(energy_kwh),

                "mean_co2e_kg":
                    statistics.mean(co2e),
            })

            efficiency_results.append({

                "query_id": query["id"],
                "group": query["group"],

                "filas_devueltas":
                    waste_sample["filas_devueltas"],

                "filas_descartadas":
                    waste_sample["filas_descartadas"],

                "porcentaje_desperdicio":
                    waste_sample["porcentaje_desperdicio"],

                # Indicador de coste de transferencia (NO energia, NO medido):
                # ancho_fila_estimado es Plan Width (bytes/fila estimados por el
                # planner) y bytes_transferencia_estimados = ancho x filas.
                # Es una ESTIMACIóN del planner, no tráfico real; EXPLAIN ANALYZE
                # descarta la salida y no transfiere nada al cliente.
                "ancho_fila_estimado":
                    ancho_fila_sample,

                "bytes_transferencia_estimados":
                    bytes_transferencia(
                        ancho_fila_sample,
                        waste_sample["filas_devueltas"],
                    ),
            })

    finally:

        cursor.close()
        conn.close()

    save_csv(
        "results_energy.csv",
        energy_results
    )

    save_csv(
        "results_efficiency.csv",
        efficiency_results
    )

    print("Benchmark completado.")


if __name__ == "__main__":
    run_benchmark()


