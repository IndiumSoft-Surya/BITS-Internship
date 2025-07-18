import plotly.express as px
import pandas as pd
 
def filter_by_account_type(df, card_type):
    return df[df['card_type'] == card_type]
 
def fraud_trend_chart(df):
    df['date'] = pd.to_datetime(df['date'])
    trend = df.groupby(df['date'].dt.date)['is_fraud'].sum().reset_index(name='Fraud Count')
    return px.line(trend, x='date', y='Fraud Count', title='Fraud Trend Over Time')
 
def volume_chart(df):
    df['date'] = pd.to_datetime(df['date'])
    volume = df.groupby(df['date'].dt.date).size().reset_index(name='Transaction Volume')
    return px.bar(volume, x='date', y='Transaction Volume', title='Transaction Volume Over Time')