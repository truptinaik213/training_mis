"""Database helpers for the MIS Clover project (MySQL only)."""
import mysql.connector
import pandas as pd
import numpy as np
import streamlit as st
MYSQL_HOST = st.secrets["mysql.railway.internal"]
MYSQL_USER = st.secrets["root"]
MYSQL_PASSWORD = st.secrets["HxfVqsFkuNfOKKfKtaDElGbeAxEssJiN"]
MYSQL_DATABASE = st.secrets["railway"]
MYSQL_PORT = st.secrets["3306"]
def connect_db():
    con = mysql.connector.connect(
    host="mysql.railway.internal",
    user="root",
    password="HxfVqsFkuNfOKKfKtaDElGbeAxEssJiN",
    database="railway",
    port="3306",
)
    return con


def table_exists(con):
    cursor = con.cursor()
    cursor.execute("SHOW TABLES LIKE 'training_data'")
    result = cursor.fetchone()
    cursor.close()
    return result is not None


def create_table(con):
    cursor = con.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS training_data (
            category        VARCHAR(100),
            training_topic  VARCHAR(255),
            date_from       DATE,
            date_to         DATE,
            sessions        INT,
            nominated       INT,
            confirmed       INT,
            attendance_pct  DECIMAL(5,2),
            training_type   VARCHAR(100),
            client_name     VARCHAR(255),
            mode            VARCHAR(100),
            remarks         TEXT,
            status          VARCHAR(100),
            month           VARCHAR(20),
            year            INT,
            upload_time     DATETIME
        )
        """
    )
    con.commit()
    cursor.close()


def create_users_table(con):
    cursor = con.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id       INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE,
            password VARCHAR(255)
        )
        """
    )
    con.commit()
    cursor.execute(
        "INSERT IGNORE INTO users (username, password) VALUES ('admin', 'admin123')"
    )
    con.commit()
    cursor.close()


def authenticate_user(con, username, password):
    cursor = con.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM users WHERE username=%s AND password=%s",
        (username, password),
    )
    result = cursor.fetchone()[0]
    cursor.close()
    return result > 0


def month_exists(con, selected_month):
    cursor = con.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM training_data WHERE month=%s",
        (selected_month,),
    )
    result = cursor.fetchone()[0]
    cursor.close()
    return result > 0


def insert_new_month(con, df: pd.DataFrame):
    cursor = con.cursor()
    query = (
        "INSERT INTO training_data (category, training_topic, date_from, date_to,"
        " sessions, nominated, confirmed, attendance_pct, training_type, client_name,"
        " mode, remarks, status, month, year, upload_time) VALUES ("
        + ",".join(["%s"] * 16)
        + ")"
    )

    df = df.where(pd.notnull(df), None)
    df["year"] = pd.to_numeric(df["year"], errors="coerce").fillna(0).astype(int)
    df = df[[
        "category", "training_topic", "date_from", "date_to",
        "sessions", "nominated", "confirmed", "attendance_pct",
        "training_type", "client_name", "mode", "remarks",
        "status", "month", "year", "upload_time",
    ]]

    data = []
    for row in df.itertuples(index=False):
        clean_row = []
        for v in row:
            try:
                is_null = pd.isna(v)
            except (TypeError, ValueError):
                is_null = False
            if is_null:
                clean_row.append(None)
            elif isinstance(v, np.integer):
                clean_row.append(int(v))
            elif isinstance(v, np.floating):
                clean_row.append(float(v))
            elif isinstance(v, pd.Timestamp):
                clean_row.append(v.to_pydatetime())
            else:
                clean_row.append(v)
        data.append(tuple(clean_row))

    cursor.executemany(query, data)
    con.commit()
    cursor.close()


def overwrite_month(con, df: pd.DataFrame, selected_month):
    cursor = con.cursor()
    cursor.execute("DELETE FROM training_data WHERE month=%s", (selected_month,))
    con.commit()
    cursor.close()
    insert_new_month(con, df)


def fetch_data(con):
    return pd.read_sql("SELECT * FROM training_data", con)


def get_available_months(con):
    query = "SELECT month FROM training_data GROUP BY month ORDER BY MIN(date_from)"
    return pd.read_sql(query, con)["month"].tolist()


def get_available_years(con):
    query = "SELECT DISTINCT year FROM training_data ORDER BY year"
    return pd.read_sql(query, con)["year"].tolist()
