package local.foundev.zap.report;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Risk;

import java.time.Instant;
import java.util.List;

/** Renders the alert store as a self-contained HTML report page. */
public final class HtmlReportWriter {

    private HtmlReportWriter() {
    }

    public static String render(String target, List<Alert> alerts) {
        List<Alert> sorted = ReportSupport.sorted(alerts);
        StringBuilder sb = new StringBuilder(8192);

        sb.append("<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n");
        sb.append("<meta charset=\"utf-8\">\n");
        sb.append("<title>Security assessment report</title>\n");
        sb.append("<style>\n");
        sb.append("body{font-family:Segoe UI,Helvetica,Arial,sans-serif;margin:2rem;color:#1c2733;background:#f6f8fa;}\n");
        sb.append("h1{font-size:1.5rem;}\n");
        sb.append(".meta{color:#57606a;}\n");
        sb.append("table{border-collapse:collapse;width:100%;background:#fff;}\n");
        sb.append("th,td{border:1px solid #d8dee4;padding:.5rem .6rem;text-align:left;vertical-align:top;font-size:.9rem;}\n");
        sb.append("th{background:#eaeef2;}\n");
        sb.append(".risk{font-weight:600;text-align:center;white-space:nowrap;}\n");
        sb.append(".risk-HIGH{background:#ffd6d6;color:#8b0000;}\n");
        sb.append(".risk-MEDIUM{background:#ffe9c8;color:#7a4b00;}\n");
        sb.append(".risk-LOW{background:#fff6c9;color:#6b5b00;}\n");
        sb.append(".risk-INFORMATIONAL{background:#dbe9ff;color:#0b3d91;}\n");
        sb.append(".summary span{display:inline-block;margin-right:1rem;padding:.2rem .6rem;border-radius:.6rem;}\n");
        sb.append("</style>\n</head>\n<body>\n");

        sb.append("<h1>Security assessment report</h1>\n");
        sb.append("<p class=\"meta\">Target: ").append(ReportSupport.htmlEscape(target));
        sb.append("<br>Generated: ").append(ReportSupport.htmlEscape(Instant.now().toString()));
        sb.append("<br>Tool: ").append(ReportSupport.htmlEscape(JsonReportWriter.TOOL_NAME));
        sb.append(" &mdash; authorised testing only</p>\n");

        sb.append("<p class=\"summary\">");
        sb.append("<span class=\"risk risk-HIGH\">High: ").append(ReportSupport.count(sorted, Risk.HIGH)).append("</span>");
        sb.append("<span class=\"risk risk-MEDIUM\">Medium: ").append(ReportSupport.count(sorted, Risk.MEDIUM)).append("</span>");
        sb.append("<span class=\"risk risk-LOW\">Low: ").append(ReportSupport.count(sorted, Risk.LOW)).append("</span>");
        sb.append("<span class=\"risk risk-INFORMATIONAL\">Informational: ").append(ReportSupport.count(sorted, Risk.INFORMATIONAL)).append("</span>");
        sb.append("<span>Total: ").append(sorted.size()).append("</span>");
        sb.append("</p>\n");

        sb.append("<table>\n<thead><tr><th>Risk</th><th>Confidence</th><th>Alert</th><th>URL</th>")
                .append("<th>Parameter</th><th>Evidence</th><th>Description</th><th>Remediation</th></tr></thead>\n<tbody>\n");
        if (sorted.isEmpty()) {
            sb.append("<tr><td colspan=\"8\">No alerts.</td></tr>\n");
        }
        for (Alert a : sorted) {
            sb.append("<tr>");
            sb.append("<td class=\"risk risk-").append(a.getRisk().name()).append("\">")
                    .append(ReportSupport.htmlEscape(a.getRisk().label())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getConfidence().label())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getName())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getUrl())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getParameter())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getEvidence())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getDescription())).append("</td>");
            sb.append("<td>").append(ReportSupport.htmlEscape(a.getRemediation())).append("</td>");
            sb.append("</tr>\n");
        }
        sb.append("</tbody>\n</table>\n</body>\n</html>\n");
        return sb.toString();
    }
}
