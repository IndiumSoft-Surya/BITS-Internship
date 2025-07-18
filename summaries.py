# summaries.py

from datetime import datetime, timedelta
from db_conn import get_connection
from queries import (
    get_overall_activity_summary,
    get_comparison_period_stats,
    get_daily_activity_summary_with_comparison,
    get_user_spending_summary,
    get_user_info,
    get_transaction_date_bounds,
)

def get_overview_summary():
    engine = get_connection()
    df = get_overall_activity_summary(engine)
    s = df.iloc[0]
    return (
        f"🏦 *Overview Summary*\n"
        f"- Total Volume: ${s['total_transaction_volume']:,.0f}\n"
        f"- Transactions: {s['total_transactions']:,}\n"
        f"- Active Clients: {s['total_clients']:,}\n"
        f"- Avg. Txn Value: ${s['avg_transaction_value']:.2f}"
    )

def get_fraud_summary(days: int = 30):
    engine = get_connection()
    # Determine dataset date bounds and convert to datetime.date
    bounds = get_transaction_date_bounds(engine)
    raw_max = bounds['max_date']
    max_date = raw_max.date() if hasattr(raw_max, 'date') else raw_max

    today = datetime.now().date()
    end = min(today, max_date)
    start = end - timedelta(days=days - 1)

    stats_df = get_comparison_period_stats(engine, start, end)
    stats = stats_df.iloc[0]

    # Safely default None to 0
    amt = stats.get('fraud_amount') or 0
    prev_amt = stats.get('prev_fraud_amount') or 0
    cnt = stats.get('fraud_count') or 0
    prev_cnt = stats.get('prev_fraud_count') or 0

    pct_amt = (amt - prev_amt) / prev_amt * 100 if prev_amt else 0
    pct_cnt = (cnt - prev_cnt) / prev_cnt * 100 if prev_cnt else 0

    return (
        f"🚨 *Fraud Summary ({days}d)*\n"
        f"- Fraud Amount: ${amt:,.0f} ({pct_amt:.1f}% vs. prior)\n"
        f"- Fraud Count: {cnt:,} ({pct_cnt:.1f}% vs. prior)"
    )

def get_daily_summary(date_str: str = None):
    engine = get_connection()
    # Determine dataset date bounds and convert to datetime.date
    bounds = get_transaction_date_bounds(engine)
    raw_min, raw_max = bounds['min_date'], bounds['max_date']
    min_date = raw_min.date() if hasattr(raw_min, 'date') else raw_min
    max_date = raw_max.date() if hasattr(raw_max, 'date') else raw_max

    # Parse requested date or default to today
    requested = (
        datetime.strptime(date_str, '%Y-%m-%d').date()
        if date_str
        else datetime.now().date()
    )
    # Cap to available range
    date = min(max(requested, min_date), max_date)

    df = get_daily_activity_summary_with_comparison(engine, date)
    s = df.iloc[0]

    # Safely handle NULLs from SQL by defaulting to 0
    total_amount = s.get('total_amount') or 0
    prev_amount = s.get('prev_day_total_amount') or 0
    total_txns = s.get('total_txns') or 0
    prev_txns = s.get('prev_day_total_txns') or 0

    delta_amt = total_amount - prev_amount
    delta_txn = total_txns - prev_txns

    return (
        f"📅 *Daily Summary for {date:%Y-%m-%d}*\n"
        f"- Total Amount: ${total_amount:,.2f} ({delta_amt:+,.2f} vs. prev)\n"
        f"- Transactions: {total_txns:,} ({delta_txn:+,} vs. prev)"
    )

def get_client_summary(client_id: str):
    engine = get_connection()
    info_df = get_user_info(engine, client_id)
    summary_df = get_user_spending_summary(engine, client_id)
    info = info_df.iloc[0]
    s = summary_df.iloc[0]

    return (
        f"👤 *Client {client_id} Summary*\n"
        f"- Name: {info['name']}\n"
        f"- Age/Gender: {info['current_age']}/{info['gender']}\n"
        f"- Card Type: {info['card_type'].title()}\n"
        f"- Lifetime Txns: {s['total_count']:,}, Spent: ${s['total_spent']:,.2f}"
    )
