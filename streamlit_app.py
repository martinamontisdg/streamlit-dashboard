# Import python packages
import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import snowflake.connector

st.set_page_config(layout="wide")

st.title("Test Dashboard to Learn")

# Connessione a Snowflake
conn = snowflake.connector.connect(
    user=st.secrets["SNOWFLAKE_USER"],
    password=st.secrets["SNOWFLAKE_PASSWORD"],
    account=st.secrets["SNOWFLAKE_ACCOUNT"],
    warehouse=st.secrets["SNOWFLAKE_WAREHOUSE"],
    database=st.secrets["SNOWFLAKE_DATABASE"],
    schema=st.secrets["SNOWFLAKE_SCHEMA"],
)

query = "SELECT * FROM TRAINIG_FASTSHIP.DWH.MM_DWF_ORDERS"
df = pd.read_sql(query, conn)

conn.close()


st.subheader("Display the first rows")
st.write(df.head())
