package local.foundev.zap.core;

/** Callbacks fired while the spider walks a site. */
public interface CrawlListener {

    /** One page was fetched successfully. */
    void pageCrawled(FetchResult page, int fetched, int queued);

    /** A link was found inside a page and queued for the crawl. */
    void linkDiscovered(String url, String parentUrl);

    /** A URL could not be fetched and was skipped. */
    void error(String url, String message);

    CrawlListener NONE = new CrawlListener() {
        @Override
        public void pageCrawled(FetchResult page, int fetched, int queued) {
        }

        @Override
        public void linkDiscovered(String url, String parentUrl) {
        }

        @Override
        public void error(String url, String message) {
        }
    };
}
