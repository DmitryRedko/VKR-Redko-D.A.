import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dropout, Dense
from tensorflow.keras.optimizers import Adam
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import MinMaxScaler
from PostgreSQLbase import PostgreSQLbase
from config import db_settings
import warnings
warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')
# import psycopg2
# from psycopg2 import sql
# from config import db_settings
# import pandas as pd
# from datetime import datetime
# import numpy as np


# class PostgreSQLbase:
#     def __init__(self, dbname, user, password, host):
#         self.conn = psycopg2.connect(dbname=dbname, user=user, password=password, host=host)
#         self.cursor = self.conn.cursor()

#     def execute_query(self, query, columns_names = None):
#         query = sql.SQL(query)
#         self.cursor.execute(query)
#         rows = self.cursor.fetchall()
        
#         if columns_names:
#             df = pd.DataFrame(rows, columns=columns_names)
#         else:
#             df = pd.DataFrame(rows)
        
#         return df


# db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])

# columns = ['ticker', 'date', 'close_price', 'volume', 'price_change', 'real_score']

# query = """
# SELECT 
# 	sq.ticker,
# 	sq.date,
# 	sq.close_price,
# 	sq.volume,
# 	ROUND(sq.close_price - LAG(sq.close_price) OVER (PARTITION BY sq.ticker ORDER BY sq.date),2) AS price_change,
#     sn.real_score AS real_score
# FROM 
# 	stocks_app.stock_quotes sq
# LEFT JOIN (
# 	SELECT 
# 		* 
# 	FROM 
# 		stocks_app.stock_news
# ) sn ON 
# 	sq.ticker = sn.ticker 
# 	AND sq.date = sn.date
# WHERE
# 	sq.ticker = 'SBER';
# """

# data = db.execute_query(query, columns)
# data['date'] = pd.to_datetime(data['date'], format="%Y-%m-%d")
# data['close_price'] = data['close_price'].astype(float)
# data['price_change'] = data['price_change'].astype(float)
# data['volume'] = data['volume'].astype(float)
# data['real_score'] = data['real_score'].astype(float)

# data.dropna(inplace=True)

# df = data.copy()

# Q1 = df['price_change'].quantile(0.25)
# Q3 = df['price_change'].quantile(0.75)

# IQR = Q3 - Q1

# lower_bound = Q1 - 1.5 * IQR
# upper_bound = Q3 + 1.5 * IQR

# df = df[(df['price_change'] >= lower_bound) & (df['price_change'] <= upper_bound)]

# print("Размер данных до удаления выбросов:", data.shape)
# print("Размер данных после удаления выбросов:", df.shape)



class StockPricePredictor:
    def __init__(self, prediction_days, custom_lr, EPOCHS, BATCH_SIZE, n_features):
        self.prediction_days = prediction_days
        self.custom_lr = custom_lr
        self.EPOCHS = EPOCHS
        self.BATCH_SIZE = BATCH_SIZE
        self.db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
        self.model = self._build_model(n_features)
        
    def split_train_x_y(self, df, features_to_train):
        
        train_df = df[features_to_train]
        train_df = np.array(train_df)
        x_train = []
        y_train = []

        for day in range(self.prediction_days, len(train_df)):      
            
            x_train.append(train_df[day-self.prediction_days:day])
            y_train.append(train_df[day])                     
        x_train, y_train = np.array(x_train), np.array(y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], x_train.shape[2]))
        
        return x_train, y_train
    
    def split_train_x_y(self, data, features_to_train):
        
        df = data[features_to_train]
        df_arr = np.array(df)
        x_train = []
        y_train = []

        for day in range(self.prediction_days, len(df_arr)):      
            
            x_train.append(df_arr[day-self.prediction_days:day])
            y_train.append(df_arr[day])                     
        x_train, y_train = np.array(x_train), np.array(y_train)
        
        # print(x_train, y_train)
        x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], x_train.shape[2]))
        
        return x_train, y_train
    
    def split_test_x(self, data, features_to_train):
        
        df = data[features_to_train]
        df_arr = np.array([np.array(df)])
        
        # print(df_arr)
        # print(df_arr.shape)
        x_test = np.reshape(df_arr, (df_arr.shape[0], df_arr.shape[1], df_arr.shape[2]))
        
        return x_test

    def _build_model(self, n_features):
        model = Sequential()
        model.add(LSTM(units=128, return_sequences=True, input_shape=(self.prediction_days, n_features)))
        model.add(Dropout(0.2))
        model.add(LSTM(units=64, return_sequences=True))
        model.add(Dropout(0.2))
        model.add(LSTM(units=32))
        model.add(Dropout(0.2))
        model.add(Dense(units=n_features, activation="linear"))
        model.compile(optimizer=Adam(learning_rate=self.custom_lr), loss='mean_squared_error')
        return model
    
    def load_model_from_base(self, ticker):
        self.model = self.db.get_model_by_ticker_and_date(ticker)
        
    def train(self, x_train, y_train):
        history = self.model.fit(x_train, y_train, epochs=self.EPOCHS, batch_size=self.BATCH_SIZE)
        return history

    def predict(self, x_test):
        predicted_prices = self.model.predict(x_test)
        return predicted_prices

    def evaluate(self, test_df, predicted_prices):
        rmse = mean_squared_error(test_df,predicted_prices, squared=False)
        return rmse
    
    def save_model(self, date, ticker):
        self.db.save_model_to_database(date, ticker, self.model)



