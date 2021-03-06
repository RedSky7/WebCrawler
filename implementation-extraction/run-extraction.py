import sys
from os import walk
import argparse, json, re
from lxml import html
from lxml.html.clean import Cleaner


#
# Regular expressions
#


def extract(match, group_number=1):
    if match is not None:
        result = match.group(group_number)
        if result is None:
            return ''
        return result.lstrip().rstrip()
    return ''

def extract_this(iterator):
    items = {}
    for item in iterator:
        items[item.group(1)] = extract(item, 2)
    return items



def regular_expressions(site_name, html_content):
    html_content = html_content.replace("\n", "").replace("\t", "")

    extracted = {}
    if site_name == "rtvslo.si":
        extracted['Title'] = extract(re.search("<h1>(.*?)</h1>", html_content))
        extracted['SubTitle'] = extract(re.search("<div class=\"subtitle\">(.*?)</div>", html_content))
        extracted['Lead'] = extract(re.search("<p class=\"lead\">(.*?)</p>", html_content))
        extracted['Content'] = extract(
            re.search("<div class=\"article-body\">(.*?)</div>[ ]*<div class=\"article-column\">", html_content))
        extracted['Author'] = extract(re.search("<div class=\"author-name\">(.*?)</div>", html_content))
        extracted['PublishedTime'] = extract(re.search("<div class=\"publish-meta\">(.*?)<br>", html_content))

    elif site_name == "overstock.com":
        extracted_array = []
        items = "<td valign=\"top\">\W*<a.*?PROD_ID=([0-9]+)\".*?"

        titles = extract_this(re.finditer(items + "<b>(.*?)</b></a>", html_content))
        contents = extract_this(re.finditer(items + "<span class=\"normal\">(.*?)<br>", html_content))
        listPrices = extract_this(re.finditer(items + "<s>(.*?)</s>", html_content))
        prices = extract_this(re.finditer(items + "<span class=\"bigred\"><b>(.*?)</b>", html_content))
        wholeSavings = re.finditer(items + "<span class=\"littleorange\">(.*?) \(([0-9]{0,2}%)\)</span>", html_content)
        savings = {}
        savingsPercent = {}

        for item in wholeSavings:
            savings[item.group(1)] = item.group(2)
            savingsPercent[item.group(1)] = item.group(3)

        for (key, value) in titles.items():
            sub_extracted = {}

            sub_extracted['Title'] = value
            sub_extracted['Content'] = contents.get(key, '')
            sub_extracted['ListPrice'] = listPrices.get(key, '')
            sub_extracted['Price'] = prices.get(key, '')
            sub_extracted['Saving'] = savings.get(key, '')
            sub_extracted['SavingPercent'] = savingsPercent.get(key, '')

            extracted_array.append(sub_extracted)
        return extracted_array

    elif site_name == "mimovrste.si":
        extracted['Title'] = extract(re.search("<h3.*?>(.*?)</h3>", html_content))
        extracted['Description'] = extract(re.search("<p.*?itemprop=\"description\".*?>(.*?)<a", html_content))
        extracted['OldPrice'] = extract(re.search("<del.*?class=\"rrp-price\".*?>(.*?)</del>", html_content))
        extracted['Price'] = extract(re.search("<b class=\"pro-price.*?>(.*?)</b>", html_content))
        extracted['Availability'] = extract(re.search("<a data-sel=\"availability-detail\".*?>(.*?)</a>", html_content))

        tags = []
        for tag in re.finditer("<em class=\"label.*?>(.*?)</em>", html_content):
            tags.append(extract(tag))
        extracted['Tags'] = tags

        extracted['Savings'] = extract(re.search("<div class=\"label--round-sale.*?>(.*?)</div>", html_content))

    elif site_name == "ceneje.si":
        extracted_array = []

        items = "<div class=\"innerProductBox\">.*?<img.*?alt=\"(.*?)\".*?"

        images = extract_this(re.finditer(items + "src=\"(.*?)\"", html_content))
        titles = extract_this(re.finditer(items + "<h3>\W*<.*?>(.*?)</.*?>", html_content))
        minPrices = extract_this(re.finditer(items + "<b>(.*?)</b>", html_content))
        stores = extract_this(re.finditer(items + "class=\"qtySellers\">\W*<b>(.*?)</b>",  html_content))
        actions = extract_this(re.finditer(items + "<div class=\"rBox\">\W*<.*?>(.*?)</.*?>", html_content))

        for (key, value) in titles.items():
            sub_extracted = {}

            sub_extracted['Image'] = images.get(key, '')
            sub_extracted['Title'] = value
            sub_extracted['MinPrice'] = minPrices.get(key,'')
            sub_extracted['Stores'] = stores.get(key,'')
            sub_extracted['Action'] = actions.get(key,'')

            extracted_array.append(sub_extracted)
        return extracted_array

    return extracted


