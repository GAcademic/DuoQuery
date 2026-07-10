import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.getenv("DB_HOST", "db")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "duoquery")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

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
        cur.execute(query, params or ())
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
        cur.execute(query, params or ())
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
        cur.execute(query, params or ())

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
        cur.execute(explain_sql, params or ())
        return cur.fetchone()[0]
    finally:
        if cur is not None:
            cur.close()
        if conn is not None:
            conn.close()

def is_select(query):
    q = query.strip().lower()
    return q.startswith("select") or q.startswith("with")
