import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

class StockParser:
    def __init__(self, tickers, start_date, end_date):
        self.tickers = tickers
        self.start_date = start_date
        self.end_date = end_date
        self.data = pd.DataFrame(columns=tickers)

    def fetch_stock_data(self):
        for ticker in self.tickers:
            self.data[ticker] = yf.download(ticker, self.start_date, self.end_date)['Adj Close']

    def plot_stock_data(self):
        for ticker in self.tickers:
            self.data[ticker].plot(label=ticker)

        plt.title('Stock Prices')
        plt.xlabel('Date')
        plt.ylabel('Adj Close Price')
        plt.legend()
        plt.show()

