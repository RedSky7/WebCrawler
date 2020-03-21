package com.company;

import com.jaunt.ResponseException;
import com.jaunt.UserAgent;
import com.jauntium.Browser;
import com.jauntium.Element;
import com.jauntium.Elements;
import com.panforge.robotstxt.RobotsTxt;
import org.openqa.selenium.Alert;
import org.openqa.selenium.NoAlertPresentException;
import org.openqa.selenium.Point;
import org.openqa.selenium.chrome.ChromeDriver;
import org.openqa.selenium.chrome.ChromeOptions;

import java.io.ByteArrayInputStream;
import java.io.InputStream;
import java.net.URL;
import java.sql.Timestamp;
import java.time.Instant;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.locks.Lock;
import java.util.concurrent.locks.ReentrantLock;

public class WebCrawler {

    private static final String URL_GOV = "gov.si";
    private static final String URL_EVEM_GOV = "evem.gov.si";
    private static final String URL_E_UPRAVA_GOV = "e-uprava.gov.si";
    private static final String URL_E_PROSTOR_GOV = "e-prostor.gov.si";

    private static final String[] crawlDomains = new String[] {
            URL_GOV,
            URL_EVEM_GOV,
            URL_E_UPRAVA_GOV,
            URL_E_PROSTOR_GOV
    };

    private static final String USER_AGENT = "fri-ieps-20";

    private static final int THREAD_COUNT = 3;  // Number of workers
    private static final int DELAY = 5000;        // In ms. Min value should be 5000
    private static final int MAX_LINKS = 1000;

    public static Lock frontierLock = new ReentrantLock();
    public static LinkedList<CrawlerUrl> frontier = new LinkedList<>();

    public static HashMap<CrawlerUrl, Boolean> processedLinks  = new HashMap<>();

    public static HashMap<String, Long> permittedTimes = new HashMap<>();

    public static HashMap<String, RobotsTxt> domainRobots = new HashMap<>();

    public static void main(String[] args) {
        System.setProperty("webdriver.chrome.driver", "libs\\chromedriver.exe");  //setup

        ChromeOptions chromeOptions = new ChromeOptions();
        chromeOptions.addArguments("--user-agent=\"" + USER_AGENT + "\"");
        chromeOptions.addArguments("--ignore-certificate-errors");

        // TODO: Uncomment bellow. TK
        //chromeOptions.addArguments("--headless");


        for(String crawlDomain : crawlDomains) {
            CrawlerUrl crawlerUrl = new CrawlerUrl("http://" + crawlDomain);
            int siteId = DatabaseHandler.addSite(crawlerUrl.getDomainName(), null, null);
            System.out.println("main: siteId = " + siteId);
            DatabaseHandler.addPage(siteId, DatabaseHandler.PAGE_TYPE_CODE.HTML, crawlerUrl.getUrl(), null, 200, Timestamp.from(Instant.now()));
            fetchDomainRobots(crawlerUrl.getDomainName(), "https://" + (!crawlDomain.equals(URL_E_UPRAVA_GOV) ? "www." : "") + crawlDomain);
            frontier.add(crawlerUrl);
        }


        for(int i = 0; i < THREAD_COUNT; i++) {
            new CrawlerThread(new ChromeDriver(chromeOptions)).start();
        }
    }


    private static void fetchDomainRobots(String domainName, String url) {
        if(domainRobots.containsKey(domainName))
            return;

        RobotsTxt robotsTxt = null;
        int siteId = DatabaseHandler.getSiteId(domainName);
        try (InputStream robotsTxtStream = new URL(url + "/robots.txt").openStream()) {
            byte[] bytes = robotsTxtStream.readAllBytes();
            System.out.println("fetchDomainRobots: url = " + url + "/robots.txt" + "\nrobots = " + new String(bytes));
            robotsTxt = RobotsTxt.read(new ByteArrayInputStream(bytes));
            DatabaseHandler.editSite(siteId, domainName, new String(bytes), Arrays.toString(robotsTxt.getSitemaps().toArray()));
        }
        catch (Exception e) {
            //e.printStackTrace();
            System.err.println("File robots.txt not found for domainName = " + domainName);
        }
        finally {
            domainRobots.put(domainName, robotsTxt);
        }
    }

