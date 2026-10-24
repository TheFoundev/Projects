package local.foundev.zap.model;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

/**
 * Thread-safe in-memory store for the alerts of the current scan.
 * Identical findings (same name, URL and parameter) are stored only once.
 */
public final class AlertStore {

    private final List<Alert> alerts = new ArrayList<>();
    private final Set<String> seenKeys = new HashSet<>();

    /** Returns true when the alert was new and has been stored. */
    public synchronized boolean add(Alert alert) {
        if (alert == null) {
            return false;
        }
        if (!seenKeys.add(alert.dedupKey())) {
            return false;
        }
        alerts.add(alert);
        return true;
    }

    /** Stores every new alert from the list, returns how many were added. */
    public synchronized int addAll(List<Alert> items) {
        if (items == null) {
            return 0;
        }
        int added = 0;
        for (Alert alert : items) {
            if (add(alert)) {
                added++;
            }
        }
        return added;
    }

    public synchronized void clear() {
        alerts.clear();
        seenKeys.clear();
    }

    /** A mutable copy of every stored alert. */
    public synchronized List<Alert> snapshot() {
        return new ArrayList<>(alerts);
    }

    /** Only the alerts at exactly the given risk level. */
    public synchronized List<Alert> byRisk(Risk risk) {
        List<Alert> out = new ArrayList<>();
        for (Alert alert : alerts) {
            if (alert.getRisk() == risk) {
                out.add(alert);
            }
        }
        return out;
    }

    public synchronized int countByRisk(Risk risk) {
        int count = 0;
        for (Alert alert : alerts) {
            if (alert.getRisk() == risk) {
                count++;
            }
        }
        return count;
    }

    public synchronized int size() {
        return alerts.size();
    }
}
