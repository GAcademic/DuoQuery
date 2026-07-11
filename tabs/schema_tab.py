import pandas as pd
import streamlit as st

from schema import get_schema_summary, get_table_names, get_table_detail

def render_schema_tab():
    st.subheader("Esquema de la base de datos")
    st.caption("Vista básica: tabla, clave primaria, columnas y claves foráneas.")

    summary_df = get_schema_summary()
    if summary_df is not None and not summary_df.empty:
        st.markdown("### Resumen del esquema")
        st.dataframe(summary_df, use_container_width=True)

    st.markdown("### Tablas")
    table_names = get_table_names()

    for table_name in table_names:
        detail = get_table_detail(table_name)

        with st.expander(table_name, expanded=False):
            st.markdown("**Clave primaria**")
            pk = detail.get("primary_key")
            if pk:
                st.write(f"{pk['constraint_name']}: {', '.join(pk['columns'])}")
            else:
                st.write("No definida")

            st.markdown("**Columnas y tipo**")
            cols = detail.get("columns", [])
            if cols:
                cols_df = pd.DataFrame(cols)[["column_name", "data_type"]]
                cols_df.columns = ["column_name", "data_type"]
                st.dataframe(cols_df, use_container_width=True, hide_index=True)
            else:
                st.write("Sin columnas.")

            st.markdown("**Claves foráneas**")
            fks = detail.get("foreign_keys", [])
            if fks:
                fk_rows = []
                for fk in fks:
                    for item in fk["columns"]:
                        fk_rows.append({
                            "constraint_name": fk["constraint_name"],
                            "column_name": item["column_name"],
                            "referenced_table": item["referenced_table"],
                            "referenced_column": item["referenced_column"],
                        })
                fk_df = pd.DataFrame(fk_rows)
                st.dataframe(fk_df, use_container_width=True, hide_index=True)
            else:
                st.write("No definidas.")


