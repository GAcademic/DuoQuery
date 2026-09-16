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


import os
import psycopg2
import sqlparse

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "pagila")
DB_USER = os.getenv("DB_USER", "duoquery")
DB_PASSWORD = os.getenv("DB_PASSWORD", "duoquery")

def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )

def fetch_all(query, params=None):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or None)
        return cur.fetchall()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def fetch_one(query, params=None):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or None)
        return cur.fetchone()
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def run_query(query, params=None):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(query, params or None)

        if cur.description is None:
            conn.commit()
            return None

        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        return columns, rows
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def run_explain(query, params=None, analyze=True, buffers=True, verbose=True, format_json=True):
    conn = None
    cur = None
    try:
        conn = get_connection()
        cur = conn.cursor()

        options = []
        if analyze:
            options.append("ANALYZE")
        if buffers:
            options.append("BUFFERS")
        if verbose:
            options.append("VERBOSE")
        if format_json:
            options.append("FORMAT JSON")

        explain_sql = f"EXPLAIN ({', '.join(options)}) {query}"
        cur.execute(explain_sql, params or None)
        return cur.fetchone()[0]
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def is_select(query):
    """
    Valida que la query sea una única sentencia de lectura (SELECT, o WITH ... SELECT).

    A diferencia de un simple startswith(), esto rechaza:
    - varias sentencias apiladas separadas por ';' (p. ej. 'SELECT 1; DROP TABLE film;'),
    - sentencias no-SELECT precedidas de comentarios (p. ej. '-- x\nDROP TABLE film;'),
    - cadenas vacias o solo con comentarios/espacios.
    """
    if not query or not query.strip():
        return False

    statements = [
        s for s in sqlparse.parse(query)
        if s.token_first(skip_cm=True) is not None
    ]

    if len(statements) != 1:
        return False

    return statements[0].get_type() == "SELECT"
