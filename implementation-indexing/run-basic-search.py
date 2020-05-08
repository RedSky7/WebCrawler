import os
from processing import index_pages, format_results, get_snippet, create_database
import sqlite3
import time

if not os.path.exists("inverted-index.db"):
    create_database()
    index_pages()

# TODO: Get real query. TK
query = "trgovina"

time_before = time.time()
#TODO: Open sequentially.
time_taken = (time.time() - time_before) * 1000

results = []
for row in c.fetchall():
    frequency, document, indexes = row[0], row[1], row[2]
    snippet = get_snippet(document, indexes.split(","))
    results.append((frequency, document, snippet))

print(format_results(query, time_taken, results))


