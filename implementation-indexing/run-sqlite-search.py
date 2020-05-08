import os
from processing import index_pages, format_results, get_snippet, create_database
import sqlite3
import time

if not os.path.exists("inverted-index.db"):
    create_database()
    index_pages()

# TODO: Get real query. TK
query = "trgovina"

conn = sqlite3.connect('inverted-index.db')
c = conn.cursor()
select = "SELECT frequency, documentName, indexes " \
         "FROM Posting WHERE word = ? " \
         "ORDER BY frequency DESC " \
         "LIMIT 10"

time_before = time.time()
c.execute(select, (query,))
time_taken = (time.time() - time_before) * 1000

results = []
for row in c.fetchall():
    frequency, document, indexes = row[0], row[1], row[2]
    snippet = get_snippet(document, indexes.split(","))
    results.append((frequency, document, snippet))

print(format_results(query, time_taken, results))


