package local.foundev.zap.core;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Confidence;
import local.foundev.zap.model.Risk;

import java.net.URI;
import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.function.BooleanSupplier;

/**
 * Active checks, deliberately few and safe. Every probe is a single GET that
 * appends one marker payload to one query parameter of a URL the spider
 * already visited; no request is ever sent unless the caller explicitly
 * confirms authorization for the target.
 */
public final class ActiveAnalyzer {

    /** Cap on parameter/probe combinations so a scan stays polite. */
    private static final int MAX_PARAMS = 20;

    static final String XSS_PAYLOAD = "<script>window.__foundev_zap_marker__=1</script>";
    static final String SQLI_PAYLOAD = "'";
    static final String TRAVERSAL_PAYLOAD = "../../../../etc/passwd";

    private static final String[] SQL_ERROR_MARKERS = {
            "you have an error in your sql syntax",
            "warning: mysql",
            "mysqli",
            "sqlstate[",
            "unclosed quotation mark",
            "unterminated quoted string",
            "ora-00933",
            "ora-01756",
            "postgresql",
            "pg_query",
            "sqlite.exception",
            "odbc sql server driver",
            "microsoft odbc"
    };

    private final HttpFetcher fetcher;

    public ActiveAnalyzer(HttpFetcher fetcher) {
        this.fetcher = fetcher;
    }

    /**
     * Runs the probes against query parameters of already-crawled pages.
     *
     * @throws IllegalStateException when authorization was not confirmed
     */
    public List<Alert> analyze(URI target, List<FetchResult> pages, boolean authorized,
                               BooleanSupplier cancelled, ScanProgress progress) {
        if (!authorized) {
            throw new IllegalStateException("Active scanning requires explicit authorization for the target");
        }
        List<Alert> out = new ArrayList<>();
        if (pages == null || pages.isEmpty()) {
            return out;
        }
        ScanProgress p = progress == null ? ScanProgress.NONE : progress;

        for (String[] pair : collectParams(pages)) {
            if (cancelled != null && cancelled.getAsBoolean()) {
                break;
            }
            URI base;
            try {
                base = URI.create(pair[0]);
            } catch (IllegalArgumentException e) {
                continue;
            }
            if (!Uris.sameOrigin(target, base)) {
                continue;
            }
            String param = pair[1];
            p.onStatus("Active probe: " + pair[0] + " [" + param + "]");
            probeReflectedXss(base, param, out);
            probeSqlInjection(base, param, out);
            probePathTraversal(base, param, out);
        }
        return out;
    }

    private void probeReflectedXss(URI base, String param, List<Alert> out) {
        FetchResult response = get(base, param, XSS_PAYLOAD);
        if (response == null) {
            return;
        }
        String body = response.getBody();
        int idx = body.indexOf(XSS_PAYLOAD);
        if (idx < 0) {
            return;
        }
        out.add(new Alert(
                "Reflected cross-site scripting (query parameter)",
                Risk.HIGH,
                Confidence.MEDIUM,
                base.toString(),
                param,
                snippet(body, idx, XSS_PAYLOAD.length()),
                "The value supplied for this parameter is reflected in the response body without HTML encoding, so an attacker can inject script that runs in the victim's browser.",
                "HTML-encode all untrusted input before embedding it in the response, and deploy a Content-Security-Policy as defence in depth."));
    }

    private void probeSqlInjection(URI base, String param, List<Alert> out) {
        FetchResult response = get(base, param, SQLI_PAYLOAD);
        if (response == null) {
            return;
        }
        String body = response.getBody();
        String lower = body.toLowerCase(Locale.ROOT);
        for (String marker : SQL_ERROR_MARKERS) {
            int idx = lower.indexOf(marker);
            if (idx < 0) {
                continue;
            }
            out.add(new Alert(
                    "SQL injection (error-based)",
                    Risk.HIGH,
                    Confidence.MEDIUM,
                    base.toString(),
                    param,
                    snippet(body, idx, marker.length()),
                    "Appending a single quote to this parameter made the application return a database error message, which suggests user input reaches a SQL query unsanitised.",
                    "Use parameterised queries or prepared statements for every database access, and avoid returning raw database errors to clients."));
            return;
        }
    }

