package local.foundev.zap.core;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.AlertStore;

import java.net.URI;
import java.util.List;

/**
 * Orchestrates one run: crawl the target, run the passive analyzer on every
 * page as it arrives, then - only when authorization was explicitly confirmed
 * - run the active probes. All alerts land in the shared {@link AlertStore}.
 */
public final class ScanEngine {

    public static final int DEFAULT_MAX_PAGES = 50;

    private final AlertStore store;
    private final HttpFetcher fetcher;

    private volatile WebCrawler crawler;
    private volatile boolean cancelled;

    public ScanEngine(AlertStore store) {
        this.store = store;
        this.fetcher = new HttpFetcher();
    }

    public AlertStore getStore() {
        return store;
    }

    /** Cancels a run in progress: the crawl loop exits, active probes stop. */
    public void cancel() {
        cancelled = true;
        WebCrawler c = crawler;
        if (c != null) {
            c.stop();
        }
    }

    public ScanSummary run(URI target, boolean authorizedActive, int maxPages, ScanProgress progress) {
        ScanProgress p = progress == null ? ScanProgress.NONE : progress;
        cancelled = false;
        store.clear();
        long started = System.currentTimeMillis();

        PassiveAnalyzer passive = new PassiveAnalyzer();
        WebCrawler crawl = new WebCrawler(fetcher);
        crawler = crawl;

        int crawled = 0;
        boolean stoppedEarly = false;
        boolean activeRan = false;
        try {
            CrawlResult result = crawl.crawl(target, maxPages, new CrawlListener() {
                @Override
                public void pageCrawled(FetchResult page, int fetched, int queued) {
                    store.addAll(passive.analyze(page));
                    p.onStatus("Crawled " + page.getUri() + " (" + fetched + " pages, " + queued + " queued)");
                }

                @Override
                public void linkDiscovered(String url, String parentUrl) {
                    p.onLink(url, parentUrl);
                }

                @Override
                public void error(String url, String message) {
                    p.onStatus("Skipped " + url + ": " + message);
                }
            });
            crawled = result.getPages().size();
            stoppedEarly = result.isStopped() || cancelled;

            // Active checks are refused unless the caller passed the gate.
            if (authorizedActive && !cancelled && !result.getPages().isEmpty()) {
                ActiveAnalyzer active = new ActiveAnalyzer(fetcher);
                List<Alert> found = active.analyze(target, result.getPages(), true, () -> cancelled, p);
                store.addAll(found);
                activeRan = true;
            }
        } finally {
            crawler = null;
        }

        ScanSummary summary = new ScanSummary(
                target,
                crawled,
                store.size(),
                activeRan,
                stoppedEarly,
                System.currentTimeMillis() - started);
        p.onFinished(summary);
        return summary;
    }
}
