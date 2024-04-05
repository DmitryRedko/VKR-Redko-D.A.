import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import locale
# import nltk
# nltk.download('punkt')
from nltk.tokenize import sent_tokenize
from sentiment_analyzer import NewsSentimentAnalyzer

keywords_dict = {
    "SBER":["СБЕР", "Сбербанк", "Сбер", "Сберколл", "Сбербизнес", "Сбертек", "Сбермаркет", "Мегамаркет", "Греф", "Сберколлектор", "Сбербизнес", "Сбертек", "Сбермаркет", "СберЛогистика", "СберЛизинг", "СберНедвижимость", "Сбербанк-АСТ", "Сбербанк-Резерв", "Сбербанк-Спасение", "Сбербанк-Страхование", "Сбербанк-Технологии", "Сбербанк-Эквайринг", "Сбербанк-Эксперт", "Сбербанк-Контактный Центр"],
    "GAZP":["GAZP", "Газстройпром", "Газпрома","Газпром", "Газпромнефть", "Газпромбанк", "Газпроммедиа", "Газпромтранс", "Газпромдобыча", "Газпромэнерго", "Газпромавиа", "Газпроммежрегионгаз", "Газпроминвестходинг", "Газпромнедра", "Газпромпереработка", "Газпромпоставка", "Газпроммонтаж", "Газпромвнешэкономбанк", "Газпромснаб", "Газпромавтоматизация", "Газпромкомплектация", "Газпромгазораспределение", "Газпромэнергосбыт", "Газпромнефтегаз", "Газпромгазэнергосбыт", "Газпромкапитал", "Газпромстрой", "Газпромнефтьцентр", "Газпромтрансгаз", "Газпромбурение", "Газпромперевозка", "Газпромавтоматика"],
    "LKOH":["LKOH", "Лукойл", "Лукойл-Нефтепродукт", "Лукойл-Гарант", "Лукойл-Инжиниринг", "Лукойл-Москва", "Лукойл-Пермь", "Лукойл-Уралнефтегаз", "Лукойл-Западная Сибирь", "Лукойл-Волгограднефтепродукт", "Лукойл-Калуга", "Лукойл-Трейд", "Лукойл-Нижегороднефтепродукт", "Лукойл-Югнефтепродукт", "Лукойл-Кубаньнефтепродукт", "Лукойл-Казахстан", "Лукойл-Азербайджан", "Лукойл-Украина", "Лукойл-Гео", "Лукойл-Газпром", "Лукойл-Технологии", "Лукойл-Центрнефтепродукт", "Лукойл-Волгограднефтехим", "Лукойл-Юг", "Лукойл-Информ", "Лукойл-Север", "Лукойл-Калининграднефтепродукт", "Лукойл-Центр", "Лукойл-Санкт-Петербург", "Лукойл-Северозапад", "Лукойл-Московиянефтепродукт", "Лукойл-Сургутнефтепродукт", "Лукойл-Холдинг", "Лукойл-Сибирь", "Лукойл-Энергосбыт"],
    "MTSS": ["MTSS", "МТС", "Мобильные ТелеСистемы", "МТС-Банк", "MTS Money", "МТС-Медиа", "МТС-Телеком", "МТС-Украина", "МТС-Туркменистан", "МТС-Беларусь", "МТС-Армения", "МТС-Киргизия", "МТС-Узбекистан", "МТС-Индия", "МТС-Таджикистан", "МТС-Армения", "МТС-Казахстан", "МТС-Туркменистан", "МТС-Туркменистан", "МТС-Турция", "МТС-Грузия", "МТС-Киргизия", "МТС-Монтенегро", "МТС-Мьянма", "МТС-Сейшелы", "МТС-Шри-Ланка", "МТС-Гана", "МТС-Нигерия", "МТС-Иран", "МТС-Афганистан", "МТС-Пакистан", "МТС-Армения"]
}

