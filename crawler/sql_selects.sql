// PAGE COUNT
SELECT COUNT(page.id) FROM crawldb.page page WHERE page.page_type_code != 'FRONTIER';


// BINARY
SELECT COUNT(page.id) FROM crawldb.page page WHERE page.page_type_code = 'BINARY';

// DUPLICATE
SELECT COUNT(page.id) FROM crawldb.page page WHERE page.page_type_code = 'DUPLICATE';


SELECT COUNT(page_data.id), page_data.data_type_code FROM crawldb.page_data page_data GROUP BY page_data.data_type_code;

SELECT page.accessed_time FROM crawldb.page page ORDER BY page.accessed_time DESC

SELECT link.from_page, link.to_page, page.site_id FROM crawldb.link link, crawldb.page page WHERE page.id = link.from_page;


COPY (SELECT page.id, page.site_id FROM crawldb.page page) TO 'D:\vertF.csv' DELIMITER ',' CSV HEADER;

COPY (SELECT link.from_page, link.to_page, page.site_id FROM crawldb.link link, crawldb.page page WHERE page.id = link.from_page) TO 'D:\edgeF.csv' DELIMITER ',' CSV HEADER;