    private static class CrawlerThread extends Thread {
        private UserAgent userAgent;
        private Browser browser;

        public CrawlerThread(ChromeDriver chromeDriver) {
            browser = new Browser(chromeDriver);
            browser.driver.manage().window().setPosition(new Point(1920,0));

            browser.driver.manage().timeouts().pageLoadTimeout(5, TimeUnit.SECONDS);
            browser.driver.manage().timeouts().setScriptTimeout(5, TimeUnit.SECONDS);

            userAgent = new UserAgent();
            userAgent.settings.defaultRequestHeaders.put("user-agent", USER_AGENT);
        }



        @Override
        public void run() {
            while (processedLinks.size() < MAX_LINKS) {
                CrawlerUrl urlToVisit = null;

                do {
                    if (frontierLock.tryLock()) {
                        if (frontier.size() == 0) {
                            frontierLock.unlock();
                            browser.close();
                            System.out.println("no more links.");
                            return;
                        }

                        System.out.println("frontier size = " + frontier.size());

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
                            System.out.println("link found");
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
                processedLinks.put(urlToVisit, false);

                System.out.println("-------------------------------------");
                try {
                    int pageId = DatabaseHandler.getPageId(urlToVisit.getUrl());

                    // Check content-type in HEAD
                    handleHEAD(pageId, urlToVisit);

                    browser.visit(urlToVisit.getUrl());

                    // Wait for the page to load
                    Thread.sleep(3000);

                    // Handle dialogs
                    try {
                        // Add a wait timeout before this statement to make
                        // sure you are not checking for the alert too soon.
                        Alert alt = browser.driver.switchTo().alert();
                        alt.dismiss();

                        System.out.println("dialog found and dismissed");

                    } catch(NoAlertPresentException noe) {
                        // No alert found on page, proceed with test.
                    }

                    int duplicateId = DatabaseHandler.containsPageContent(browser.doc.getTextContent());
                    boolean duplicate = duplicateId != -1;

                    int siteId = DatabaseHandler.getSiteId(urlToVisit.getDomainName());

                    // Edit page as HTML
                    DatabaseHandler.editPage(pageId,
                            duplicate ? DatabaseHandler.PAGE_TYPE_CODE.DUPLICATE : DatabaseHandler.getPageTypeCode(urlToVisit.getUrl()),
                            duplicate ? null : browser.doc.getTextContent(),
                            userAgent.response.getStatus(),
                            Timestamp.from(Instant.now()));

                    // If duplicate don't process it
                    if(duplicate) {
                        DatabaseHandler.addLink(pageId, duplicateId);
                        System.out.println("run: duplicateId = " + duplicateId);
                        throw new Exception("DUPLICATE skip.");
                    }

                    // Handle links <a>
                    HashSet<CrawlerUrl> frontierExpansion = new HashSet<>();
                    Elements links = browser.doc.findEvery("<a>");    //find search result links
                    for (Element link : links) {
                        List<String> attributeNames = link.getAttributeNames();
                        if(attributeNames.contains("href")) {
                            String href = link.getAttribute("href");
                            if (href != null) {
                                handleFrontierExpansion(frontierExpansion, href);
                            }
                        }
                        if(attributeNames.contains("onclick")) {
                            String onClick = link.getAttribute("onclick");
                            String url = null;
                            if (onClick != null) {
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
                                    handleFrontierExpansion(frontierExpansion, url);
                            }
                        }
                    }

                    System.out.println("frontierExpansion size = " + frontierExpansion.size());

                    for(CrawlerUrl crawlerUrl : frontierExpansion) {
                        System.out.println("run: addPage url = " + crawlerUrl.getUrl());
                        int newPageId = DatabaseHandler.addPage(siteId, DatabaseHandler.PAGE_TYPE_CODE.FRONTIER, crawlerUrl.getUrl(), null, 0, Timestamp.from(Instant.now()));
                        DatabaseHandler.addLink(pageId, newPageId);
                    }

                    // Handle images <img>
                    Elements images = browser.doc.findEvery("<img>");    //find search result links
                    for(Element img : images) {
                        String src = img.getAttribute("src");
                        if(src == null || src.startsWith("data")) {
                            // This is not a link so continue...
                            continue;
                        }
                        DatabaseHandler.addImage(pageId, src, DatabaseHandler.getImageType(src).name(), null, Timestamp.from(Instant.now()));
                    }

                    if(frontierLock.tryLock(1000, TimeUnit.MILLISECONDS)) {
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
                    processedLinks.replace(urlToVisit, true);
                }
            }
            browser.close();
        }

        private void handleHEAD(int pageId, CrawlerUrl crawlerUrl) throws Exception {
            try {
                userAgent.sendHEAD(crawlerUrl.getUrl());
            }
            catch (ResponseException e) {
                System.err.println("handleHEAD: exception = " + e.getMessage());
                return;
            }
            //System.out.println("handleHEAD: status =" + userAgent.response.getStatus());

            //System.out.println("handleHEAD: location =" + userAgent.response.getHeader("location"));
            //System.out.println("handleHEAD: content-type =" + userAgent.response.getHeader("content-type"));

            String location = userAgent.response.getHeader("location");
            String contentType = userAgent.response.getHeader("content-type");

            if(contentType == null) {
                if(location != null) {
                    processedLinks.replace(crawlerUrl, true);
                    crawlerUrl = new CrawlerUrl(location);
                    if(processedLinks.containsKey(crawlerUrl))
                        throw new Exception("Already visited.");

                    processedLinks.put(crawlerUrl, false);

                    Thread.sleep(500);
                    handleHEAD(pageId, crawlerUrl);
                }
                return;
            }

            if (contentType.contains("text/html")) {
                DatabaseHandler.editPage(pageId, DatabaseHandler.PAGE_TYPE_CODE.HTML, null, userAgent.response.getStatus(), Timestamp.from(Instant.now()));
            }
            else {
                DatabaseHandler.DATA_TYPE dataType = DatabaseHandler.getDataType(contentType);
                DatabaseHandler.editPage(pageId, DatabaseHandler.PAGE_TYPE_CODE.BINARY, null, userAgent.response.getStatus(), Timestamp.from(Instant.now()));
                DatabaseHandler.addPageData(pageId, dataType, null);
                throw new Exception("BINARY not supported");
            }
        }



        private boolean isCrawlContained(String domainName) {
            for(String domainUrl : crawlDomains) {
                if(domainName.equals(domainUrl))
                    return true;
            }
            return false;
        }

        private boolean hasBeenVisited(CrawlerUrl url) {
            return processedLinks.containsKey(url);
        }

        private void handleFrontierExpansion(HashSet<CrawlerUrl> frontierExpansion, String url) {
            CrawlerUrl crawlerUrl = new CrawlerUrl(url);
            if(url == null
                    || url.length() == 0
                    || !crawlerUrl.isValid()
                    || hasBeenVisited(crawlerUrl)
                    || frontierExpansion.contains(crawlerUrl)
                    || frontier.contains(crawlerUrl))
                return;

            String domainName = crawlerUrl.getDomainName();
            if(domainName == null || !isCrawlContained(domainName))
                return;

            if(domainRobots.get(domainName) == null
                    || domainRobots.get(domainName).ask(USER_AGENT, url).hasAccess()) {
                frontierExpansion.add(crawlerUrl);
            }
        }
    }
}
