import os
from processing import format_results, get_snippet, handle_indexing
import sqlite3
import time

if not os.path.exists("inverted-index.db"):
    handle_indexing()

# TODO: Get real query. TK
query = "trgovina pravosodje"
queries = query.split(" ")

conn = sqlite3.connect('inverted-index.db')
c = conn.cursor()
sub_results = {}
time_before = time.time()

for query_word in queries:
    select = "SELECT frequency, documentName, indexes " \
             "FROM Posting WHERE word = ? " \
             "ORDER BY frequency DESC " \
             "LIMIT 10"

    c.execute(select, (query_word,))

    for row in c.fetchall():
        frequency, document, indexes = row[0], row[1], row[2]
        snippet = get_snippet(document, indexes.split(","))

        if document in sub_results:
            sub_results[document].append((frequency, document, snippet))
        else:
            sub_results[document] = [(frequency, document, snippet)]

time_taken = (time.time() - time_before) * 1000

results = []
for document, list in sub_results.items():
    results.append((sum(sub[0] for sub in list), document, "...".join([sub[2] for sub in list])))

results.sort(key=lambda tup: tup[0], reverse=True)  # sorts in place

print(format_results(query, time_taken, results))


