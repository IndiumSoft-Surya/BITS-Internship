import pandas as pd
from sqlalchemy import text
 
# ============ OVERVIEW & DAILY SNAPSHOT QUERIES ============
 
def get_overall_activity_summary(engine):
    """Fetches high-level summary statistics for ALL transactions in the dataset."""
    query = text("""
    SELECT
        COUNT(DISTINCT t.client_id) AS total_clients,
        SUM(t.amount) AS total_transaction_volume,
        COUNT(t.id) AS total_transactions,
        AVG(t.amount) AS avg_transaction_value
    FROM transactions_data t;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
 
def get_avg_activity_by_dow(engine):
    """Calculates the average transaction count and amount for each day of the week."""
    query = text("""
    WITH daily_dow_summary AS (
        SELECT
            t.date::date AS day,
            EXTRACT(DOW FROM t.date) AS day_of_week_num,
            CASE EXTRACT(DOW FROM t.date)
                WHEN 0 THEN 'Sunday' WHEN 1 THEN 'Monday' WHEN 2 THEN 'Tuesday'
                WHEN 3 THEN 'Wednesday' WHEN 4 THEN 'Thursday' WHEN 5 THEN 'Friday'
                WHEN 6 THEN 'Saturday'
            END AS day_of_week_name,
            COUNT(t.id) AS total_count,
            SUM(t.amount) AS total_amount
        FROM transactions_data t
        GROUP BY day, day_of_week_num, day_of_week_name
    )
    SELECT
        day_of_week_num,
        day_of_week_name,
        AVG(total_count) AS avg_txns_count,
        AVG(total_amount) AS avg_txns_amount
    FROM daily_dow_summary
    GROUP BY day_of_week_num, day_of_week_name
    ORDER BY day_of_week_num;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
 
def get_avg_activity_by_hour(engine):
    """Calculates the average transaction count and amount for each hour of the day."""
    query = text("""
    SELECT
        EXTRACT(HOUR FROM date) AS hour,
        COUNT(id) / CAST(COUNT(DISTINCT date::date) AS NUMERIC) AS avg_txns_count,
        SUM(amount) / CAST(COUNT(DISTINCT date::date) AS NUMERIC) AS avg_txns_amount
    FROM transactions_data
    GROUP BY hour
    ORDER BY hour;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
 
def get_overall_daily_trend(engine):
    """Gets the daily count and amount of all transactions over the entire history."""
    query = text("""
    SELECT
        date::date AS day,
        COUNT(id) AS total_count,
        SUM(amount) AS total_amount
    FROM transactions_data
    GROUP BY day
    ORDER BY day;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, parse_dates=["day"])
 
def get_activity_by_gender_overall(engine):
    """Gets total transaction count and amount by gender for the entire dataset."""
    query = text("""
    SELECT u.gender, COUNT(t.id) AS transaction_count, SUM(t.amount) AS total_amount
    FROM transactions_data t
    JOIN users_data u ON t.client_id = u.id
    GROUP BY u.gender;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
 
def get_activity_by_age_overall(engine):
    """Gets total transaction count and amount by age group for the entire dataset."""
    query = text("""
    SELECT
        CASE
            WHEN u.current_age < 20 THEN '<20' WHEN u.current_age BETWEEN 20 AND 29 THEN '20-29'
            WHEN u.current_age BETWEEN 30 AND 39 THEN '30-39' WHEN u.current_age BETWEEN 40 AND 49 THEN '40-49'
            WHEN u.current_age BETWEEN 50 AND 59 THEN '50-59' WHEN u.current_age BETWEEN 60 AND 69 THEN '60-69'
            ELSE '70+'
        END AS age_group,
        COUNT(t.id) AS transaction_count,
        SUM(t.amount) AS total_amount
    FROM transactions_data t
    JOIN users_data u ON t.client_id = u.id
    GROUP BY age_group
    ORDER BY age_group;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
 
def get_daily_activity_summary_with_comparison(engine, on_date):
    """Fetches key TOTAL activity metrics for a given day and the previous day."""
    query = text("""
    SELECT
        SUM(CASE WHEN t.date::date = CAST(:on_date AS DATE) THEN 1 ELSE 0 END) AS total_txns,
        SUM(CASE WHEN t.date::date = CAST(:on_date AS DATE) THEN t.amount ELSE 0 END) AS total_amount,
        SUM(CASE WHEN t.date::date = CAST(:on_date AS DATE) - INTERVAL '1 day' THEN 1 ELSE 0 END) AS prev_day_total_txns,
        SUM(CASE WHEN t.date::date = CAST(:on_date AS DATE) - INTERVAL '1 day' THEN t.amount ELSE 0 END) AS prev_day_total_amount
    FROM transactions_data t
    WHERE t.date::date = CAST(:on_date AS DATE) OR t.date::date = CAST(:on_date AS DATE) - INTERVAL '1 day';
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"on_date": on_date})
 
def activity_by_mcc(engine, on_date):
    """Finds the top 10 merchant categories with the most transactions (count and amount) on a given day."""
    query = text("""
    SELECT m.description AS mcc_category, COUNT(t.id) AS transaction_count, SUM(t.amount) as total_amount
    FROM transactions_data t
    JOIN mcc_codes m ON t.mcc::text = m.mcc_code::text
    WHERE t.date::date = :on_date
    GROUP BY m.description
    ORDER BY transaction_count DESC
    LIMIT 10;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"on_date": on_date})
 
def activity_by_hour(engine, on_date):
    """Counts total transactions (count and amount) for each hour of the day."""
    query = text("""
    SELECT EXTRACT(HOUR FROM date) AS hour, COUNT(t.id) AS transaction_count, SUM(t.amount) as total_amount
    FROM transactions_data t
    WHERE date::date = :on_date
    GROUP BY hour
    ORDER BY hour;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"on_date": on_date})
 
def gender_distribution_activity(engine, on_date):
    """Shows gender distribution for total transactions (count and amount)."""
    query = text("""
    SELECT u.gender, COUNT(t.id) AS transaction_count, SUM(t.amount) as total_amount
    FROM transactions_data t
    JOIN users_data u ON t.client_id = u.id
    WHERE t.date::date = :on_date
    GROUP BY u.gender;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"on_date": on_date})
 
