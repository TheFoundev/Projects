package local.foundev.zap.core;

import java.net.URI;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;

/**
 * Immutable view of one HTTP response: final URI (after redirects), status
 * code, case-insensitive headers and the (possibly truncated) body.
 */
public final class FetchResult {

    private final URI uri;
    private final int statusCode;
    private final Map<String, List<String>> headersByLowerName;
    private final String body;

    public FetchResult(URI uri, int statusCode, Map<String, List<String>> headers, String body) {
        this.uri = uri;
        this.statusCode = statusCode;
        this.headersByLowerName = new LinkedHashMap<>();
        if (headers != null) {
            for (Map.Entry<String, List<String>> entry : headers.entrySet()) {
                if (entry.getKey() == null) {
                    continue;
                }
                String key = entry.getKey().toLowerCase(Locale.ROOT);
                List<String> bucket = headersByLowerName.computeIfAbsent(key, k -> new ArrayList<>());
                if (entry.getValue() != null) {
                    bucket.addAll(entry.getValue());
                }
            }
        }
        this.body = body == null ? "" : body;
    }

    /** The URI the response was actually served from (after redirects). */
    public URI getUri() {
        return uri;
    }

    public int getStatusCode() {
        return statusCode;
    }

    /** First value of the header, looked up case-insensitively, or null. */
    public String header(String name) {
        List<String> values = headers(name);
        return values.isEmpty() ? null : values.get(0);
    }

    /** All values of the header, looked up case-insensitively, never null. */
    public List<String> headers(String name) {
        if (name == null) {
            return List.of();
        }
        List<String> values = headersByLowerName.get(name.toLowerCase(Locale.ROOT));
        return values == null ? List.of() : values;
    }

    public String getBody() {
        return body;
    }

    public boolean isHtml() {
        String contentType = header("Content-Type");
        return contentType != null && contentType.toLowerCase(Locale.ROOT).contains("text/html");
    }
}
