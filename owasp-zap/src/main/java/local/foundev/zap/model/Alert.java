package local.foundev.zap.model;

import java.util.Objects;

/**
 * A single security finding produced by a passive or active check.
 *
 * <p>Immutable: risk, confidence, the affected URL, the parameter (empty when
 * the finding is not tied to one), evidence taken from the traffic, a short
 * description and remediation advice.</p>
 */
public final class Alert {

    private final String name;
    private final Risk risk;
    private final Confidence confidence;
    private final String url;
    private final String parameter;
    private final String evidence;
    private final String description;
    private final String remediation;

    public Alert(String name,
                 Risk risk,
                 Confidence confidence,
                 String url,
                 String parameter,
                 String evidence,
                 String description,
                 String remediation) {
        this.name = Objects.requireNonNull(name, "name");
        this.risk = Objects.requireNonNull(risk, "risk");
        this.confidence = Objects.requireNonNull(confidence, "confidence");
        this.url = Objects.requireNonNull(url, "url");
        this.parameter = parameter == null ? "" : parameter;
        this.evidence = evidence == null ? "" : evidence;
        this.description = description == null ? "" : description;
        this.remediation = remediation == null ? "" : remediation;
    }

    public String getName() {
        return name;
    }

    public Risk getRisk() {
        return risk;
    }

    public Confidence getConfidence() {
        return confidence;
    }

    public String getUrl() {
        return url;
    }

    public String getParameter() {
        return parameter;
    }

    public String getEvidence() {
        return evidence;
    }

    public String getDescription() {
        return description;
    }

    public String getRemediation() {
        return remediation;
    }

    /** Used by the alert store to de-duplicate identical findings. */
    public String dedupKey() {
        return name + "|" + url + "|" + parameter;
    }

    @Override
    public String toString() {
        return risk.label() + " " + name + " (" + url + ")";
    }
}