def get_activity_by_age_group_daily(engine, on_date):
    """Creates transaction distribution by age group (count and amount) for a single day."""
    query = text("""
    SELECT
        CASE
            WHEN u.current_age < 20 THEN '<20' WHEN u.current_age BETWEEN 20 AND 29 THEN '20-29'
            WHEN u.current_age BETWEEN 30 AND 39 THEN '30-39' WHEN u.current_age BETWEEN 40 AND 49 THEN '40-49'
            WHEN u.current_age BETWEEN 50 AND 59 THEN '50-59' WHEN u.current_age BETWEEN 60 AND 69 THEN '60-69'
            ELSE '70+'
        END AS age_group,
        COUNT(t.id) AS transaction_count, SUM(t.amount) as total_amount
    FROM transactions_data t
    JOIN users_data u ON t.client_id = u.id
    WHERE t.date::date = :on_date
    GROUP BY age_group
    ORDER BY age_group;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"on_date": on_date})
 
def get_top_spending_clients_daily(engine, on_date):
    """Gets a list of top spending clients on a specific day."""
    query = text("""
    SELECT t.client_id, COUNT(*) AS transaction_count, SUM(t.amount) AS total_spent
    FROM transactions_data t
    WHERE t.date::date = :on_date
    GROUP BY t.client_id
    ORDER BY total_spent DESC
    LIMIT 20;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"on_date": on_date})
 
