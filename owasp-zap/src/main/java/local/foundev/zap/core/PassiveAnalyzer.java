package local.foundev.zap.core;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Confidence;
import local.foundev.zap.model.Risk;

import java.util.ArrayList;
import java.util.List;
import java.util.Locale;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Passive checks: nothing is sent beyond the request that was already made to
 * fetch the page. Everything is inferred from the response as received.
 */
public final class PassiveAnalyzer {

    private static final Pattern INSECURE_RESOURCE =
            Pattern.compile("(?i)(?:src|href)\\s*=\\s*[\"']http://[^\"']+[\"']");

    public List<Alert> analyze(FetchResult page) {
        List<Alert> out = new ArrayList<>();
        String url = page.getUri().toString();
        String body = page.getBody();
        boolean https = "https".equalsIgnoreCase(page.getUri().getScheme());

        if (page.isHtml()) {
            if (isBlank(page.header("Content-Security-Policy"))) {
                out.add(new Alert(
                        "Content-Security-Policy header not set",
                        Risk.LOW,
                        Confidence.MEDIUM,
                        url,
                        "",
                        "",
                        "The response does not carry a Content-Security-Policy header, so the browser places no restriction on script origins, inline script or frame sources.",
                        "Define a Content-Security-Policy that whitelists the required script, style and frame origins; prefer nonces or hashes over 'unsafe-inline'."));
            }
            if (isBlank(page.header("X-Frame-Options")) && !hasFrameAncestors(page.header("Content-Security-Policy"))) {
                out.add(new Alert(
                        "X-Frame-Options header not set",
                        Risk.LOW,
                        Confidence.MEDIUM,
                        url,
                        "",
                        "",
                        "The page can be embedded in a frame on another origin, which enables clickjacking.",
                        "Set X-Frame-Options: DENY (or SAMEORIGIN), or declare frame-ancestors in the Content-Security-Policy header."));
            }
            if (isBlank(page.header("X-Content-Type-Options"))) {
                out.add(new Alert(
                        "X-Content-Type-Options header not set",
                        Risk.INFORMATIONAL,
                        Confidence.MEDIUM,
                        url,
                        "",
                        "",
                        "Without nosniff the browser may reinterpret a response as a different content type (MIME sniffing).",
                        "Set X-Content-Type-Options: nosniff on all responses."));
            }
        }

        if (https && isBlank(page.header("Strict-Transport-Security"))) {
            out.add(new Alert(
                    "Strict-Transport-Security header not set",
                    Risk.MEDIUM,
                    Confidence.MEDIUM,
                    url,
                    "",
                    "",
                    "The HTTPS response does not enable HSTS, so the first visit (or a downgrade) can be intercepted before the browser knows to force HTTPS.",
                    "Set Strict-Transport-Security: max-age=31536000; includeSubDomains on the HTTPS site."));
        }

        String server = page.header("Server");
        if (!isBlank(server)) {
            out.add(new Alert(
                    "Server banner disclosed",
                    Risk.INFORMATIONAL,
                    Confidence.HIGH,
                    url,
                    "",
                    server,
                    "The Server header discloses the web server product and version, which helps an attacker match it against known vulnerabilities.",
                    "Suppress or genericise the Server header; do not advertise exact software versions."));
        }

        String poweredBy = page.header("X-Powered-By");
        if (!isBlank(poweredBy)) {
            out.add(new Alert(
                    "X-Powered-By banner disclosed",
                    Risk.INFORMATIONAL,
                    Confidence.HIGH,
                    url,
                    "",
                    poweredBy,
                    "The X-Powered-By header discloses the framework or runtime behind the application.",
                    "Remove the X-Powered-By header (e.g. disable the Express 'x-powered-by' option or the ASP.NET Server header)."));
        }

        for (String cookie : page.headers("Set-Cookie")) {
            analyzeCookie(out, url, cookie);
        }

        if (page.isHtml() && body.toLowerCase(Locale.ROOT).contains("index of /")) {
            out.add(new Alert(
                    "Directory listing enabled",
                    Risk.MEDIUM,
                    Confidence.HIGH,
                    url,
                    "",
                    "index of /",
                    "The server renders a directory index, disclosing file names and structure to anyone who requests the folder.",
                    "Disable directory listing in the web server configuration, or place an empty index file in every browsable directory."));
        }

        if (https && page.isHtml()) {
            Matcher m = INSECURE_RESOURCE.matcher(body);
            if (m.find()) {
                out.add(new Alert(
                        "Mixed content: insecure resource on HTTPS page",
                        Risk.MEDIUM,
                        Confidence.HIGH,
                        url,
                        "",
                        m.group(),
                        "The page is served over HTTPS but embeds resources over plain HTTP, which can be tampered with in transit.",
                        "Reference every embedded resource with https:// URLs, or use protocol-relative URLs sparingly."));
            }
        }
        return out;
    }

    private static void analyzeCookie(List<Alert> out, String url, String cookie) {
        if (isBlank(cookie)) {
            return;
        }
        // RFC 6265: the name/value pair ends at the first ';', the attributes
        // follow it. Splitting the whole header would read a value that
        // contains a ';' as if it were an attribute.
        String pair = cookie;
        String attributePart = "";
        int separator = cookie.indexOf(';');
        if (separator >= 0) {
            pair = cookie.substring(0, separator);
            attributePart = cookie.substring(separator + 1);
        }
        int equals = pair.indexOf('=');
        String name = (equals >= 0 ? pair.substring(0, equals) : pair).trim();
        boolean secure = false;
        boolean httpOnly = false;
        boolean sameSite = false;
        for (String part : attributePart.split(";")) {
            String flag = part.trim();
            if (flag.equalsIgnoreCase("Secure")) {
                secure = true;
            } else if (flag.equalsIgnoreCase("HttpOnly")) {
                httpOnly = true;
            } else if (flag.toLowerCase(Locale.ROOT).startsWith("samesite")) {
                sameSite = true;
            }
        }
        String evidence = cookie.length() > 120 ? cookie.substring(0, 120) + "..." : cookie;

        if (!secure) {
            out.add(new Alert(
                    "Cookie '" + name + "' missing Secure flag",
                    Risk.MEDIUM,
                    Confidence.HIGH,
                    url,
                    name,
                    evidence,
                    "The Secure flag is absent, so the cookie is also sent over unencrypted connections and can be intercepted.",
                    "Set the Secure attribute on cookies that must never travel over plain HTTP."));
        }
        if (!httpOnly) {
            out.add(new Alert(
                    "Cookie '" + name + "' missing HttpOnly flag",
                    Risk.MEDIUM,
                    Confidence.HIGH,
                    url,
                    name,
                    evidence,
                    "The HttpOnly flag is absent, so the cookie is readable from JavaScript (document.cookie), which increases the impact of any XSS.",
                    "Set the HttpOnly attribute on session and authentication cookies."));
        }
        if (!sameSite) {
            out.add(new Alert(
                    "Cookie '" + name + "' missing SameSite attribute",
                    Risk.LOW,
                    Confidence.HIGH,
                    url,
                    name,
                    evidence,
                    "No SameSite attribute is set, so the cookie is attached to cross-site requests and the session is exposed to CSRF.",
                    "Set SameSite=Lax (or Strict where compatible) on cookies."));
        }
    }

    private static boolean hasFrameAncestors(String csp) {
        return csp != null && csp.toLowerCase(Locale.ROOT).contains("frame-ancestors");
    }

    private static boolean isBlank(String s) {
        return s == null || s.trim().isEmpty();
    }
}
