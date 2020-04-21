from os import walk
import argparse, json, re
from lxml import html


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
        extract_list = []

        items = "/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr[1]/"
        titles = tree.xpath(items + "td[2]/a/b/text()")
        contents = tree.xpath(items + "td[2]/table/tbody/tr/td[2]/span/text()")
        listPrices = tree.xpath(items + "td[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/s/text()")
        prices = tree.xpath(items + "td[2]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/span/b/text()")
        wholeSavings = tree.xpath(items + "td[2]/table/tbody/tr/td[1]/table/tbody/tr[3]/td[2]/span/text()")

        for item in wholeSavings:
            subitems = item.split(" ")
            savings = subitems[0]
            savingsPercent = subitems[1]

        for i, _ in enumerate(titles):

            sub_extracted = {}

            sub_extracted['Title'] = titles[i]
            sub_extracted['Content'] = contents[i]
            sub_extracted['ListPrice'] = listPrices[i]
            sub_extracted['Price'] = prices[i]
            sub_extracted['Saving'] = savings[i]
            sub_extracted['SavingPercent'] = savingsPercent[i]

            extract_list.append(sub_extracted)
        return extract_list

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
        extract_list = []

        items = "//*[@class=\"productBoxGrid\"]/"
        sub = "a"
        # sub_extracted['Image'] = item.xpath("div/div[1]/a/img/@src") and was sub="span"

        images = x_path(items + "div/div[1]/img/@src", html_content)
        titles = x_path(items + "div/div[2]/h3/" + sub + "/text()", html_content)
        minPrices = x_path(items + "div/div[2]/p/" + sub + "[1]/b/text()", html_content)
        stores = x_path(items + "div/div[2]/p/" + sub + "[2]/b/text()", html_content)
        actions = x_path(items + "div/div[3]/" + sub + "/text()", html_content)

        for i, _ in enumerate(images):
            sub_extracted = {}

            sub_extracted['Image'] = images[i]
            sub_extracted['Title'] = titles[i]
            sub_extracted['MinPrice'] = minPrices[i]
            sub_extracted['Stores'] = stores[i]
            sub_extracted['Action'] = actions[i]

            extract_list.append(sub_extracted)
        return extract_list

    return extracted


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

        print(data)
        print("\n")
        with open("data_" + file.replace(".html", "") + ".json", "w", encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
