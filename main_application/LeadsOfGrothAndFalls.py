class LeadsOfGrowthAndFalls:
    def __init__(self, db):
        self.db = db

    def calculate_leads(self, date, num_leads=10):
        # Получаем все уникальные тикеры
        tickers = self.db.get_unique_tickers()
        
        # Словарь для хранения приращений цен за день
        price_increments = {}
        
        # Проходим по каждому тикеру и вычисляем приращение цен за день
        for ticker in tickers:
            # Получаем данные за предыдущий день
            yesterday_data = self.db.get_latest_price_before_date(ticker, date)
            if yesterday_data:
                yesterday_close_price = yesterday_data[5]  # Получаем цену закрытия за предыдущий день
            else:
                yesterday_close_price = None
            
            # Получаем данные за сегодняшний день
            today_data = self.db.get_ticker_quotes_by_date(ticker, date)
            if today_data:
                today_close_price = today_data[5]  # Получаем цену закрытия за сегодняшний день
            else:
                today_close_price = None
            
            # Вычисляем приращение цен за день
            if yesterday_close_price and today_close_price:
                increment = today_close_price - yesterday_close_price
                price_increments[ticker] = [yesterday_close_price,today_close_price,round(increment,2), round((today_close_price-yesterday_close_price)/yesterday_close_price*100,2), self.db.get_limit_prices_before_date(ticker,date)]
        
        # Сортируем тикеры по приращениям цен за день
        sorted_increments = sorted(price_increments.items(), key=lambda x: x[1], reverse=True)
        sorted_increments_up = [[x[0],x[1][0],x[1][1],x[1][2],x[1][3]] for x in sorted_increments if x[1][2]>0]
        sorted_increments_down = [[x[0],x[1][0],x[1][1],x[1][2],x[1][3]] for x in sorted_increments if x[1][2]<0]
        # Получаем лидеров роста и падения
        leaders_of_growth = sorted_increments_up[:num_leads]
        leaders_of_fall = sorted_increments_down[-num_leads:]
        
        # Возвращаем лидеров роста и падения в виде двух списков
        return leaders_of_growth, leaders_of_fall

if __name__ == '__main__':
    # Пример использования
    db = PostgreSQLbase(db_settings['dbname'], db_settings['user'], db_settings['password'], db_settings['host'])
    leads_calculator = LeadsOfGrowthAndFalls(db)
    leaders_of_growth, leaders_of_fall = leads_calculator.calculate_leads('2016-04-01')
    print("Лидеры роста:")
    for leader in leaders_of_growth:
        print(f"{leader[0]}: {leader[1]}")
    print("\nЛидеры падения:")
    for leader in leaders_of_fall:
        print(f"{leader[0]}: {leader[1]}")
    db.close()