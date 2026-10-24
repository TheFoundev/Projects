package local.foundev.zap.model;

/** How sure the scanner is that a finding is real. */
public enum Confidence {

    LOW("Low"),
    MEDIUM("Medium"),
    HIGH("High");

    private final String label;

    Confidence(String label) {
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
