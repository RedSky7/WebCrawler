import nltk

#Dependencies
nltk.download('stopwords')
nltk.download('punkt')

from stopwords import *
from lxml import html
import os
from os import walk
import sqlite3
from lxml.html.clean import Cleaner
import re

def retrieve_tokens(text):
    tokens = nltk.word_tokenize(text)
    tokens = [word.lower() for word in tokens]
    cleaned = [word for word in tokens if word not in stop_words_slovene]
    return cleaned



def get_html_content(site, file):
    root = '../input-indexing/' + site + "/"
    encoding = 'utf-8'
    html_content = open(root + file, mode='r', encoding=encoding).read()
    html_content = re.sub("<\?xml.*?\?>", "", html_content)
    return html_content


if not os.path.exists('inverted-index.db'):
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()
    c.execute("CREATE TABLE IndexWord (\
      word TEXT PRIMARY KEY\
    );")
    c.execute("CREATE TABLE Posting (\
      word TEXT NOT NULL,\
      documentName TEXT NOT NULL,\
      frequency INTEGER NOT NULL,\
      indexes TEXT NOT NULL,\
      PRIMARY KEY(word, documentName),\
      FOREIGN KEY (word) REFERENCES IndexWord(word)\
    );")

sites = ['e-prostor.gov.si', 'e-uprava.gov.si', 'evem.gov.si', 'podatki.gov.si']

for site in sites:
    root = '../input-indexing/' + site + "/"
    (_, _, filenames) = next(walk(root))
    html_files = []
    for file in filenames:
        if file.endswith(".html"):
            html_files.append(file)

    for file in html_files:
        print(file)
        html_content = get_html_content(site, file)
        tree = html.fromstring(html_content)
        cleaner = Cleaner(style=True, kill_tags={"nav", "footer"}, remove_unknown_tags=False)
        tree1 = cleaner.clean_html(tree)
        text = tree.body.text_content()
        #print(text)
        tokens = retrieve_tokens(text)
        print(tokens)
        #for token in tokens:
        #    c.execute("INSERT INTO IndexWord VALUES ")
