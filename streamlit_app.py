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

query = "SELECT * FROM CSV_FASTSHIP_ORDERS"
df = pd.read_sql(query, conn)

conn.close()
st.subheader("Display the first rows")
st.write(df.head())

st.sidebar.subheader("Dynamic Filter")
max_filter = max(1, len(df.columns))
num_filters = st.sidebar.number_input(
    "Number of filters to add", min_value=0, max_value=max_filter, value=0, step=1
)

selected_filters = []
selected_values = []

if num_filters > 0:
    for i in range(num_filters):
        col1, col2 = st.columns(2)
        with col1:
            filter_column = st.selectbox(
                "Select the column to filter by",
                df.columns.to_list(),
                key=f"f{i}_column",
            )
            unique_values = df[filter_column].dropna().unique()
        with col2:
            filter_value = st.selectbox(
                "Select the value to filter by",
                unique_values,
                key=f"f{i}_value",
            )
        selected_filters.append(filter_column)
        selected_values.append(filter_value)

    df_filtered = df.copy()
    for col, val in zip(selected_filters, selected_values):
        df_filtered = df_filtered[df_filtered[col] == val]

    st.subheader("Filtered Data:")
    st.write(df_filtered)

    st.download_button(
        label="Download filtered data as CSV file",
        data=df_filtered.to_csv(index=False),
        file_name="filtered_data.csv",
        mime="text/csv",
    )

    tab1, tab2, tab3 = st.tabs(["Dati", "Visualization", "Esportazione & Statistiche"])

    with tab1:
        st.subheader("Correlation Chart Between 2 Categories")
        if len(selected_filters) >= 2:
            pivot = pd.crosstab(
                df_filtered[selected_filters[0]], df_filtered[selected_filters[1]]
            )
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(pivot, annot=True, fmt="d", cmap="Blues", cbar=True, ax=ax)
            ax.set_xlabel(selected_filters[0])
            ax.set_ylabel(selected_filters[1])
            ax.set_title(
                f"Correlation between {selected_filters[0]} and {selected_filters[1]}"
            )
            st.pyplot(fig)
        else:
            st.warning("Please apply at least 2 filters to show the correlation chart.")

    with tab2:
        st.subheader("Bar Chart of Numerical Column")
        numerical_cols = df_filtered.select_dtypes(include=["number"]).columns.tolist()
        if numerical_cols:
            selected_num_col = st.selectbox(
                "Select numerical column to plot", numerical_cols
            )
            selected_cat_col = st.selectbox(
                "Group by column", df_filtered.columns, index=0
            )
            bar_data = (
                df_filtered.groupby(selected_cat_col)[selected_num_col]
                .sum()
                .reset_index()
            )
            fig2, ax2 = plt.subplots(figsize=(10, 6))
            sns.barplot(data=bar_data, x=selected_cat_col, y=selected_num_col, ax=ax2)
            ax2.set_title(f"{selected_num_col} by {selected_cat_col}")
            st.pyplot(fig2)
        else:
            st.info("No numerical columns available for bar chart.")

    with tab3:
        st.subheader("Statistical Summary")
        st.write(df_filtered.describe())
else:
    st.info("Add at least one filter to access full dashboard features.")
