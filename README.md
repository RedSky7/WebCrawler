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
