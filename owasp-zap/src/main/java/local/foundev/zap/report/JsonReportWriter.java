package local.foundev.zap.report;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Risk;

import java.time.Instant;
import java.util.List;

/** Renders the alert store as a small JSON document, without any libraries. */
public final class JsonReportWriter {

    public static final String TOOL_NAME = "Foundev OWASP ZAP MVP";

    private JsonReportWriter() {
    }

    public static String render(String target, List<Alert> alerts) {
        List<Alert> sorted = ReportSupport.sorted(alerts);
        StringBuilder sb = new StringBuilder(4096);
        sb.append("{\n");
        sb.append("  \"tool\": ").append(quote(TOOL_NAME)).append(",\n");
        sb.append("  \"target\": ").append(quote(target)).append(",\n");
        sb.append("  \"generatedAt\": ").append(quote(Instant.now().toString())).append(",\n");
        sb.append("  \"summary\": {");
        sb.append("\"high\": ").append(ReportSupport.count(sorted, Risk.HIGH));
        sb.append(", \"medium\": ").append(ReportSupport.count(sorted, Risk.MEDIUM));
        sb.append(", \"low\": ").append(ReportSupport.count(sorted, Risk.LOW));
        sb.append(", \"informational\": ").append(ReportSupport.count(sorted, Risk.INFORMATIONAL));
        sb.append(", \"total\": ").append(sorted.size());
        sb.append("},\n");
        sb.append("  \"alerts\": [");
        for (int i = 0; i < sorted.size(); i++) {
            Alert a = sorted.get(i);
            sb.append(i == 0 ? "\n" : ",\n");
            sb.append("    {");
            sb.append("\"name\": ").append(quote(a.getName()));
            sb.append(", \"risk\": ").append(quote(a.getRisk().name()));
            sb.append(", \"confidence\": ").append(quote(a.getConfidence().name()));
            sb.append(", \"url\": ").append(quote(a.getUrl()));
            sb.append(", \"parameter\": ").append(quote(a.getParameter()));
            sb.append(", \"evidence\": ").append(quote(a.getEvidence()));
            sb.append(", \"description\": ").append(quote(a.getDescription()));
            sb.append(", \"remediation\": ").append(quote(a.getRemediation()));
            sb.append("}");
        }
        if (!sorted.isEmpty()) {
            sb.append("\n  ");
        }
        sb.append("]\n}\n");
        return sb.toString();
    }

    private static String quote(String s) {
        if (s == null) {
            return "\"\"";
        }
        StringBuilder sb = new StringBuilder(s.length() + 2);
        sb.append('"');
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            switch (ch) {
                case '"':
                    sb.append("\\\"");
                    break;
                case '\\':
                    sb.append("\\\\");
                    break;
                case '\n':
                    sb.append("\\n");
                    break;
                case '\r':
                    sb.append("\\r");
                    break;
                case '\t':
                    sb.append("\\t");
                    break;
                case '\b':
                    sb.append("\\b");
                    break;
                case '\f':
                    sb.append("\\f");
                    break;
                default:
                    if (ch < 0x20) {
                        String hex = Integer.toHexString(ch);
                        sb.append("\\u");
                        for (int pad = hex.length(); pad < 4; pad++) {
                            sb.append('0');
                        }
                        sb.append(hex);
                    } else {
                        sb.append(ch);
                    }
            }
        }
        sb.append('"');
        return sb.toString();
    }
}
