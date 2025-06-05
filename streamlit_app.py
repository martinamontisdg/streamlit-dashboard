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

# Assicuriamoci che le colonne data siano in formato datetime
for col in df.columns:
    if "date" in col.lower():
        df[col] = pd.to_datetime(df[col], errors="coerce")

st.subheader("Display the first rows")
st.write(df.head())

st.sidebar.subheader("Dynamic Filter")

st.write("Select the number of filters to apply to the data.")
max_filter = max(1, len(df.columns))
num_filters = st.number_input(
    "Number of filters to add", min_value=0, max_value=max_filter, value=0, step=1
)

selected_filters = []

if num_filters > 0:
    for i in range(num_filters):
        col1, col2, col3 = st.columns([3, 2, 3])
        with col1:
            filter_column = st.selectbox(
                f"Filter {i+1}: Select column",
                df.columns.to_list(),
                key=f"f{i}_column",
            )
        with col2:
            operator = st.selectbox(
                f"Filter {i+1}: Operator",
                ["==", ">", ">=", "<", "<="],
                key=f"f{i}_operator",
            )
        with col3:
            if pd.api.types.is_numeric_dtype(df[filter_column]):
                filter_value = st.number_input(
                    f"Filter {i+1}: Value",
                    value=float(df[filter_column].min()),
                    key=f"f{i}_value",
                )
            elif pd.api.types.is_datetime64_any_dtype(df[filter_column]):
                min_date = df[filter_column].min()
                max_date = df[filter_column].max()
                filter_value = st.date_input(
                    f"Filter {i+1}: Date",
                    value=min_date.date() if pd.notnull(min_date) else None,
                    min_value=min_date.date() if pd.notnull(min_date) else None,
                    max_value=max_date.date() if pd.notnull(max_date) else None,
                    key=f"f{i}_value",
                )
                filter_value = pd.to_datetime(filter_value)
            else:
                unique_values = df[filter_column].dropna().unique()
                filter_value = st.selectbox(
                    f"Filter {i+1}: Value",
                    unique_values,
                    key=f"f{i}_value",
                )
        selected_filters.append((filter_column, operator, filter_value))

    df_filtered = df.copy()
    for col, op, val in selected_filters:
        if op == "==":
            df_filtered = df_filtered[df_filtered[col] == val]
        elif op == ">":
            df_filtered = df_filtered[df_filtered[col] > val]
        elif op == ">=":
            df_filtered = df_filtered[df_filtered[col] >= val]
        elif op == "<":
            df_filtered = df_filtered[df_filtered[col] < val]
        elif op == "<=":
            df_filtered = df_filtered[df_filtered[col] <= val]

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
                df_filtered[selected_filters[0][0]], df_filtered[selected_filters[1][0]]
            )
            fig, ax = plt.subplots(figsize=(10, 6))
            sns.heatmap(pivot, annot=True, fmt="d", cmap="Blues", cbar=True, ax=ax)
            ax.set_xlabel(selected_filters[0][0])
            ax.set_ylabel(selected_filters[1][0])
            ax.set_title(
                f"Correlation between {selected_filters[0][0]} and {selected_filters[1][0]}"
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
