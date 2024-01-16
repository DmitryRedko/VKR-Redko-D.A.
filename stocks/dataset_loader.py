from news_parser import NewsParser
from stocks_parser import StockParser

sberbank_keywords = ["СБЕР", "Сбербанк", "Сбер", "Сберколл", "Сбербизнес", "Сбертек", "Сбермаркет", "Мегамаркет", "Греф", "Сберколлектор", "Сбербизнес", "Сбертек", "Сбермаркет", "СберЛогистика", "СберЛизинг", "СберНедвижимость", "Сбербанк-АСТ", "Сбербанк-Резерв", "Сбербанк-Спасение", "Сбербанк-Страхование", "Сбербанк-Технологии", "Сбербанк-Эквайринг", "Сбербанк-Эксперт", "Сбербанк-Контактный Центр"]


news_parser = NewsParser("https://bcs-express.ru/category/sberbank", sberbank_keywords)

dataset = news_parser.parse_and_return_dataset()
print(dataset)