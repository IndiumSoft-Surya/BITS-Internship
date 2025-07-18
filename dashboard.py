import streamlit as st
import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime, timedelta

import queries

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Smart Bank Transaction Data Dashboard",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- INITIALIZE SESSION STATE ---
if 'selected_client_id' not in st.session_state:
    st.session_state.selected_client_id = ""
# NEW: Session state to manage which tab is active
if 'active_tab_index' not in st.session_state:
    st.session_state.active_tab_index = 0


# --- LOAD ENVIRONMENT VARIABLES & CONNECT TO DB ---
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    st.error("❌ DATABASE_URL environment variable not found. Please create a .env file.")
    st.stop()

engine = create_engine(DATABASE_URL)


# --- CACHED DATA FUNCTIONS ---
@st.cache_data(ttl=600)
def get_min_max_dates():
    return queries.get_date_range(engine)

@st.cache_data(ttl=3600)
def fetch_overview_data():
    data = {
        "summary": queries.get_overall_activity_summary(engine),
        "by_dow": queries.get_avg_activity_by_dow(engine),
        "by_hour": queries.get_avg_activity_by_hour(engine),
        "daily_trend": queries.get_overall_daily_trend(engine),
        "by_gender": queries.get_activity_by_gender_overall(engine),
        "by_age": queries.get_activity_by_age_overall(engine)
    }
    return data

@st.cache_data(ttl=600)
def fetch_daily_data(date):
    date_str = date.strftime('%Y-%m-%d')
    data = {
        "summary": queries.get_daily_activity_summary_with_comparison(engine, on_date=date_str),
        "by_hour": queries.activity_by_hour(engine, date_str),
        "by_mcc": queries.activity_by_mcc(engine, date_str),
        "by_gender": queries.gender_distribution_activity(engine, date_str),
        "by_age": queries.get_activity_by_age_group_daily(engine, date_str),
        "top_clients": queries.get_top_spending_clients_daily(engine, date_str)
    }
    return data

@st.cache_data(ttl=600)
def fetch_user_data(client_id):
    data = {
        "info": queries.get_user_info(engine, client_id),
        "transactions": queries.get_user_transactions(engine, client_id),
        "summary": queries.get_user_spending_summary(engine, client_id)
    }
    return data

@st.cache_data(ttl=600)
def fetch_period_data_fraud(start_date, end_date):
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    data = {
        "summary_stats": queries.get_summary_stats_for_period(engine, start_str, end_str),
        "trend": queries.get_daily_trend_for_period(engine, start_str, end_str),
        "by_gender": queries.get_fraud_by_gender_for_period(engine, start_str, end_str),
        "avg_by_hour": queries.get_average_fraud_by_hour_for_period(engine, start_str, end_str),
        "by_age": queries.get_fraud_by_age_for_period(engine, start_str, end_str),
        "fraudulent_clients": queries.get_fraudulent_clients_for_period(engine, start_str, end_str),
        "comparison": queries.get_comparison_period_stats(engine, start_str, end_str)
    }
    return data


# --- HELPER FUNCTIONS ---
def create_donut_chart(df, names_col, values_col, title):
    fig = px.pie(df, names=names_col, values=values_col, title=title, hole=0.4)
    fig.update_layout(showlegend=True, margin=dict(t=40, b=0, l=0, r=0))
    return fig

def highlight_fraud(s):
    is_fraud = s['is_fraud'] == 1
    return ['background-color: #FADBD8;']*len(s) if is_fraud else ['']*len(s)

def handle_client_selection(df, table_key):
    if table_key in st.session_state:
        selection_info = st.session_state[table_key].get("selection")
        if selection_info and selection_info["rows"]:
            selected_row_index = selection_info["rows"][0]
            if selected_row_index < len(df):
                client_id = df.iloc[selected_row_index]["client_id"]
                # Set client id and also the active tab index for redirection
                st.session_state.selected_client_id = client_id
                st.session_state.active_tab_index = 3 # Index 3 is Client Deep-Dive
                st.rerun()


# --- UI LAYOUT ---
st.title("🏦 Smart Bank Transaction Data Dashboard")
st.markdown("An interactive tool for monitoring and analyzing transaction activity.")

