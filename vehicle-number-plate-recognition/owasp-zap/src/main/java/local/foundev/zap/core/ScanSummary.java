package local.foundev.zap.core;

import java.net.URI;

/** Outcome of one full scan run. */
public final class ScanSummary {

    private final URI target;
    private final int pagesCrawled;
    private final int alertCount;
    private final boolean activeRan;
    private final boolean cancelled;
    private final long elapsedMillis;

    public ScanSummary(URI target, int pagesCrawled, int alertCount,
                       boolean activeRan, boolean cancelled, long elapsedMillis) {
        this.target = target;
        this.pagesCrawled = pagesCrawled;
        this.alertCount = alertCount;
        this.activeRan = activeRan;
        this.cancelled = cancelled;
        this.elapsedMillis = elapsedMillis;
    }

    public URI getTarget() {
        return target;
    }

    public int getPagesCrawled() {
        return pagesCrawled;
    }

    public int getAlertCount() {
        return alertCount;
    }

    /** True when the active phase was requested and completed. */
    public boolean isActiveRan() {
        return activeRan;
    }

    /** True when the user stopped the scan before it completed. */
    public boolean isCancelled() {
        return cancelled;
    }

    public long getElapsedMillis() {
        return elapsedMillis;
    }
}