def get_user_spending_summary(engine, client_id):
    """Summarizes a user's total spending."""
    # FIX: Use COALESCE to ensure that SUM() returns 0 instead of NULL for clients with no transactions.
    query = text("""
    SELECT
        COALESCE(SUM(amount), 0) AS total_spent,
        COUNT(t.id) as total_count
    FROM transactions_data t
    WHERE t.client_id = :client_id;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"client_id": client_id})
 
 
# ============ FRAUD ANALYSIS QUERIES ============
 
def get_date_range(engine):
    """Fetches the minimum and maximum transaction dates from the database."""
    query = "SELECT MIN(date)::date AS min_date, MAX(date)::date AS max_date FROM transactions_data;"
    with engine.connect() as conn:
        return pd.read_sql(query, conn)
 
def get_user_transactions(engine, client_id):
    """Retrieves all transactions for a specific client, flagging fraud."""
    query = text("""
    SELECT t.*, CASE WHEN f.target = 'Yes' THEN 1 ELSE 0 END AS is_fraud
    FROM transactions_data t
    LEFT JOIN train_fraud_labels f ON t.id = f.id
    WHERE t.client_id = :client_id
    ORDER BY t.date DESC;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"client_id": client_id}, parse_dates=["date"])
 
def get_user_info(engine, client_id):
    """Gets profile information for a specific client."""
    query = text("""
    SELECT u.*, c.card_type, u.id AS name
    FROM users_data u
    JOIN cards_data c ON u.id = c.client_id
    WHERE u.id = :client_id;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"client_id": client_id})
 
def get_summary_stats_for_period(engine, start_date, end_date):
    """Calculates high-level KPIs over a date range, including average fraud amount."""
    query = text("""
    SELECT
        SUM(CASE WHEN f.target = 'Yes' THEN amount ELSE 0 END) AS fraud_amount,
        SUM(amount) AS total_amount,
        COUNT(CASE WHEN f.target = 'Yes' THEN 1 END) AS fraud_txns,
        COUNT(t.id) as total_txns,
        AVG(CASE WHEN f.target = 'Yes' THEN amount END) AS avg_fraud_amount
    FROM transactions_data t
    LEFT JOIN train_fraud_labels f ON t.id = f.id
    WHERE t.date::date BETWEEN :start_date AND :end_date;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
 
def get_daily_trend_for_period(engine, start_date, end_date):
    """Gets the daily count AND amount of transactions and frauds over a period."""
    query = text("""
    SELECT
        t.date::date AS day,
        COUNT(CASE WHEN f.target = 'Yes' THEN 1 END) AS fraud_count,
        COUNT(t.id) as total_count,
        SUM(CASE WHEN f.target = 'Yes' THEN t.amount ELSE 0 END) as fraud_amount,
        SUM(t.amount) as total_amount
    FROM transactions_data t
    LEFT JOIN train_fraud_labels f ON t.id = f.id
    WHERE t.date::date BETWEEN :start_date AND :end_date
    GROUP BY day
    ORDER BY day;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date}, parse_dates=["day"])
 
# FIXED to return consistent column names
def get_fraud_by_gender_for_period(engine, start_date, end_date):
    """Shows gender distribution for fraudulent transactions (count and amount) over a period."""
    query = text("""
    SELECT
        u.gender,
        COUNT(*) AS fraud_count,
        SUM(t.amount) AS fraud_amount
    FROM transactions_data t
    JOIN train_fraud_labels f ON t.id = f.id AND f.target = 'Yes'
    JOIN users_data u ON t.client_id = u.id
    WHERE t.date::date BETWEEN :start_date AND :end_date
    GROUP BY u.gender;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
 
def get_average_fraud_by_hour_for_period(engine, start_date, end_date):
    """Calculates the TOTAL fraud count per hour over a period."""
    query = text("""
    SELECT EXTRACT(HOUR FROM date) AS hour, COUNT(*) AS total_frauds_in_period
    FROM transactions_data t
    JOIN train_fraud_labels f ON t.id = f.id AND f.target = 'Yes'
    WHERE date::date BETWEEN :start_date AND :end_date
    GROUP BY hour
    ORDER BY hour;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
 
# FIXED to return consistent column names
def get_fraud_by_age_for_period(engine, start_date, end_date):
    """Creates fraud distribution by 10-year age groups (count and amount) over a period."""
    query = text("""
    SELECT
        CASE
            WHEN u.current_age < 20 THEN '<20' WHEN u.current_age BETWEEN 20 AND 29 THEN '20-29'
            WHEN u.current_age BETWEEN 30 AND 39 THEN '30-39' WHEN u.current_age BETWEEN 40 AND 49 THEN '40-49'
            WHEN u.current_age BETWEEN 50 AND 59 THEN '50-59' WHEN u.current_age BETWEEN 60 AND 69 THEN '60-69'
            ELSE '70+'
        END AS age_group,
        COUNT(*) AS fraud_count,
        SUM(t.amount) AS fraud_amount
    FROM transactions_data t
    JOIN train_fraud_labels f ON t.id = f.id AND f.target = 'Yes'
    JOIN users_data u ON t.client_id = u.id
    WHERE t.date::date BETWEEN :start_date AND :end_date
    GROUP BY age_group
    ORDER BY age_group;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
 
def get_fraudulent_clients_for_period(engine, start_date, end_date):
    """Gets a list of client IDs with fraudulent transactions over a period."""
    query = text("""
    SELECT
        t.client_id,
        STRING_AGG(DISTINCT TO_CHAR(t.date, 'YYYY-MM-DD'), ', ' ORDER BY TO_CHAR(t.date, 'YYYY-MM-DD')) AS fraud_dates,
        COUNT(*) AS fraud_count,
        SUM(t.amount) AS total_fraud_amount
    FROM transactions_data t
    JOIN train_fraud_labels f ON t.id = f.id AND f.target = 'Yes'
    WHERE t.date::date BETWEEN :start_date AND :end_date
    GROUP BY t.client_id
    ORDER BY total_fraud_amount DESC;
    """)
    with engine.connect() as conn:
        return pd.read_sql(query, conn, params={"start_date": start_date, "end_date": end_date})
 
def get_comparison_period_stats(engine, start_date_str, end_date_str):
    """Fetches fraud stats for a period and the preceding period for comparison."""
    query = text("""
    WITH date_params AS (
        SELECT
            CAST(:start_date AS DATE) AS current_start,
            CAST(:end_date AS DATE) AS current_end,
            CAST(:start_date AS DATE) - (CAST(:end_date AS DATE) - CAST(:start_date AS DATE) + 1) AS prev_start,
            CAST(:start_date AS DATE) - INTERVAL '1 day' AS prev_end
    )
    SELECT
        COALESCE(SUM(CASE WHEN t.date::date BETWEEN dp.current_start AND dp.current_end THEN t.amount END), 0) AS fraud_amount,
        COALESCE(SUM(CASE WHEN t.date::date BETWEEN dp.prev_start AND dp.prev_end THEN t.amount END), 0) AS prev_fraud_amount,
        COALESCE(COUNT(CASE WHEN t.date::date BETWEEN dp.current_start AND dp.current_end THEN 1 END), 0) AS fraud_count,
        COALESCE(COUNT(CASE WHEN t.date::date BETWEEN dp.prev_start AND dp.prev_end THEN 1 END), 0) AS prev_fraud_count
    FROM transactions_data t
    JOIN train_fraud_labels f ON t.id = f.id AND f.target = 'Yes'
    CROSS JOIN date_params dp
    WHERE t.date::date BETWEEN dp.prev_start AND dp.current_end;
    """)
    with engine.connect() as conn:
        params = {"start_date": start_date_str, "end_date": end_date_str}
        return pd.read_sql(query, conn, params=params)


def get_transaction_date_bounds(engine):
    """
    Returns the earliest and latest transaction dates in the dataset.
    """
    sql = text("""
        SELECT
          MIN(date) AS min_date,
          MAX(date) AS max_date
        FROM transactions_data
    """)
    with engine.connect() as conn:
        bounds = pd.read_sql(sql, conn).iloc[0]
    return bounds