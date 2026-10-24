package local.foundev.zap.ui;

import local.foundev.zap.core.ScanEngine;
import local.foundev.zap.core.ScanProgress;
import local.foundev.zap.core.ScanSummary;
import local.foundev.zap.core.Uris;
import local.foundev.zap.model.Alert;
import local.foundev.zap.model.AlertStore;
import local.foundev.zap.model.Risk;
import local.foundev.zap.report.HtmlReportWriter;
import local.foundev.zap.report.JsonReportWriter;

import javax.swing.BorderFactory;
import javax.swing.JButton;
import javax.swing.JCheckBox;
import javax.swing.JComboBox;
import javax.swing.JFileChooser;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JProgressBar;
import javax.swing.JScrollPane;
import javax.swing.JSplitPane;
import javax.swing.JTable;
import javax.swing.JTextField;
import javax.swing.JTree;
import javax.swing.SwingUtilities;
import javax.swing.SwingWorker;
import javax.swing.filechooser.FileNameExtensionFilter;
import javax.swing.table.DefaultTableCellRenderer;
import javax.swing.tree.DefaultMutableTreeNode;
import javax.swing.tree.DefaultTreeModel;
import java.awt.BorderLayout;
import java.awt.Color;
import java.awt.Component;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.io.File;
import java.io.IOException;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.ExecutionException;

/**
 * Main window: target URL bar, the "I am authorized" gate, crawl progress,
 * the discovered-site tree, a color-coded alerts grid and report export.
 * Active checks stay disabled until the checkbox is ticked.
 */
public final class ScannerFrame extends JFrame {

    private static final Color HIGH_BG = new Color(0xFF, 0xD6, 0xD6);
    private static final Color HIGH_FG = new Color(0x8B, 0x00, 0x00);
    private static final Color MEDIUM_BG = new Color(0xFF, 0xE9, 0xC8);
    private static final Color MEDIUM_FG = new Color(0x7A, 0x4B, 0x00);
    private static final Color LOW_BG = new Color(0xFF, 0xF6, 0xC9);
    private static final Color LOW_FG = new Color(0x6B, 0x5B, 0x00);
    private static final Color INFO_BG = new Color(0xDB, 0xE9, 0xFF);
    private static final Color INFO_FG = new Color(0x0B, 0x3D, 0x91);

    private final AlertStore store;
    private final ScanEngine engine;
    private final AlertTableModel tableModel;
    private final Map<String, DefaultMutableTreeNode> nodeMap = new HashMap<>();

    private JTextField urlField;
    private JCheckBox authorizedCheck;
    private JButton startButton;
    private JButton stopButton;
    private JButton exportHtmlButton;
    private JButton exportJsonButton;
    private JComboBox<Object> riskFilter;
    private JProgressBar progressBar;
    private JLabel statusLabel;
    private JTree siteTree;
    private JTable alertsTable;
    private URI lastTarget;

    private final ScanProgress uiProgress = new ScanProgress() {
        @Override
        public void onStatus(String message) {
            SwingUtilities.invokeLater(() -> {
                statusLabel.setText(message);
                refreshAlerts();
            });
        }

        @Override
        public void onLink(String url, String parentUrl) {
            SwingUtilities.invokeLater(() -> addTreeNode(url, parentUrl));
        }

        @Override
        public void onFinished(ScanSummary summary) {
            // The summary line is shown from SwingWorker#done() on the EDT.
        }
    };

    public ScannerFrame() {
        super("OWASP ZAP - Foundev web security scanner");
        store = new AlertStore();
        engine = new ScanEngine(store);
        tableModel = new AlertTableModel();
        buildUi();
    }

