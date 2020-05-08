import os
from processing import format_results, get_snippet, handle_indexing, index_pages
import time

if not os.path.exists("inverted-index.db"):
    handle_indexing()

# TODO: Get real query. TK
query = "trgovina"

time_before = time.time()
_, data = index_pages()
manual_results = []
for row in data:
    if row[0] != query:
        continue
    manual_results.append((int(row[2]), row[1], row[3]))
time_taken = (time.time() - time_before) * 1000

manual_results.sort(key=lambda tup: tup[0])  # sorts in place

results = []
for row in manual_results:
    frequency, document, indexes = row[0], row[1], row[2]
    snippet = get_snippet(document, indexes.split(","))
    results.append((frequency, document, snippet))

print(format_results(query, time_taken, results))


