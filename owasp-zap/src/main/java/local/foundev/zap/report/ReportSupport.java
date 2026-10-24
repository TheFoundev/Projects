package local.foundev.zap.report;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Risk;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

/** Shared helpers for the report writers. */
final class ReportSupport {

    private ReportSupport() {
    }

    /** Most severe first, then by name. */
    static List<Alert> sorted(List<Alert> alerts) {
        List<Alert> copy = new ArrayList<>(alerts == null ? List.of() : alerts);
        copy.sort(Comparator.comparingInt((Alert a) -> a.getRisk().ordinal()).reversed()
                .thenComparing(Alert::getName, String.CASE_INSENSITIVE_ORDER));
        return copy;
    }

    static int count(List<Alert> alerts, Risk risk) {
        int count = 0;
        for (Alert alert : alerts) {
            if (alert.getRisk() == risk) {
                count++;
            }
        }
        return count;
    }

    static String htmlEscape(String s) {
        if (s == null || s.isEmpty()) {
            return "";
        }
        StringBuilder sb = new StringBuilder(s.length() + 16);
        for (int i = 0; i < s.length(); i++) {
            char ch = s.charAt(i);
            switch (ch) {
                case '&':
                    sb.append("&amp;");
                    break;
                case '<':
                    sb.append("&lt;");
                    break;
                case '>':
                    sb.append("&gt;");
                    break;
                case '"':
                    sb.append("&quot;");
                    break;
                case '\'':
                    sb.append("&#39;");
                    break;
                default:
                    sb.append(ch);
            }
        }
        return sb.toString();
    }
}
