package local.foundev.zap.core;

import java.net.URI;

/** Small URI helpers shared by the spider and the active checks. */
public final class Uris {

    private Uris() {
    }

    /** Removes the fragment part of a URL; fragments never change a request. */
    public static String stripFragment(String url) {
        if (url == null) {
            return "";
        }
        int hash = url.indexOf('#');
        return hash >= 0 ? url.substring(0, hash) : url;
    }

    /** True when both URIs share scheme, host and effective port over http(s). */
    public static boolean sameOrigin(URI a, URI b) {
        if (a == null || b == null) {
            return false;
        }
        String schemeA = a.getScheme();
        String schemeB = b.getScheme();
        if (schemeA == null || schemeB == null || !schemeA.equalsIgnoreCase(schemeB)) {
            return false;
        }
        if (!"http".equalsIgnoreCase(schemeA) && !"https".equalsIgnoreCase(schemeA)) {
            return false;
        }
        String hostA = a.getHost();
        String hostB = b.getHost();
        if (hostA == null || hostB == null || !hostA.equalsIgnoreCase(hostB)) {
            return false;
        }
        return portOf(a) == portOf(b);
    }

    /** The explicit port, or the scheme default (80/443). */
    public static int portOf(URI uri) {
        int port = uri.getPort();
        if (port != -1) {
            return port;
        }
        String scheme = uri.getScheme();
        if (scheme == null) {
            return -1;
        }
        if ("http".equalsIgnoreCase(scheme)) {
            return 80;
        }
        if ("https".equalsIgnoreCase(scheme)) {
            return 443;
        }
        return -1;
    }
}