    private void buildUi() {
        setDefaultCloseOperation(JFrame.EXIT_ON_CLOSE);
        setPreferredSize(new Dimension(1150, 720));

        urlField = new JTextField("http://localhost:8080/");
        authorizedCheck = new JCheckBox("I am authorized to actively test this target");
        authorizedCheck.setToolTipText("Active probes stay disabled until this box is checked.");
        startButton = new JButton("Start scan");
        stopButton = new JButton("Stop");
        stopButton.setEnabled(false);
        riskFilter = new JComboBox<>(new Object[]{"All risks", Risk.HIGH, Risk.MEDIUM, Risk.LOW, Risk.INFORMATIONAL});
        exportHtmlButton = new JButton("Export HTML...");
        exportJsonButton = new JButton("Export JSON...");
        statusLabel = new JLabel("Ready. Enter a target URL you are authorized to test.");
        progressBar = new JProgressBar();
        progressBar.setStringPainted(true);

        siteTree = new JTree();
        siteTree.setShowsRootHandles(true);
        resetTree("No site crawled yet");

        alertsTable = new JTable(tableModel);
        alertsTable.setAutoCreateRowSorter(true);
        alertsTable.setFillsViewportHeight(true);
        alertsTable.setRowHeight(22);
        alertsTable.getColumnModel().getColumn(0).setCellRenderer(new RiskCellRenderer());
        alertsTable.getColumnModel().getColumn(0).setPreferredWidth(80);
        alertsTable.getColumnModel().getColumn(1).setPreferredWidth(80);
        alertsTable.getColumnModel().getColumn(2).setPreferredWidth(220);
        alertsTable.getColumnModel().getColumn(3).setPreferredWidth(280);
        alertsTable.getColumnModel().getColumn(4).setPreferredWidth(90);
        alertsTable.getColumnModel().getColumn(5).setPreferredWidth(260);

        JPanel actionRow = new JPanel(new FlowLayout(FlowLayout.RIGHT, 6, 0));
        actionRow.add(startButton);
        actionRow.add(stopButton);
        JPanel urlRow = new JPanel(new BorderLayout(8, 0));
        urlRow.add(new JLabel("Target URL:"), BorderLayout.WEST);
        urlRow.add(urlField, BorderLayout.CENTER);
        urlRow.add(actionRow, BorderLayout.EAST);

        JPanel optsRow = new JPanel(new FlowLayout(FlowLayout.LEFT, 6, 0));
        optsRow.add(authorizedCheck);
        optsRow.add(new JLabel("Risk filter:"));
        optsRow.add(riskFilter);
        optsRow.add(exportHtmlButton);
        optsRow.add(exportJsonButton);

        progressBar.setPreferredSize(new Dimension(220, 18));
        JPanel statusRow = new JPanel(new BorderLayout(8, 0));
        statusRow.add(progressBar, BorderLayout.WEST);
        statusRow.add(statusLabel, BorderLayout.CENTER);

        JPanel north = new JPanel(new BorderLayout(6, 6));
        north.setBorder(BorderFactory.createEmptyBorder(8, 8, 0, 8));
        north.add(urlRow, BorderLayout.NORTH);
        north.add(optsRow, BorderLayout.CENTER);
        north.add(statusRow, BorderLayout.SOUTH);
        add(north, BorderLayout.NORTH);

        JSplitPane split = new JSplitPane(JSplitPane.HORIZONTAL_SPLIT);
        split.setResizeWeight(0.32);
        split.setLeftComponent(new JScrollPane(siteTree));
        split.setRightComponent(new JScrollPane(alertsTable));
        split.setBorder(BorderFactory.createEmptyBorder(8, 8, 8, 8));
        add(split, BorderLayout.CENTER);

        startButton.addActionListener(e -> startScan());
        stopButton.addActionListener(e -> stopScan());
        exportHtmlButton.addActionListener(e -> exportReport(true));
        exportJsonButton.addActionListener(e -> exportReport(false));
        riskFilter.addActionListener(e -> refreshAlerts());

        pack();
        setLocationRelativeTo(null);
    }

