from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime, timedelta
from LeadsOfGrothAndFalls import LeadsOfGrowthAndFalls
from PostgreSQLbase import PostgreSQLbase
from NNModel import DataPreprocessor, StockPricePredictor
from config import db_settings
from datetime import datetime, timedelta
import pandas as pd
import json
import locale
import warnings
warnings.filterwarnings("ignore")
import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
import tensorflow as tf
tf.get_logger().setLevel('ERROR')

locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')

class App:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'da.gjlkdgj;oiw3u2m3r8[32m0r8m2398vn32b48nr[ymxhfp234m'
        self.db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
        real_date =  datetime(2020, 4, 10)
        self.current_date = real_date.strftime('%d.%m.%Y')
        self.weekday = real_date.strftime('%A')
        self.current_user = ""
        self.flag_update = 0
        self.new_portfolio_json = ""
        self.register_routes()
    
    def register_routes(self):
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/portfolio', 'portfolio', self.portfolio, methods=['GET', 'POST'])
        self.app.add_url_rule('/prediction', 'prediction', self.prediction, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)
        self.app.add_url_rule('/get_purchase_price', 'get_purchase_price', self.get_purchase_price)  
        self.app.add_url_rule('/get_sentiment', 'get_sentiment', self.get_sentiment)  
        self.app.add_url_rule('/get_current_date', 'get_current_date', self.get_current_date)  
        self.app.add_url_rule('/process_form_data', 'process_form_data', self.process_form_data, methods=['GET', 'POST'])  
        self.app.add_url_rule('/get_chart_data', 'get_chart_data', self.get_chart_data, methods=['GET'])
        self.app.add_url_rule('/get_chart_data_with_prediction', 'get_chart_data_with_prediction', self.get_chart_data_with_prediction, methods=['GET'])

    def login(self):
        if request.method == 'POST':
            username = request.form['username']
            password = request.form['password']
            if self.db.authenticate_user(username, password):
                session['username'] = username
                self.current_user = username
                return redirect(url_for('home'))
            else:
                return render_template('login.html', message='Неверное имя пользователя или пароль.')
        return render_template('login.html')

    def home(self):
        if 'username' not in session or session['username'] != self.current_user:
            return redirect(url_for('login'))
        leads_calculator = LeadsOfGrowthAndFalls(self.db)
        leaders_of_growth, leaders_of_fall = leads_calculator.calculate_leads(self.current_date)
        tickers = self.db.get_unique_tickers()
        
        last_news = []
        for ticker in tickers:
            last_news+=self.db.get_latest_news_before_date(ticker, self.current_date)
        
        last_news.sort(key=lambda x: datetime.strptime(x[1], '%Y-%m-%d'), reverse=True)
        
        # print(leaders_of_growth)
        # print(leaders_of_fall)
        
        return render_template('index.html', current_date=self.current_date, 
                               leaders_of_growth=leaders_of_growth,
                               leaders_of_fall=leaders_of_fall,
                               last_news=last_news,
                                weekday = self.weekday,
                               user=self.current_user)

    def process_form_data(self):
        data = request.json['data']
        purchase_dates = []
        tickers = []
        quantities = []
        purchase_price = []
        
        for key, value in data.items():
            ticker = ""
            if('new' in key):
                print(f"Key: {key}")
                print("Value:")
                for k, v in value.items():
                    print(f"\t{k}: {v}")
                    if(k == 'purchase_date'):
                        purchase_dates.append(v)
                    if(k == 'ticker'):
                        ticker = v
                        tickers.append(v)
                    if(k == 'new_quantity'):
                        quantities.append(v)
                    if(k == 'new_purchase_price'):
                        purchase_price.append(self.db.get_ticker_quotes_by_date(ticker,self.current_date)[5])
            else:
                print(f"Key: {key}")
                print("Value:")
                for k, v in value.items():
                    print(f"\t{k}: {v}")
                    if(k == 'purchase_date'):
                        purchase_dates.append(v)
                    if(k == 'ticker'):
                        tickers.append(v)
                    if(k == 'new_quantity'):
                        quantities.append(v)
                    if(k == 'new_purchase_price'):
                        purchase_price.append(v)

        portfolio_data = {
                'tickers': tickers,
                'quantities': quantities,
                'purchase_prices': purchase_price,
                'purchase_dates': purchase_dates
            }
        self.new_portfolio_json = json.dumps(portfolio_data)
        self.flag_update = 1
        return redirect(url_for('portfolio'))
        
    def get_current_date(self):
        return self.current_date
    
    def get_purchase_price(self):
        ticker = request.args.get('ticker')
        purchase_price = self.db.get_ticker_quotes_by_date(ticker,self.current_date)[5]
        return str(purchase_price)  
     
    def get_sentiment(self):
        ticker = request.args.get('ticker')
        sentiment = round(self.db.get_latest_news_before_date(ticker,self.current_date)[0][-1],2)
        return str(sentiment)  
     
    def create_recomendation(self, sentiment):
        if(sentiment >= 0.7):
            return "Покупать"
        if(sentiment >= 0.25 and sentiment<0.7):
            return "Возможен рост"
        if(sentiment >= -0.25 and sentiment<0.25):
            return "Держать"
        if(sentiment >= -0.7 and sentiment<-0.25):
            return "Возможно падение"
        if(sentiment<-0.7):
            return "Продавать"
        
    def create_graph_data(self, date, period):
        if isinstance(date, str):
            date = datetime.strptime(date, '%d.%m.%Y')
            
        previous_days = [date.strftime('%d.%m.%Y')]

        for i in range(1, period):
            previous_day = date - timedelta(days=i)
            previous_days.append(previous_day.strftime('%d.%m.%Y'))
        
        dates = []
        purchase_portfolio_data = []
        dynamic_portfolio_data = []
        
        for date in previous_days:
            temp_val = self.db.get_portfolio(self.current_user,date)[0]
            if(temp_val is not None):
                temp1 = 0
                temp2 = 0
                for i in range(len(temp_val['tickers'])):
                    print(temp_val['quantities'][i],temp_val['purchase_prices'][i],temp_val['tickers'][i],self.db.get_ticker_quotes_by_date(temp_val['tickers'][i],date)[5])
                    temp1 += int(temp_val['quantities'][i])*float(temp_val['purchase_prices'][i])
                    temp2 += int(temp_val['quantities'][i])*self.db.get_ticker_quotes_by_date(temp_val['tickers'][i],date)[5]
                dates += [date]
                purchase_portfolio_data += [round(temp1,2)]
                dynamic_portfolio_data += [round(temp2,2)]
            
        return dates, purchase_portfolio_data, dynamic_portfolio_data
        
    def get_current_portfolio_info(self):
        
        portfolio_mass = []
        
        portfolio_data, _ = self.db.get_portfolio(self.current_user, self.current_date)
        total_portfolio_value = 0

        for i in range(len(portfolio_data['tickers'])):
            quantity = int(portfolio_data['quantities'][i])
            purchase_price = float(portfolio_data['purchase_prices'][i])
            total_portfolio_value += quantity * purchase_price


        for i in range(len(portfolio_data['tickers'])):
            temp_dict = {}
            temp_dict['ticker'] = portfolio_data['tickers'][i]
            temp_dict['quantity'] = int(portfolio_data['quantities'][i])
            temp_dict['purchase_price'] = float(portfolio_data['purchase_prices'][i])
            temp_dict['purchase_date'] = portfolio_data['purchase_dates'][i]
            temp_dict['current_price'] = float(self.db.get_ticker_quotes_by_date(temp_dict['ticker'],self.current_date)[5])
            temp_dict['total_cost'] = round(temp_dict['quantity'] * temp_dict['purchase_price'],2)
            temp_dict['persent'] = round(temp_dict['quantity'] * temp_dict['purchase_price']/total_portfolio_value*100,2)
            temp_dict['sentiment'] = round(self.db.get_one_last_headline_before_date(portfolio_data['tickers'][i], self.current_date)[0][-1],2)
            temp_dict['recomendation'] = self.create_recomendation(temp_dict['sentiment'])
            
            portfolio_mass+=[temp_dict]
        
        total_portfolio_value = round(total_portfolio_value,2)
        
        return portfolio_mass, total_portfolio_value    
    
    def portfolio(self):
        if 'username' not in session or session['username'] != self.current_user:
            return redirect(url_for('login'))
        
        tickers = ""
        
        if(self.flag_update == 1):
            self.db.save_or_update_portfolio_as_json(self.current_user, self.new_portfolio_json, self.current_date)
            self.flag_update = 0
            return redirect(url_for('portfolio'))

        
        if(request.method == 'POST' and 'add_save_portfolio' in request.form):
            tickers = request.form.getlist('selected_tickers')[0].split(',')
            quantities = request.form.getlist('quantity')
            purchase_dates = request.form.getlist('purchase-date')

            portfolio_data = {
                'tickers': tickers,
                'quantities': quantities,
                'purchase_prices': [self.db.get_ticker_quotes_by_date(ticker,self.current_date)[5] for ticker in tickers],
                'purchase_dates': purchase_dates
            }
            portfolio_json = json.dumps(portfolio_data)
            
            self.db.add_portfolio(self.current_user, portfolio_json, self.current_date)
            return redirect(url_for('portfolio'))
        
        try:
            self.db.refresh_db()
            tickers = self.db.get_unique_tickers()
        except Exception as e:
            print("Ошибка 1:", e)
        
        portfolio_mass = []
        total_portfolio_value = ""
        
        try:
            portfolio_mass, total_portfolio_value = self.get_current_portfolio_info()
        except Exception as e:
            print("Ошибка 2:", e)
            
        graph_dates = []
        graph_purchase_portfolio_data = []
        graph_dynamic_portfolio_data = []
            
        try:
            graph_dates, graph_purchase_portfolio_data, graph_dynamic_portfolio_data = self.create_graph_data(self.current_date, 365)
        except Exception as e:
            print("Ошибка 2:", e)

        create_portfolio_status = ""
        if portfolio_mass:
            create_portfolio_status = "hidden"
            
        return render_template('portfolio.html',
                            user=self.current_user,
                            create_portfolio_status = create_portfolio_status,
                            current_date=self.current_date,
                            weekday = self.weekday,
                            tickers=tickers,
                            portfolio_mass = portfolio_mass,
                            total_portfolio_value = total_portfolio_value,
                            graph_dates=list(reversed(graph_dates)),
                            graph_purchase_portfolio_data=list(reversed(graph_purchase_portfolio_data)),
                            graph_dynamic_portfolio_data=list(reversed(graph_dynamic_portfolio_data)))

    def prediction(self):
        if 'username' not in session or session['username'] != self.current_user:
             redirect(url_for('login'))
             
        available_tickers = ""
        try:
            self.db.refresh_db()
            available_tickers = self.db.get_unique_tickers()
        except Exception as e:
            print("Ошибка при получении доступных тикеров:", e)
        
        return render_template('prediction.html',
                               available_tickers=available_tickers,
                               current_date = self.current_date,
                               weekday = self.weekday,
                               user=self.current_user)
    
    def get_graph_data(self, ticker, range_dates_str, prediction = None):
        range_dates =0
        if(range_dates_str == 'week'):
            range_dates =7
        if(range_dates_str == 'month'):
            range_dates =31
        if(range_dates_str == 'half-year'):
            range_dates =183
        if(range_dates_str == 'year'):
            range_dates =365
        
        temp_query = self.db.get_limit_prices_before_date_with_date(ticker, self.current_date, limit=range_dates)
        ticker_mass = list(reversed([x[5] for x in temp_query])) 
        dates_mass =  list(reversed([x[1] for x in temp_query]))   
            
        if prediction is not None:
            ticker_mass += prediction
            last_date = datetime.strptime(dates_mass[-1], '%Y-%m-%d')  
            next_date = last_date + timedelta(days=1)

            while next_date.weekday() >= 5: 
                next_date += timedelta(days=1)

            dates_mass.append(next_date.strftime('%Y-%m-%d'))
            
        news_sentiment = ""
        purchase_price = ""
            
        if(ticker != ''):
            news_sentiment = round(self.db.get_latest_news_before_date(ticker,self.current_date)[0][-1],2)
            purchase_price = self.db.get_ticker_quotes_by_date(ticker,self.current_date)[5]
            
        print(ticker)
        print(range_dates_str)
        print(range_dates)
        print(ticker_mass)
        print(dates_mass)

        chart_data = {
            "ticker": ticker,
            "labels": dates_mass,
            "dataset": ticker_mass,
            "newsSentiment": news_sentiment,
            "currentPrice": purchase_price
        }
        return chart_data
    
    def check_model_status(self,ticker, date):
        return self.db.check_model_in_database(ticker, date)
    
    def train_model(self, ticker):
        df =  self.db.get_data_for_predictions(self.current_date)
        data_scaler = DataPreprocessor(['date'])
        
        df = data_scaler.fit_transform(df[['date','close_price', 'volume', 'real_score']])   
        
        predictor = StockPricePredictor(prediction_days=20, custom_lr=0.001, EPOCHS=5, BATCH_SIZE=16, n_features=3)  
        x_train, y_train = predictor.split_train_x_y(df,['close_price', 'volume', 'real_score'])
        history = predictor.train(x_train, y_train)
        data_scaler.save_scaler_to_database(ticker)
        predictor.save_model(self.current_date, ticker)
        
    def get_chart_data_with_prediction(self):
        ticker = request.args.get('ticker')
        range_dates_str = request.args.get('range')

        if self.check_model_status(ticker, self.current_date) == False:
            return "Требуется обучить модель"

        test_df = self.db.get_data_for_predictions_with_limit(self.current_date, 19)

        # print(test_df)
        
        data_scaler = DataPreprocessor(['date'])
        data_scaler.load_scaler_from_database(ticker)
        test_df = data_scaler.transform(test_df[['date','close_price', 'volume', 'real_score']])
        
        predictor = StockPricePredictor(prediction_days=20, custom_lr=0.001, EPOCHS=5, BATCH_SIZE=16, n_features=3)  
        x_test = predictor.split_test_x(test_df,['close_price', 'volume', 'real_score'])
        predictor.load_model_from_base(ticker)
        predicted_prices = predictor.predict(x_test)
        
        # prices_real = data_scaler.inverse_transform(pd.DataFrame(y_test,columns=['close_price', 'volume', 'real_score']))
        predicted_prices = data_scaler.inverse_transform(pd.DataFrame(predicted_prices,columns=['close_price', 'volume', 'real_score']))

        # print(list(predicted_prices['close_price']))
        # print(prices_real)
                
        # rmse = predictor.evaluate(prices_real['close_price'], predicted_prices['close_price'])

        # print(rmse)
        
        return self.get_graph_data(ticker, range_dates_str, prediction = list(predicted_prices['close_price']))
    
    def get_chart_data(self):
        ticker = request.args.get('ticker')
        range_dates_str = request.args.get('range')
        # print("here")
        return self.get_graph_data(ticker, range_dates_str)
        
    def logout(self):
        session.pop('username', None)
        return redirect(url_for('home'))

    def run(self):
        self.app.run(debug=True, port=5013)

if __name__ == '__main__':
    app = App()
    app.run()