# --- NEW: TAB NAVIGATION CONTROL ---
# We use st.radio to create a tab-like interface that we can control programmatically.
TAB_LABELS = [
    "👑 **Overview**",
    "📈 **Fraud Analysis**",
    "📅 **Daily Activity Snapshot**",
    "👤 **Client Deep-Dive**"
]

# When a user manually clicks a tab, this updates the session state.
# The `index` parameter makes sure the correct tab is selected on a programmatic redirect.
selected_tab_label = st.radio(
    "Main navigation",
    options=TAB_LABELS,
    index=st.session_state.active_tab_index,
    horizontal=True,
    label_visibility="collapsed"
)
st.session_state.active_tab_index = TAB_LABELS.index(selected_tab_label)
st.markdown("---")

# ==============================================================================
#                                TAB 0: OVERVIEW
# ==============================================================================
if selected_tab_label == TAB_LABELS[0]:
    st.header("Overall Business Activity Overview")

    view_by_overview = st.radio(
        "Select Metric View for All Charts:",
        ["By Count", "By Amount"],
        key="master_toggle_overview",
        horizontal=True,
    )

    overview_data = fetch_overview_data()

    st.markdown("#### All-Time Key Metrics")
    summary = overview_data['summary'].iloc[0]
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Transaction Volume", f"${summary['total_transaction_volume']:,.0f}")
    kpi2.metric("Total Transactions", f"{summary['total_transactions']:,}")
    kpi3.metric("Total Active Clients", f"{summary['total_clients']:,}")
    kpi4.metric("Avg. Transaction Value", f"${summary['avg_transaction_value']:.2f}")

    st.markdown("---")
    # ... (Rest of the Overview tab content remains unchanged)
    st.subheader("Historical Daily Transaction Volume")
    df_daily_trend = overview_data['daily_trend']
    if not df_daily_trend.empty:
        y_col = 'total_count' if view_by_overview == "By Count" else 'total_amount'
        y_title = "Total Transactions" if view_by_overview == "By Count" else "Total Transaction Volume ($)"
        fig_trend = px.area(df_daily_trend, x='day', y=y_col, title=f"Daily Transactions: By {view_by_overview.replace('By ', '')}")
        fig_trend.update_layout(yaxis_title=y_title, xaxis_title="Date")
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("No daily trend data available.")

    st.markdown("---")
    st.header("Average Activity Patterns")
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Average Activity by Day of the Week")
        df_dow = overview_data['by_dow']
        if not df_dow.empty:
            days_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            df_dow['day_of_week_name'] = pd.Categorical(df_dow['day_of_week_name'], categories=days_order, ordered=True)
            df_dow = df_dow.sort_values('day_of_week_name')
            y_col = 'avg_txns_count' if view_by_overview == "By Count" else 'avg_txns_amount'
            y_title = "Average Transaction Count" if view_by_overview == "By Count" else "Average Transaction Amount ($)"
            fig_dow = go.Figure(go.Scatter(x=df_dow['day_of_week_name'], y=df_dow[y_col], mode='lines+markers', name='Average'))
            fig_dow.update_layout(title=f"Average Transactions by {view_by_overview.replace('By ', '')}", xaxis_title="Day of Week", yaxis_title=y_title, showlegend=False)
            st.plotly_chart(fig_dow, use_container_width=True)
        else:
            st.info("No day-of-week data available.")
    with col2:
        st.subheader("Average Activity by Hour of Day")
        df_hour = overview_data['by_hour']
        if not df_hour.empty:
            y_col = 'avg_txns_count' if view_by_overview == "By Count" else 'avg_txns_amount'
            y_title = "Average Transaction Count" if view_by_overview == "By Count" else "Average Transaction Amount ($)"
            text_format = '.0f' if view_by_overview == "By Count" else '.2f'
            fig_hour = px.bar(df_hour, x='hour', y=y_col, text_auto=text_format, title=f"Average Hourly Transactions by {view_by_overview.replace('By ', '')}")
            fig_hour.update_layout(yaxis_title=y_title, xaxis_title="Hour of Day (24h)")
            st.plotly_chart(fig_hour, use_container_width=True)
        else:
            st.info("No hourly data available.")

    st.markdown("---")
    st.header("Customer Demographics (Overall)")
    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Transactions by Gender")
        df_gender = overview_data['by_gender']
        if not df_gender.empty:
            val_col = 'transaction_count' if view_by_overview == "By Count" else 'total_amount'
            st.plotly_chart(create_donut_chart(df_gender, 'gender', val_col, f"Distribution by {view_by_overview.replace('By ', '')}"), use_container_width=True)
        else:
            st.info("No gender data available.")
    with col4:
        st.subheader("Transactions by Age Group")
        df_age = overview_data['by_age']
        if not df_age.empty:
            val_col = 'transaction_count' if view_by_overview == "By Count" else 'total_amount'
            st.plotly_chart(create_donut_chart(df_age, 'age_group', val_col, f"Distribution by {view_by_overview.replace('By ', '')}"), use_container_width=True)
        else:
            st.info("No age data available.")

