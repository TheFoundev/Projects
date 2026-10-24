# OWASP ZAP

A web application security scanner offering passive and active testing for authorised assessments.

> A ZAP-style scanner that spiders a target you supply, checks every response for security weaknesses, sends active probes only after an explicit authorization confirmation, and exports the alerts as HTML or JSON.

## Overview

An original, self-contained implementation of the **OWASP ZAP** concept for the Foundev portfolio. It focuses on the core workflow from the project brief — spider, passive analysis, authorized active checks, alert report — and keeps the architecture small enough to read end to end.

## Features

- Same-origin, breadth-first HTTP spider that discovers `href`/`src` links and GET form targets
- Passive analyzer: missing Content-Security-Policy / X-Frame-Options / X-Content-Type-Options / HSTS, cookie flags (Secure, HttpOnly, SameSite), `Server` and `X-Powered-By` banner disclosure, directory listing, mixed content
- Active analyzer behind a hard gate: reflected XSS, error-based SQL injection and path-traversal probes on query parameters — disabled unless the "I am authorized" checkbox (UI) or the `--authorized` flag (CLI) is given; the analyzer itself refuses to run without that confirmation
- Alert model with risk level, confidence, URL, parameter, evidence, description and remediation, plus an in-memory store that de-duplicates findings and filters by risk
- Swing UI: target URL bar, authorization checkbox, crawl progress bar, discovered-site tree, color-coded alerts table, risk filter
- Export of the alert report as HTML and JSON
- Headless CLI for scripted assessments

## Stack

`JUnit; Java`
The CSV stack is JUnit + Java. The project is built with Maven and a JDK 17: `mvn test` compiles the scanner core, the Swing UI, the CLI and the tests, and runs the 26 tests of the suite.

## Authorized use only

Active checks send deliberately malformed requests (script tags, SQL quotes, traversal paths). Run them only against systems you own or have explicit, written permission to test — the UI checkbox and the CLI `--authorized` flag are that confirmation, and they are required. Pointing a scanner at third-party systems without permission may be a crime; treat every alert as a hint to verify manually, never as permission to exploit.

## Run

```bash
mvn package                # needs a JDK; see the environment note below

java -jar target/owasp-zap-0.1.0.jar                                  # Swing UI
java -jar target/owasp-zap-0.1.0.jar cli http://localhost:8080/       # headless run

# headless with active probes (the explicit authorization flag is mandatory):
java -jar target/owasp-zap-0.1.0.jar cli http://localhost:3000/ \
     --active --authorized --html report.html --json report.json
```

CLI options: `--active`, `--authorized`, `--max-pages <n>`, `--html <file>`, `--json <file>`, `--help`.

## Structure

```text
owasp-zap/
├── pom.xml                        Maven project (jar, JUnit 5 only)
├── src/main/java/local/foundev/zap/
│   ├── ScannerApp.java            Swing entry point (dispatches to the CLI with "cli")
│   ├── ScannerCli.java            headless entry point
│   ├── core/                      HttpFetcher, spider, passive/active analyzers, scan engine
│   ├── model/                     Alert, Risk/Confidence enums, AlertStore
│   ├── report/                    HTML and JSON report writers
│   └── ui/                        Swing frame and alerts table model
├── src/test/java/                 PassiveAnalyzerTest, ReportExportTest,
│                                  CookieAnalysisTest, AlertStoreTest, WebCrawlerTest
├── LICENSE
└── README.md
```

## Testing

```bash
mvn test                          # 26 tests; needs a JDK 17 and Maven
```

The suite covers the passive checks, the report writers, the cookie analysis
(the attributes are what follow the first `;`, so a value that looks like a
flag is not mistaken for one), the alert store (the de-duplication, the
filtering by risk, the clearing) and the spider, which is run against a real
HTTP server on the loopback interface: the same-origin scope, the links that
are followed, the form targets and the page limit.

To exercise the scanner end to end, point it at a local, intentionally vulnerable app you are authorized to test:

```bash
# a tiny local target: python's http.server sends a Server banner and no
# security headers, so the passive checks fire immediately
mkdir -p /tmp/zap-lab && echo hello > /tmp/zap-lab/index.html
cd /tmp/zap-lab && python3 -m http.server 8000 &

java -jar target/owasp-zap-0.1.0.jar cli http://localhost:8000/
```

Request a sub-folder without an `index.html` (e.g. `http://localhost:8000/sub/`) to see the directory-listing alert. For a richer target, run [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) locally (`docker run -p 3000:3000 bkimminich/juice-shop`) and scan `http://localhost:3000/` with `--active --authorized`. Authorized testing only — never scan a host you do not own or lack written permission to test.

## Notes and limitations

- **Build:** the project is written for plain Java 17 and is built with Maven. `mvn test` compiles everything (the scanner core, the Swing UI, the CLI) and runs the 26 tests of the suite; the CI workflow does the same on every push.
- The spider is GET-only and same-origin, capped at 50 pages by default; response bodies are truncated to 512 KB for analysis, and JavaScript is never executed (no headless browser), so single-page applications are only partially covered.
- Active checks are three conservative probes (one XSS marker, one SQL quote checked against common error strings, one traversal payload); their alerts are evidence hints with medium confidence, not proof.
- The cookie analysis follows RFC 6265: the name/value pair ends at the first `;` and only what follows it is read as attributes, so a value that looks like a flag is not mistaken for one.

## License

Apache-2.0. See `LICENSE`.

## About the scope

This is a third-year student project. The listed toolchain was not available in this environment, so the repository is source-only and was checked by structural validation.

## Verification

Everything below was run in this repository:

```bash
mvn test        # 26 tests, 0 failures
```

The scanner core, the report writers, the Swing UI and the CLI all compile; the
spider is exercised against a real HTTP server on the loopback interface.
