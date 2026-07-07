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
