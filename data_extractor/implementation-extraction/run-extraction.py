from os import walk
import argparse, json, re
from lxml import html


#
# Regular expressions
#

def extract(match):
    if match is not None:
        result = match.group(1)
        return result.lstrip().rstrip()
    return ''


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
        extract_list = []
        for iter_item in re.finditer(
                "<tr bgcolor=\".{7}\">[ ]*<td valign=\"top\"(.*?)<tr><td colspan=\"2\" height=\"4\"", html_content):
            item = iter_item.group(1)
            sub_extracted = {}

            sub_extracted['Title'] = extract(re.search("<b>(.*?)</b>", item))
            sub_extracted['Content'] = extract(re.search("<span class=\"normal\">(.*?)<br>", item))
            sub_extracted['ListPrice'] = extract(re.search("<s>(.*?)</s>", item))
            sub_extracted['Price'] = extract(re.search("<span class=\"bigred\"><b>(.*?)</b>", item))

            whole_saving = re.search("<span class=\"littleorange\">(.*?) \(([0-9]{0,2}%)\)</span>", item)

            saving = whole_saving.group(1)
            sub_extracted['Saving'] = saving
            saving_percent = whole_saving.group(2)
            sub_extracted['SavingPercent'] = saving_percent

            extract_list.append(sub_extracted)
        return extract_list

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
        extract_list = []

        for iter_item in re.finditer("<div class=\"innerProductBox\">(.*?)<a class=\"browseCompareLink\"",
                                     html_content):
            item = iter_item.group(1)

            sub_extracted = {}
            sub_extracted['Image'] = extract(re.search("<img.*?src=\"(.*?)\"", item))
            sub_extracted['Title'] = extract(re.search("<h3>\W*<a.*?>(.*?)</a>", item))
            sub_extracted['MinPrice'] = extract(re.search("<b>(.*?)</b>", item))
            sub_extracted['Stores'] = extract(re.search("class=\"qtySellers\">\W*<b>(.*?)</b>", item))
            sub_extracted['Action'] = extract(re.search("<div class=\"rBox\">\W*<a.*?>(.*?)</a>", item))

            extract_list.append(sub_extracted)
        return extract_list

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

        sub_tree = tree.xpath(
            "/html/body/table[2]/tbody/tr[1]/td[5]/table/tbody/tr[2]/td/table/tbody/tr/td/table/tbody/tr")

        for item in sub_tree:

            sub_extracted = {}

            title = extract_x_path(item.xpath("td[2]/a/b/text()"))
            if len(title) == 0:
                continue

            sub_extracted['Title'] = title
            sub_extracted['Content'] = extract_x_path(item.xpath("td[2]/table/tbody/tr/td[2]/span/text()"))
            sub_extracted['ListPrice'] = extract_x_path(item.xpath("td[2]/table/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/s/text()"))
            sub_extracted['Price'] = extract_x_path(item.xpath("td[2]/table/tbody/tr/td[1]/table/tbody/tr[2]/td[2]/span/b/text()"))

            whole_saving = extract_x_path(item.xpath("td[2]/table/tbody/tr/td[1]/table/tbody/tr[3]/td[2]/span/text()")).split(" ")
            sub_extracted['Saving'] = whole_saving[0]
            sub_extracted['SavingPercent'] = whole_saving[1].replace("(", "").replace(")", "")

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

        sub_tree = tree.xpath("//*[@class=\"productBoxGrid\"]")

        for item in sub_tree:
            sub_extracted = {}

            sub = None
            if extract_x_path(item.xpath("div/div[1]/span/text()")) is '':
                sub = "a"
                sub_extracted['Image'] = item.xpath("div/div[1]/a/img/@src")
            else:
                sub = "span"
                sub_extracted['Image'] = item.xpath("div/div[1]/img/@src")

            sub_extracted['Title'] = extract_x_path(item.xpath("div/div[2]/h3/" + sub + "/text()"))
            sub_extracted['MinPrice'] = extract_x_path(item.xpath("div/div[2]/p/" + sub + "[1]/b/text()"))
            sub_extracted['Stores'] = extract_x_path(item.xpath("div/div[2]/p/" + sub + "[2]/b/text()"))
            sub_extracted['Action'] = extract_x_path(item.xpath("div/div[3]/" + sub + "/text()"))

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
