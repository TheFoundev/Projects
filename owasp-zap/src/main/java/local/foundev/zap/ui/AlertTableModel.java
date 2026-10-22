package local.foundev.zap.ui;

import local.foundev.zap.model.Alert;
import local.foundev.zap.model.Confidence;
import local.foundev.zap.model.Risk;

import javax.swing.table.AbstractTableModel;
import java.util.ArrayList;
import java.util.List;

/** Table model behind the alerts grid. */
public final class AlertTableModel extends AbstractTableModel {

    private static final String[] COLUMNS = {"Risk", "Confidence", "Alert", "URL", "Parameter", "Evidence"};

    private List<Alert> rows = new ArrayList<>();

    public void setAlerts(List<Alert> alerts) {
        this.rows = new ArrayList<>(alerts == null ? List.of() : alerts);
        fireTableDataChanged();
    }

    @Override
    public int getRowCount() {
        return rows.size();
    }

    @Override
    public int getColumnCount() {
        return COLUMNS.length;
    }

    @Override
    public String getColumnName(int column) {
        return COLUMNS[column];
    }

    @Override
    public Class<?> getColumnClass(int column) {
        if (column == 0) {
            return Risk.class;
        }
        if (column == 1) {
            return Confidence.class;
        }
        return String.class;
    }

    @Override
    public Object getValueAt(int row, int column) {
        Alert a = rows.get(row);
        switch (column) {
            case 0:
                return a.getRisk();
            case 1:
                return a.getConfidence();
            case 2:
                return a.getName();
            case 3:
                return a.getUrl();
            case 4:
                return a.getParameter();
            case 5:
                return a.getEvidence();
            default:
                return "";
        }
    }
}
