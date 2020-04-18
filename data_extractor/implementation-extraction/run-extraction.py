from os import walk
import argparse, json, re

def regular_expressions(site_name, html_content):
    html_content = html_content.replace("\n", "").replace("\t", "")

    extracted = []
    if site_name == "rtvslo.si":
        title = re.search("<h1>(.*?)</h1>", html_content).group(1)
        extracted.append(title)

        subtitle = re.search("<div class=\"subtitle\">(.*?)</div>", html_content).group(1)
        extracted.append(subtitle)

        lead = re.search("<p class=\"lead\">(.*?)</p>", html_content).group(1)
        extracted.append(lead)

        content = re.search("<div class=\"article-body\">(.*?)</div>[ ]*<div class=\"article-column\">", html_content).group(1)
        extracted.append(content)

        author = re.search("<div class=\"author-name\">(.*?)</div>", html_content).group(1)
        extracted.append(author)

        published_time = re.search("<div class=\"publish-meta\">(.*?)<br>", html_content).group(1).lstrip()
        extracted.append(published_time)

        return extracted
    if site_name == "overstock.com":
        items = re.findall("<tr bgcolor=\".{7}\">[ ]*<td valign=\"top\"(.*?)<tr><td colspan=\"2\" height=\"4\"", html_content)

        for item in items:
            sub_extracted = []
            title = re.search("<b>(.*?)</b>", item).group(1)
            sub_extracted.append(title)

            content = re.search("<span class=\"normal\">(.*?)<br>", item).group(1)
            sub_extracted.append(content)

            list_price = re.search("<s>(.*?)</s>", item).group(1)
            sub_extracted.append(list_price)

            price = re.search("<span class=\"bigred\"><b>(.*?)</b>", item).group(1)
            sub_extracted.append(price)

            whole_saving = re.search("<span class=\"littleorange\">(.*?) \(([0-9]{0,2}%)\)</span>", item)

            saving = whole_saving.group(1)
            sub_extracted.append(saving)

            saving_percent = whole_saving.group(2)
            sub_extracted.append(saving_percent)

            extracted.append(sub_extracted)
    if site_name == "mimovrste.si":
        # TODO: Extract what you need. TK

        return extracted
    if site_name == "ceneje.si":
        items = re.findall("<tr bgcolor=\".{7}\">[ ]*<td valign=\"top\"(.*?)<tr><td colspan=\"2\" height=\"4\"",
                           html_content)
        for item in items:
            sub_extracted = []

            # TODO: Extract what you need. TK

            extracted.append(sub_extracted)

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

        if args.type == 'A':
            print("Handle A: REGULAR_EXPRESSIONS... site = " + site)
            print("path = " + str(root + file))
            print(regular_expressions(site, open(root + file, mode='r', encoding='unicode_escape').read()))
        elif args.type == 'B':
            print("Handle B: XPATH...")
        elif args.type == 'C':
            print("Handle C: AUTOMATIC_WEB_EXTRACTION...")




