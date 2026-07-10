from collections import defaultdict

import pandas as pd

from db import fetch_all


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


def get_table_detail(table_name):
    columns_sql = """
    SELECT
        column_name,
        data_type,
        ordinal_position
    FROM information_schema.columns
    WHERE table_schema = 'public'
      AND table_name = %s
    ORDER BY ordinal_position;
    """

    pk_sql = """
    SELECT
        tc.constraint_name,
        kcu.column_name
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
     AND tc.table_name = kcu.table_name
    WHERE tc.table_schema = 'public'
      AND tc.table_name = %s
      AND tc.constraint_type = 'PRIMARY KEY'
    ORDER BY kcu.ordinal_position;
    """

    fk_sql = """
    SELECT
        tc.constraint_name,
        kcu.column_name,
        ccu.table_name AS referenced_table,
        ccu.column_name AS referenced_column
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
     AND tc.table_schema = kcu.table_schema
     AND tc.table_name = kcu.table_name
    JOIN information_schema.constraint_column_usage ccu
      ON ccu.constraint_name = tc.constraint_name
    WHERE tc.table_schema = 'public'
      AND tc.table_name = %s
      AND tc.constraint_type = 'FOREIGN KEY'
    ORDER BY kcu.ordinal_position;
    """

    cols_rows = fetch_all(columns_sql, (table_name,))
    pk_rows = fetch_all(pk_sql, (table_name,))
    fk_rows = fetch_all(fk_sql, (table_name,))

    columns = [
        {
            "column_name": r[0],
            "data_type": r[1],
            "ordinal_position": r[2],
        }
        for r in (cols_rows or [])
    ]

    primary_key = None
    if pk_rows:
        primary_key = {
            "constraint_name": pk_rows[0][0],
            "columns": [r[1] for r in pk_rows],
        }

    foreign_keys_map = defaultdict(list)
    for r in fk_rows or []:
        foreign_keys_map[r[0]].append({
            "column_name": r[1],
            "referenced_table": r[2],
            "referenced_column": r[3],
        })

    foreign_keys = []
    for constraint_name, items in foreign_keys_map.items():
        foreign_keys.append({
            "constraint_name": constraint_name,
            "columns": items,
        })

    return {
        "table_name": table_name,
        "columns": columns,
        "primary_key": primary_key,
        "foreign_keys": foreign_keys,
    }


def get_schema_summary_df():
    table_names = get_table_names()
    rows = []
    for table_name in table_names:
        detail = get_table_detail(table_name)
        rows.append({
            "table_name": table_name,
            "primary_key": detail["primary_key"]["constraint_name"] if detail["primary_key"] else None,
            "columns": ", ".join(
                f"{c['column_name']} ({c['data_type']})" for c in detail["columns"]
            ),
            "foreign_keys": ", ".join(
                f"{fk['constraint_name']}" for fk in detail["foreign_keys"]
            ) or None,
        })
    return pd.DataFrame(rows)

