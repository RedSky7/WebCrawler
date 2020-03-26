// PAGE COUNT
SELECT COUNT(page.id) FROM crawldb.page page WHERE page.site_id = 1;


// BINARY
SELECT COUNT(page.id) FROM crawldb.page page WHERE page.site_id = 1 AND page.page_type_code = 'BINARY';

// DUPLICATE
SELECT COUNT(page.id) FROM crawldb.page page WHERE page.site_id = 1 AND page.page_type_code = 'DUPLICATE';
