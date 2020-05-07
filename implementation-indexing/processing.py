import nltk
from stopwords import stop_words_slovene

def retrieve_tokens(text):
    tokens = nltk.word_tokenize(text)
    cleaned = [word.lower() not in stop_words_slovene for word in tokens]
    return cleaned