import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

class Stock_Analysis():

    def get_stock_data(self, ticker, start_date, end_date):
        stock = yf.Ticker(ticker)
        df = stock.history(start=start_date, end=end_date)
        return df

    def get_earnings_dates(self, ticker, start_date, end_date):
        stock = yf.Ticker(ticker)
        earnings = stock.earnings_dates
        return earnings[(earnings.index >= start_date) & (earnings.index <= end_date)]

    def analyze_stock_performance(self, ticker, start_date, end_date, days_before=5, days_after=20):
        # Get stock data and earnings dates
        stock_data = self.get_stock_data(ticker, start_date, end_date)
        earnings_dates = self.get_earnings_dates(ticker, start_date, end_date)


        # Ensure both DataFrames have aligned timezone-aware indices
        earnings_dates.index = earnings_dates.index.tz_localize(None)
        stock_data.index = stock_data.index.tz_localize(None)

        results = []

        for earnings_date in earnings_dates.index:
            start = earnings_date - timedelta(days=days_before)
            end = earnings_date + timedelta(days=days_after)
            
            period_data = stock_data.loc[start:end]

            if earnings_date.floor('D') not in period_data.index:
                print(f"Warning: Earnings date {earnings_date} not found in stock_data.")
                continue
            
            # Calculate daily range and average daily range
            daily_range = period_data['High'] - period_data['Low']
            avg_daily_range = daily_range.mean()
            
            # Calculate return since earnings
            returns = (period_data['Close'] / period_data.loc[earnings_date.floor('D'), 'Close'] - 1) * 100
            
            # Find the day with maximum return
            max_return_day = returns.idxmax()
            max_return = returns.max()
            days_to_max = (max_return_day - earnings_date).days
            
            results.append({
                'Earnings_Date': earnings_date,
                'Avg_Daily_Range': avg_daily_range,
                'Max_Return': max_return,
                'Days_to_Max': days_to_max
            })
        
        return pd.DataFrame(results)

    def plot_performance(self, ticker, start_date, end_date, analysis_results):
        stock_data = self.get_stock_data(ticker, start_date, end_date)
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10), sharex=True)
        
        # Plot stock price
        ax1.plot(stock_data.index, stock_data['Close'])
        ax1.set_title(f'{ticker} Stock Price and Earnings Dates')
        ax1.set_ylabel('Stock Price')
        
        # Plot earnings dates
        for date in analysis_results['Earnings_Date']:
            ax1.axvline(x=date, color='r', linestyle='--', alpha=0.5)
        
        # Plot average daily range
        ax2.plot(analysis_results['Earnings_Date'], analysis_results['Avg_Daily_Range'])
        ax2.set_title('Average Daily Range around Earnings Dates')
        ax2.set_ylabel('Average Daily Range')
        ax2.set_xlabel('Date')
        
        plt.tight_layout()
        plt.show()
