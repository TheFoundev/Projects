package local.foundev.zap;

import local.foundev.zap.core.FetchResult;
import local.foundev.zap.core.PassiveAnalyzer;
import local.foundev.zap.model.Alert;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The cookie analysis follows RFC 6265: the name/value pair ends at the
 * first ';', the attributes follow it.
 */
class CookieAnalysisTest {

    private static List<Alert> analyze(String setCookie) {
        Map<String, List<String>> headers = new HashMap<>();
        headers.put("Content-Type", List.of("text/html"));
        headers.put("Set-Cookie", List.of(setCookie));
        FetchResult page = new FetchResult(URI.create("https://shop.example.test/"), 200, headers,
                "<html><body>hello</body></html>");
        return new PassiveAnalyzer().analyze(page);
    }

    private static boolean hasAlert(List<Alert> alerts, String fragment) {
        return alerts.stream().anyMatch(alert -> alert.getName().contains(fragment));
    }

    @Test
    void aCookieWithoutAttributesMissesEveryFlag() {
        List<Alert> alerts = analyze("SESSIONid=abc123");

        assertTrue(hasAlert(alerts, "Secure flag"), "missing Secure");
        assertTrue(hasAlert(alerts, "HttpOnly flag"), "missing HttpOnly");
        assertTrue(hasAlert(alerts, "SameSite"), "missing SameSite");
    }

    @Test
    void aWellConfiguredCookieRaisesNothing() {
        List<Alert> alerts = analyze("SESSIONid=abc123; Path=/; Secure; HttpOnly; SameSite=Lax");

        assertFalse(hasAlert(alerts, "Secure flag"), "Secure must be seen");
        assertFalse(hasAlert(alerts, "HttpOnly flag"), "HttpOnly must be seen");
        assertFalse(hasAlert(alerts, "SameSite"), "SameSite must be seen");
    }

    @Test
    void theAttributesAreWhatFollowsTheFirstSemicolon() {
        // RFC 6265: the pair is "SESSIONid=abc", the attributes are the
        // parts that follow the first ';'.
        List<Alert> alerts = analyze("SESSIONid=abc; HttpOnly; Path=/");

        assertFalse(hasAlert(alerts, "HttpOnly flag"), "HttpOnly is a real attribute");
        assertTrue(hasAlert(alerts, "Secure flag"), "Secure is really absent");
    }

    @Test
    void aValueThatLooksLikeASecureFlagIsNotAnAttribute() {
        List<Alert> alerts = analyze("SESSIONid=Secure");

        assertTrue(hasAlert(alerts, "Secure flag"), "the value is not the attribute");
    }

    @Test
    void theNameIsThePartBeforeTheFirstEquals() {
        List<Alert> alerts = analyze("SESSIONid=a=b; Path=/");

        assertTrue(alerts.stream().allMatch(alert -> !alert.getName().contains("SESSIONid=a")),
                "the name of the cookie is SESSIONid, got: " + alerts);
    }

    @Test
    void anExpiresAttributeIsNotMistakenForAFlag() {
        List<Alert> alerts = analyze("SESSIONid=abc; Expires=Wed, 21 Oct 2026 07:28:00 GMT; Secure; HttpOnly");

        assertFalse(hasAlert(alerts, "Secure flag"), "Secure must be seen");
        assertFalse(hasAlert(alerts, "HttpOnly flag"), "HttpOnly must be seen");
        assertTrue(hasAlert(alerts, "SameSite"), "SameSite is really absent");
    }
}
