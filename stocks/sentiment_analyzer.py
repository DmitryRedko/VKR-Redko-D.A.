from transformers import MarianMTModel, MarianTokenizer, AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd

class NewsSentimentAnalyzer:
    def __init__(self, financial_text_russian, translation_model_name="Helsinki-NLP/opus-mt-ru-en", finbert_model_name="ProsusAI/finbert"):
        self.financial_text_russian = financial_text_russian
        self.translation_model_name = translation_model_name
        self.finbert_model_name = finbert_model_name
        self.translation_model = MarianMTModel.from_pretrained(translation_model_name)
        self.translation_tokenizer = MarianTokenizer.from_pretrained(translation_model_name)
        self.finbert_tokenizer = AutoTokenizer.from_pretrained(finbert_model_name)
        self.finbert_model = AutoModelForSequenceClassification.from_pretrained(finbert_model_name)
        self.df = None

    def translate_text(self, text):
        inputs = self.translation_tokenizer(text, return_tensors="pt", padding=True, truncation=True)
        outputs = self.translation_model.generate(**inputs)
        translated_text = self.translation_tokenizer.batch_decode(outputs, skip_special_tokens=True)
        return translated_text

    def analyze_sentiment(self):
        # Translate text
        translated_text = self.translate_text(self.financial_text_russian)

        # Tokenize translated text for FinBERT
        inputs = self.finbert_tokenizer(translated_text, padding=True, truncation=True, return_tensors='pt')

        # Make predictions with FinBERT
        outputs = self.finbert_model(**inputs)
        predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)

        positive = predictions[:, 0].tolist()
        negative = predictions[:, 1].tolist()
        neutral = predictions[:, 2].tolist()

        # Create DataFrame
        table = {'Headline': self.financial_text_russian,
                 'En Headline': translated_text,
                 "Positive": positive,
                 "Negative": negative,
                 "Neutral": neutral}

        self.df = pd.DataFrame(table, columns=["Headline", 'En Headline', "Positive", "Negative", "Neutral"])
        self.df['real_score'] = self.df['Positive'] - self.df['Negative']

    def get_sentiment_dataframe(self):
        if self.df is not None:
            return self.df
        else:
            print("Please run analyze_sentiment() first.")

# # Example Usage
# financial_text_russian = ["Компания X объявила о рекордных прибылях за последний квартал.",
#                           "Компания X объявила о рекордных убытках за последний квартал.",
#                           "Компания X имеет показатели без изменений.",
#                           "Электромобильный стартап Arrival экс-главы Yota уйдет из России.",
#                           "Шрёдер отклонил предложение войти в совет директоров «Газпрома»",
#                           "Шельф берут в разработку // Генподрядчиком «Газпрома» на море может стать компания Андрея Патрушева",
#                           "Чистая прибыль 'РусГидро' по РСБУ за 1 полугодие выросла на 17%",
#                           "Финский производитель шин Nokian Tyres решил уйти из России",
#                           "Федун ушел с поста вице-президента ЛУКОЙЛа на пенсию",
#                           "Промсвязьбанк укрепил свои позиции в топ-10 российских банков по портфелю кредитов организациям."
#                           ]

# analyzer = NewsSentimentAnalyzer(financial_text_russian)
# analyzer.analyze_sentiment()
# result_df = analyzer.get_sentiment_dataframe()
# print(result_df)
