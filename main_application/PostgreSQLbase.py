import pandas as pd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from datetime import datetime
from config import db_settings
import pickle
import re
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
import warnings
warnings.filterwarnings("ignore")


class PostgreSQLbase:
    def __init__(self, dbname, user, password, host):
        self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
        self.cursor = self.conn.cursor()

    def __convert_to_normal_stocks(self, rows):
        data = [(row[0], row[1].strftime('%Y-%m-%d'), float(row[2]), float(row[3]), float(row[4]), float(row[5]), row[6]) for row in rows]
        return data

    def __convert_to_normal_news(self,rows):
        data = [(row[0], row[1].strftime('%Y-%m-%d'), row[2], row[3], row[4], row[5], row[6], row[7], row[8]) for row in rows]
        return data
    
    def get_unique_tickers(self):
        query = sql.SQL("""
            SELECT DISTINCT ticker
            FROM stocks_app.stock_quotes
        """)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        tickers = [row[0] for row in rows]
        return tickers

    def refresh_db(self):
        self.conn.commit()
        self.conn.autocommit = True
        
    def get_stock_quotes(self):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM
                stocks_app.stock_quotes
            """)
        self.cursor.execute(query)
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_stocks(rows)

    def get_ticker_quotes_between_dates(self, ticker, start_date, end_date):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM
                stocks_app.stock_quotes
            WHERE
                ticker = %s
                AND date BETWEEN %s AND %s
        """)
        self.cursor.execute(query, (ticker, start_date, end_date))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_stocks(rows)
   
    def load_stocks_from_file(self, file_path):
        # Определяем тип файла и читаем данные
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.txt'):
            df = pd.read_csv(file_path, sep='\t')  
        else:
            raise ValueError("Unsupported file type")


        data = df.values.tolist()  # Изменено для получения списка списков
        columns = ','.join(df.columns)

        # Формируем запрос на вставку данных с проверкой на конфликт
        query = ("""
            INSERT INTO stocks_app.stock_quotes ({columns})
            VALUES %s
            ON CONFLICT (date, ticker) DO NOTHING
        """).format(
            columns=columns
        )

        # Вставляем данные в базу
        execute_values(self.cursor, query, data)
        self.conn.commit()

    def load_news_from_file(self, file_path):
        # Определяем тип файла и читаем данные
        if file_path.endswith('.csv'):
           df = pd.read_csv(file_path)
        elif file_path.endswith('.xls') or file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        elif file_path.endswith('.txt'):
            df = pd.read_csv(file_path, sep='\t')  
        else:
            raise ValueError("Unsupported file type")

        # Подготавливаем данные для вставки в базу
        data = df.values.tolist()  # Изменено для получения списка списков
        columns = ','.join(df.columns)

        # Формируем запрос на вставку данных с проверкой на конфликт
        query = ("""
            INSERT INTO stocks_app.stock_news ({columns})
            VALUES %s
            ON CONFLICT (date, ticker) DO NOTHING
        """).format(
            columns=columns
        )

        # Вставляем данные в базу
        execute_values(self.cursor, query, data)
        self.conn.commit()
    
    def get_ticker_quotes_by_date(self, ticker, date):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM
                stocks_app.stock_quotes
            WHERE
                ticker = %s
                AND date <= %s
            ORDER BY date DESC
            LIMIT 1
        """)
        self.cursor.execute(query, (ticker, date))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_stocks(rows)[0]

    def get_latest_price_before_date(self, ticker, target_date):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM
                stocks_app.stock_quotes
            WHERE
                ticker = %s
                AND date < %s
            ORDER BY date DESC
            LIMIT 1
        """)
        self.cursor.execute(query, (ticker, target_date))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_stocks(rows)[0]

    def get_limit_prices_before_date(self, ticker, target_date, limit=10):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM
                stocks_app.stock_quotes
            WHERE
                ticker = %s
                AND date < %s
            ORDER BY date DESC
            LIMIT %s
        """)
        self.cursor.execute(query, (ticker, target_date, limit))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_stocks(rows)
    
    def get_limit_prices_before_date_with_date(self, ticker, target_date, limit=10):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                open_price,
                high_price,
                low_price,
                close_price,
                volume
            FROM
                stocks_app.stock_quotes
            WHERE
                ticker = %s
                AND date <= %s
            ORDER BY date DESC
            LIMIT %s
        """)
        self.cursor.execute(query, (ticker, target_date, limit))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_stocks(rows)

    def get_news_by_ticker(self, ticker):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                title,
                news_content,
                filtred_content
            FROM
                stocks_app.stock_news
            WHERE
                ticker = %s
        """)
        self.cursor.execute(query, (ticker,))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_news(rows)

    def get_news_between_dates(self, start_date, end_date):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                title,
                news_content,
                filtred_content
            FROM
                stocks_app.stock_news
            WHERE
                date BETWEEN %s AND %s
        """)
        self.cursor.execute(query, (start_date, end_date))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_news(rows)

    def get_news_by_ticker_between_dates(self, ticker, start_date, end_date):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                title,
                news_content,
                filtred_content
            FROM
                stocks_app.stock_news
            WHERE
                ticker = %s
                AND date BETWEEN %s AND %s
        """)
        self.cursor.execute(query, (ticker, start_date, end_date))
        rows = self.cursor.fetchall()
        return self.__convert_to_normal_news(rows)
    
    def get_one_last_headline_before_date(self, ticker, target_date):
        return self.get_latest_news_before_date(ticker, target_date, limit=1)
    
    def get_latest_news_before_date(self, ticker, target_date, limit=10):
        query = sql.SQL("""
            SELECT
                ticker,
                date,
                title,
                content,
                filtered_content,
                positive,
                negative,
                neutral,
                real_score
            FROM
                stocks_app.stock_news
            WHERE
                ticker = %s
                AND date <= %s
            ORDER BY date DESC
            LIMIT %s
        """)
        self.cursor.execute(query, (ticker, target_date, limit))

        rows = self.cursor.fetchall()
        return self.__convert_to_normal_news(rows)

    def add_portfolio(self, username, portfolio_data, date):
        query = """
            INSERT INTO stocks_app.portfolio (username, portfolio_data, created_at)
            VALUES (%s, %s, %s)
        """
        self.cursor.execute(query, (username, portfolio_data,date))
        self.conn.commit()
        
    def save_or_update_portfolio_as_json(self, username, portfolio_json, date):
        
        existing_portfolio, portfolio_date = self.get_portfolio(username, date)
        
        if existing_portfolio and  portfolio_date == datetime.strptime(date, '%d.%m.%Y'):
            if portfolio_date is not None:
                self.update_portfolio(username, portfolio_json, date)
                return "Portfolio updated successfully."
        else:
            if portfolio_date is not None:
                self.add_portfolio(username, portfolio_json, date)
                return "Portfolio added successfully."
        
        return "ОШИБКА"
    
    def update_portfolio(self, username, new_portfolio_data, date):
        query = """
            UPDATE stocks_app.portfolio
            SET 
                portfolio_data = %s
            WHERE 
                username = %s
                and created_at = %s
        """
        self.cursor.execute(query, (new_portfolio_data, username, date))
        self.conn.commit()

    def delete_portfolio(self, username):
        query = """
            DELETE FROM stocks_app.portfolio
            WHERE username = %s
        """
        self.cursor.execute(query, (username,))
        self.conn.commit()

    def get_portfolio(self, username, date):

        if isinstance(date, str):
            date_obj = datetime.strptime(date, '%d.%m.%Y')
        elif isinstance(date, datetime):
            date_obj = date
            
            
        query = """
            SELECT portfolio_data, created_at
            FROM stocks_app.portfolio
            WHERE username = %s
            AND created_at <= %s
            ORDER BY created_at DESC
            LIMIT 1
        """
        # print("Executing SQL query:", query)
        self.cursor.execute(query, (username, date_obj))
        portfolio_data = self.cursor.fetchone()
        if portfolio_data:
            return portfolio_data[0], portfolio_data[1]

        return None, None
    
    def close(self):
        self.cursor.close()
        self.conn.close()        
        
    def authenticate_user(self, username, password):
        query = """
            SELECT *
            FROM stocks_app.authentication
            WHERE username = %s AND password = %s
        """
        self.cursor.execute(query, (username, password))
        user = self.cursor.fetchone()
        if user:
            return True
        return False
    
    def get_data_for_predictions(self, date, filter_flag = 1):
        columns = ['ticker', 'date', 'close_price', 'volume', 'price_change', 'real_score']

        query = """
            SELECT 
                sq.ticker,
                sq.date,
                sq.close_price,
                sq.volume,
                ROUND(sq.close_price - LAG(sq.close_price) OVER (PARTITION BY sq.ticker ORDER BY sq.date),2) AS price_change,
                sn.real_score AS real_score
            FROM 
                stocks_app.stock_quotes sq
            LEFT JOIN (
                SELECT 
                    * 
                FROM 
                    stocks_app.stock_news
            ) sn ON 
                sq.ticker = sn.ticker 
                AND sq.date = sn.date
            WHERE
                sq.ticker = 'SBER'
                and sq.date <= %s
            ORDER BY
                sn.date
            """
        date_obj = datetime.strptime(date, '%d.%m.%Y')
        query = sql.SQL(query)
        self.cursor.execute(query, (date_obj,))
        rows = self.cursor.fetchall()
        data = pd.DataFrame(rows, columns=columns)
        
        data['date'] = pd.to_datetime(data['date'], format="%Y-%m-%d")
        data['close_price'] = data['close_price'].astype(float)
        data['price_change'] = data['price_change'].astype(float)
        data['volume'] = data['volume'].astype(float)
        data['real_score'] = data['real_score'].astype(float)

        data.dropna(inplace=True)

        df = data.copy()
        
        if(filter_flag == 1):
            Q1 = df['price_change'].quantile(0.25)
            Q3 = df['price_change'].quantile(0.75)

            IQR = Q3 - Q1

            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            df = df[(df['price_change'] >= lower_bound) & (df['price_change'] <= upper_bound)]

            print("Размер данных до удаления выбросов:", data.shape)
            print("Размер данных после удаления выбросов:", df.shape)
        
        return df
    
    def get_data_for_predictions_with_limit(self, date, limit):
        data = self.get_data_for_predictions(date, filter_flag=0)
        limited_data = data.tail(limit+1)
        return limited_data
    
    def save_model_to_database(self, model_date, ticker, model):
        
        serialized_model = pickle.dumps(model)

        query = """
            INSERT INTO stocks_app.models (model_date, ticker, model)
            VALUES (%s, %s, %s)
            ON CONFLICT (model_date, ticker) DO UPDATE SET model = EXCLUDED.model
        """

        self.cursor.execute(query, (model_date, ticker, serialized_model))
        self.conn.commit()

        print("Модель успешно сохранена в базе данных.")
    
    def get_model_by_ticker_and_date(self, ticker):
        query = """
            SELECT *
            FROM stocks_app.models
            WHERE ticker = %s
        """
        self.cursor.execute(query, (ticker,))
        model_data = self.cursor.fetchone()
        
        print(model_data)
        if model_data:
            model = pickle.loads(model_data[3])  
            return model
        else:
            return None
        
    def check_model_in_database(self, ticker, date):
        query = """
            SELECT model_date
            FROM stocks_app.models
            WHERE ticker = %s
        """
        self.cursor.execute(query, (ticker,))
        model_dates = self.cursor.fetchall()

        # Convert date string to datetime object
        date_obj = datetime.strptime(date, '%d.%m.%Y')

        for model_date in model_dates:
            model_date_datetime = datetime.combine(model_date[0], datetime.min.time())
            delta = date_obj - model_date_datetime
            if abs(delta.days) < 7:
                return True  
        return False  
    
    def save_scaler_to_database(self, ticker, scaler):
        serialized_scaler = pickle.dumps(scaler)
        query = """
            INSERT INTO stocks_app.scalers (ticker, scaler_data)
            VALUES (%s, %s)
            ON CONFLICT (ticker) DO UPDATE SET scaler_data = EXCLUDED.scaler_data
        """
        self.cursor.execute(query, (ticker, serialized_scaler))
        self.conn.commit()

    def load_scaler_from_database(self, ticker):
        query = """
            SELECT scaler_data
            FROM stocks_app.scalers
            WHERE ticker = %s
        """
        self.cursor.execute(query, (ticker,))
        scaler_data = self.cursor.fetchone()
        if scaler_data:
            scaler = pickle.loads(scaler_data[0])
            return scaler
        else:
            return None

if __name__ == "__main__":
    db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
    db.load_news_from_file('main_application/SBER_news_filtered.csv')
    

