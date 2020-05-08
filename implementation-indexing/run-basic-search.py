import os
from processing import format_results, get_snippet, handle_indexing, index_pages
import time

if not os.path.exists("inverted-index.db"):
    handle_indexing()

# TODO: Get real query. TK
query = "trgovina pravosodje"
queries = query.split(" ")

sub_results = {}
time_before = time.time()

_, data = index_pages()
manual_results = []
for row in data:
    if row[0] not in queries:
        continue
    manual_results.append((int(row[2]), row[1], row[3]))

for row in manual_results:
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


