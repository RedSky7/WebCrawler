package com.company;

import java.net.URI;
import java.net.URISyntaxException;

public class Utils {

    public static String getDomainName(String url) {
        try {
            URI uri = new URI(url);
            String domain = uri.getHost();
            return domain.startsWith("www.") ? domain.substring(4) : domain;
        }
        catch (Exception e) {
            //e.printStackTrace();
            System.err.println("BAD = " + url);
            return null;
        }
    }
}
