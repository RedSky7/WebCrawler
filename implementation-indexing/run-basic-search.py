import os
from processing import format_results, get_snippets, handle_indexing, index_pages
import time
import argparse

parser = argparse.ArgumentParser(description='Extracts data from a webpage.')
parser.add_argument('query', metavar='T', type=str, help='query words.')

args = parser.parse_args()

#if not os.path.exists("inverted-index.db"):
#    handle_indexing()

query = args.query
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

    if document in sub_results:
        sub_results[document].append((frequency, document, indexes))
    else:
        sub_results[document] = [(frequency, document, indexes)]

print("Results found. Merging results and processing snippets...")

time_taken = (time.time() - time_before) * 1000

results = []
for document, list in sub_results.items():
    results.append((sum(sub[0] for sub in list), document,
                    get_snippets(document, ",".join([sub[2] for sub in list]).split(","))))

results.sort(key=lambda tup: tup[0], reverse=True)  # sorts in place

print(format_results(query, time_taken, results))


