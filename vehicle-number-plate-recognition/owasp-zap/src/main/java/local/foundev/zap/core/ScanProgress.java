package local.foundev.zap.core;

/** Progress callbacks delivered by {@link ScanEngine} while a scan runs. */
public interface ScanProgress {

    /** Human-readable progress line (crawl page, active probe, skip, ...). */
    void onStatus(String message);

    /** A link was discovered; lets the UI grow its site tree. */
    void onLink(String url, String parentUrl);

    /** The scan finished; the summary carries the final counts. */
    void onFinished(ScanSummary summary);

    ScanProgress NONE = new ScanProgress() {
        @Override
        public void onStatus(String message) {
        }

        @Override
        public void onLink(String url, String parentUrl) {
        }

        @Override
        public void onFinished(ScanSummary summary) {
        }
    };
}
