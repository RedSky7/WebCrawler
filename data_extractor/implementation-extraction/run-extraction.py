from os import walk
import argparse, json, re
from lxml import html


#
# Regular expressions
#
from lxml.html.clean import Cleaner


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

        print(len(titles))
        print(len(contents))
        print(len(listPrices))
        print(len(prices))
        print(len(savings))
        print(len(savingsPercent))

        for (key, value) in titles.items():
            sub_extracted = {}

            sub_extracted['Title'] = value
            sub_extracted['Content'] = contents.get(key, '')
            sub_extracted['ListPrice'] = listPrices.get(key, '')
            sub_extracted['Price'] = prices.get(key, '')
            sub_extracted['Saving'] = savings.get(key, '')
            sub_extracted['SavingPercent'] = savingsPercent.get(key, '')

            extracted[key] = sub_extracted

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

            extracted[key] = sub_extracted

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
        i = 1
        fail_count = 0
        while True:

            #item = "/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/"
            item = "/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[" + str(i) + "]/"

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

            extracted[title] = sub_extracted

            i = i + 1

    elif site_name == "mimovrste.si":
        extracted['Title'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/h3/text()"))
        extracted['Description'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/p[2]/text()"))
        extracted['OldPrice'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/div[3]/div[1]/div[1]/div/del/text()"))
        extracted['Price'] = extract_x_path(tree.xpath("//*[@class=\"price-wrapper\"]/div[1]/div[1]/b/text()"))
        extracted['Availability'] = extract_x_path(tree.xpath("//*[@class=\"delivery-wrapper\"]/a/text()"))

        tags = []
        for tag in tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/p[1]/em"):
            tags.append(extract_x_path(tag.xpath("text()")))
        extracted['Tags'] = tags

        extracted['Savings'] = extract_x_path(tree.xpath("//*[@id=\"content\"]/div/article/div[1]/section[2]/div[3]/div[1]/div[2]/text()"))

    elif site_name == "ceneje.si":
        i = 1
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

            extracted[title] = sub_extracted

            i = i + 1

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
    return node_1.attrib.get('id', None) != node_2.attrib.get('id', None)

def auto_ex(node_1, node_2):
    #TODO: FIX mismatches. which look for more than just one back one forward

    wrapper = ""
    prev_tag = ""
    count = 0
    for i, child in enumerate(node_1.getchildren()):
        # Check if there is no nodes left to check in node_2
        if count >= len(node_2.getchildren()):
            wrapper += "(<" + str(child.tag).upper() + "... >)?"
            continue

        target = node_2.getchildren()[count]

        print("one = " + str(child.tag) + add_attributes(child) + ", second = " + str(target.tag) + add_attributes(target))

        if child.tag != target.tag or id_mismatch(child, target):
            if contains(node_2, count, child):
                wrapper += "(<" + target.tag.upper() + "... >)?"
                count += 1
                # CHECK AGAIN
            else:
                wrapper += "(<" + str(child.tag).upper() + "... >)?"
            continue

        new_tag = "<" + str(child.tag).upper() + add_attributes(child) + ">"

        if child.text is not None:
            if child.text == target.text:
                new_tag += child.text
            elif child.text != target.text:
                new_tag += "#text"

        new_tag += auto_ex(child, target)

        new_tag += "</" + str(child.tag).upper() + ">"

        if new_tag == prev_tag:
            wrapper = re.sub(new_tag + "$", "(" + new_tag + ")+", wrapper)
            continue

        wrapper += new_tag

        prev_tag = new_tag
        count += 1

        if i == len(node_1.getchildren()) - 1 \
            and count < len(node_2.getchildren()) \
            and node_2.getchildren()[count].tag != child.tag:
            wrapper += "(<" + node_2.getchildren()[count].tag.upper() + "... >)?"
    return wrapper



def auto_extraction(html1, html2):
    tree1 = html.fromstring(html1)
    tree2 = html.fromstring(html2)

    cleaner = Cleaner(style=True, remove_unknown_tags=False)
    tree1 = cleaner.clean_html(tree1)
    tree2 = cleaner.clean_html(tree2)

    result = auto_ex(tree1.body, tree2.body)
    result = re.sub("\n{2,}?", "\n", result)

    return result









parser = argparse.ArgumentParser(description='Extracts data from a webpage.')
parser.add_argument('type', metavar='T', type=str, help='type of data extraction. Can be A, B or C.')

args = parser.parse_args()

sites = ['rtvslo.si', 'overstock.com', 'mimovrste.si', 'ceneje.si']


for site in sites:
    root = '../input-extraction/' + site + "/"
    (_, _, filenames) = next(walk(root))
    for file in filenames:
        if not file.endswith(".html"):
            continue

        data = None

        encoding = 'utf-8'
        if site == 'overstock.com':
            encoding = 'unicode_escape'
        html_content = open(root + file, mode='r', encoding=encoding).read()

        if args.type == 'A':
            data = regular_expressions(site, html_content)
        if args.type == 'B':
            data = x_path(site, html_content)
        if args.type == 'C':
            '''html1 = open('../input-extraction/example1.html', mode='r', encoding=encoding).read()
            html2 = open('../input-extraction/example2.html', mode='r', encoding=encoding).read()'''
            html1 = open('../input-extraction/rtvslo.si/Audi A6 50 TDI quattro_ nemir v premijskem razredu - RTVSLO.si.html', mode='r', encoding=encoding).read()
            html2 = open('../input-extraction/rtvslo.si/Volvo XC 40 D4 AWD momentum_ suvereno med najboljše v razredu - RTVSLO.si.html', mode='r', encoding=encoding).read()
            data = auto_extraction(html1, html2)

        print(data)
        print("\n")
        with open("data_" + file.replace(".html", "") + ".json", "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

        if args.type == 'C':
            exit(0)
