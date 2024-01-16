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
        self.__url = url
        self.__keywords = keywords
        self.__driver = None
        self.__news = None

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
            formatted_date = datetime.strptime(date, '%d %B в %H:%M').strftime('2024-%m-%d')
        else:
            locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')
            formatted_date = datetime.strptime(date, '%d %B %Y').strftime('%Y-%m-%d')            
        
        return formatted_date

    def __parse_news(self, news_block):
        date = news_block.find("time").text.strip()
        title = news_block.find("a", class_="iKzE").text.strip()
        href = news_block.find("a", class_="iKzE")["href"]

        self.__driver.execute_script(f"window.open('{href}', '_blank');")
        self.__driver.switch_to.window(self.__driver.window_handles[1])

        content_html = BeautifulSoup(self.__driver.page_source, 'html.parser')
        content = content_html.find("div", class_="YjHz UBOr RkGZ").text.strip()

        self.__driver.close()
        self.__driver.switch_to.window(self.__driver.window_handles[0])

        # print(date, end=" ************** ")
        formatted_date = self.__format_date(date)
        # print(formatted_date)
        
        return {
            'date': formatted_date,
            'title': title,
            'content': content,
            'filtered_content': self.__extract_sentences(content)
        }


    def parse_news(self, len_dataset=500, stop_date = None):
        self.__driver = webdriver.Chrome()
        self.__driver.get(self.__url)

        self.__news = []
        try:
            while True:
                show_more_button = WebDriverWait(self.__driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='nlJ0' and contains(text(), 'Показать еще новости')]"))
                )

                self.__driver.execute_script("arguments[0].click();", show_more_button)
                time.sleep(2)

                updated_html = BeautifulSoup(self.__driver.page_source, 'html.parser')
                news_blocks = updated_html.find_all("div", class_="TjB6 KSLV Ncpb E6j8")

                show_more_button = WebDriverWait(self.__driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//span[@class='nlJ0' and contains(text(), 'Показать еще новости')]"))
                )

                if not show_more_button.is_displayed():
                    break

                for news_block in news_blocks[len(self.__news):]:
                    try:
                        news_data = self.__parse_news(news_block)
                        if(len(self.__news)>len_dataset or (news_data['date']<stop_date and bool(stop_date))):
                            break
                    except:
                        pass
                    # print(news_data['date'])
                    self.__news.append(news_data)
                    # print(bool(stop_date), len(self.__news),self.__news[-1]['date'])
                    if(len(self.__news)%10 ==0):
                        print("News parsed successfully:", len(self.__news))
                
                if(len(self.__news)>len_dataset or (news_data['date']<stop_date and bool(stop_date))):
                            break
                
        finally:
            self.__driver.quit()
    
    def get_news_dataframe(self):
        if self.__news is not None:
            dataset = pd.DataFrame(self.__news)
            return dataset
        else:
            print("Please run parse_news() first.")
            
    def save_to_csv(self, output_filename):
        if self.__news is not None:
            df = pd.DataFrame(pd.DataFrame(self.__news))
            df.to_csv(output_filename, index=False)
        else:
            print("Please run parse_news() first.")