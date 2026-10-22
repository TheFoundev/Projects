package local.foundev.zap.core;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.nio.charset.StandardCharsets;
import java.time.Duration;

/**
 * Thin wrapper around {@link java.net.http.HttpClient}: fixed timeouts, a
 * honest user agent, redirects followed, bodies truncated for analysis.
 */
public final class HttpFetcher {

    public static final String USER_AGENT = "Foundev-Zap/0.1 (authorised security testing)";

    /** Bodies are cut here to keep very large downloads from exhausting memory. */
    private static final int MAX_BODY_CHARS = 512 * 1024;

    private final HttpClient client;

    public HttpFetcher() {
        client = HttpClient.newBuilder()
                .followRedirects(HttpClient.Redirect.NORMAL)
                .connectTimeout(Duration.ofSeconds(10))
                .build();
    }

    public FetchResult fetch(URI uri) throws FetchException {
        HttpRequest request = HttpRequest.newBuilder(uri)
                .timeout(Duration.ofSeconds(15))
                .header("User-Agent", USER_AGENT)
                .header("Accept", "text/html,application/xhtml+xml,*/*;q=0.8")
                .GET()
                .build();
        try {
            HttpResponse<String> response =
                    client.send(request, HttpResponse.BodyHandlers.ofString(StandardCharsets.UTF_8));
            String body = response.body() == null ? "" : response.body();
            if (body.length() > MAX_BODY_CHARS) {
                body = body.substring(0, MAX_BODY_CHARS);
            }
            URI effective = response.uri() != null ? response.uri() : uri;
            return new FetchResult(effective, response.statusCode(), response.headers().map(), body);
        } catch (IOException e) {
            throw new FetchException("request failed: " + e, e);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new FetchException("interrupted while fetching", e);
        }
    }
}
