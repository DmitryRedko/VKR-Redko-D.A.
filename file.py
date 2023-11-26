from transformers import MarianMTModel, MarianTokenizer, AutoTokenizer, AutoModelForSequenceClassification
import torch
import pandas as pd

def bert_sentiment(financial_text_russian):
    translation_model_name = "Helsinki-NLP/opus-mt-ru-en"
    translation_model = MarianMTModel.from_pretrained(translation_model_name)
    translation_tokenizer = MarianTokenizer.from_pretrained(translation_model_name)

    inputs = translation_tokenizer(financial_text_russian, return_tensors="pt", padding=True, truncation=True)
    outputs = translation_model.generate(**inputs)
    translated_text = translation_tokenizer.batch_decode(outputs, skip_special_tokens=True)
    # print("Translated Text:", translated_text)

    # Choose the FinBERT model and tokenizer for classification
    finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
    finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")

    # Tokenize the translated text for FinBERT
    inputs = finbert_tokenizer(translated_text, padding = True, truncation = True, return_tensors='pt')

    # Make predictions with FinBERT
    outputs = finbert_model(**inputs)
    predictions = torch.nn.functional.softmax(outputs.logits, dim=-1)
    return predictions