    private void probePathTraversal(URI base, String param, List<Alert> out) {
        FetchResult response = get(base, param, TRAVERSAL_PAYLOAD);
        if (response == null) {
            return;
        }
        String body = response.getBody();
        int idx = body.indexOf("root:x:0:0");
        if (idx < 0) {
            return;
        }
        out.add(new Alert(
                "Path traversal via query parameter",
                Risk.HIGH,
                Confidence.MEDIUM,
                base.toString(),
                param,
                snippet(body, idx, "root:x:0:0".length()),
                "A '../' sequence in this parameter made the server disclose the contents of /etc/passwd, which indicates an unchecked file path.",
                "Canonicalise and validate file paths server side, and never build paths from raw user input."));
    }

    private FetchResult get(URI base, String param, String value) {
        URI target = withParam(base, param, value);
        if (target == null) {
            return null;
        }
        try {
            return fetcher.fetch(target);
        } catch (FetchException e) {
            return null;
        }
    }

    /** A copy of the URL with the given parameter replaced by the payload. */
    static URI withParam(URI base, String param, String value) {
        try {
            String full = Uris.stripFragment(base.toString());
            String query = base.getRawQuery();
            String encodedValue = URLEncoder.encode(value, StandardCharsets.UTF_8);
            StringBuilder newQuery = new StringBuilder();
            boolean found = false;
            if (query != null && !query.isEmpty()) {
                for (String pair : query.split("&")) {
                    if (pair.isEmpty()) {
                        continue;
                    }
                    if (newQuery.length() > 0) {
                        newQuery.append('&');
                    }
                    int eq = pair.indexOf('=');
                    String name = eq >= 0 ? pair.substring(0, eq) : pair;
                    if (name.equals(param)) {
                        newQuery.append(name).append('=').append(encodedValue);
                        found = true;
                    } else {
                        newQuery.append(pair);
                    }
                }
            }
            if (!found) {
                if (newQuery.length() > 0) {
                    newQuery.append('&');
                }
                newQuery.append(param).append('=').append(encodedValue);
            }
            int q = full.indexOf('?');
            String head = q >= 0 ? full.substring(0, q) : full;
            return URI.create(head + "?" + newQuery);
        } catch (IllegalArgumentException e) {
            return null;
        }
    }

    /** Up to {@link #MAX_PARAMS} distinct (url, parameter) pairs from the crawl. */
    static List<String[]> collectParams(List<FetchResult> pages) {
        List<String[]> out = new ArrayList<>();
        Set<String> seen = new LinkedHashSet<>();
        for (FetchResult page : pages) {
            URI uri = page.getUri();
            String rawQuery = uri.getRawQuery();
            if (rawQuery == null || rawQuery.isEmpty()) {
                continue;
            }
            String url = Uris.stripFragment(uri.toString());
            for (String pair : rawQuery.split("&")) {
                if (pair.isEmpty()) {
                    continue;
                }
                int eq = pair.indexOf('=');
                String name = eq >= 0 ? pair.substring(0, eq) : pair;
                if (name.isEmpty()) {
                    continue;
                }
                if (!seen.add(url + "\n" + name)) {
                    continue;
                }
                out.add(new String[] {url, name});
                if (out.size() >= MAX_PARAMS) {
                    return out;
                }
            }
        }
        return out;
    }

    private static String snippet(String body, int idx, int length) {
        int from = Math.max(0, idx - 30);
        int to = Math.min(body.length(), idx + length + 30);
        String cut = body.substring(from, to).replaceAll("\\s+", " ").trim();
        return cut.length() > 120 ? cut.substring(0, 120) + "..." : cut;
    }
}
