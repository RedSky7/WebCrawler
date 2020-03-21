package com.company;

import java.net.InetAddress;
import java.net.URI;
import java.net.URISyntaxException;
import java.util.Objects;

public class CrawlerUrl {

    private String url, domainName, serverIp;

    public CrawlerUrl(String url) {
        setUrl(url);
    }

    public void setUrl(String url) {
        if(url == null
                || url.startsWith("javascript:")
                || url.startsWith("tel:")
                || url.startsWith("mailto:")
                || url.length() == 0)
            return;

        try {
            this.url = getUrlWithoutParameters(url).split("#")[0]
                    .replaceAll("\\.html", "");

            this.domainName = Utils.getDomainName(getUrl());
            this.serverIp = InetAddress.getByName(getDomainName()).getHostAddress();
        }
        catch (Exception e) {
            //e.printStackTrace();
            System.err.println("setUrl: exception = " + e.getMessage());
        }
    }

    public boolean isValid() {
        return getUrl() != null && getDomainName() != null && getServerIp() != null;
    }

    private String getUrlWithoutParameters(String url) throws URISyntaxException {
        URI uri = new URI(url);
        return new URI(uri.getScheme(),
                uri.getAuthority(),
                uri.getPath(),
                null, // Ignore the query part of the input url
                uri.getFragment()).toString();
    }

    public String getDomainName() {
        return domainName;
    }

    public String getUrl() {
        return url;
    }

    public String getServerIp() {
        return serverIp;
    }


    @Override
    public boolean equals(Object o) {
        if (this == o) return true;
        if (o == null || getClass() != o.getClass()) return false;
        CrawlerUrl that = (CrawlerUrl) o;
        return this.url.replaceAll("https", "http").equals(that.getUrl().replace("https", "http"));
        //return this.url.equals(that.getUrl());
    }

    @Override
    public int hashCode() {
        return Objects.hash(url.replaceAll("https", "http"));
        //return Objects.hash(url);
    }
}
