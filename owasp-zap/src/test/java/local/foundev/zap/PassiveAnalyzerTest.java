package local.foundev.zap;

import local.foundev.zap.core.FetchResult;
import local.foundev.zap.core.PassiveAnalyzer;
import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Risk;
import org.junit.jupiter.api.Test;

import java.net.URI;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class PassiveAnalyzerTest {

    private static FetchResult page(String url, Map<String, List<String>> headers, String body) {
        return new FetchResult(URI.create(url), 200, headers, body);
    }

    private static List<String> names(List<Alert> alerts) {
        List<String> out = new ArrayList<>();
        for (Alert alert : alerts) {
            out.add(alert.getName());
        }
        return out;
    }

    @Test
    void flagsMissingSecurityHeadersOnBareHttpsResponse() {
        Map<String, List<String>> headers = new HashMap<>();
        headers.put("Content-Type", List.of("text/html; charset=utf-8"));
        headers.put("Server", List.of("Apache/2.4.57 (Unix)"));
        headers.put("Set-Cookie", List.of("SESSIONid=abc123; Path=/"));
        FetchResult page = page("https://shop.example.test/", headers,
                "<html><body>hello</body></html>");

        List<Alert> alerts = new PassiveAnalyzer().analyze(page);
        List<String> names = names(alerts);

        assertTrue(names.contains("Content-Security-Policy header not set"), String.valueOf(names));
        assertTrue(names.contains("X-Frame-Options header not set"), String.valueOf(names));
        assertTrue(names.contains("Strict-Transport-Security header not set"), String.valueOf(names));
        assertTrue(names.contains("Server banner disclosed"), String.valueOf(names));
        assertTrue(names.stream().anyMatch(n -> n.contains("Secure flag")), String.valueOf(names));
        assertTrue(names.stream().anyMatch(n -> n.contains("HttpOnly flag")), String.valueOf(names));
        assertFalse(alerts.stream().anyMatch(a -> a.getRisk() == Risk.HIGH),
                "passive checks must not report high risk for this fixture");
    }

    @Test
    void acceptsWellConfiguredResponseWithoutAlerts() {
        Map<String, List<String>> headers = new HashMap<>();
        headers.put("Content-Type", List.of("text/html"));
        headers.put("Content-Security-Policy", List.of("default-src 'self'; frame-ancestors 'none'"));
        headers.put("X-Frame-Options", List.of("DENY"));
        headers.put("X-Content-Type-Options", List.of("nosniff"));
        headers.put("Strict-Transport-Security", List.of("max-age=31536000; includeSubDomains"));
        headers.put("Set-Cookie", List.of("SESSIONid=abc123; Path=/; Secure; HttpOnly; SameSite=Lax"));
        FetchResult page = page("https://shop.example.test/", headers,
                "<html><body>ok</body></html>");

        List<Alert> alerts = new PassiveAnalyzer().analyze(page);

        assertTrue(alerts.isEmpty(), "expected no alerts but got: " + names(alerts));
    }

    @Test
    void detectsDirectoryListingIndexPage() {
        Map<String, List<String>> headers = new HashMap<>();
        headers.put("Content-Type", List.of("text/html"));
        FetchResult page = page("http://files.example.test:8080/uploads/", headers,
                "<html><head><title>Index of /uploads</title></head><body></body></html>");

        List<Alert> alerts = new PassiveAnalyzer().analyze(page);

        assertTrue(names(alerts).contains("Directory listing enabled"), String.valueOf(names(alerts)));
    }
}