    private void startScan() {
        String raw = urlField.getText() == null ? "" : urlField.getText().trim();
        URI target;
        try {
            target = URI.create(raw);
        } catch (IllegalArgumentException e) {
            JOptionPane.showMessageDialog(this,
                    "Enter a valid URL, for example http://localhost:8080/",
                    "Invalid target", JOptionPane.WARNING_MESSAGE);
            return;
        }
        String scheme = target.getScheme();
        if (scheme == null || target.getHost() == null
                || (!"http".equalsIgnoreCase(scheme) && !"https".equalsIgnoreCase(scheme))) {
            JOptionPane.showMessageDialog(this,
                    "The target must be an http:// or https:// URL.",
                    "Invalid target", JOptionPane.WARNING_MESSAGE);
            return;
        }
        if (authorizedCheck.isSelected()) {
            int confirm = JOptionPane.showConfirmDialog(this,
                    "Active checks will send probe payloads (script tags, SQL quotes, "
                            + "traversal paths) to:\n" + target
                            + "\n\nOnly continue if you are authorized to actively test this target.",
                    "Confirm authorized assessment",
                    JOptionPane.OK_CANCEL_OPTION,
                    JOptionPane.WARNING_MESSAGE);
            if (confirm != JOptionPane.OK_OPTION) {
                return;
            }
        }

        store.clear();
        nodeMap.clear();
        resetTree(Uris.stripFragment(target.toString()));
        refreshAlerts();
        lastTarget = target;

        startButton.setEnabled(false);
        stopButton.setEnabled(true);
        exportHtmlButton.setEnabled(false);
        exportJsonButton.setEnabled(false);
        progressBar.setIndeterminate(true);
        statusLabel.setText("Scanning " + target + " ...");

        final boolean runActive = authorizedCheck.isSelected();
        SwingWorker<ScanSummary, Void> worker = new SwingWorker<ScanSummary, Void>() {
            @Override
            protected ScanSummary doInBackground() {
                return engine.run(target, runActive, ScanEngine.DEFAULT_MAX_PAGES, uiProgress);
            }

            @Override
            protected void done() {
                try {
                    ScanSummary summary = get();
                    refreshAlerts();
                    expandTree();
                    statusLabel.setText(summarize(summary));
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    statusLabel.setText("Scan interrupted.");
                } catch (ExecutionException e) {
                    Throwable cause = e.getCause() == null ? e : e.getCause();
                    statusLabel.setText("Scan failed: " + cause.getMessage());
                    JOptionPane.showMessageDialog(ScannerFrame.this,
                            "Scan failed: " + cause.getMessage(),
                            "Scan error", JOptionPane.ERROR_MESSAGE);
                } finally {
                    progressBar.setIndeterminate(false);
                    startButton.setEnabled(true);
                    stopButton.setEnabled(false);
                    exportHtmlButton.setEnabled(true);
                    exportJsonButton.setEnabled(true);
                }
            }
        };
        worker.execute();
    }

    private void stopScan() {
        engine.cancel();
        stopButton.setEnabled(false);
        statusLabel.setText("Stopping after the current request ...");
    }

    private void resetTree(String rootLabel) {
        DefaultMutableTreeNode root = new DefaultMutableTreeNode(rootLabel);
        siteTree.setModel(new DefaultTreeModel(root));
        nodeMap.clear();
        nodeMap.put(rootLabel, root);
    }

    private void addTreeNode(String url, String parentUrl) {
        if (nodeMap.containsKey(url)) {
            return;
        }
        DefaultTreeModel model = (DefaultTreeModel) siteTree.getModel();
        DefaultMutableTreeNode root = (DefaultMutableTreeNode) model.getRoot();
        DefaultMutableTreeNode parent = parentUrl == null ? null : nodeMap.get(parentUrl);
        if (parent == null) {
            parent = root;
        }
        DefaultMutableTreeNode node = new DefaultMutableTreeNode(url);
        model.insertNodeInto(node, parent, parent.getChildCount());
        nodeMap.put(url, node);
    }