class NewsParser:
    def __init__(self, url, keywords, ticker):
        self.__url = url
        self.__keywords = keywords
        self.__driver = None
        self.__news = []
        self.ticker = ''
        self.min_date = '2028-01-01'

    def __extract_sentences(self, content):
        sentences = sent_tokenize(content)
        res_sentences = [sentence for sentence in sentences if any(keyword.lower() in sentence.lower() for keyword in self.__keywords)]
        return res_sentences
    
    def __format_date(self,date):
        if 'Сегодня' in date:
            formatted_date = (datetime.now()).strftime('%Y-%m-%d') 
        elif 'Вчера' in date:
            formatted_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') 
        elif ' в 'in date:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
            formatted_date = datetime.strptime(date, '%d %B в %H:%M').strftime('%Y-%m-%d')
        else:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
            formatted_date = datetime.strptime(date, '%d %B %Y').strftime('%Y-%m-%d')            
        
        return formatted_date

    def __parse_news(self, news_block):
        try:
            date = news_block.find("time").text.strip()
            title = news_block.find("a", class_="iKzE").text.strip()
            href = news_block.find("a", class_="iKzE")["href"]
            
            return [self.__format_date(date), title, href]
            
        except Exception as e:
            print("An error occurred while parsing news:", e)
            return None

    def parse_news(self,len_dataset=500, stop_date=None):
        self.__driver = webdriver.Chrome()
        self.__driver.get(self.__url)
        
        while len(self.__news) < len_dataset:
            show_more_button = WebDriverWait(self.__driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='nlJ0' and contains(text(), 'Показать еще новости')]"))
            )

            self.__driver.execute_script("arguments[0].click();", show_more_button)

            updated_html = BeautifulSoup(self.__driver.page_source, 'html.parser')
            news_blocks = updated_html.find_all("div", class_="TjB6 KSLV Ncpb E6j8")

            show_more_button = WebDriverWait(self.__driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//span[@class='nlJ0' and contains(text(), 'Показать еще новости')]"))
            )

            if not show_more_button.is_displayed():
                break

            for news_block in news_blocks[len(self.__news):]:
                date = news_block.find("time").text.strip()
                if(date>self.min_date):
                    self.min_date = date
                title = news_block.find("a", class_="iKzE").text.strip()
                href = news_block.find("a", class_="iKzE")["href"]
                # print(date, title, href)
                self.__news.append([date, title, href])
            if len(self.__news) >= len_dataset or (stop_date and self.min_date < stop_date):
                break
            if(len(self.__news)%100==0):
                print("Загружено: ",len(self.__news))
                self.save_to_csv(f'{self.ticker}_in_progress.csv')

        self.__driver.quit()

    def get_news_list(self):
        return self.__news

    def save_to_csv(self, output_filename):
        if self.__news:
            df = pd.DataFrame(self.__news, columns=['Date', 'Title', 'URL'])
            df.to_csv(output_filename, index=False)
        else:
            print("No news data to save.")


class HelperParser:
    def __init__(self,keywords,ticker):
        self.__keywords = keywords[ticker]
        self.__driver = webdriver.Chrome()
        self.__analyzer = NewsSentimentAnalyzer()

    def parse_dataset(self, dataframe):
        parsed_data = []
        for _, row in dataframe.iterrows():
            try:
                ticker = row['Ticker']
                title = row['Title']
                date = row['Date']
                url = row['URL']
                parsed_data.append(self.parse_url(ticker, title, date, url))
                if(len(parsed_data)%10==0):
                    print("Загружено", len(parsed_data))
                    pd.DataFrame(parsed_data).to_csv(f"{ticker}_news_in_progress.csv")
            except:
                pass
        return pd.DataFrame(parsed_data)

    def parse_url(self, ticker, title, date, url):
        self.__driver.get(url)
        content_html = BeautifulSoup(self.__driver.page_source, 'html.parser')
        content = content_html.find("div", class_="YjHz UBOr RkGZ").text.strip()
        filtered_content = self.__extract_sentences(content)
        sentiment_df = self.__analyzer.analyze_sentiment(filtered_content)
        res_dict = {
            'ticker': ticker,
            'date': date,
            'title': title,
            'content': content,
            'filtered_content': filtered_content,
            'EN_filtered_content': list(sentiment_df['En Headline'])[0],
            'Positive': list(sentiment_df['Positive'])[0],
            'Negative': list(sentiment_df['Negative'])[0],
            'Neutral': list(sentiment_df['Neutral'])[0],
            'real_score': list(sentiment_df['real_score'])[0]
        }
        # print("===================================================\n===================================================\n===================================================")
        # for key, value in res_dict.items():
        #     print(f"{key}: {value}")
        # print("===================================================\n===================================================\n===================================================")
        return res_dict
    

    def __extract_sentences(self, content):
        sentences = sent_tokenize(content)
        res_sentences = [sentence.replace("\n", "").replace("•", "").replace("\\x", "").replace("\\xa0", " ").replace("Краткосрочная картина","") for sentence in sentences if any(keyword.lower() in sentence.lower() for keyword in self.__keywords)]
        res_str = ""
        for x in res_sentences:
            res_str +=x
            res_str += " "
        return res_str

    def close_driver(self):
        self.__driver.quit()


if __name__ == "__main__":
    # news_parser = NewsParser("https://bcs-express.ru/category/sber", keywords_dict['SBER'],'SBER')

    # news_parser.parse_news( len_dataset=1000000, stop_date='2015-01-01')
    # news_parser.save_to_csv('SBER_news.csv')
    df = pd.read_csv("SBER_in_progress.csv")
    df.drop_duplicates(inplace=True)
    df["Ticker"] = "SBER"
    parser = HelperParser(keywords_dict,'SBER')
    parsed_data = parser.parse_dataset(df)
    print(parsed_data)

    parser.close_driver()

