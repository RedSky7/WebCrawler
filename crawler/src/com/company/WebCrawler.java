package com.company;

import com.jaunt.ResponseException;
import com.jaunt.UserAgent;
import com.jauntium.Browser;
import com.jauntium.Element;
import com.jauntium.Elements;
import com.panforge.robotstxt.RobotsTxt;
import org.openqa.selenium.Point;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.net.URL;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.Arrays;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedList;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class WebCrawler {

    private static final String URL_GOV = "gov.si";
    private static final String URL_EVEM_GOV = "evem.gov.si";
    private static final String URL_E_UPRAVA_GOV = "e-uprava.gov.si";
    private static final String URL_E_PROSTOR_GOV = "e-prostor.gov.si";

    private static final int THREAD_COUNT = 6;  // Number of workers
    private static final int DELAY = 5000;        // In ms. Min value should be 5000
    private static final int MAX_LINKS = 50000;

    private static final String[] startDomains = new String[] {
            URL_GOV,
            URL_EVEM_GOV,
            URL_E_UPRAVA_GOV,
            URL_E_PROSTOR_GOV
    };

    private static final String USER_AGENT = "fri-ieps-20";


    public static Lock frontierLock = new ReentrantLock();
    public static LinkedList<CrawlerUrl> frontier = new LinkedList<>();

    public static HashSet<String> processedLinks  = new HashSet<>();

    public static HashMap<String, Long> permittedTimes = new HashMap<>();

    public static HashMap<String, RobotsTxt> domainRobots = new HashMap<>();

    public static void main(String[] args) {
        System.setProperty("webdriver.chrome.driver", "libs\\chromedriver.exe");  //setup

        ChromeOptions chromeOptions = new ChromeOptions();
        chromeOptions.addArguments("--user-agent=\"" + USER_AGENT + "\"");
        chromeOptions.addArguments("--ignore-certificate-errors");

        // TODO: Uncomment bellow. TK
        chromeOptions.addArguments("--headless");

        for(String crawlDomain : startDomains) {
            CrawlerUrl crawlerUrl = new CrawlerUrl("http://" + crawlDomain);
            frontier.add(crawlerUrl);
        }

        for(int i = 0; i < THREAD_COUNT; i++) {
            new CrawlerThread(new ChromeDriver(chromeOptions)).start();
        }
    }


    private static boolean fetchDomainRobots(CrawlerUrl crawlerUrl) {
        if(domainRobots.containsKey(crawlerUrl.getDomainName())
                || DatabaseHandler.getSiteId(crawlerUrl.getDomainName()) != -1)
            return false;


        int siteId = DatabaseHandler.addSite(crawlerUrl.getDomainName(), null, null);

        if(DatabaseHandler.getPageId(crawlerUrl.getUrl()) == -1)
            DatabaseHandler.addPage(siteId, DatabaseHandler.PAGE_TYPE_CODE.HTML, crawlerUrl.getUrl(), null, 200, Timestamp.from(Instant.now()));

        if(addRobots(crawlerUrl, "https://www." + crawlerUrl.getDomainName(), siteId)
                || addRobots(crawlerUrl, "https://" + crawlerUrl.getDomainName(), siteId)
                || addRobots(crawlerUrl, "http://www." + crawlerUrl.getDomainName(), siteId)
                || addRobots(crawlerUrl, "http://" + crawlerUrl.getDomainName(), siteId)
                || addRobots(crawlerUrl, crawlerUrl.getDomainName(), siteId)
                || addRobots(crawlerUrl, crawlerUrl.getUrl(), siteId))
            return true;

        // Well this is one bad site.
        System.err.println("File robots.txt not found for domainName = " + crawlerUrl.getDomainName());

        domainRobots.put(crawlerUrl.getDomainName(), null);
        return true;
    }

    private static boolean addRobots(CrawlerUrl crawlerUrl, String robotsUrl, int siteId) {
        try (InputStream robotsTxtStream = new URL(robotsUrl + "/robots.txt").openStream()) {
            RobotsTxt robotsTxt;
            byte[] bytes = robotsTxtStream.readAllBytes();
            String robotsContent = new String(bytes);
            if(robotsContent.contains("<html") || robotsContent.contains("<body")) {
                // There is a special place in hell for you 'arsq.gov.si'.
                System.err.println("addRobots: Robots.txt that is actually a web page.");
                return false;
            }

            System.out.println("fetchDomainRobots: url = " + robotsUrl + "/robots.txt" + "\nrobots = " + robotsContent);
            robotsTxt = RobotsTxt.read(new ByteArrayInputStream(bytes));
            DatabaseHandler.editSite(siteId, crawlerUrl.getDomainName(), new String(bytes), Arrays.toString(robotsTxt.getSitemaps().toArray()));
            domainRobots.put(crawlerUrl.getDomainName(), null);
            return true;
        }
        catch (Exception e) {
            //e.printStackTrace();
        }
        return false;
    }

    private static class CrawlerThread extends Thread {
        private UserAgent userAgent;
        private Browser browser;

        public CrawlerThread(ChromeDriver chromeDriver) {
            browser = new Browser(chromeDriver);
            browser.driver.manage().window().setPosition(new Point(1920,0));

            // Without this the crawler will get stuck when it is asked for a certificate.
            browser.driver.manage().timeouts().pageLoadTimeout(5, TimeUnit.SECONDS);
            browser.driver.manage().timeouts().setScriptTimeout(5, TimeUnit.SECONDS);

            userAgent = new UserAgent();
            userAgent.settings.defaultRequestHeaders.put("user-agent", USER_AGENT);
        }



        @Override
        public void run() {
            long startTime = System.currentTimeMillis();
            while (DatabaseHandler.getPageCount() < MAX_LINKS) {
                CrawlerUrl urlToVisit = null;

                System.out.println("PAGE COUNT = " + DatabaseHandler.getPageCount());

                do {
                    if (frontierLock.tryLock()) {
                        if (frontier.size() == 0) {
                            frontierLock.unlock();
                            browser.close();
                            System.out.println("no more links.");
                            return;
                        }

                        //System.out.println("frontier size = " + frontier.size());

                        for (int i = 0; i < frontier.size(); i++) {
                            CrawlerUrl crawlerUrl = frontier.get(i);
                            if (permittedTimes.containsKey(crawlerUrl.getServerIp())
                                    && System.currentTimeMillis() < permittedTimes.get(crawlerUrl.getServerIp())
                                    || permittedTimes.containsKey(crawlerUrl.getDomainName())
                                    && System.currentTimeMillis() < permittedTimes.get(crawlerUrl.getDomainName())) {
                                continue;
                            }

                            long delayForThisLink = DELAY;
                            if(domainRobots.containsKey(crawlerUrl.getDomainName())) {
                                RobotsTxt robotsTxt = domainRobots.get(crawlerUrl.getDomainName());
                                if(robotsTxt != null && robotsTxt.ask(USER_AGENT, crawlerUrl.getUrl()).getCrawlDelay() != null) {
                                    delayForThisLink = robotsTxt.ask(USER_AGENT, crawlerUrl.getUrl()).getCrawlDelay() * 1000;
                                    System.out.println("NEW DELAY = " + delayForThisLink);
                                    if (delayForThisLink == 0)
                                        delayForThisLink = DELAY;
                                }
                            }
                            Long delayedPermittedTime = System.currentTimeMillis() + delayForThisLink;

                            permittedTimes.put(crawlerUrl.getServerIp(), delayedPermittedTime);
                            permittedTimes.put(crawlerUrl.getDomainName(), delayedPermittedTime);

                            urlToVisit = crawlerUrl;
                            frontier.remove(i);
                            //System.out.println("link found");
                            break;
                        }
                        frontierLock.unlock();
                    }

                    if (urlToVisit == null) {
                        try {
                            Thread.sleep(1000);
                        } catch (InterruptedException e) {
                            e.printStackTrace();
                        }
                    }
                } while (urlToVisit == null);

                System.out.println("run: url = " + urlToVisit.getUrl());

                processedLinks.add(urlToVisit.getUrl());

                System.out.println("-------------------------------------");
                try {

                    int pageId = DatabaseHandler.getPageId(urlToVisit.getUrl());

                    // Check content-type in HEAD
                    handleHEAD(pageId, urlToVisit);

                    browser.visit(urlToVisit.getUrl());

                    urlToVisit = new CrawlerUrl(browser.getLocation());
                    if(!isCrawlContained(urlToVisit.getDomainName())) {
                        throw new Exception("NOT CRAWL CONTAINTED. Domain = " + urlToVisit.getDomainName());
                    }

                    if(fetchDomainRobots(urlToVisit)) {
                        pageId = DatabaseHandler.getPageId(urlToVisit.getUrl());
                    }

                    // Wait for the page to load
                    Thread.sleep(3000);

                    String pageContent = browser.doc.getTextContent("", false, false)
                            .replaceAll("\\s{2,}", " ");

                    int duplicateId = DatabaseHandler.containsPageContent(pageContent);
                    boolean duplicate = duplicateId != -1;

                    int siteId = DatabaseHandler.getSiteId(urlToVisit.getDomainName());

                    // Edit page as HTML
                    // Here content-type didn't tell us anything so we will try to extract the info for PAGE_TYPE from url.
                    DatabaseHandler.editPage(pageId,
                            duplicate ? DatabaseHandler.PAGE_TYPE_CODE.DUPLICATE : DatabaseHandler.getPageTypeCode(urlToVisit.getUrl()),
                            duplicate ? null : pageContent,
                            userAgent.response != null ? userAgent.response.getStatus() : 0,
                            Timestamp.from(Instant.now()));

                    // If duplicate don't process it just add a link
                    if(duplicate) {
                        DatabaseHandler.addLink(pageId, duplicateId);
                        throw new Exception("DUPLICATE skip.");
                    }

                    HashSet<CrawlerUrl> frontierExpansion = new HashSet<>();

                    // Handle links <a>

                    Elements links = browser.doc.findEvery("<a>");    //find search result links
                    for (Element link : links) {

                        try {
                            String href = link.getAttribute("href");
                            if (href != null) {
                                handleFrontierExpansion(frontierExpansion, href, siteId, pageId);
                            }
                        }
                        catch (Exception e) {
                            System.err.println("run: <a> exception = " + e.getMessage());
                        }

                        try {
                            String onClick = link.getAttribute("onclick");
                            String url = null;
                            if (onClick != null && onClick.trim().length() > 0) {
                                System.out.println("run: onclick = " + onClick);

                                if (onClick.contains("location.href")) {
                                    String[] components = onClick.split("location\\.href");
                                    url = components[components.length - 1].replaceAll("'", "").replaceAll("\"", "");
                                } else if (onClick.contains("document.location")) {
                                    String[] components = onClick.split("document\\.location");
                                    url = components[components.length - 1].replaceAll("'", "").replaceAll("\"", "");
                                }

                                System.out.println("run: onclick URL = " + url);
                                if (url != null)
                                    handleFrontierExpansion(frontierExpansion, url, siteId, pageId);
                            }
                        }
                        catch (Exception e) {
                            System.err.println("run: <a> exception = " + e.getMessage());
                        }

                    }


                    // Handle images <img>
                    Elements images = browser.doc.findEvery("<img>");    //find search result links
                    for (Element img : images) {
                        try {
                            String src = img.getAttribute("src");
                            if (src == null || src.startsWith("data")) {
                                // This is not a link so continue...
                                continue;
                            }
                            DatabaseHandler.addImage(pageId, src, DatabaseHandler.getImageType(src), null, Timestamp.from(Instant.now()));
                        }
                        catch (Exception e) {
                            System.err.println("run: <img> exception = " + e.getMessage());
                        }
                    }

                    // This shouldn't ever take so long.
                    if(frontierLock.tryLock(10000, TimeUnit.MILLISECONDS)) {
                        frontier.addAll(frontierExpansion);
                        frontierLock.unlock();
                    }
                }
                catch (ResponseException e) {
                    System.err.println("run: exception = " + e.getMessage());
                }
                catch (Exception e) {
                    System.err.println("run: exception = " + e.getMessage());
                    e.printStackTrace();
                }
                finally {
                    processedLinks.add(urlToVisit.getUrl());
                }
            }
            System.out.println("---------------------------------------------------\n"
                    + "---------------------------------------------------\n"
                    + "Time taken = " + (System.currentTimeMillis() - startTime) + " for " + MAX_LINKS);
            browser.close();
        }

        private void handleHEAD(int pageId, CrawlerUrl crawlerUrl) throws Exception {
            try {
                userAgent.sendHEAD(crawlerUrl.getUrl());
            }
            catch (ResponseException e) {
                System.err.println("handleHEAD: HEAD exception = " + e.getMessage());
                return;
            }

            String location = userAgent.response.getHeader("location");
            String contentType = userAgent.response.getHeader("content-type");

            if(contentType == null) {
                if(location != null) {
                    processedLinks.add(crawlerUrl.getUrl());
                    crawlerUrl = new CrawlerUrl(location);
                    if(processedLinks.contains(crawlerUrl.getUrl()))
                        throw new Exception("Already visited.");

                    processedLinks.add(crawlerUrl.getUrl());

                    // Some delay before sending another HEAD.
                    Thread.sleep(400);
                    handleHEAD(pageId, crawlerUrl);
                }
                return;
            }

            if(pageId == -1) {
                System.err.println("handleHEAD: pageId = " + pageId);
                return;
            }

            DatabaseHandler.DATA_TYPE dataType = DatabaseHandler.getDataType(contentType);

            if(dataType != null || DatabaseHandler.getPageTypeCode(crawlerUrl.getUrl()) == DatabaseHandler.PAGE_TYPE_CODE.BINARY) {
                DatabaseHandler.editPage(pageId, DatabaseHandler.PAGE_TYPE_CODE.BINARY, null, userAgent.response.getStatus(), Timestamp.from(Instant.now()));
                DatabaseHandler.addPageData(pageId, dataType, null);
                throw new Exception("BINARY not supported");
            }
            else {
                // Probably HTML but can't be sure
                DatabaseHandler.editPage(pageId, DatabaseHandler.PAGE_TYPE_CODE.HTML, null, userAgent.response.getStatus(), Timestamp.from(Instant.now()));
            }
        }



        private boolean isCrawlContained(String domainName) {
            //System.out.println("domainName = " + domainName + ". Ends with gov ? " + domainName.endsWith("gov.si"));
            return domainName.endsWith(".gov.si") || domainName.equals("gov.si");
        }

        private boolean hasBeenVisited(CrawlerUrl url) {
            return processedLinks.contains(url.getUrl());
        }

        private void handleFrontierExpansion(HashSet<CrawlerUrl> frontierExpansion, String url, int siteId, int pageId) {
            CrawlerUrl crawlerUrl = new CrawlerUrl(url);
            if(url == null
                    || url.length() == 0
                    || !crawlerUrl.isValid()
                    || hasBeenVisited(crawlerUrl)
                    || frontierExpansion.contains(crawlerUrl)
                    || frontier.contains(crawlerUrl)
                    || DatabaseHandler.getPageId(crawlerUrl.getUrl()) != -1)
                return;

            String domainName = crawlerUrl.getDomainName();
            if(domainName == null
                    || !isCrawlContained(domainName)
                    || DatabaseHandler.getPageTypeCode(crawlerUrl.getUrl()) == DatabaseHandler.PAGE_TYPE_CODE.BINARY)
                return;

            if(domainRobots.get(domainName) == null
                    || domainRobots.get(domainName).ask(USER_AGENT, url).hasAccess()) {
                frontierExpansion.add(crawlerUrl);
                int newPageId = DatabaseHandler.addPage(siteId, DatabaseHandler.PAGE_TYPE_CODE.FRONTIER, crawlerUrl.getUrl(), null, 0, Timestamp.from(Instant.now()));
                DatabaseHandler.addLink(pageId, newPageId);
            }
        }
    }
}
