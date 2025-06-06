import streamlit as st
import pandas as pd
import snowflake.connector


# Snowflake session
def snowflake_connection():
    conn = snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database=st.secrets["snowflake"]["database"],
        schema=st.secrets["snowflake"]["schema"],
    )
    return conn


@st.cache_data
def load_data():
    conn = snowflake_connection()
    query = "SELECT * FROM TRAINING_FASTSHIP.DWH.MM_DWF_ORDERS"
    df = pd.read_sql(query, conn)
    conn.close()
    return df


df = load_data()
editable_columns = ["RETURNED_FL", "QTY"]

column_config = {}
for col in df.columns:
    if col in editable_columns:
        dtype = df[col].dtype
        if pd.api.types.is_integer_dtype(dtype) or pd.api.types.is_float_dtype(dtype):
            column_config[col] = st.column_config.NumberColumn(disabled=False)
        elif pd.api.types.is_bool_dtype(dtype):
            column_config[col] = st.column_config.CheckboxColumn(disabled=False)
        else:
            column_config[col] = st.column_config.TextColumn(disabled=False)
    else:
        column_config[col] = st.column_config.TextColumn(disabled=True)

st.title("📝 Tabella modificabile: RETURNED_FL e QTY")
edited_df = st.data_editor(
    df, column_config=column_config, key="editable_table", use_container_width=True
)

# Detect changes
changed_rows = []
for i in range(len(df)):
    row_orig = df.iloc[i]
    row_mod = edited_df.iloc[i]
    if not row_orig[editable_columns].equals(row_mod[editable_columns]):
        changed_rows.append(row_mod)

# 🔴 Evidenzia modifiche live
if changed_rows:
    st.subheader("🔴 Righe modificate (non ancora salvate)")
    df_mod = pd.DataFrame(changed_rows)
    st.dataframe(
        df_mod.style.applymap(
            lambda val: "background-color: #ffcccc", subset=editable_columns
        )
    )
else:
    st.info("Nessuna modifica in corso.")


def update_table(original_df, modified_df, key_columns):
    changed_rows = []
    for i in range(len(original_df)):
        row_orig = original_df.iloc[i]
        row_mod = modified_df.iloc[i]
        if not row_orig[editable_columns].equals(row_mod[editable_columns]):
            changed_rows.append(row_mod)

    if changed_rows:
        for row in changed_rows:
            row_dict = row.to_dict()
            update_query = f"""
                UPDATE TRAINING_FASTSHIP.DWH.MM_DWF_ORDERS
                SET RETURNED_FL = {row_dict['RETURNED_FL']}, QTY = {row_dict['QTY']}
                WHERE ORDER_ID = '{row_dict['ORDER_ID']}'
            """
            conn = snowflake_connection()
            cursor = conn.cursor()
            try:
                cursor.execute(update_query)
            except Exception as e:
                st.error(f"Errore durante l'aggiornamento: {e}")
            finally:
                cursor.close()
            conn.close()
        st.success(f"🟢 {len(changed_rows)} righe aggiornate con successo.")
        st.dataframe(
            pd.DataFrame(changed_rows).style.applymap(
                lambda val: "background-color: #ccffcc", subset=editable_columns
            )
        )
    else:
        st.info("Nessuna modifica da salvare.")


if st.button("💾 Salva modifiche"):
    if "ORDER_ID" not in df.columns:
        st.error(
            "Colonna 'ORDER_ID' mancante: serve per identificare univocamente le righe."
        )
    else:
        update_table(df, edited_df, key_columns=["ORDER_ID"])