# ==============================================================================
#                                TAB 1: FRAUD ANALYSIS
# ==============================================================================
if selected_tab_label == TAB_LABELS[1]:
    st.header("Fraud Analysis Over a Custom Period")

    date_range = get_min_max_dates()
    min_db_date, max_db_date = date_range['min_date'][0], date_range['max_date'][0]

    st.markdown("##### Select Timeframe")
    c1, c2, c3, c4 = st.columns([1, 1, 1, 2])

    if 'start_date_fraud' not in st.session_state:
        st.session_state.start_date_fraud = max_db_date - timedelta(days=29)
        st.session_state.end_date_fraud = max_db_date

    def set_date_range_fraud(days):
        st.session_state.start_date_fraud = max_db_date - timedelta(days=days-1)
        st.session_state.end_date_fraud = max_db_date

    if c1.button("Last 7 Days", use_container_width=True, key="fa_7"): set_date_range_fraud(7)
    if c2.button("Last 30 Days", use_container_width=True, key="fa_30"): set_date_range_fraud(30)
    if c3.button("Last 90 Days", use_container_width=True, key="fa_90"): set_date_range_fraud(90)

    with c4:
        custom_range = st.date_input("Or Select a Custom Range",
            value=(st.session_state.start_date_fraud, st.session_state.end_date_fraud),
            min_value=min_db_date, max_value=max_db_date, key="custom_date_picker_fa")
        if len(custom_range) == 2:
            st.session_state.start_date_fraud, st.session_state.end_date_fraud = custom_range

    start_date = st.session_state.start_date_fraud
    end_date = st.session_state.end_date_fraud

    if start_date > end_date:
        st.error("Error: Start date must be before end date.")
    else:
        period_data = fetch_period_data_fraud(start_date, end_date)
        # ... (Manager's Summary, Daily Trends, Demographics content remains unchanged)
        st.markdown("---")
        st.subheader("Manager's Summary: Performance vs. Previous Period")
        comparison_stats = period_data['comparison']
        if not comparison_stats.empty:
            stats = comparison_stats.iloc[0]
            current_amount, prev_amount = stats.get('fraud_amount', 0), stats.get('prev_fraud_amount', 0)
            current_count, prev_count = stats.get('fraud_count', 0), stats.get('prev_fraud_count', 0)
            amount_change = ((current_amount - prev_amount) / prev_amount) * 100 if prev_amount > 0 else float('inf') if current_amount > 0 else 0
            count_change = ((current_count - prev_count) / prev_count) * 100 if prev_count > 0 else float('inf') if current_count > 0 else 0
            summary_col1, summary_col2 = st.columns(2)
            with summary_col1:
                st.metric(label="Fraud Amount", value=f"${current_amount:,.0f}", delta=f"{amount_change:.1f}% vs. prior period", delta_color="inverse")
            with summary_col2:
                st.metric(label="Fraud Count", value=f"{current_count:,}", delta=f"{count_change:.1f}% vs. prior period", delta_color="inverse")
        else:
            st.info("Not enough historical data for a comparison.")
        
        st.markdown("---")
        st.subheader("Daily Trends")
        df_trend = period_data['trend']
        if not df_trend.empty:
            trend_view = st.radio("Select Trend View", ("By Transaction Count", "By Transaction Amount", "Fraud Rate (%)"), horizontal=True, label_visibility="collapsed", key="fa_radio")
            
            if trend_view == "Fraud Rate (%)":
                df_trend['fraud_rate_count'] = (df_trend['fraud_count'] * 100 / df_trend['total_count']).fillna(0)
                fig_trend = px.area(df_trend, x='day', y='fraud_rate_count', title='Daily Fraud Rate (by Transaction Count)', labels={'fraud_rate_count': 'Fraud Rate (%)', 'day': 'Date'})
                fig_trend.update_traces(fillcolor='rgba(255, 99, 71, 0.3)', line_color='rgba(255, 99, 71, 0.8)')
            else:
                fig_trend = make_subplots(specs=[[{"secondary_y": True}]])
                y_map = {
                    "By Transaction Count": ('fraud_count', 'total_count', 'Fraudulent Transactions', 'Total Transactions', "<b>Fraud</b> Count", "<b>Total</b> Count", 'red', 'blue'),
                    "By Transaction Amount": ('fraud_amount', 'total_amount', 'Fraudulent Amount ($)', 'Total Amount ($)', "<b>Fraud</b> Amount ($)", "<b>Total</b> Amount ($)", 'orangered', 'deepskyblue')
                }
                p_col, s_col, p_name, s_name, p_title, s_title, p_color, s_color = y_map[trend_view]
                fig_trend.add_trace(go.Scatter(x=df_trend['day'], y=df_trend[p_col], name=p_name, mode='lines+markers', line=dict(color=p_color)), secondary_y=False)
                fig_trend.add_trace(go.Scatter(x=df_trend['day'], y=df_trend[s_col], name=s_name, mode='lines', line=dict(color=s_color, dash='dash')), secondary_y=True)
                fig_trend.update_layout(title_text=f"Daily Total vs. Fraudulent Transactions ({trend_view.split('By ')[1]})", legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
                fig_trend.update_yaxes(title_text=p_title, secondary_y=False, color=p_color)
                fig_trend.update_yaxes(title_text=s_title, secondary_y=True, color=s_color)
            st.plotly_chart(fig_trend, use_container_width=True)
        else:
            st.info("No transaction data available for this period.")

        st.markdown("---")
        st.subheader("Deeper Dive into Fraud Patterns")
        view_by_fraud = st.radio("View Demographic Charts By:", ["Count", "Amount"], key="master_toggle_fraud", horizontal=True)
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("##### Fraud Distribution by Gender")
            df_gender_period = period_data['by_gender']
            if not df_gender_period.empty:
                val_col = 'fraud_count' if view_by_fraud == 'Count' else 'fraud_amount'
                st.plotly_chart(create_donut_chart(df_gender_period, 'gender', val_col, f"Fraud by Gender ({view_by_fraud})"), use_container_width=True)
            else:
                st.info("No gender-specific fraud data available for this period.")
        with col2:
            st.markdown("##### Fraud Distribution by Age Group")
            df_age_period = period_data['by_age']
            if not df_age_period.empty:
                val_col = 'fraud_count' if view_by_fraud == 'Count' else 'fraud_amount'
                y_title = "Number of Frauds" if view_by_fraud == 'Count' else "Fraud Amount ($)"
                fig_age_bar = px.bar(df_age_period, x='age_group', y=val_col, title=f"Total Frauds by Age Group ({view_by_fraud})")
                fig_age_bar.update_layout(xaxis_title="Age Group", yaxis_title=y_title, title_x=0.5)
                st.plotly_chart(fig_age_bar, use_container_width=True)
            else:
                st.info("No age-specific fraud data available for this period.")

        st.markdown("---")
        st.subheader("Client-Level Fraud Insights")
        df_period_clients = period_data.get('fraudulent_clients')
        if df_period_clients is not None and not df_period_clients.empty:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("##### Top 10 Clients by Fraud Amount")
                top_by_amount = df_period_clients.nlargest(10, 'total_fraud_amount').reset_index(drop=True)
                # --- FIX #1: Changed column ratios from [3, 2, 1] to [3, 1, 1] ---
                header_cols = st.columns([3, 1, 1])
                header_cols[0].markdown("**Client ID**")
                header_cols[1].markdown("**Fraud Amount**")
                header_cols[2].markdown("**Action**")
                st.divider()
                for index, row in top_by_amount.iterrows():
                    # --- FIX #2: Changed column ratios here to match the header ---
                    row_cols = st.columns([3, 1, 1])
                    row_cols[0].code(row['client_id'], language=None)
                    row_cols[1].markdown(f"${row['total_fraud_amount']:,.2f}")
                    if row_cols[2].button("Investigate", key=f"investigate_top_{index}", use_container_width=True):
                        st.session_state.selected_client_id = row['client_id']
                        st.session_state.active_tab_index = 3 # Go to Deep-Dive tab
                        st.rerun() # Trigger the redirect
            with col2:
                st.markdown("##### Clients with Repeat Fraud Incidents")
                repeat_victims = df_period_clients[df_period_clients['fraud_count'] > 1].sort_values(by="fraud_count", ascending=False).reset_index(drop=True)
                if not repeat_victims.empty:
                    header_cols = st.columns([3, 1, 1, 1])
                    header_cols[0].markdown("**Client ID**")
                    header_cols[1].markdown("**Count**")
                    header_cols[2].markdown("**Amount**")
                    header_cols[3].markdown("**Action**")
                    st.divider()
                    for index, row in repeat_victims.iterrows():
                        row_cols = st.columns([3, 1, 1, 1])
                        row_cols[0].code(row['client_id'], language=None)
                        row_cols[1].markdown(f"{row['fraud_count']}")
                        row_cols[2].markdown(f"${row['total_fraud_amount']:,.2f}")
                        if row_cols[3].button("Investigate", key=f"investigate_repeat_{index}", use_container_width=True):
                            st.session_state.selected_client_id = row['client_id']
                            st.session_state.active_tab_index = 3 # Go to Deep-Dive tab
                            st.rerun() # Trigger the redirect
                else:
                    st.info("No clients with multiple fraud incidents in this period.")
        else:
            st.info("No fraudulent activity recorded for this period.")

# ==============================================================================
#                                TAB 2: DAILY ACTIVITY SNAPSHOT
# ==============================================================================
if selected_tab_label == TAB_LABELS[2]:
    st.header("Daily Activity Snapshot")
    date_range_daily = get_min_max_dates()
    min_date_daily, max_date_daily = date_range_daily['min_date'][0], date_range_daily['max_date'][0]
    selected_date = st.date_input("Select a Date", value=max_date_daily, min_value=min_date_daily, max_value=max_date_daily, key="daily_date")

    if selected_date:
        view_by_daily = st.radio("Select Metric View for All Charts:", ["By Count", "By Amount"], key="master_toggle_daily", horizontal=True)
        daily_data = fetch_daily_data(selected_date)
        st.subheader(f"Metrics for {selected_date.strftime('%B %d, %Y')}")
        summary = daily_data['summary'].iloc[0] if not daily_data['summary'].empty else {}
        total_amount, prev_total_amount = summary.get('total_amount', 0), summary.get('prev_day_total_amount', 0)
        total_txns, prev_total_txns = summary.get('total_txns', 0), summary.get('prev_day_total_txns', 0)
        kpi1, kpi2 = st.columns(2)
        kpi1.metric("💰 Total Amount", f"${total_amount:,.2f}", f"${(total_amount - prev_total_amount):,.2f} vs yesterday")
        kpi2.metric("💳 Total Transactions", f"{total_txns:,}", f"{(total_txns - prev_total_txns):,} vs yesterday")
        st.markdown("---")
        # ... (Rest of the Daily Snapshot content remains unchanged)
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"Activity by Hour on {selected_date.strftime('%b %d')}")
            df_hour_daily = daily_data['by_hour']
            if not df_hour_daily.empty:
                y_col = 'transaction_count' if view_by_daily == "By Count" else 'total_amount'
                y_title = "Transaction Count" if view_by_daily == "By Count" else "Transaction Amount ($)"
                text_format = '.0f' if view_by_daily == "By Count" else '.2f'
                fig_hour_daily = px.bar(df_hour_daily, x='hour', y=y_col, text_auto=text_format, title=f"Hourly Transactions by {view_by_daily.replace('By ', '')}")
                fig_hour_daily.update_layout(yaxis_title=y_title, xaxis_title="Hour of Day (24h)")
                st.plotly_chart(fig_hour_daily, use_container_width=True)
            else:
                st.info("No hourly transaction data for this day.")
        with col2:
            st.subheader("Activity by Merchant Category")
            df_mcc = daily_data['by_mcc']
            if not df_mcc.empty:
                x_col = 'transaction_count' if view_by_daily == "By Count" else 'total_amount'
                x_title = "Total Transactions" if view_by_daily == "By Count" else "Total Amount ($)"
                df_mcc_sorted = df_mcc.sort_values(x_col, ascending=True)
                fig_mcc = px.bar(df_mcc_sorted.tail(10), y='mcc_category', x=x_col, orientation='h', title=f"Top 10 Merchant Categories by {view_by_daily.replace('By ', '')}", labels={'mcc_category': 'Category', x_col: x_title})
                st.plotly_chart(fig_mcc, use_container_width=True)
            else:
                st.info("No MCC transaction data for this day.")

        st.markdown("---")
        st.subheader("Customer Demographics")
        col3, col4 = st.columns(2)
        with col3:
            st.markdown("##### By Gender")
            df_gender = daily_data['by_gender']
            if not df_gender.empty:
                val_col = 'transaction_count' if view_by_daily == "By Count" else 'total_amount'
                st.plotly_chart(create_donut_chart(df_gender, 'gender', val_col, f"Distribution by {view_by_daily.replace('By ','')}"), use_container_width=True)
            else:
                st.info("No gender data for this day.")
        with col4:
            st.markdown("##### By Age Group")
            df_age = daily_data['by_age']
            if not df_age.empty:
                val_col = 'transaction_count' if view_by_daily == "By Count" else 'total_amount'
                st.plotly_chart(create_donut_chart(df_age, 'age_group', val_col, f"Distribution by {view_by_daily.replace('By ','')}"), use_container_width=True)
            else:
                st.info("No age data for this day.")

        with st.expander(f"View Top Spending Clients on {selected_date.strftime('%B %d, %Y')}"):
            df_clients = daily_data.get('top_clients')
            if df_clients is not None and not df_clients.empty:
                st.info("💡 Click on a row to investigate the client.", icon="👉")
                # UPDATED: Using the new handle_client_selection function
                st.data_editor(df_clients, key="daily_clients_table", disabled=True, hide_index=True, use_container_width=True,
                               column_config={"total_spent": st.column_config.NumberColumn("Amount", format="$%.2f")})
                handle_client_selection(df_clients, "daily_clients_table")
            else:
                st.info("No client activity recorded for this day.")

