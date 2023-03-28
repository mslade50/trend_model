import yfinance as yf
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator
import streamlit as st
import plotly.graph_objects as go

def get_stock_data(ticker):
    stock = yf.Ticker(ticker)
    df = stock.history(period='max')
    return df

def moving_average(df, window):
    return df['Close'].rolling(window=window).mean()

def exponential_moving_average(df, window):
    return df['Close'].ewm(span=window, adjust=False).mean()

def relative_strength_index(df, window):
    rsi_indicator = RSIIndicator(df['Close'], window=window)
    rsi = rsi_indicator.rsi()
    return rsi

def process_stock_data(ticker):
    df = get_stock_data(ticker)
    
    df['200_day_MA'] = moving_average(df, 200)
    df['200_week_MA'] = moving_average(df, 200 * 5)
    df['14_day_RSI'] = relative_strength_index(df, 14)
    df['21_day_EMA'] = exponential_moving_average(df, 21)

    df['Price_vs_200_d'] = (df['Close'] - df['200_day_MA'])/df['Close']
    df['Price_vs_200_w'] = (df['Close'] - df['200_week_MA'])/df['Close']
    
    df['200_day_MA_slope'] = df['200_day_MA'].pct_change()*100
    df['200_week_MA_slope'] = df['200_week_MA'].pct_change()*100

    df['14_day_RSI_pctile'] = df['14_day_RSI'].rank(pct=True)*100

    df['21_day_EMA_vs_200_day_MA'] = (df['21_day_EMA'] - df['200_day_MA'])/df['Close']
    df['21_vs_200_pctile'] = df['21_day_EMA_vs_200_day_MA'].rank(pct=True)*100

    # Round all data points to 2 decimal places
    df = df.round(2)
    return df.tail(21)

def create_plotly_table(df, ticker):
    # Define colors for percentiles
    def color_conditions(value):
        if value < 5:
            return 'lightgreen', 'darkgreen'
        elif value > 95:
            return 'lightcoral', 'darkred'
        else:
            return 'black', 'white'

    # Define colors for positive and negative values
    def pos_neg_colors(value):
        if value > 0:
            return 'lightgreen', 'darkgreen'
        else:
            return 'lightcoral', 'darkred'

    rsi_percentile_colors = df['14_day_RSI_pctile'].apply(color_conditions)
    ema_percentile_colors = df['21_vs_200_pctile'].apply(color_conditions)

    df = df.sort_index(ascending=False)

    fig = go.Figure(data=[go.Table(
        columnwidth=[50, 55, 55, 60, 60, 60, 60],
        header=dict(values=['Date', 'Price_vs_200_d', 'Price_vs_200_w', '200_day_MA_slope', '200_week_MA_slope',
                            '14_day_RSI_pctile', '21_vs_200_pctile'],
                    fill_color='darkblue',
                    font=dict(color='white', size=12),
                    align='left'),
        cells=dict(values=[df.index.strftime('%Y-%m-%d'), df['Price_vs_200_d'], df['Price_vs_200_w'],
                           df['200_day_MA_slope'], df['200_week_MA_slope'], df['14_day_RSI_pctile'], df['21_vs_200_pctile']],
                   fill_color=[['black'] * len(df), df['Price_vs_200_d'].apply(pos_neg_colors).apply(lambda x: x[0]),
                               df['Price_vs_200_w'].apply(pos_neg_colors).apply(lambda x: x[0]),
                               df['200_day_MA_slope'].apply(pos_neg_colors).apply(lambda x: x[0]),
                               df['200_week_MA_slope'].apply(pos_neg_colors).apply(lambda x: x[0]),
                               rsi_percentile_colors.apply(lambda x: x[0]), ema_percentile_colors.apply(lambda x: x[0])],
                   font=dict(color=['white', df['Price_vs_200_d'].apply(pos_neg_colors).apply(lambda x: x[1]),
                                    df['Price_vs_200_w'].apply(pos_neg_colors).apply(lambda x: x[1]),
                                    df['200_day_MA_slope'].apply(pos_neg_colors).apply(lambda x: x[1]),
                                    df['200_week_MA_slope'].apply(pos_neg_colors).apply(lambda x: x[1]),
                                    rsi_percentile_colors.apply(lambda x: x[1]), ema_percentile_colors.apply(lambda x: x[1])], size=12),
                   align='left'))
    ])
    fig.update_layout(title=f"{ticker}")
    return fig

def main():
    st.set_page_config(layout="wide")
    st.title("Trend Dashboards")
    tickers = ['^GSPC', '^NDX','GC=F','CL=F','NG=F','SI=F','ZW=F','RB=F','ZN=F','ZT=F',
    'DX-Y.NYB','USDJPY=X','EURUSD=X','AUDUSD=X','BTC-USD','ETH-USD']
    
    for ticker in tickers:
        df = process_stock_data(ticker)
        table_figure = create_plotly_table(df, ticker)
        st.plotly_chart(table_figure,use_container_width=False,width=600)

if __name__ == '__main__':
    main()
