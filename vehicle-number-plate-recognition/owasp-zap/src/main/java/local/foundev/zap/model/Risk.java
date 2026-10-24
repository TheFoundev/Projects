package local.foundev.zap.model;

/**
 * Risk level of a finding, declared from least to most severe so that
 * {@link #ordinal()} orders alerts naturally.
 */
public enum Risk {

    INFORMATIONAL("Informational"),
    LOW("Low"),
    MEDIUM("Medium"),
    HIGH("High");

    private final String label;

    Risk(String label) {
        this.label = label;
    }

    public String label() {
        return label;
    }

    @Override
    public String toString() {
        return label;
    }
}