class DataPreprocessor:
    def __init__(self, cols_not_to_convert):
        self.not_to_convert = cols_not_to_convert
        self.data = None
        self.db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
        self.scalers = {}

    def fit_transform(self,data):
        self.data = data
        for x in self.data.columns:
            print(x, data.columns,self.not_to_convert)
            if(x not in self.not_to_convert):
                self.scalers[x] = MinMaxScaler(feature_range=(0, 1))
                self.data[[x]] = self.scalers[x].fit_transform(self.data[[x]].values.reshape(-1, 1))
        
        return self.data
                
    def fit(self,data):
        self.data = data
        for x in self.data.columns:
            if(x not in self.not_to_convert):
                self.scalers[x] = MinMaxScaler(feature_range=(0, 1))
    
    def transform(self, data):
        for x in data.columns:
            if(x not in self.not_to_convert):
                data[[x]] = self.scalers[x].fit_transform(data[[x]].values.reshape(-1, 1))
        return data


    def inverse_transform(self, data):
        for x in data.columns:
            if(x not in self.not_to_convert):
                data[[x]] = self.scalers[x].inverse_transform(data[[x]].values.reshape(-1, 1))
        return data
    
    def save_scaler_to_database(self, ticker):
        self.db.save_scaler_to_database(ticker, self.scalers)
    
    def load_scaler_from_database(self, ticker):
        self.scalers = self.db.load_scaler_from_database(ticker)        
    
        
    

# prediction_days = 20
# custom_lr = 0.001
# EPOCHS = 50
# BATCH_SIZE = 16
# n_features = 3
# features_to_train = ['close_price', 'volume', 'real_score']

# data_scaler = DataPreprocessor(['date'])

# df = data_scaler.fit_transform(df[['date','close_price', 'volume', 'real_score']])

# test_df = df.loc[df['date'] > '2023-9-01']
# train_df = df.loc[(df['date'] < '2023-9-01') & (df['date'] > '2016-11-01')]    

# predictor = StockPricePredictor(prediction_days=20, custom_lr=0.001, EPOCHS=50, BATCH_SIZE=16, n_features=n_features)

# x_train, y_train = predictor.split_x_y(train_df,features_to_train)
# x_test, y_test = predictor.split_x_y(test_df,features_to_train)

# print(x_train)
# print(y_train)

# history = predictor.train(x_train, y_train)
# predicted_prices = predictor.predict(x_test)

# prices_real = data_scaler.inverse_transform(pd.DataFrame(y_test,columns=['close_price', 'volume', 'real_score']))
# predicted_prices = data_scaler.inverse_transform(pd.DataFrame(predicted_prices,columns=['close_price', 'volume', 'real_score']))

# print(predicted_prices[:5])
# print(prices_real[:5])

# rmse = predictor.evaluate(prices_real['close_price'], predicted_prices['close_price'])

# print(rmse)