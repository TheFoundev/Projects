package local.foundev.zap;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Confidence;
import local.foundev.zap.model.Risk;
import local.foundev.zap.report.HtmlReportWriter;
import local.foundev.zap.report.JsonReportWriter;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertTrue;

class ReportExportTest {

    private static final List<Alert> FIXTURE = List.of(
            new Alert(
                    "Reflected cross-site scripting (query parameter)",
                    Risk.HIGH,
                    Confidence.MEDIUM,
                    "https://shop.example.test/search?q=<script>",
                    "q",
                    "<script>alert(\"1\")</script>",
                    "User input is reflected unencoded.",
                    "HTML-encode all untrusted output."),
            new Alert(
                    "Content-Security-Policy header not set",
                    Risk.LOW,
                    Confidence.HIGH,
                    "https://shop.example.test/",
                    "",
                    "",
                    "No CSP header is set.",
                    "Define a Content-Security-Policy."));

    @Test
    void jsonReportContainsEscapedAlertData() {
        String json = JsonReportWriter.render("https://shop.example.test/", FIXTURE);

        assertTrue(json.startsWith("{"), json);
        assertTrue(json.contains("\"tool\""), json);
        assertTrue(json.contains("\"target\": \"https://shop.example.test/\""), json);
        assertTrue(json.contains("\"alerts\""), json);
        assertTrue(json.contains("\"risk\": \"HIGH\""), json);
        assertTrue(json.contains("\"high\": 1"), json);
        assertTrue(json.contains("<script>alert(\\\"1\\\")</script>"), json);
        assertFalse(json.contains("alert(\"1\")"), "quotes must be escaped: " + json);
        assertTrue(json.trim().endsWith("}"), json);
    }

    @Test
    void htmlReportEscapesMarkupAndRanksRiskFirst() {
        String html = HtmlReportWriter.render("https://shop.example.test/", FIXTURE);

        assertTrue(html.contains("<!DOCTYPE html>"), html);
        assertTrue(html.contains("Security assessment report"), html);
        assertTrue(html.contains("risk-HIGH"), html);
        assertTrue(html.contains("&lt;script&gt;"), html);
        assertFalse(html.contains("<script>alert"), "markup from evidence must be escaped");

        int highFirst = html.indexOf("Reflected cross-site scripting (query parameter)");
        int lowSecond = html.indexOf("Content-Security-Policy header not set");
        assertTrue(highFirst >= 0, html);
        assertTrue(lowSecond >= 0, html);
        assertTrue(highFirst < lowSecond, "the high risk alert should be listed before the low risk one");
        assertTrue(html.trim().endsWith("</html>"), html);
    }
}
