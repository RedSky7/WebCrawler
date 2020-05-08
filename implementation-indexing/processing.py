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
    # TODO: Maybe stem of words, remove special characters. TK
    tokens = [re.sub("\'", "", word.lower()) for word in tokens]
    cleaned = [word for word in tokens if word not in stop_words_slovene]
    return cleaned



def get_html_content(site, file):
    root = '../input-indexing/' + site + "/"
    encoding = 'utf-8'
    html_content = open(root + file, mode='r', encoding=encoding).read()
    html_content = re.sub("<\?xml.*?\?>", "", html_content)
    return html_content

def get_text(html_content):
    tree = html.fromstring(html_content)
    cleaner = Cleaner(style=True, kill_tags={"nav", "footer"}, remove_unknown_tags=False)
    tree = cleaner.clean_html(tree)
    text = tree.body.text_content()
    return text

def create_database():
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()

    c.execute("CREATE TABLE IndexWord (\
          word TEXT PRIMARY KEY\
        )")
    conn.commit()

    c.execute("CREATE TABLE Posting (\
          word TEXT NOT NULL,\
          documentName TEXT NOT NULL,\
          frequency INTEGER NOT NULL,\
          indexes TEXT NOT NULL,\
          PRIMARY KEY(word, documentName),\
          FOREIGN KEY (word) REFERENCES IndexWord(word)\
        )")
    conn.commit()


def index_pages():
    conn = sqlite3.connect('inverted-index.db')
    c = conn.cursor()

    sites = ['e-prostor.gov.si', 'e-uprava.gov.si', 'evem.gov.si', 'podatki.gov.si']
    remembered_tokens = []

    for site in sites:
        root = '../input-indexing/' + site + "/"
        (_, _, filenames) = next(walk(root))
        html_files = []
        for file in filenames:
            if file.endswith(".html"):
                html_files.append(file)

        for file in html_files:

            text = get_text(get_html_content(site, file))

            tokens = retrieve_tokens(text)
            tokens_to_insert = []

            freq_table = {}
            indices = {}
            for i, token in enumerate(tokens):
                if token not in remembered_tokens:
                    tokens_to_insert.append((token,))
                    remembered_tokens.append(token)

                #https://towardsdatascience.com/text-summarization-using-tf-idf-e64a0644ace3
                if token in freq_table:
                    freq_table[token] += 1
                    indices[token].append(str(i))
                else:
                    freq_table[token] = 1
                    indices[token] = [str(i)]

            '''for word, frequency in freq_table.items():
                data = (word, site + '/' + file, frequency, ','.join(indices[word]))
                insert = ("INSERT INTO Posting VALUES (?, ?, ?, ?)")
                print(insert)
                print(data)
                c.execute(insert, data)
                conn.commit()'''

            if len(tokens_to_insert) > 0:
                insert = "INSERT INTO IndexWord VALUES (?)"
                print(tokens_to_insert)
                c.executemany(insert, tokens_to_insert)
                conn.commit()

            data = []
            for word, frequency in freq_table.items():
                data.append((word, site + '/' + file, frequency, ','.join(indices[word])))

            print(data)
            insert = ("INSERT INTO Posting (word, documentName, frequency, indexes) "
                      "VALUES (?, ?, ?, ?)")
            c.executemany(insert, data)
            conn.commit()

def get_snippet(document, indexes):
    snippets = []
    site, file = document.split("/")
    text = get_text(get_html_content(site, file))
    tokens = retrieve_tokens(text)
    for index in indexes:
        index = int(index)
        content = tokens[index - 3 : index + 3]
        snippets.append(' '.join(content))
    return ' ... '.join(snippets)

def format_results(query, time, results):
    head = "Results for a query: \"{}\"\n\n" \
    "Results found in {:.0f}ms.\n\n" \
    "Frequencies Document                                  Snippet\n" \
    "----------- ----------------------------------------- -----------------------------------------------------------\n".format(query, time)
    body = ''
    for frequency, document, snippet in results:
        body += '{}\t\t\t{}\t\t\t{}\n'.format(frequency, document, snippet)

    return head + body

