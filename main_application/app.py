from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime
from LeadsOfGrothAndFalls import LeadsOfGrowthAndFalls
from PostgreSQLbase import PostgreSQLbase
from config import db_settings

app = Flask(__name__)
db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
app.secret_key = 'da.gjlkdgj;oiw3u2m3r8[32m0r8m2398vn32b48nr[ymxhfp234m'

# current_date = datetime.now().strftime('%d.%m.%Y')
current_date = datetime(2020, 2, 7).strftime('%d.%m.%Y')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if db.authenticate_user(username, password):
            session['username'] = username
            return redirect(url_for('home'))
        else:
            return render_template('login.html', message='Неверное имя пользователя или пароль.')
    return render_template('login.html')

@app.route('/')
def home():
    if 'username' not in session:
        return redirect(url_for('login'))
    leads_calculator = LeadsOfGrowthAndFalls(db)
    leaders_of_growth, leaders_of_fall = leads_calculator.calculate_leads(current_date)
    print(leaders_of_growth)
    print(leaders_of_fall)
    
    last_news = db.get_latest_news_before_date('SBER',current_date)
    
    return render_template('index.html', current_date=current_date, leaders_of_growth=leaders_of_growth, leaders_of_fall=leaders_of_fall, last_news = last_news)

@app.route('/portfolio')
def portfolio():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('portfolio.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)