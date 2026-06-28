def validate(df):
    errors = []
    #mandatory fields cannot be empty
    mandatory_columns = [
    "category",
    "training_topic",
    "date_from",
    "date_to",
    "sessions",
    "attendance_pct",
    "training_type",
    "nominated",
    "confirmed",
    "mode",
    "status"
    ]
    for col in mandatory_columns:

        if df[col].isnull().any():

            errors.append(
                f"Missing values found in {col}"
            )

    if len(
        df[
            df["confirmed"]
            >
            df["nominated"]
        ]
    ) > 0:

        errors.append(
            "Confirmed cannot exceed nominations."
        )

    if len(
        df[
            (df["attendance_pct"] < 0)
            |
            (df["attendance_pct"] > 100)
        ]
    ) > 0:

        errors.append(
            "Attendance percentage must be between 0 and 100."
        )

    if len(
        df[
            df["date_to"]
            <
            df["date_from"]
        ]
    ) > 0:

        errors.append(
            "Date To cannot be earlier than Date From."
        )

    valid_categories = [
        "Infra",
        "ADMS",
        "Soft Skills"
    ]

    if len(
        df[
            ~df["category"].isin(
                valid_categories
            )
        ]
    ) > 0:

        errors.append(
            "Invalid category found."
        )
    invalid_rows = df[
    (df["training_type"] == "Client Request")
    &
    (
        df["client_name"].isnull()
    )
    ]
    if len(invalid_rows) > 0:
        errors.append(
        "Client Name required for Client Request trainings."
    )

    return errors

def validate_single_month(df):

    months = (
        df["date_from"]
        .dt.strftime("%b-%Y")
        .unique()
    )

    if len(months) > 1:

        return (
            f"File contains multiple months: "
            f"{', '.join(months)}"
        )

    return None