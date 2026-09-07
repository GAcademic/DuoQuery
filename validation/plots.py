"""
plots.py - Genera las figuras del capítulo de validación a partir de los CSV.

Lee results_energy.csv y results_efficiency.csv (y el diccionario de factores de
emisión del modelo) y produce cinco figuras PNG en validation/figures/.

Los PNG son un derivado determinista de los CSV: no se versionan (ver .gitignore),
se regeneran ejecutando este script. Se ejecuta desde la raiz del proyecto para
que el import de energy funcione:

    python -m validation.plots
"""

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sin ventana; solo guarda ficheros
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

from energy.model import FACTORES_EMISION


BASE = Path(__file__).parent
FIG_DIR = BASE / "figures"

# Paleta consistente para toda la memoria.
AZUL = "#4C72B0"      # neutro / proyección de columnas / CPU
ROJO = "#C44E52"      # foco: SELECT * (fig. 3) y España (fig. 5)
NARANJA = "#DD8452"   # trabajo desperdiciado (métrica distinta)
MORADO = "#9467BD"    # memoria (paleta accesible, sin rojo/verde)
GRIS = "#8C8C8C"      # disco


def _leer(nombre):
    with open(BASE / nombre, encoding="utf-8") as f:
        return {fila["query_id"]: fila for fila in csv.DictReader(f)}


def _guardar(fig, nombre):
    ruta = FIG_DIR / nombre
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  {ruta.name}")


# --- Figura 1: energía total por consulta -----------------------------------

def figura_1_energia_total(energy):
    datos = sorted(
        ((qid, float(f["mean_energy_total_j"])) for qid, f in energy.items()),
        key=lambda x: x[1],
    )
    etiquetas = [d[0] for d in datos]
    valores = [d[1] for d in datos]

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.barh(etiquetas, valores, color=AZUL)
    ax.set_xscale("log")
    ax.set_xlabel("Energía total estimada (J, escala logarítmica)")
    ax.set_title("Energía estimada por consulta")
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    _guardar(fig, "1_energia_total.png")


# --- Figura 2: desglose CPU / memoria / disco -------------------------------

def figura_2_desglose(energy):
    ids = ["Q1B", "Q2B", "Q1W", "Q2W"]
    cpu = [float(energy[q]["mean_energy_cpu_j"]) for q in ids]
    mem = [float(energy[q]["mean_energy_memory_j"]) for q in ids]
    disco = [float(energy[q]["mean_energy_disk_j"]) for q in ids]

    x = range(len(ids))
    w = 0.26

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar([i - w for i in x], cpu, w, label="CPU", color=AZUL)
    ax.bar(list(x), mem, w, label="Memoria", color=MORADO)
    ax.bar([i + w for i in x], disco, w, label="Disco", color=GRIS)
    ax.set_yscale("log")
    ax.set_ylabel("Energía estimada (J, escala logarítmica)")
    ax.set_title("Aporte energético por componente")
    ax.set_xticks(list(x))
    ax.set_xticklabels(ids)
    ax.legend()
    _guardar(fig, "2_desglose_componentes.png")


# --- Figura 3: SELECT * frente a proyección (energia vs transferencia) -------

def figura_3_select_star(energy, eff):
    tablas = ["normal", "grande", "ancha"]
    pares = {"normal": ("Q1", "Q2"),
             "grande": ("Q1B", "Q2B"),
             "ancha": ("Q1W", "Q2W")}

    e_star = [float(energy[pares[t][0]]["mean_energy_total_j"]) for t in tablas]
    e_col = [float(energy[pares[t][1]]["mean_energy_total_j"]) for t in tablas]
    b_star = [float(eff[pares[t][0]]["bytes_transferencia_estimados"]) for t in tablas]
    b_col = [float(eff[pares[t][1]]["bytes_transferencia_estimados"]) for t in tablas]

    x = range(len(tablas))
    w = 0.38
    izq = [i - w / 2 for i in x]
    der = [i + w / 2 for i in x]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 5))

    ax1.bar(izq, e_star, w, label="SELECT *", color=ROJO)
    ax1.bar(der, e_col, w, label="Columnas", color=AZUL)
    ax1.set_yscale("log")
    ax1.set_ylabel("Energía estimada (J, log)")
    ax1.set_title("Energía")
    ax1.set_xticks(list(x))
    ax1.set_xticklabels(tablas)
    ax1.legend()

    ax2.bar(izq, b_star, w, label="SELECT *", color=ROJO)
    ax2.bar(der, b_col, w, label="Columnas", color=AZUL)
    ax2.set_yscale("log")
    ax2.set_ylabel("Transferencia estimada (bytes, log)")
    ax2.set_title("Transferencia estimada")
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(tablas)
    ax2.legend()

    fig.suptitle("Energía y transferencia estimadas")
    _guardar(fig, "3_select_star.png")


# --- Figura 4: trabajo desperdiciado ----------------------------------------

def figura_4_desperdiciado(eff):
    ids = ["Q4", "Q5", "STAR", "Q6"]
    valores = [float(eff[q]["porcentaje_desperdicio"]) for q in ids]

    fig, ax = plt.subplots(figsize=(7, 5))
    ax.bar(ids, valores, color=NARANJA)
    ax.set_ylabel("Trabajo desperdiciado (%)")
    ax.set_title("Trabajo desperdiciado por consulta")
    ax.set_ylim(0, 105)
    for i, v in enumerate(valores):
        ax.text(i, v + 1.5, f"{v:.1f}%", ha="center", va="bottom", fontsize=9)
    _guardar(fig, "4_trabajo_desperdiciado.png")


# --- Figura 5: CO2e por país -------------------------------------------------

def figura_5_co2e_pais():
    items = sorted(FACTORES_EMISION.items(), key=lambda kv: kv[1][0])
    paises = [k for k, _ in items]
    factores = [v[0] for _, v in items]
    colores = [ROJO if "España" in p else AZUL for p in paises]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(paises, factores, color=colores)
    ax.set_xlabel("Factor de emisión (kg CO₂e por kWh)")
    ax.set_title("Factor de emisión por país y fuente")
    ax.grid(axis="x", linestyle=":", alpha=0.6)
    ax.legend(handles=[
        Patch(color=ROJO, label="España (MITECO / Ember)"),
        Patch(color=AZUL, label="Otros países"),
    ])
    _guardar(fig, "5_co2e_por_pais.png")


def main():
    FIG_DIR.mkdir(exist_ok=True)
    energy = _leer("results_energy.csv")
    eff = _leer("results_efficiency.csv")

    print("Generando figuras:")
    figura_1_energia_total(energy)
    figura_2_desglose(energy)
    figura_3_select_star(energy, eff)
    figura_4_desperdiciado(eff)
    figura_5_co2e_pais()
    print(f"Listo. Figuras en {FIG_DIR}")


if __name__ == "__main__":
    main()
