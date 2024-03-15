from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from datetime import datetime
from LeadsOfGrothAndFalls import LeadsOfGrowthAndFalls
from PostgreSQLbase import PostgreSQLbase
from config import db_settings

class App:
    def __init__(self):
        self.app = Flask(__name__)
        self.app.secret_key = 'da.gjlkdgj;oiw3u2m3r8[32m0r8m2398vn32b48nr[ymxhfp234m'
        self.db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
        self.current_date = datetime(2020, 2, 7).strftime('%d.%m.%Y')
        self.current_user = ""
        self.register_routes()
    
    def register_routes(self):
        self.app.add_url_rule('/login', 'login', self.login, methods=['GET', 'POST'])
        self.app.add_url_rule('/', 'home', self.home)
        self.app.add_url_rule('/portfolio', 'portfolio', self.portfolio, methods=['GET', 'POST'])
        self.app.add_url_rule('/logout', 'logout', self.logout)
        self.app.add_url_rule('/get_purchase_price', 'get_purchase_price', self.get_purchase_price)  

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
        last_news = self.db.get_latest_news_before_date('SBER', self.current_date)
        return render_template('index.html', current_date=self.current_date, 
                               leaders_of_growth=leaders_of_growth,
                               leaders_of_fall=leaders_of_fall,
                               last_news=last_news,
                               user=self.current_user)

    def get_purchase_price(self):
        ticker = request.args.get('ticker')
        purchase_price = self.db.get_ticker_quotes_by_date(ticker,self.current_date)[5]
        print(purchase_price)
        return str(purchase_price)  
        
    
    def portfolio(self):
        if 'username' not in session or session['username'] != self.current_user:
            return redirect(url_for('login'))
        
        
        if request.method == 'POST':
            tickers = request.form.getlist('selected_tickers')
            quantities = request.form.getlist('quantity')
            purchase_dates = request.form.getlist('purchase-date')
            print(tickers)
            print(quantities)
            print(purchase_dates)
            for ticker, quantity, purchase_date in zip(tickers, quantities, purchase_dates):
                print(ticker,quantity,purchase_date)

            return redirect(url_for('portfolio'))
                
        tickers = self.db.get_unique_tickers()
        
        return render_template('portfolio.html',
                            user=self.current_user,
                            current_date=self.current_date,
                            tickers=tickers)

    def logout(self):
        session.pop('username', None)
        return redirect(url_for('home'))

    def run(self):
        self.app.run(debug=True)

if __name__ == '__main__':
    app = App()
    app.run()
