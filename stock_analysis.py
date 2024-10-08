import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta

class Stock_Analysis:

    def get_stock_data(self, ticker, start_date, end_date):
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        return df

    def get_earnings_dates(self, ticker, start_date, end_date):
        stock = yf.Ticker(ticker)
        earnings = stock.earnings_dates
        return earnings[(earnings.index >= start_date) & (earnings.index <= end_date)]

    def get_merged_data(self, ticker, start_date, end_date):
        stock_data = self.get_stock_data(ticker, start_date, end_date)
        earnings_data = self.get_earnings_dates(ticker, start_date, end_date)

        # Ensure both DataFrames have aligned timezone-aware indices
        stock_data.index = stock_data.index.tz_localize(None)
        earnings_data.index = earnings_data.index.tz_localize(None)

        earnings_data.index = earnings_data.index.strftime('%Y-%m-%d')
        stock_data.index = stock_data.index.strftime('%Y-%m-%d')

        # Merge the DataFrames on the Date index, using outer join to keep all dates
        merged_data = pd.merge(stock_data, earnings_data, left_index=True, right_index=True, how='outer')
        merged_data.index = pd.to_datetime(merged_data.index)

        return merged_data

    def transform(self, df):
        # Calculate the daily percentage change (High - Low) / High * 100
        df['daily_perc_change'] = ((df['High'] - df['Low']) / df['High']) * 100
        df['daily_change'] = (df['High'] - df['Low'])
        
        return df

    # This funnction will filter the dataframe to remove all data except the data before and after the earning report
    def earnings_dates(self, df, days_before, days_after):
        # Find rows where there is a Reported EPS (assuming this is the earnings date)
        earnings_dates = df.dropna(subset=['Reported EPS']).index

        # Create an empty DataFrame to store the filtered results
        filtered_df = pd.DataFrame()

        for date in earnings_dates:
            # Get the range of dates around the earnings date
            start_date = date - pd.Timedelta(days=days_before)
            end_date = date + pd.Timedelta(days=days_after)

            # Filter the rows within the date range and append to the filtered DataFrame
            filtered_df = pd.concat([filtered_df, df.loc[start_date:end_date]])

        return filtered_df

    def analyze_stock_performance(self, ticker, start_date, end_date, days_before=7, days_after=28):
        # Get merged data
        merged_data = self.get_merged_data(ticker, start_date, end_date)

        results = []

        for earnings_date in merged_data.index[merged_data['Reported EPS'].notna()]:
            start = earnings_date - timedelta(days=days_before)
            end = earnings_date + timedelta(days=days_after)

            period_data = merged_data.loc[start:end]

            # Calculate daily range and average daily range
            period_data['daily_range_perc'] = ((period_data['High'] - period_data['Low']) / period_data['High']) * 100
            period_data['daily_range'] = (period_data['High'] - period_data['Low'])

            # Calculate return since earnings
            returns = (period_data['Close'] / period_data.loc[earnings_date, 'Close'] - 1) * 100

            # Find the day with maximum return
            max_return_day = returns.idxmax()
            max_return = returns.max()
            days_to_max = (max_return_day - earnings_date).days

            results.append({
                'Earnings_Date': earnings_date,
                'Max_Return': max_return,
                'Days_to_Max': days_to_max
            })

        results_df = pd.DataFrame(results)
        merged_df = pd.merge(results_df, merged_data, left_on='Earnings_Date', right_index=True, how='left')

        return merged_df

    def plot_stock(self, ticker, start_date, end_date, analysis_results):
        stock_data = self.get_stock_data(ticker, start_date, end_date)

        fig, ax1 = plt.subplots(figsize=(12, 6))

        # Plot earnings dates
        for date in analysis_results['Earnings_Date'].values:
            ax1.axvline(x=date, color='r', linestyle='--', alpha=0.5)

        # Plot stock price
        ax1.plot(stock_data.index, stock_data['Close'])
        ax1.set_title(f'{ticker} Stock Price and Earnings Dates')
        ax1.set_ylabel('Stock Price')
        ax1.set_xlabel('Date')

        plt.tight_layout()
        plt.show()

    def plot_daily(self, df, col):
        # Plot daily_change
        fig, ax1 = plt.subplots(figsize=(18, 6))
        ax1.plot(df.index, df[col], linestyle='-', color='b')

        # Plot earnings dates
        earnings_dates = []
        for idx, row in df.iterrows():
            if pd.notna(row['Reported EPS']):
                ax1.axvline(x=idx, color='r', linestyle='--', alpha=0.5)
                earnings_dates.append(idx)
        
        # Set the x-ticks and labels to be the earnings dates only
        ax1.set_xticks(earnings_dates)
        ax1.set_xticklabels([date.strftime('%Y-%m-%d') for date in earnings_dates], rotation=45, ha='right')

        # Set labels and title
        ax1.set_xlabel('Date')
        ax1.set_ylabel(col)
        ax1.set_title(f'{col} and Earnings Dates')

        plt.tight_layout()
        plt.show()

    def box_plot_days_to_max(self, ticker_list, analysis_list):
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.set_ylabel('Days to Max')
        ax.set_title('Distribution of Days to Max Return After Earnings')

        bplot = ax.boxplot(analysis_list, labels=ticker_list)

        plt.tight_layout()
        plt.show()