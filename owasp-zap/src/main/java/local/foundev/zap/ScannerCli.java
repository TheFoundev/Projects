package local.foundev.zap;

import local.foundev.zap.core.ScanEngine;
import local.foundev.zap.core.ScanProgress;
import local.foundev.zap.core.ScanSummary;
import local.foundev.zap.model.Alert;
import local.foundev.zap.model.AlertStore;
import local.foundev.zap.report.HtmlReportWriter;
import local.foundev.zap.report.JsonReportWriter;

import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/**
 * Headless entry point: crawl, passive checks, optional authorized active
 * checks, then print the alerts and optionally export the reports.
 */
public final class ScannerCli {

    private ScannerCli() {
    }

    public static void main(String[] args) {
        System.exit(run(args));
    }

    private static int run(String[] args) {
        String url = null;
        boolean active = false;
        boolean authorized = false;
        int maxPages = ScanEngine.DEFAULT_MAX_PAGES;
        Path htmlOut = null;
        Path jsonOut = null;

        for (int i = 0; i < args.length; i++) {
            String arg = args[i];
            switch (arg) {
                case "--help":
                case "-h":
                    printUsage();
                    return 0;
                case "--active":
                    active = true;
                    break;
                case "--authorized":
                    authorized = true;
                    break;
                case "--max-pages":
                    if (i + 1 >= args.length) {
                        System.err.println("--max-pages needs a value.");
                        return 2;
                    }
                    try {
                        maxPages = Integer.parseInt(args[++i]);
                    } catch (NumberFormatException e) {
                        System.err.println("Invalid --max-pages value: " + args[i]);
                        return 2;
                    }
                    break;
                case "--html":
                    if (i + 1 >= args.length) {
                        System.err.println("--html needs a file path.");
                        return 2;
                    }
                    htmlOut = Path.of(args[++i]);
                    break;
                case "--json":
                    if (i + 1 >= args.length) {
                        System.err.println("--json needs a file path.");
                        return 2;
                    }
                    jsonOut = Path.of(args[++i]);
                    break;
                default:
                    if (arg.startsWith("--")) {
                        System.err.println("Unknown option: " + arg);
                        printUsage();
                        return 2;
                    }
                    if (url != null) {
                        System.err.println("Only one target URL may be given.");
                        return 2;
                    }
                    url = arg;
            }
        }

        if (url == null) {
            printUsage();
            return 2;
        }
        if (active && !authorized) {
            System.err.println("Active checks refused: pass --authorized to confirm you are "
                    + "permitted to actively test this target.");
            return 2;
        }
        URI target;
        try {
            target = URI.create(url);
        } catch (IllegalArgumentException e) {
            System.err.println("Invalid URL: " + url);
            return 2;
        }
        String scheme = target.getScheme();
        if (scheme == null || target.getHost() == null
                || (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme))) {
            System.err.println("The target must be an http:// or https:// URL.");
            return 2;
        }

        ScanProgress progress = new ScanProgress() {
            @Override
            public void onStatus(String message) {
                System.out.println("[scan] " + message);
            }

            @Override
            public void onLink(String url, String parentUrl) {
                System.out.println("[link] " + url);
            }

            @Override
            public void onFinished(ScanSummary summary) {
            }
        };

        System.out.println("Target        : " + target);
        System.out.println("Active checks : " + (active ? "yes (authorized confirmed)" : "no (pass --active --authorized)"));

        AlertStore store = new AlertStore();
        ScanEngine engine = new ScanEngine(store);
        ScanSummary summary = engine.run(target, active, maxPages, progress);

        List<Alert> sorted = new ArrayList<>(store.snapshot());
        sorted.sort(Comparator.comparingInt((Alert a) -> a.getRisk().ordinal()).reversed()
                .thenComparing(Alert::getName, String.CASE_INSENSITIVE_ORDER));

        System.out.println();
        if (sorted.isEmpty()) {
            System.out.println("No alerts.");
        } else {
            System.out.println(String.format("%-14s %-11s %-42.42s %s", "RISK", "CONFIDENCE", "ALERT", "URL"));
            for (Alert a : sorted) {
                System.out.println(String.format("%-14s %-11s %-42.42s %s",
                        a.getRisk().label(), a.getConfidence().label(), a.getName(), a.getUrl()));
            }
        }
        System.out.println();

        try {
            if (htmlOut != null) {
                Files.writeString(htmlOut, HtmlReportWriter.render(target.toString(), store.snapshot()),
                        StandardCharsets.UTF_8);
                System.out.println("HTML report   : " + htmlOut);
            }
            if (jsonOut != null) {
                Files.writeString(jsonOut, JsonReportWriter.render(target.toString(), store.snapshot()),
                        StandardCharsets.UTF_8);
                System.out.println("JSON report   : " + jsonOut);
            }
        } catch (IOException e) {
            System.err.println("Failed to write a report: " + e.getMessage());
            return 1;
        }

        System.out.println();
        System.out.println("Pages crawled : " + summary.getPagesCrawled());
        System.out.println("Alerts        : " + summary.getAlertCount());
        System.out.println("Active checks : " + (summary.isActiveRan() ? "ran" : "skipped"));
        System.out.println("Elapsed       : " + summary.getElapsedMillis() + " ms");

        if (summary.getPagesCrawled() == 0) {
            System.err.println("No pages could be fetched; check the target URL and that the host is reachable.");
            return 1;
        }
        return 0;
    }

    private static void printUsage() {
        System.out.println("Usage: java -jar owasp-zap-0.1.0.jar cli <url> [options]");
        System.out.println();
        System.out.println("Options:");
        System.out.println("  --active          run the active probes (requires --authorized)");
        System.out.println("  --authorized      confirm you are authorized to actively test the target");
        System.out.println("  --max-pages <n>   crawl limit (default " + ScanEngine.DEFAULT_MAX_PAGES + ")");
        System.out.println("  --html <file>     write an HTML alert report");
        System.out.println("  --json <file>     write a JSON alert report");
        System.out.println("  --help            show this help");
        System.out.println();
        System.out.println("Only scan systems you own or have explicit written permission to test.");
    }
}
