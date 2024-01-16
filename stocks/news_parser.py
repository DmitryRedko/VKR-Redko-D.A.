import time
import pandas as pd
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import locale
from nltk.tokenize import sent_tokenize

class NewsParser:
    def __init__(self, url, keywords):
        self.url = url
        self.keywords = keywords
        self.driver = None
        self.news = []

    def __extract_sentences(self, content):
        sentences = sent_tokenize(content)
        res_sentences = [sentence for sentence in sentences if any(keyword.lower() in sentence.lower() for keyword in self.keywords)]
        return res_sentences
    
    def __format_date(self,date):
        if 'Сегодня' in date:
            formatted_date = (datetime.now()).strftime('%Y-%m-%d') + ' ' + date.split()[-1]
        elif 'Вчера' in date:
            formatted_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d') + ' ' + date.split()[-1]
        elif ' в 'in date:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
            formatted_date = datetime.strptime(date, '%d %B в %H:%M').strftime('2024-%m-%d')
        else:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
            formatted_date = datetime.strptime(date, '%d %B %Y').strftime('%Y-%m-%d')            
        
        return formatted_date

    def __parse_news(self, news_block):
        category = news_block.find("div", class_="bvzt").text.strip()
        date = news_block.find("time").text.strip()
        title = news_block.find("a", class_="iKzE").text.strip()
        href = news_block.find("a", class_="iKzE")["href"]

        self.driver.execute_script(f"window.open('{href}', '_blank');")
        self.driver.switch_to.window(self.driver.window_handles[1])

        content_html = BeautifulSoup(self.driver.page_source, 'html.parser')
        content = content_html.find("div", class_="YjHz UBOr RkGZ").text.strip()

        self.driver.close()
        self.driver.switch_to.window(self.driver.window_handles[0])

        print(date, end=" ************** ")
        formatted_date = self.__format_date(date)
        print(formatted_date)
        
        return {
            'date': formatted_date,
            'title': title,
            'content': content,
            'filtered_content': self.__extract_sentences(content)
        }


    def parse_and_return_dataset(self, len_dataset=500, stop_date = None):
        self.driver = webdriver.Chrome()
        self.driver.get(self.url)

        try:
            while True:
                show_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='nlJ0' and contains(text(), 'Показать еще новости')]"))
                )

                self.driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(2)

                updated_html = BeautifulSoup(self.driver.page_source, 'html.parser')
                news_blocks = updated_html.find_all("div", class_="TjB6 KSLV Ncpb E6j8")

                show_more_button = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='nlJ0' and contains(text(), 'Показать еще новости')]"))
                )

                if not show_more_button.is_displayed():
                    break

                for news_block in news_blocks[len(self.news):]:
                    try:
                        news_data = self.__parse_news(news_block)
                    except:
                        pass
                    self.news.append(news_data)

        finally:
            self.driver.quit()

        # Формируем Pandas датафрейм
        dataset = pd.DataFrame(self.news)
        return dataset

    def save_to_excel(self, file_path):
        df = pd.DataFrame(pd.DataFrame(self.news))
        df.to_excel(file_path, index=False)