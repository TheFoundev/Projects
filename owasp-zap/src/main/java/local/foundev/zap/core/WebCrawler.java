package local.foundev.zap.core;

import java.net.URI;
import java.util.ArrayDeque;
import java.util.ArrayList;
import java.util.Deque;
import java.util.HashSet;
import java.util.List;
import java.util.Locale;
import java.util.Set;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Same-origin, breadth-first HTTP spider. It discovers href/src links and
 * enqueues GET form targets (named inputs appended as empty query values).
 * Every request it makes is a plain GET.
 */
public final class WebCrawler {

    // The fragment is part of the value: it is stripped when the link is
    // resolved, so a link with a fragment is followed like any other one.
    private static final Pattern LINK =
            Pattern.compile("(?i)(?:href|src)\\s*=\\s*[\"']([^\"']+)[\"']");
    private static final Pattern FORM_BLOCK =
            Pattern.compile("(?is)<form\\b([^>]*)>(.*?)</form>");
    private static final Pattern FORM_ACTION =
            Pattern.compile("(?i)action\\s*=\\s*[\"']([^\"']*)[\"']");
    private static final Pattern FORM_METHOD =
            Pattern.compile("(?i)method\\s*=\\s*[\"']([^\"']*)[\"']");
    private static final Pattern INPUT_NAME =
            Pattern.compile("(?i)<(?:input|select|textarea)\\b[^>]*\\bname\\s*=\\s*[\"']([^\"']+)");

    private final HttpFetcher fetcher;
    private volatile boolean stopRequested;

    public WebCrawler(HttpFetcher fetcher) {
        this.fetcher = fetcher;
    }

    /** Ask the crawl loop to finish once the request in flight returns. */
    public void stop() {
        stopRequested = true;
    }

    public CrawlResult crawl(URI start, int maxPages, CrawlListener listener) {
        CrawlListener l = listener == null ? CrawlListener.NONE : listener;
        List<FetchResult> pages = new ArrayList<>();
        Set<String> seen = new HashSet<>();
        Deque<String> queue = new ArrayDeque<>();

        String startUrl = Uris.stripFragment(start.toString());
        seen.add(startUrl);
        queue.add(startUrl);
        int fetched = 0;
        int limit = Math.max(1, maxPages);

        while (!queue.isEmpty() && fetched < limit && !stopRequested) {
            String url = queue.poll();

            FetchResult page;
            try {
                page = fetcher.fetch(URI.create(url));
            } catch (FetchException e) {
                l.error(url, e.getMessage());
                continue;
            } catch (IllegalArgumentException e) {
                l.error(url, "unusable URL: " + e.getMessage());
                continue;
            }

            fetched++;
            pages.add(page);
            l.pageCrawled(page, fetched, queue.size());

            if (!page.isHtml()) {
                continue;
            }
            for (String link : extractLinks(page, start)) {
                if (seen.add(link)) {
                    l.linkDiscovered(link, url);
                    queue.add(link);
                }
            }
        }
        return new CrawlResult(pages, stopRequested);
    }

    /** Absolute, fragment-free, same-origin URLs found in one HTML page. */
    private List<String> extractLinks(FetchResult page, URI origin) {
        List<String> out = new ArrayList<>();

        Matcher links = LINK.matcher(page.getBody());
        while (links.find()) {
            addIfUsable(out, page.getUri(), links.group(1).trim(), origin);
        }

        Matcher forms = FORM_BLOCK.matcher(page.getBody());
        while (forms.find()) {
            String attrs = forms.group(1);
            String inner = forms.group(2);

            String action = "";
            Matcher actionMatcher = FORM_ACTION.matcher(attrs);
            if (actionMatcher.find()) {
                action = actionMatcher.group(1).trim();
            }
            String method = "get";
            Matcher methodMatcher = FORM_METHOD.matcher(attrs);
            if (methodMatcher.find()) {
                method = methodMatcher.group(1).trim().toLowerCase(Locale.ROOT);
            }

            URI resolved;
            try {
                resolved = action.isEmpty() ? page.getUri() : page.getUri().resolve(action);
            } catch (IllegalArgumentException e) {
                continue;
            }
            if (!Uris.sameOrigin(origin, resolved)) {
                continue;
            }
            String target = Uris.stripFragment(resolved.toString());
            if (!"post".equals(method)) {
                String params = inputNames(inner);
                if (!params.isEmpty()) {
                    target = target + (target.indexOf('?') >= 0 ? "&" : "?") + params;
                }
            }
            try {
                URI.create(target);
            } catch (IllegalArgumentException e) {
                continue;
            }
            if (!out.contains(target)) {
                out.add(target);
            }
        }
        return out;
    }

    private static void addIfUsable(List<String> out, URI base, String raw, URI origin) {
        if (raw.isEmpty()) {
            return;
        }
        String lower = raw.toLowerCase(Locale.ROOT);
        if (lower.startsWith("javascript:") || lower.startsWith("mailto:")
                || lower.startsWith("tel:") || lower.startsWith("data:")
                || lower.startsWith("about:") || lower.startsWith("file:")) {
            return;
        }
        URI resolved;
        try {
            resolved = base.resolve(raw);
        } catch (IllegalArgumentException e) {
            return;
        }
        if (!Uris.sameOrigin(origin, resolved)) {
            return;
        }
        String url = Uris.stripFragment(resolved.toString());
        if (!out.contains(url)) {
            out.add(url);
        }
    }

    /** "a=&b=&c=" from the named inputs of one form; empty when none are named. */
    private static String inputNames(String formInner) {
        StringBuilder sb = new StringBuilder();
        Matcher m = INPUT_NAME.matcher(formInner);
        while (m.find()) {
            String name = m.group(1).trim();
            if (name.isEmpty()) {
                continue;
            }
            if (sb.length() > 0) {
                sb.append('&');
            }
            sb.append(name).append('=');
        }
        return sb.toString();
    }
}
