import argparse

parser = argparse.ArgumentParser(description='Extracts data from a webpage.')
parser.add_argument('type', metavar='T', type=str, help='type of data extraction. Can be A, B or C.')

args = parser.parse_args()

if args.type == 'A':
    print("Handle A")

elif args.type == 'B':
    print("Handle B")

elif args.type == 'C':
    print("Handle C")
