import pandas as pd


def build_filter(months=None, year=None, category=None):
    conditions = []

    if months and year:
        raise ValueError("Use either months or year, not both.")

    if months:
        placeholders = ", ".join(["%s"] * len(months))
        conditions.append(f"month IN ({placeholders})")

    if year:
        conditions.append("year = %s")

    if category and category != "All":
        conditions.append("category = %s")

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    return where


def _params(months=None, year=None, category=None):
    p = []
    if months:
        p.extend(months)
    if year:
        p.append(year)
    if category and category != "All":
        p.append(category)
    return tuple(p)


def _scalar(con, sql, params=()):
    cursor = con.cursor()
    cursor.execute(sql, params)
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None


def get_total_trainings(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"SELECT COUNT(*) FROM training_data {where}"
    return _scalar(con, sql, _params(months, year, category)) or 0


def get_total_nominations(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"SELECT COALESCE(SUM(nominated), 0) FROM training_data {where}"
    return _scalar(con, sql, _params(months, year, category)) or 0


def get_total_confirmed(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"SELECT COALESCE(SUM(confirmed), 0) FROM training_data {where}"
    return _scalar(con, sql, _params(months, year, category)) or 0


def get_average_attendance(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"SELECT AVG(attendance_pct) FROM training_data {where}"
    result = _scalar(con, sql, _params(months, year, category))
    return round(float(result), 2) if result is not None else 0


def get_conversion_rate(con, months=None, year=None, category=None):
    nominations = get_total_nominations(con, months, year, category)
    confirmed = get_total_confirmed(con, months, year, category)
    if nominations == 0:
        return 0
    return round((confirmed / nominations) * 100, 2)


def get_category_analysis(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"""
        SELECT
            category,
            SUM(nominated)                AS total_nominations,
            SUM(confirmed)                AS total_confirmed,
            ROUND(AVG(attendance_pct), 2) AS avg_attendance
        FROM training_data
        {where}
        GROUP BY category
        ORDER BY total_confirmed DESC
    """
    return pd.read_sql(sql, con, params=_params(months, year, category))


def get_confirmed_by_category(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"""
        SELECT
            category,
            SUM(confirmed) AS participants
        FROM training_data
        {where}
        GROUP BY category
        ORDER BY participants DESC
    """
    return pd.read_sql(sql, con, params=_params(months, year, category))


def get_topic_popularity(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"""
        SELECT
            training_topic,
            SUM(confirmed) AS participants
        FROM training_data
        {where}
        GROUP BY training_topic
        ORDER BY participants DESC
        LIMIT 10
    """
    return pd.read_sql(sql, con, params=_params(months, year, category))


def get_training_type_distribution(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"""
        SELECT
            training_type,
            COUNT(*) AS trainings
        FROM training_data
        {where}
        GROUP BY training_type
    """
    return pd.read_sql(sql, con, params=_params(months, year, category))


def get_mode_by_category(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    sql = f"""
        SELECT
            category,
            mode,
            COUNT(*) AS trainings
        FROM training_data
        {where}
        GROUP BY category, mode
    """
    return pd.read_sql(sql, con, params=_params(months, year, category))


def get_attendance_trend(con, category=None):
    if category and category != "All":
        where = "WHERE category = %s"
        params = (category,)
    else:
        where = ""
        params = ()

    sql = f"""
        SELECT * FROM (
            SELECT
                month,
                MIN(date_from)                AS month_date,
                ROUND(AVG(attendance_pct), 2) AS avg_attendance
            FROM training_data
            {where}
            GROUP BY month
        ) sub
        ORDER BY month_date
    """
    return pd.read_sql(sql, con, params=params)


def get_client_analysis(con, months=None, year=None, category=None):
    where = build_filter(months, year, category)
    extra = "client_name IS NOT NULL AND TRIM(client_name) <> ''"
    if where:
        where += f" AND {extra}"
    else:
        where = f"WHERE {extra}"

    sql = f"""
        SELECT
            client_name,
            COUNT(*)       AS trainings,
            SUM(confirmed) AS participants
        FROM training_data
        {where}
        GROUP BY client_name
        ORDER BY participants DESC
    """
    return pd.read_sql(sql, con, params=_params(months, year, category))
