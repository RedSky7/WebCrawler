# WebCrawler
 
You can use this crawler by replacing static Strings which start with URL_* with your own.

Some settings you might want to change:

THREAD_COUNT specifies the number of threads the program will use. More threads will improve the speed if you are crawling web pages on seperate IPs and seperate domains. The crawler uses a modified strategy of breadth first crawl but will skip frontier pages that are not yet available for crawling (because the delay time has not yet passed).

DELAY specifies the default delay the crawler will use to crawl pages on the same domain or IP address. This can be overriden if the robots.txt specifies another crawl-delay in which case that one is used.

MAX_LINKS specifies the number of links that the crawler will visit (or attempt to do so) before the crawler stops.

USER_AGENT specifies the name of the crawler, which you should change.
