package local.foundev.zap;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.AlertStore;
import local.foundev.zap.model.Confidence;
import local.foundev.zap.model.Risk;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/** The store keeps every finding once and can be filtered by risk. */
class AlertStoreTest {

    private static Alert alert(String name, String url, String parameter, Risk risk) {
        return new Alert(name, risk, Confidence.HIGH, url, parameter, "evidence", "why", "fix");
    }

    @Test
    void anAlertIsStoredOnce() {
        AlertStore store = new AlertStore();

        assertTrue(store.add(alert("XSS", "http://a/", "q", Risk.HIGH)));
        assertFalse(store.add(alert("XSS", "http://a/", "q", Risk.HIGH)));

        assertEquals(1, store.size());
    }

    @Test
    void theSameFindingOnAnotherUrlIsAnotherAlert() {
        AlertStore store = new AlertStore();

        store.add(alert("XSS", "http://a/", "q", Risk.HIGH));
        store.add(alert("XSS", "http://b/", "q", Risk.HIGH));

        assertEquals(2, store.size());
    }

    @Test
    void theSameFindingOnAnotherParameterIsAnotherAlert() {
        AlertStore store = new AlertStore();

        store.add(alert("XSS", "http://a/", "q", Risk.HIGH));
        store.add(alert("XSS", "http://a/", "id", Risk.HIGH));

        assertEquals(2, store.size());
    }

    @Test
    void aNullAlertIsRefused() {
        AlertStore store = new AlertStore();

        assertFalse(store.add(null));
        assertEquals(0, store.size());
    }

    @Test
    void addAllCountsOnlyTheNewAlerts() {
        AlertStore store = new AlertStore();
        store.add(alert("XSS", "http://a/", "q", Risk.HIGH));

        int added = store.addAll(List.of(
                alert("XSS", "http://a/", "q", Risk.HIGH),
                alert("SQLi", "http://a/", "q", Risk.HIGH),
                alert("HSTS", "http://a/", "", Risk.LOW)));

        assertEquals(2, added);
        assertEquals(3, store.size());
    }

    @Test
    void addAllOfNullIsZero() {
        AlertStore store = new AlertStore();

        assertEquals(0, store.addAll(null));
    }

    @Test
    void theAlertsCanBeFilteredByRisk() {
        AlertStore store = new AlertStore();
        store.add(alert("XSS", "http://a/", "q", Risk.HIGH));
        store.add(alert("HSTS", "http://a/", "", Risk.LOW));
        store.add(alert("CSP", "http://a/", "", Risk.MEDIUM));

        assertEquals(1, store.countByRisk(Risk.HIGH));
        assertEquals(3, store.byRisk(Risk.HIGH).size() + store.byRisk(Risk.LOW).size()
                + store.byRisk(Risk.MEDIUM).size());
        assertTrue(store.byRisk(Risk.HIGH).get(0).getName().equals("XSS"));
    }

    @Test
    void clearingRemovesEverything() {
        AlertStore store = new AlertStore();
        store.add(alert("XSS", "http://a/", "q", Risk.HIGH));

        store.clear();

        assertEquals(0, store.size());
        // After a clear the same alert is new again.
        assertTrue(store.add(alert("XSS", "http://a/", "q", Risk.HIGH)));
    }

    @Test
    void theSnapshotIsACopy() {
        AlertStore store = new AlertStore();
        store.add(alert("XSS", "http://a/", "q", Risk.HIGH));

        List<Alert> snapshot = store.snapshot();
        snapshot.clear();

        assertEquals(1, store.size());
    }
}
