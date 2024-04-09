class LeadsOfGrowthAndFalls:
    def __init__(self, db):
        self.db = db

    def calculate_leads(self, date, num_leads=10):
        tickers = self.db.get_unique_tickers()
        
        price_increments = {}
        
        for ticker in tickers:
            yesterday_data = self.db.get_latest_price_before_date(ticker, date)
            if yesterday_data:
                yesterday_close_price = yesterday_data[5]  
            else:
                yesterday_close_price = None
            
            today_data = self.db.get_ticker_quotes_by_date(ticker, date)
            if today_data:
                today_close_price = today_data[5]  
            else:
                today_close_price = None
                
            sentiment = round(self.db.get_one_last_headline_before_date(ticker, date)[0][-1],2)
            # print(len(sentiment))
            print(sentiment)
            
            if yesterday_close_price and today_close_price:
                increment = today_close_price - yesterday_close_price
                print(sentiment)
                price_increments[ticker] = [yesterday_close_price,today_close_price,round(increment,2), round((today_close_price-yesterday_close_price)/yesterday_close_price*100,2), sentiment]
            
        print(price_increments)
        # Сортируем тикеры по приращениям цен за день
        sorted_increments = sorted(price_increments.items(), key=lambda x: x[1], reverse=True)
        
        sorted_increments_up = [[x[0],x[1][0],x[1][1],x[1][2],x[1][3],x[1][4]] for x in sorted_increments if x[1][2]>0]
        sorted_increments_down = [[x[0],x[1][0],x[1][1],x[1][2],x[1][3],x[1][4]] for x in sorted_increments if x[1][2]<0]
        # Получаем лидеров роста и падения
        leaders_of_growth = sorted_increments_up[:num_leads]
        leaders_of_fall = sorted_increments_down[-num_leads:]
        
        # Возвращаем лидеров роста и падения в виде двух списков
        return leaders_of_growth, leaders_of_fall