#
#   X_Path
#

def extract_x_path(items):
    if len(items) == 0:
        return ''
    else:
        return items[0].replace("\n", "").replace("\t", "").lstrip().rstrip()

def x_path(site_name, html_content):
    tree = html.fromstring(html_content)
    extracted = {}

    if site_name == "rtvslo.si":
        extracted['Title'] = extract_x_path(tree.xpath("//*[@id=\"main-container\"]/div[3]/div/header/h1/text()"))
        extracted['SubTitle'] = extract_x_path(tree.xpath("//*[@id=\"main-container\"]/div[3]/div/header/div[2]/text()"))
        extracted['Lead'] = extract_x_path(tree.xpath("//*[@id=\"main-container\"]/div[3]/div/header/p/text()"))
        extracted['Content'] = tree.xpath("string(//*[@id=\"main-container\"]/div[3]/div/div[2])")
        extracted['Author'] = extract_x_path(tree.xpath("//*[@id=\"main-container\"]/div[3]/div/div[1]/div[1]/div/text()"))
        extracted['PublishedTime'] = extract_x_path(tree.xpath("//*[@id=\"main-container\"]/div[3]/div/div[1]/div[2]/text()[1]"))

    elif site_name == "overstock.com":
        extracted_array = []

        i = 1
        fail_count = 0
        while True:

            # This is more robust but longer
            #item = "/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[" + str(i) + "]/"

            # This works but only because of the design choice of this table having a padding of 2.
            item = "//table[@cellpadding='2']/tbody/tr[" + str(i) + "]/"
            title = extract_x_path(tree.xpath(item + "td[2]/a/b/text()"))

            if fail_count > 3:
                break

            if len(title) == 0:
                fail_count = fail_count + 1
                i = i + 1
                continue

            fail_count = 0

            content = extract_x_path(tree.xpath(item + "td[2]/table/tbody/tr/td[2]/span/text()"))
            listPrice = extract_x_path(tree.xpath(item + "td[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/s/text()"))
            price = extract_x_path(tree.xpath(item + "td[2]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/span/b/text()"))
            wholeSavings = extract_x_path(tree.xpath(item + "td[2]/table/tbody/tr/td[1]/table/tbody/tr[3]/td[2]/span/text()"))
            components = wholeSavings.split(" ")
            saving = components[0]
            savingPercent = components[1]

            sub_extracted = {}

            sub_extracted['Title'] = title
            sub_extracted['Content'] = content
            sub_extracted['ListPrice'] = listPrice
            sub_extracted['Price'] = price
            sub_extracted['Saving'] = saving
            sub_extracted['SavingPercent'] = savingPercent

            extracted_array.append(sub_extracted)

            i = i + 1
        return extracted_array

    elif site_name == "mimovrste.si":
        extracted['Title'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/h3/text()"))
        extracted['Description'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/p[2]/text()"))
        extracted['OldPrice'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/div[3]/div[1]/div[1]/div/del/text()"))
        extracted['Price'] = extract_x_path(tree.xpath("//*[@class=\"price-wrapper\"]/div[1]/div[1]/b/text()"))
        extracted['Availability'] = extract_x_path(tree.xpath("//*[@class=\"delivery-wrapper\"]/a/text()"))

        tags = []
        i = 1
        while True:
            tag = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/p[1]/em[" + str(i) + "]/text()"))
            if len(tag) == 0:
                break
            tags.append(tag)
            i += 1

        extracted['Tags'] = tags

        extracted['Savings'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/div[3]/div[1]/div[2]/text()"))

    elif site_name == "ceneje.si":
        i = 1
        extracted_array = []

        while True:
            item = "//*[@id=\"productGrid\"]/div[" + str(i) + "]/"
            # sub_extracted['Image'] = item.xpath("div/div[1]/a/img/@src") and was sub="span"


            title = extract_x_path(tree.xpath(item + "div/div[2]/h3/a/text()"))
            if len(title) == 0:
                break


            image = extract_x_path(tree.xpath(item + "div/div[1]/a/img/@src"))
            minPrice = extract_x_path(tree.xpath(item + "div/div[2]/p/a[1]/b/text()"))
            store = extract_x_path(tree.xpath(item + "div/div[2]/p/a[2]/b/text()"))
            action = extract_x_path(tree.xpath(item + "div/div[3]/a/text()"))

            sub_extracted = {}

            sub_extracted['Image'] = image
            sub_extracted['Title'] = title
            sub_extracted['MinPrice'] = minPrice
            sub_extracted['Stores'] = store
            sub_extracted['Action'] = action

            extracted_array.append(sub_extracted)

            i = i + 1
        return extracted_array

    return extracted

def contains(node, start_index, target):
    for i in range(start_index, start_index + 1):
        if node[i].tag == target.tag:
            return True
    return False

def add_attributes(node):
    result = " "
    for key, value in node.attrib.items():
        result += key + "=\"" + value + "\" "
    return result

def id_mismatch(node_1, node_2):
    id1 = node_1.attrib.get('id', None)
    id2 = node_2.attrib.get('id', None)
    mismatch = id1 != id2

    # If the id contains a few numbers then probably another sort of id (like ads)
    if mismatch and id1 is not None and len(re.findall('[0-9]', id1)) > 3:

        # Base your decision on other tags. Maybe use Levenshtein distance.
        att1 = re.sub("id=\".*?\"", "", add_attributes(node_1))
        att2 = re.sub("id=\".*?\"", "", add_attributes(node_2))
        return att1 != att2
    return mismatch


def mismatch(node_1, node_2):
    return node_1.tag != node_2.tag or id_mismatch(node_1, node_2)

def get_smt(node_1, node_2):
    if node_1 == node_2:
        return node_1
    elif node_1 != node_2:
        return "#text"

def get_target(tree, position):
    if tree is None or position >= len(tree.getchildren()):
        return None
    return tree.getchildren()[position]

def auto_ex(node_1, node_2):
    #TODO: FIX mismatches. which look for more than just one back one forward

    wrapper = ""
    prev_tag = ""
    count = 0
    for i, child in enumerate(node_1.getchildren()):

        # Check if there is any node on count position in tree2
        target = get_target(node_2, count)
        if target is None:
            wrapper += "(<" + str(child.tag).upper() + "... >)?"
            continue

        # Handle tag mismatches
        if mismatch(child, target):
            if contains(node_2, count, child):
                wrapper += "(<" + target.tag.upper() + "... >)?"
                count += 1
                target = get_target(node_2, count)
            else:
                wrapper += "(<" + str(child.tag).upper() + "... >)?"
                continue
        # Add starting tag
        new_tag = "<" + str(child.tag).upper() + ">"

        # Add text inside of the tag
        if child.text is not None:
            new_tag += get_smt(child.text, target.text)

        # Handle children of this node
        new_tag += auto_ex(child, target)

        # Add a closing tag
        new_tag += "</" + str(child.tag).upper() + ">"

        # Handle text after the current node
        if child.tail is not None:
            tail = child.tail.lstrip().rstrip()
            if len(tail) > 0:
                new_tag += get_smt(tail, target.tail.lstrip().rstrip())
                #print("TEXT AFTER = " + tail)

        # Replace multiple occurrences with a special tag
        if new_tag == prev_tag:
            wrapper = re.sub(new_tag + "$", "(" + new_tag + ")+", wrapper)
            continue

        wrapper += new_tag

        prev_tag = new_tag
        count += 1

        # If this is the last node in tree1 but there are still nodes in tree2 this one must be optional
        if i == len(node_1.getchildren()) - 1 \
                and count < len(node_2.getchildren()) \
                and mismatch(child, node_2.getchildren()[count]):
            wrapper += "(<" + node_2.getchildren()[count].tag.upper() + "... >)?"

    return wrapper



def auto_extraction(html1, html2):
    tree1 = html.fromstring(html1)
    tree2 = html.fromstring(html2)

    cleaner = Cleaner(style=True, kill_tags={"nav", "footer"}, remove_unknown_tags=False)
    tree1 = cleaner.clean_html(tree1)
    tree2 = cleaner.clean_html(tree2)

    result = auto_ex(tree1.body, tree2.body)
    result = re.sub("\n{2,}?", "\n", result)

    return result


def get_html_content(site, file):
    root = '../input-extraction/' + site + "/"
    encoding = 'utf-8'
    if site == 'overstock.com':
        encoding = 'unicode_escape'
    html_content = open(root + file, mode='r', encoding=encoding).read()
    return html_content






parser = argparse.ArgumentParser(description='Extracts data from a webpage.')
parser.add_argument('type', metavar='T', type=str, help='type of data extraction. Can be A, B or C.')

args = parser.parse_args()

sites = ['rtvslo.si', 'overstock.com', 'mimovrste.si', 'ceneje.si']


for site in sites:
    root = '../input-extraction/' + site + "/"
    (_, _, filenames) = next(walk(root))
    html_files = []
    for file in filenames:
        if file.endswith(".html"):
            html_files.append(file)

    if args.type == 'A' or args.type == 'B':
        for file in html_files:

            html_content = get_html_content(site, file)

            if args.type == 'A':
                data = regular_expressions(site, html_content)
            else:
                data = x_path(site, html_content)

            json.dump(data, sys.stdout, indent=4)
            with open("data_" + file.replace(".html", "") + ".json", "w", encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)

    elif args.type == 'C':

        file_1 = html_files[0]
        file_2 = html_files[1]

        html1 = get_html_content(site, file_1)
        html2 = get_html_content(site, file_2)

        data = auto_extraction(html1, html2)

        print(data)
        print("\n\n\n-------\n\n\n")