    private void expandTree() {
        for (int row = 0; row < siteTree.getRowCount(); row++) {
            siteTree.expandRow(row);
        }
    }

    private void refreshAlerts() {
        List<Alert> alerts = store.snapshot();
        Object selected = riskFilter.getSelectedItem();
        if (selected instanceof Risk risk) {
            List<Alert> filtered = new ArrayList<>();
            for (Alert alert : alerts) {
                if (alert.getRisk() == risk) {
                    filtered.add(alert);
                }
            }
            alerts = filtered;
        }
        alerts.sort(Comparator.comparingInt((Alert a) -> a.getRisk().ordinal()).reversed()
                .thenComparing(Alert::getName, String.CASE_INSENSITIVE_ORDER));
        tableModel.setAlerts(alerts);
    }

    private void exportReport(boolean html) {
        if (lastTarget == null) {
            JOptionPane.showMessageDialog(this, "Run a scan first.", "Nothing to export",
                    JOptionPane.INFORMATION_MESSAGE);
            return;
        }
        JFileChooser chooser = new JFileChooser();
        chooser.setSelectedFile(new File(html ? "zap-report.html" : "zap-report.json"));
        if (html) {
            chooser.setFileFilter(new FileNameExtensionFilter("HTML report", "html", "htm"));
        }
        int result = chooser.showSaveDialog(this);
        if (result != JFileChooser.APPROVE_OPTION) {
            return;
        }
        Path path = chooser.getSelectedFile().toPath();
        try {
            String content = html
                    ? HtmlReportWriter.render(lastTarget.toString(), store.snapshot())
                    : JsonReportWriter.render(lastTarget.toString(), store.snapshot());
            Files.writeString(path, content, StandardCharsets.UTF_8);
            JOptionPane.showMessageDialog(this, "Report written to " + path);
        } catch (IOException e) {
            JOptionPane.showMessageDialog(this,
                    "Could not write the report: " + e.getMessage(),
                    "Export failed", JOptionPane.ERROR_MESSAGE);
        }
    }

    private static String summarize(ScanSummary s) {
        StringBuilder sb = new StringBuilder();
        sb.append(s.getPagesCrawled()).append(" pages, ").append(s.getAlertCount()).append(" alerts");
        if (s.isActiveRan()) {
            sb.append(", active checks completed");
        }
        if (s.isCancelled()) {
            sb.append(" (stopped early)");
        }
        sb.append(" in ").append(s.getElapsedMillis()).append(" ms");
        return sb.toString();
    }

    /** Paints the Risk column as a colored badge. */
    private static final class RiskCellRenderer extends DefaultTableCellRenderer {

        @Override
        public Component getTableCellRendererComponent(JTable table, Object value, boolean isSelected,
                                                       boolean hasFocus, int row, int column) {
            super.getTableCellRendererComponent(table, value, isSelected, hasFocus, row, column);
            if (value instanceof Risk risk) {
                setHorizontalAlignment(CENTER);
                setOpaque(true);
                if (isSelected) {
                    setForeground(table.getSelectionForeground());
                    setBackground(table.getSelectionBackground());
                } else {
                    setForeground(textColor(risk));
                    setBackgroundColor(risk);
                }
            } else {
                setOpaque(false);
                setHorizontalAlignment(LEFT);
            }
            return this;
        }

        private void setBackgroundColor(Risk risk) {
            switch (risk) {
                case HIGH:
                    setBackground(HIGH_BG);
                    break;
                case MEDIUM:
                    setBackground(MEDIUM_BG);
                    break;
                case LOW:
                    setBackground(LOW_BG);
                    break;
                default:
                    setBackground(INFO_BG);
            }
        }

        private static Color textColor(Risk risk) {
            switch (risk) {
                case HIGH:
                    return HIGH_FG;
                case MEDIUM:
                    return MEDIUM_FG;
                case LOW:
                    return LOW_FG;
                default:
                    return INFO_FG;
            }
        }
    }
}
