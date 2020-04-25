# WebCrawler
 
A web crawler implemented in Java that can be used in order to obtain the information from web sites on specific domains. 
 
You can use this crawler by replacing static Strings which start with URL_* with your own.

Some settings you might want to change:

__URL\_\*__ strings that specify the starting domains. Default ones are of gov.si.

__THREAD_COUNT__ specifies the number of threads the program will use. More threads will improve the speed if you are crawling web pages on seperate IPs and seperate domains. The crawler uses a modified strategy of breadth first crawl but will skip frontier pages that are not yet available for crawling (because the delay time has not yet passed).

__DELAY__ specifies the default delay the crawler will use to crawl pages on the same domain or IP address. This can be overriden if the robots.txt specifies another crawl-delay in which case that one is used.

__MAX_LINKS__ specifies the number of links that the crawler will visit (or attempt to do so) before the crawler stops.

__USER_AGENT__ specifies the name of the crawler, which you should change.

Running:
You can simply run the program preferably in IntelliJ.


# DataExtractor

A web data extractor implemented in Python 3.6 can be used to gather specific data from predetermined websites that are located inside of input-extraction directory.

Required Python libraries:
-sys,
-os,
-argparse,
-json,
-re,
-lxml.html.

Arguments for running run-extraction.py:
-A: Regular Expressions extraction,
-B: XPath extraction,
-C: Automatic Web extraction.

Running:
You can simply run the program preferably in PyCharm, where you can provide arguments in EditConfigurations option, or run it via python in a command prompt. Arguments required are listed above.
