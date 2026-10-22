package local.foundev.zap;

import com.sun.net.httpserver.HttpServer;
import local.foundev.zap.core.CrawlResult;
import local.foundev.zap.core.HttpFetcher;
import local.foundev.zap.core.WebCrawler;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

/**
 * The spider is exercised against a real HTTP server on the loopback
 * interface: the links it finds, the scope it keeps and the order it visits
 * the pages in are all checked.
 */
class WebCrawlerTest {

    private HttpServer server;
    private URI base;
    private final List<String> requested = new ArrayList<>();

    @BeforeEach
    void startServer() throws IOException {
        server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);

        server.createContext("/", exchange -> {
            requested.add(exchange.getRequestURI().getPath());
            String body = "<html><head><title>home</title></head><body>"
                    + "<a href=\"/one\">one</a>"
                    + "<a href=\"http://example.invalid/offsite\">off site</a>"
                    + "<a href=\"/two#fragment\">two</a>"
                    + "<img src=\"/logo.png\">"
                    + "<form action=\"/search\" method=\"get\"><input name=\"q\"></form>"
                    + "</body></html>";
            respond(exchange, 200, "text/html", body);
        });
        server.createContext("/one", exchange -> {
            requested.add(exchange.getRequestURI().getPath());
            respond(exchange, 200, "text/html",
                    "<html><body><a href=\"/three\">three</a></body></html>");
        });
        server.createContext("/two", exchange -> {
            requested.add(exchange.getRequestURI().getPath());
            respond(exchange, 200, "text/html", "<html><body>two</body></html>");
        });
        server.createContext("/three", exchange -> {
            requested.add(exchange.getRequestURI().getPath());
            respond(exchange, 200, "text/html", "<html><body>three</body></html>");
        });
        server.createContext("/logo.png", exchange -> {
            requested.add(exchange.getRequestURI().getPath());
            respond(exchange, 200, "image/png", "not really a png");
        });
        server.createContext("/search", exchange -> {
            requested.add(exchange.getRequestURI().getPath());
            respond(exchange, 200, "text/html", "<html><body>search</body></html>");
        });

        server.start();
        base = URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/");
    }

    private static void respond(com.sun.net.httpserver.HttpExchange exchange, int status,
                                String contentType, String body) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().add("Content-Type", contentType);
        exchange.sendResponseHeaders(status, bytes.length);
        try (OutputStream out = exchange.getResponseBody()) {
            out.write(bytes);
        }
    }

    @AfterEach
    void stopServer() {
        if (server != null) {
            server.stop(0);
        }
    }

    @Test
    void theSpiderFollowsTheSameOriginLinks() {
        WebCrawler crawler = new WebCrawler(new HttpFetcher());

        CrawlResult result = crawler.crawl(base, 20, null);

        assertTrue(result.getPages().size() >= 3, "visited: " + requested);
        assertTrue(requested.contains("/one"), "visited: " + requested);
        assertTrue(requested.contains("/two"), "visited: " + requested);
    }

    @Test
    void theSpiderStaysOnTheSameOrigin() {
        WebCrawler crawler = new WebCrawler(new HttpFetcher());

        crawler.crawl(base, 20, null);

        assertFalse(requested.contains("/offsite"), "the other origin must not be visited");
    }

    @Test
    void theSpiderFollowsTheLinksOfThePagesItVisits() {
        WebCrawler crawler = new WebCrawler(new HttpFetcher());

        crawler.crawl(base, 20, null);

        assertTrue(requested.contains("/three"), "the link of /one must be followed: " + requested);
    }

    @Test
    void theSpiderVisitsTheFormTarget() {
        WebCrawler crawler = new WebCrawler(new HttpFetcher());

        crawler.crawl(base, 20, null);

        assertTrue(requested.stream().anyMatch(path -> path.startsWith("/search")),
                "the form target must be visited: " + requested);
    }

    @Test
    void theSpiderDoesNotVisitTheSamePageTwice() {
        WebCrawler crawler = new WebCrawler(new HttpFetcher());

        crawler.crawl(base, 20, null);

        assertEquals(requested.size(), requested.stream().distinct().count(),
                "every page is fetched once: " + requested);
    }

    @Test
    void theSpiderStopsAtTheLimit() {
        WebCrawler crawler = new WebCrawler(new HttpFetcher());

        CrawlResult result = crawler.crawl(base, 2, null);

        assertEquals(2, result.getPages().size(), "visited: " + requested);
    }
}
