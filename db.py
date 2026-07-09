import os
import psycopg2

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        port=os.getenv("DB_PORT", "5432"),
        dbname=os.getenv("DB_NAME", "pagila"),
        user=os.getenv("DB_USER", "duoquery"),
        password=os.getenv("DB_PASSWORD", "duoquery"),
    )

def is_select(query):
    q = query.strip().lower()
    return q.startswith("select")

def run_query(query):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query)
            if cur.description is None:
                return None
            columns = [desc[0] for desc in cur.description]
            rows = cur.fetchall()
        return columns, rows
    finally:
        conn.close()

def run_explain(query):
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}")
            result = cur.fetchone()[0]
        return result
    finally:
        conn.close()
