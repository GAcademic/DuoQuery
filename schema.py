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


from collections import defaultdict

import pandas as pd
import streamlit as st

from db import fetch_all


@st.cache_data(ttl=300, show_spinner=False)
def get_table_names():
    sql = """
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
      AND table_type = 'BASE TABLE'
    ORDER BY table_name;
    """
    rows = fetch_all(sql)
    return [r[0] for r in rows] if rows else []


@st.cache_data(ttl=300, show_spinner=False)
def get_schema_summary():
    sql = """
    SELECT
        table_name,
        COUNT(*) AS total_columns
    FROM information_schema.columns
    WHERE table_schema = 'public'
    GROUP BY table_name
    ORDER BY table_name;
    """
    rows = fetch_all(sql)
    if not rows:
        return pd.DataFrame(columns=["table_name", "total_columns"])
    return pd.DataFrame(rows, columns=["table_name", "total_columns"])


@st.cache_data(ttl=300, show_spinner=False)
def get_all_table_details():
    """
    Trae columnas, clave primaria y claves foraneas de TODAS las tablas en solo
    3 consultas (en vez de 3 consultas por tabla, como antes), agrupadas en Python.

    Devuelve: {table_name: {table_name, columns, primary_key, foreign_keys}}
    """
    columns_sql = """
    SELECT table_name, column_name, data_type, ordinal_position
    FROM information_schema.columns
    WHERE table_schema = 'public'
    ORDER BY table_name, ordinal_position;
    """

    pk_sql = """
    SELECT tc.table_name, tc.constraint_name, kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
     AND tc.table_name = kcu.table_name
    WHERE tc.table_schema = 'public'
      AND tc.constraint_type = 'PRIMARY KEY'
    ORDER BY tc.table_name, kcu.ordinal_position;
    """

    fk_sql = """
    SELECT tc.table_name, tc.constraint_name, kcu.column_name,
           ccu.table_name AS referenced_table, ccu.column_name AS referenced_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
     AND tc.table_name = kcu.table_name
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_schema = 'public'
      AND tc.constraint_type = 'FOREIGN KEY'
    ORDER BY tc.table_name, kcu.ordinal_position;
    """

    columns_rows = fetch_all(columns_sql) or []
    pk_rows = fetch_all(pk_sql) or []
    fk_rows = fetch_all(fk_sql) or []

    columns_by_table = defaultdict(list)
    for table_name, column_name, data_type, ordinal_position in columns_rows:
        columns_by_table[table_name].append({
            "column_name": column_name,
            "data_type": data_type,
            "ordinal_position": ordinal_position,
        })

    pk_by_table = {}
    for table_name, constraint_name, column_name in pk_rows:
        pk = pk_by_table.setdefault(
            table_name, {"constraint_name": constraint_name, "columns": []}
        )
        pk["columns"].append(column_name)

    fk_columns_by_table = defaultdict(lambda: defaultdict(list))
    for table_name, constraint_name, column_name, referenced_table, referenced_column in fk_rows:
        fk_columns_by_table[table_name][constraint_name].append({
            "column_name": column_name,
            "referenced_table": referenced_table,
            "referenced_column": referenced_column,
        })

    all_tables = set(columns_by_table) | set(pk_by_table) | set(fk_columns_by_table)

    details = {}
    for table_name in all_tables:
        foreign_keys = [
            {"constraint_name": constraint_name, "columns": items}
            for constraint_name, items in fk_columns_by_table.get(table_name, {}).items()
        ]
        details[table_name] = {
            "table_name": table_name,
            "columns": columns_by_table.get(table_name, []),
            "primary_key": pk_by_table.get(table_name),
            "foreign_keys": foreign_keys,
        }

    return details


def get_table_detail(table_name):
    """
    Mantiene la misma firma que antes (detalle de una tabla), pero ahora reutiliza
    la cache de get_all_table_details() en vez de lanzar 3 consultas nuevas cada vez.
    """
    details = get_all_table_details()
    return details.get(table_name, {
        "table_name": table_name,
        "columns": [],
        "primary_key": None,
        "foreign_keys": [],
    })


def get_schema_summary_df():
    details = get_all_table_details()
    rows = []
    for table_name in sorted(details.keys()):
        detail = details[table_name]
        rows.append({
            "table_name": table_name,
            "primary_key": detail["primary_key"]["constraint_name"] if detail["primary_key"] else None,
            "columns": ", ".join(
                f"{c['column_name']} ({c['data_type']})" for c in detail["columns"]
            ),
            "foreign_keys": ", ".join(
                fk["constraint_name"] for fk in detail["foreign_keys"]
            ) or None,
        })
    return pd.DataFrame(rows)