# ==============================================================================
#                                TAB 3: CLIENT DEEP-DIVE
# ==============================================================================
if selected_tab_label == TAB_LABELS[3]:
    st.header("Investigate a Specific Client")
    
    # The text input's value is now controlled by st.session_state.selected_client_id
    client_id_input = st.text_input(
        "Enter Client ID or select one from another tab",
        value=st.session_state.selected_client_id,
        placeholder="e.g., 556c28f0-5afd-46c2-8d7b-c99787595535",
        key="client_id_input_box"
    ).strip()

    st.session_state.selected_client_id = client_id_input

    if client_id_input:
        user_data = fetch_user_data(client_id_input)
        if user_data.get('info') is None or user_data['info'].empty:
            st.warning("Client ID not found. Please check the ID and try again.")
        else:
            user_info = user_data['info'].iloc[0]
            summary = user_data['summary'].iloc[0]
            st.markdown("---")
            st.subheader(f"Profile for Client: {user_info['name']}")
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Age", f"{user_info['current_age']}")
            c2.metric("Gender", user_info['gender'])
            c3.metric("Credit Score", f"{user_info['credit_score']}")
            c4.metric("Card Type", user_info['card_type'].title())

            st.markdown("##### Lifetime Activity Summary")
            c1_sum, c2_sum = st.columns(2)
            c1_sum.metric("Lifetime Total Transactions", f"{summary['total_count']:,}")
            c2_sum.metric("Lifetime Total Spent", f"${summary['total_spent']:,.2f}")

            st.markdown("---")
            st.subheader("Transaction History")
            st.info("Fraudulent transactions (if any) are flagged in the 'is_fraud' column.")
            df_trans = user_data.get('transactions')
            if df_trans is not None and not df_trans.empty:
                st.dataframe(
                    df_trans.style.apply(highlight_fraud, axis=1).format({
                        "amount": "${:,.2f}", "date": "{:%Y-%m-%d %H:%M:%S}"
                    }),
                    column_config={"is_fraud": "Is Fraud?", "client_id": None, "id": "Transaction ID"},
                    use_container_width=True, hide_index=True
                )
            else:
                st.info("No transaction history found for this client.")