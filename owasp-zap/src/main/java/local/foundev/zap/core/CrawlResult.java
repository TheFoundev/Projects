package local.foundev.zap.core;

import java.util.List;

/** Result of one crawl: the pages that were fetched, and whether it stopped early. */
public final class CrawlResult {

    private final List<FetchResult> pages;
    private final boolean stopped;

    public CrawlResult(List<FetchResult> pages, boolean stopped) {
        this.pages = List.copyOf(pages);
        this.stopped = stopped;
    }

    public List<FetchResult> getPages() {
        return pages;
    }

    /** True when the crawl was cancelled (not when it hit the page limit). */
    public boolean isStopped() {
        return stopped;
    }
}
