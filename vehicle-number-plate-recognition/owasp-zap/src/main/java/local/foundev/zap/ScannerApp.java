package local.foundev.zap;

import local.foundev.zap.ui.ScannerFrame;

import javax.swing.SwingUtilities;
import javax.swing.UIManager;

/**
 * Application entry point: launches the Swing UI with no arguments, and the
 * headless CLI when given "cli", any option, or a target URL
 * (so {@code java -jar owasp-zap.jar cli http://localhost:8080/} works).
 */
public final class ScannerApp {

    private ScannerApp() {
    }

    public static void main(String[] args) {
        if (args.length > 0 && isCliInvocation(args[0])) {
            String[] rest = args;
            if ("cli".equals(args[0]) || "--cli".equals(args[0])) {
                rest = new String[args.length - 1];
                System.arraycopy(args, 1, rest, 0, rest.length);
            }
            ScannerCli.main(rest);
            return;
        }
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (Exception ignored) {
            // Keep the platform default look and feel.
        }
        SwingUtilities.invokeLater(() -> {
            ScannerFrame frame = new ScannerFrame();
            frame.setVisible(true);
        });
    }

    private static boolean isCliInvocation(String first) {
        return "cli".equals(first) || "--cli".equals(first)
                || first.startsWith("-")
                || first.startsWith("http://")
                || first.startsWith("https://");
    }
}
