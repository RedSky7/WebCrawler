package com.company;

import java.sql.*;

public class DatabaseHandler {

    private static Connection connection;

    private static Connection getConnection(){
        if(connection == null) {
            try {
                connection = DriverManager.getConnection("jdbc:postgresql://localhost:5432/crawldb", "postgres", "root");
            }
            catch (Exception e) {
                e.printStackTrace();
            }
        }
        return connection;
    }

    public static int addSite(String domain, String robotsContent, String sitemapContent) {
        try {
            String sql = "INSERT INTO crawldb.site (domain,robots_content,sitemap_content) "
                    + "VALUES (?,?,?);";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setString(1, domain);
            statement.setString(2, robotsContent);
            statement.setString(3, sitemapContent);
            statement.executeUpdate();

            return getSiteId(domain);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return -1;
    }

    public static void editSite(int siteId, String domain, String robotsContent, String sitemapContent) {
        if(siteId == -1) {
            System.err.println("editSite: id is -1.");
            return;
        }
        try {
            String sql = "UPDATE crawldb.site "
                    + "SET domain = ?, robots_content = ?, sitemap_content = ? WHERE id = ?;";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setString(1, domain);
            statement.setString(2, robotsContent);
            statement.setString(3, sitemapContent);
            statement.setInt(4, siteId);
            statement.executeUpdate();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static int getSiteId(String domain) {
        try {
            System.out.println("getSiteId: domain = " + domain);
            String sql = "SELECT id FROM crawldb.site WHERE domain LIKE ?;";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setString(1, domain);
            ResultSet resultSet = statement.executeQuery();
            if(resultSet.next()) {
                return resultSet.getInt("id");
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return -1;
    }

    public static int getPageId(String url) {
        try {
            String sql = "SELECT id FROM crawldb.page WHERE url LIKE ?;";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setString(1, url);
            ResultSet resultSet = statement.executeQuery();
            if(resultSet.next()) {
                return resultSet.getInt("id");
            }
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return -1;
    }

    public static int addPage(int siteId, PAGE_TYPE_CODE pageType, String url, String htmlContent, int httpStatusCode, Timestamp timestamp) {
        if(siteId == -1) {
            System.err.println("addPage: id is -1.");
            return -1;
        }
        try {
            String sql = "INSERT INTO crawldb.page (site_id,page_type_code,url,html_content,http_status_code,accessed_time) "
                    + "VALUES (?,?,?,?,?,?);";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setInt(1, siteId);
            statement.setString(2, pageType.name());
            statement.setString(3, url);
            statement.setString(4, htmlContent);
            statement.setInt(5, httpStatusCode);
            statement.setTimestamp(6, timestamp);
            statement.executeUpdate();

            return getPageId(url);
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return -1;
    }

    public static void editPage(int id, PAGE_TYPE_CODE pageType, String htmlContent, int httpStatusCode, Timestamp timestamp) {
        if(id == -1) {
            System.err.println("editPage: id is -1.");
            return;
        }
        try {
            String sql = "UPDATE crawldb.page "
                    + "SET page_type_code = ?, html_content = ?, http_status_code = ?, accessed_time = ? WHERE id = ?;";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setString(1, pageType.name());
            statement.setString(2, htmlContent);
            statement.setInt(3, httpStatusCode);
            statement.setTimestamp(4, timestamp);
            statement.setInt(5, id);
            statement.executeUpdate();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static int containsPageContent(String pageContent) {
        try {
            String sql = "SELECT id FROM crawldb.page WHERE html_content LIKE ?;";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setString(1, pageContent);
            ResultSet resultSet = statement.executeQuery();
            if(resultSet.next()) {
                return resultSet.getInt("id");
            }
            return -1;
        }
        catch (Exception e) {
            e.printStackTrace();
        }
        return -1;
    }

    public static void addPageData(int pageId, DATA_TYPE dataType, byte[] data) {
        if(pageId == -1) {
            System.err.println("addPageData: id is -1.");
            return;
        }
        try {
            String sql = "INSERT INTO crawldb.page_data (page_id,data_type_code,data) "
                    + "VALUES (?,?,?);";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setInt(1, pageId);
            statement.setString(2, dataType != null ? dataType.name() : null);
            statement.setBytes(3, data);
            statement.executeUpdate();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void addLink(int fromPageId, int toPageId) {
        if(fromPageId == -1 || toPageId == -1) {
            System.err.println("addLink: one of id's is -1.");
            return;
        }
        try {
            String sql = "INSERT INTO crawldb.link (from_page,to_page) "
                    + "VALUES (?,?);";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            statement.setInt(1, fromPageId);
            statement.setInt(2, toPageId);
            statement.executeUpdate();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static void addImage(int pageId, String fileName, String contentType, byte[] data, Timestamp timestamp) {
        if(pageId == -1) {
            System.err.println("addLink: id is -1.");
            return;
        }
        try {
            String sql = "INSERT INTO crawldb.image (page_id,filename,content_type,data,accessed_time) "
                    + "VALUES (?,?,?,?,?);";
            PreparedStatement statement = getConnection().prepareStatement(sql);
            //statement.setInt(1, id);
            statement.setInt(1, pageId);
            statement.setString(2, fileName);
            statement.setString(3, contentType);
            statement.setBytes(4, data);
            statement.setTimestamp(5, timestamp);
            statement.executeUpdate();
        }
        catch (Exception e) {
            e.printStackTrace();
        }
    }

    public static DATA_TYPE getDataType(String contentType) {
        if(contentType == null)
            return null;

        switch (contentType) {
            case "application/pdf":
                return DATA_TYPE.PDF;
            case "application/msword":
                return DATA_TYPE.DOC;
            case "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                return DATA_TYPE.DOCX;
            case "application/vnd.ms-powerpoint":
                return DATA_TYPE.PPT;
            case "application/vnd.openxmlformats-officedocument.presentationml.presentation":
                return DATA_TYPE.PPTX;
        }
        return null;
    }

    public enum DATA_TYPE {
        PDF,
        DOC,
        DOCX,
        PPT,
        PPTX
    }

    public static PAGE_TYPE_CODE getPageTypeCode(String url) {
        String[] urlComponents = url.split("\\.");
        switch (urlComponents[urlComponents.length - 1].toLowerCase()) {
            case "pdf":
            case "doc":
            case "docx":
            case "xlsx":
            case "zip":
            case "rar":
            case "csv":
            case "ods":
            case "mp3":
            case "jpg":
            case "png":
            case "gif":
            case "jpeg":
            case "tif":
                return PAGE_TYPE_CODE.BINARY;
            default:
                return PAGE_TYPE_CODE.HTML;
        }
    }

    public static String getImageType(String url) {
        String[] urlComponents = url.split("\\.");
        switch (urlComponents[urlComponents.length - 1].toLowerCase()) {
            case "apng":
                return "image/apgn";
            case "bmp":
                return "image/bmp";
            case "gif":
                return "image/gif";
            case "ico":
            case "cur":
                return "image/x-icon";
            case "jpeg":
            case "jpg":
            case "jfif":
            case "pjpeg":
            case "pjp":
                return "image/jpeg";
            case "png":
                return "image/png";
            case "svn":
                return "image/svg+xml";
            case "tif":
            case "tiff":
                return "image/tiff";
            case "webp":
                return "image/webp";
            default:
                return "other";
        }
    }


    public enum PAGE_TYPE_CODE {
        HTML,
        BINARY,
        DUPLICATE,
        FRONTIER
    }
}
