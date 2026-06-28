import pandas as pd
import datetime


def read_excel(file_path):
    df = pd.read_excel(file_path)
    df = df.rename(columns={
        "Category": "category",
        "Training Topic": "training_topic",
        "Date From": "date_from",
        "Date To": "date_to",
        "No. of Sessions": "sessions",
        "Nominated": "nominated",
        "Confirmed": "confirmed",
        "Avg Attendance": "attendance_pct",
        "Training Type": "training_type",
        "Client Name": "client_name",
        "Mode": "mode",
        "Remarks": "remarks",
        "Status": "status",
    })

    # FIX: drop any row that has no category AND no training_topic
    # these are blank/total rows at the bottom of the Excel
    df = df.dropna(subset=["category", "training_topic"], how="all")

    # FIX: also drop rows where category is NaN (summary/total rows)
    df = df[df["category"].notna()]

    df["date_from"] = pd.to_datetime(
        df["date_from"], errors="coerce", dayfirst=True
    )
    df["date_to"] = pd.to_datetime(
        df["date_to"], errors="coerce", dayfirst=True
    )

    # FIX: strip whitespace so MySQL GROUP BY works correctly
    for col in ["category", "mode", "training_type", "status"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            # replace string 'nan' that astype(str) produces for NaN cells
            df[col] = df[col].replace("nan", None)

    # FIX: cast numeric columns to proper int (Excel stores as float when NaN present)
    for col in ["sessions", "nominated", "confirmed"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    df["attendance_pct"] = pd.to_numeric(
        df["attendance_pct"], errors="coerce"
    )

    # System columns
    df["month"] = df["date_from"].dt.strftime("%b-%Y")
    df["year"] = (
        df["date_from"].dt.year.fillna(0).astype(int)
    )
    df["upload_time"] = datetime.datetime.now()

    return df
