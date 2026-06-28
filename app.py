import traceback

import streamlit as st
import pandas as pd

from modules.database import authenticate_user
from modules.ingestion import read_excel
from modules.validation import validate, validate_single_month

from modules.database import (
    connect_db,
    table_exists,
    create_table,
    create_users_table,
    month_exists,
    insert_new_month,
    overwrite_month,
    get_available_months,
    get_available_years,
)

from modules.analytics import (
    get_total_trainings,
    get_total_nominations,
    get_total_confirmed,
    get_average_attendance,
    get_conversion_rate,
    get_confirmed_by_category,
    get_topic_popularity,
    get_attendance_trend,
    get_training_type_distribution,
    get_mode_by_category,
    get_category_analysis,
)

from modules.charts import (
    topic_distribution_chart,
    topic_popularity_chart,
    attendance_trend_chart,
    training_type_donut,
    mode_category_chart,
)

# -----------------------------------
# PAGE CONFIG
# -----------------------------------

st.set_page_config(
    page_title="Training MIS Dashboard",
    layout="wide",
)

# -----------------------------------
# DATABASE CONNECTION
# -----------------------------------

con = connect_db()

# Ensure the users table exists on first run
create_users_table(con)

# -----------------------------------
# LOGIN
# -----------------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown(
        """
        ## Clover Training MIS

        Please sign in to continue.
        """
    )

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if authenticate_user(con, username, password):
            st.session_state.logged_in = True
            st.rerun()
        else:
            st.error("Invalid username or password.")

    st.stop()

st.title("Training MIS Dashboard")

# -----------------------------------
# DATABASE CHECK
# -----------------------------------

data_loaded = table_exists(con)

# -----------------------------------
# DATA UPLOAD
# -----------------------------------

st.sidebar.header("Data Upload")

uploaded_file = st.sidebar.file_uploader(
    "Upload Monthly Excel",
    type=["xlsx"],
)

overwrite_existing = st.sidebar.checkbox("Overwrite Existing Month")

if st.sidebar.button("Load Data"):

    if uploaded_file is None:
        st.sidebar.error("Please upload an Excel file.")

    else:
        try:
            clean_df = read_excel(uploaded_file)
            selected_month = clean_df["month"].iloc[0]
            st.sidebar.info(f"Detected Month: {selected_month}")

            month_error = validate_single_month(clean_df)
            if month_error:
                st.sidebar.error(month_error)
                st.stop()

            errors = validate(clean_df)
            if errors:
                for error in errors:
                    st.sidebar.error(error)
                st.stop()

            if not table_exists(con):
                create_table(con)
                insert_new_month(con, clean_df)
                st.sidebar.success("Database created and data loaded.")
                data_loaded = True

            else:
                exists = month_exists(con, selected_month)

                if exists:
                    if overwrite_existing:
                        overwrite_month(con, clean_df, selected_month)
                        st.sidebar.success(
                            f"{selected_month} overwritten successfully."
                        )
                    else:
                        st.sidebar.warning(
                            f"{selected_month} already exists. "
                            "Tick overwrite if you want to replace it."
                        )
                else:
                    insert_new_month(con, clean_df)
                    st.sidebar.success(
                        f"{selected_month} loaded successfully."
                    )
                    st.rerun()

        except Exception as e:
            traceback.print_exc()
            st.sidebar.error(str(e))

# -----------------------------------
# NO DATA LOADED YET
# -----------------------------------

if not data_loaded:
    st.info(
        "No training data available yet. "
        "Upload your first monthly Excel file from the sidebar."
    )
    st.stop()

# -----------------------------------
# DASHBOARD
# -----------------------------------

st.sidebar.header("Filters")

report_type = st.sidebar.selectbox(
    "Report Type",
    ["Overall", "Monthly", "Yearly"],
)

months = None
year = None

if report_type == "Monthly":
    months = st.sidebar.multiselect(
        "Select Month(s)",
        get_available_months(con),
    )

elif report_type == "Yearly":
    year = st.sidebar.selectbox(
        "Select Year",
        get_available_years(con),
    )

category = st.sidebar.selectbox(
    "Category",
    ["All", "Infra", "ADMS", "Soft Skills"],
)

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# -----------------------------------
# KPI CARDS
# -----------------------------------

total_trainings   = get_total_trainings(con, months, year, category)
total_nominations = get_total_nominations(con, months, year, category)
total_confirmed   = get_total_confirmed(con, months, year, category)
avg_attendance    = get_average_attendance(con, months, year, category)
conversion_rate   = get_conversion_rate(con, months, year, category)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Trainings", total_trainings)

with col2:
    st.metric("Nominations", total_nominations)

with col3:
    st.metric("Confirmed", total_confirmed)

with col4:
    st.metric("Attendance %", avg_attendance)

with col5:
    st.metric("Conversion %", conversion_rate)

st.markdown("---")

# -----------------------------------
# CHARTS
# -----------------------------------

# Chart 1 – Confirmed participants by category
category_bar_df = get_confirmed_by_category(con, months, year, category)
st.plotly_chart(
    topic_distribution_chart(category_bar_df),
    use_container_width=True,
)

# Chart 2 – Top training topics
topic_popularity_df = get_topic_popularity(con, months, year, category)
st.plotly_chart(
    topic_popularity_chart(topic_popularity_df),
    use_container_width=True,
)

# Chart 3 – Attendance trend
attendance_df = get_attendance_trend(con, category)
st.plotly_chart(
    attendance_trend_chart(attendance_df),
    use_container_width=True,
)

# Charts 4 & 5 side by side
col1, col2 = st.columns(2)

with col1:
    training_type_df = get_training_type_distribution(
        con, months, year, category
    )
    st.plotly_chart(
        training_type_donut(training_type_df),
        use_container_width=True,
    )

with col2:
    mode_df = get_mode_by_category(con, months, year, category)
    st.plotly_chart(
        mode_category_chart(mode_df),
        use_container_width=True,
    )

# -----------------------------------
# SUMMARY TABLE
# -----------------------------------

st.markdown("---")

summary_df = get_category_analysis(con, months, year, category)
st.table(summary_df)
