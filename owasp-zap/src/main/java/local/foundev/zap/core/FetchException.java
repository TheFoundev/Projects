package local.foundev.zap.core;

/** Checked failure to retrieve one URL (network error, timeout, bad request). */
public class FetchException extends Exception {

    private static final long serialVersionUID = 1L;

    public FetchException(String message) {
        super(message);
    }

    public FetchException(String message, Throwable cause) {
        super(message, cause);
    }
}
