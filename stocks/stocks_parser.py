from urllib.request import urlopen
from io import StringIO
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt

stocks_url_dict = {
 'SBER' : 3,
 'GAZP' : 16842,
 'LKOH' : 8,
 'MTSS' : 15523
}

class StockParser:
    def __init__(self, tickers: list, start_date = None, end_date = None):
        self.__tickers = tickers
        self.__year_start = start_date[0:4] if start_date is not None else str(datetime.now().year)
        self.__month_start = start_date[5:7] if start_date is not None else str(datetime.now().month).zfill(2)
        self.__day_start = start_date[8:10] if start_date is not None else str(datetime.now().day).zfill(2)
        self.__year_end = end_date[0:4] if end_date is not None else str(datetime.now().year)
        self.__month_end = end_date[5:7] if end_date is not None else str(datetime.now().month).zfill(2)
        self.__day_end = end_date[8:10] if end_date is not None else str(datetime.now().day).zfill(2)
        self.__data = {}

    def generate_url(self, ticker):
        
        url_template = 'https://export.finam.ru/export9.out?apply=0&p=8&e=.csv&dtf=2&tmf=1&MSOR=0&mstime=on&mstimever=1&sep=3&sep2=1&datf=1&at=0&from={start_date}&to={end_date}&market=0&em={em}&code={ticker}&f={ticker}&cn={ticker}&yf={year_start}&yt={year_end}&df={day_start}&dt={day_end}&mf=0&mt=0'

        url = url_template.format(
            start_date=f"{self.__day_start}.{self.__month_start}.{self.__year_start}",
            end_date=f"{self.__day_end}.{self.__month_end}.{self.__year_end}",
            em=stocks_url_dict[ticker],
            ticker=ticker,
            year_start=self.__year_start,
            year_end=self.__year_end,
            day_start=self.__day_start,
            day_end=self.__day_end
        )
        
        # url = stocks_url_dict[ticker]
        return url

    def parse_stocks(self):
        for ticker in self.__tickers:
            url = self.generate_url(ticker)
            # print(url)
            with urlopen(url) as page:
                content = page.read().decode('utf-8')
                df = pd.read_csv(StringIO(content), delimiter=';', names=['ticker', 'per', 'date', 'time', 'open', 'high', 'low', 'close', 'vol'])
                # print(df)
                df['date'] = pd.to_datetime(df['date'], format='%y%m%d')
                self.__data[ticker] = df

    def plot_stock_data(self):
        plt.figure(figsize=(10, 6))  # Adjust the figure size as needed

        for ticker in self.__tickers:
            plt.plot(self.__data[ticker]['date'], self.__data[ticker]['close'], label=ticker, linewidth=2)  # Adjust linewidth as needed

        plt.title('Stock Prices', fontsize=16)
        plt.xlabel('Date', fontsize=14)
        plt.ylabel('Close Price', fontsize=14)
        plt.legend(fontsize=12)
        plt.grid(True, linestyle='--', alpha=0.7)  # Enable grid with dashed lines and reduced opacity
        plt.style.use('seaborn-darkgrid')  # Apply a seaborn style

        plt.show()


    def get_stocks_dataframe(self):
        if self.__data:
            return self.__data
        else:
            print("Please run parse_stocks() first.")

    def save_to_csv(self, output_folder):
        if self.__data:
            for ticker, df in self.__data.items():
                output_filename = f'{output_folder}/{ticker}_stock_data.csv'
                df.to_csv(output_filename, index=False)
            print("CSV files saved successfully.")
        else:
            print("Please run parse_stocks() first.")

