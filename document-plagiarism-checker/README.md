# Similarity Radar — Document Plagiarism Checker

*Folder id: `document-plagiarism-checker` · Upstream: `regiapriandi012/plagiarism-check` (badges reference `plagiarism-checker-flask`)*

**Similarity Radar** is a Flask web application that checks how much of a document or
passage already exists on the public web. It splits the input into sentences, quotes each
sentence verbatim into a live Google search, filters out hits on social-network and
marketplace domains, and reports a **similarity index** as
`matched sentences ÷ total sentences × 100`, together with the matched sentences and the
source URLs that produced the hits.

The UI is server-rendered Jinja (`templates/index.html`) with a small vanilla-JS layer
(`static/js/app.js`) — no front-end framework, no JavaScript build step, no API keys.
The only real external dependency is **Google itself**: every sentence becomes a live
search query, so the checker needs an internet connection to produce a score.

> The interface was redesigned after the original upstream project; the original template is
> preserved verbatim at `templates/index.html.bak`.

---

## Features

### Implemented and verified

| Feature | Where | Notes |
|---|---|---|
| Paste-text scan | `app.py:24-50` `index()` | Text is written to `word.txt` and the browser is redirected to `/plagiarism/word#hasil` |
| PDF upload scan | `app.py:33-46`, `app.py:88-95` | PDF only, 16 MB cap, saved to `uploads/` with `secure_filename`, text extracted page by page with PyPDF2 |
| Sentence-level quoted Google search | `app.py:107-113`, `134-140`, `166-173`, `203-209` | `search(query, tld="co.id", num=10, stop=10, pause=2)` |
| Blocked-domain filtering | `app.py:66-67` | LinkedIn, YouTube, Instagram, Facebook, Twitter, Reddit, Tokopedia, Bukalapak, Shopee, Blibli |
| Similarity index | `app.py:127-129`, `154-156`, `223-225` | `(matched ÷ total sentences) × 100` |
| Radar gauge + status stamp | `templates/index.html:137-168` | SVG gauge with needle/arc, statuses *Original* / *Minor overlap* / *High overlap* (thresholds set on the page: 0 %, < 30 %, ≥ 30 %) |
| Matched-sentence list with source links | `templates/index.html:170-198` | Each match shows the sentence, its source URL, and copy buttons |
| Input desk with text / PDF tabs | `static/js/app.js:101-152` | Tab state persisted in `localStorage["radarInputMode"]` |
| Live character + sentence counters | `static/js/app.js:72-87` | Sentence count mirrors the backend split on `". "` |
| Drag-and-drop PDF zone with client-side validation | `static/js/app.js:205-285` | Rejects non-PDF and > 16 MB before upload |
| Scanning overlay with honest warning | `templates/index.html:105-113` | "Long texts can take a minute or two" |
| Copy sentence / copy link | `static/js/app.js:500-525` | Clipboard API with `execCommand` fallback |
| `Ctrl`/`⌘` + `Enter` shortcut to scan | `static/js/app.js:339-346` | |
| Flash messages for invalid submissions | `app.py:35,41,48` | "Please fill the form", "No file part", "No selected file" |
| Smoke test | `test_app.py` | `pytest` asserts `GET /` returns 200 |
| Docker image + GitHub Actions CI | `Dockerfile`, `Procfile`, `.github/workflows/` | `python:3.8.2`, `gunicorn app:app`, pytest / CodeQL / dependency-review / docker publish workflows |

### Not available / requires external setup

- **No local corpus comparison.** Despite the folder metadata mentioning "TF-IDF" and
  "N-gram/fingerprint similarity across a local corpus", there is **no TF-IDF code and no
  local corpus** in this repository. The only comparison performed is against live Google
  results.
- **No semantic similarity.** The index is a *web-presence* measure (exact quoted sentences
  found in the top-10 results), not a paraphrase-aware similarity score.
- **No API key.** Google is queried through the `googlesearch` library by scraping the
  public results page; there is no Google Custom Search API key to configure.
- **No user accounts, database, history or report export.** The last pasted text survives in
  `word.txt` on the server; nothing else is persisted.
- **No DOCX/PPTX/plain-text file upload** — the server accepts PDF only.
- **No multi-user isolation**: `word.txt` and `uploads/` are shared by every visitor.

---

## Technology Stack

| Layer | Technology | Version pinned in `requirements.txt` |
|---|---|---|
| Web framework | Flask | `2.2.2` |
| WSGI utils | Werkzeug | `2.2.2` (provides `secure_filename`) |
| Templating | Jinja2 | `3.1.2` |
| Search scraper | `google` (imports as `googlesearch`) | `3.0.0` |
| PDF text extraction | PyPDF2 | `2.11.1` |
| HTML parsing (dependency of `googlesearch`) | beautifulsoup4 / soupsieve | `4.11.1` / `2.3.2.post1` |
| Templating helpers | MarkupSafe, itsdangerous, click, importlib-metadata, typing-extensions, zipp | `2.1.1`, `2.1.2`, `8.1.3`, `5.0.0`, `4.4.0`, `3.10.0` |
| Production server | gunicorn | `20.1.0` |
| Test runner | pytest | `7.0.1` |
| Front end | Vanilla HTML5 + CSS + ES5 JavaScript, Jinja templates, no framework, no bundler | — |
| Icons / fonts | Inline SVG, Google Fonts (IBM Plex Mono, Lora, Newsreader) | — |

---

## Prerequisites

- **Windows 10/11** with PowerShell (commands below are Windows-first).
- **Python 3.12.1** — the bundled `.venv` was created with it, and all pinned packages
  install cleanly on 3.12.
- **An internet connection** — every scan performs live Google queries.
- Optional: **Docker Desktop** if you prefer the container path.
- Linux/macOS: the same commands work; only the venv activation line differs.

---

## Project Structure

```
document-plagiarism-checker/
├── app.py                      # Flask backend: routes, PDF extraction, Google search, scoring
├── templates/
│   ├── index.html              # Redesigned server-rendered UI (Similarity Radar)
│   └── index.html.bak          # Original upstream template, preserved
├── static/
│   ├── css/style.css           # Radar / gauge / stamp styling
│   └── js/app.js               # Tabs, counters, drag-drop, gauge animation, copy buttons
├── uploads/                    # Uploaded PDFs land here (created from os.getcwd())
├── word.txt                    # Last pasted text (44 bytes: "The quick brown fox jumps over the lazy dog.")
├── .google-cookie              # LWP cookie jar used by the googlesearch library
├── requirements.txt            # Pinned runtime + dev dependencies
├── test_app.py                 # pytest smoke test (GET / == 200)
├── Dockerfile                  # python:3.8.2 + flask run --host=0.0.0.0
├── Procfile                    # web: gunicorn app:app --log-file=-
├── LICENSE.md                  # MIT, Copyright (c) 2022 Regi Apriandi
├── project-metadata.json       # Folder metadata (id, stack, license, entry point)
├── .github/workflows/          # CI: main.yml (pytest), python-app.yml, codeql.yml,
│                               #      dependency-review.yml, docker-image.yml, docker-publish.yml
└── .venv/                      # Ready-made Python 3.12.1 virtualenv (Flask 2.2.2, PyPDF2 2.11.1, google 3.0.0)
```

Key paths the code actually uses:

| Purpose | Path used by the code |
|---|---|
| Upload target | `UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')` — `app.py:7-8` |
| Pasted-text scratch file | `word.txt` in the current working directory — `app.py:30`, `104` |
| Re-opened PDF (relative!) | `open('uploads/{}'.format(filename), 'rb')` — `app.py:88`, `193` |
| Upload size cap | `MAX_CONTENT_LENGTH = 16 * 1000 * 1000` — `app.py:16` |
| Session signing key | `SECRET_KEY = 'super secret key'` — `app.py:17` |
| Blocked domains | `link_blocked` list — `app.py:66-67` |

---

## Installation

The repository already ships a working `.venv` (Python 3.12.1). Use it as-is:

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, allow it for the current session and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Prefer to build your own environment instead:

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Linux/macOS:

```bash
cd document-plagiarism-checker
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Docker alternative (uses the pinned `python:3.8.2` image):

```powershell
docker build -t similarity-radar .
docker run --rm -p 5000:5000 similarity-radar
```

---

## Environment Configuration

The application reads **no custom environment variables** — there is no `.env`, no `.env.example`
and no configuration file. The only environment values that influence it are inherited from
third-party code:

| Variable | Read by | Effect |
|---|---|---|
| `HOME` | `googlesearch` | Location of the `.google-cookie` cookie jar: `os.path.join(HOME, '.google-cookie')` |
| `USERHOME` | `googlesearch` | Fallback for `HOME` (note: the library spells it `USERHOME`, **not** `USERPROFILE`) |
| *(fallback)* | `googlesearch` | If neither is set, the jar resolves to the **current working directory** — on a typical Windows shell that is why the committed `.google-cookie` file in the project root is the one that gets used |
| `FLASK_*` | Flask CLI | Only if you start the app with `flask run` instead of `python app.py` (e.g. `FLASK_APP`, `FLASK_DEBUG`) |

Two configuration values are hard-coded in `app.py` and can only be changed by editing the file:

- `app.config['MAX_CONTENT_LENGTH'] = 16 * 1000 * 1000` (`app.py:16`)
- `app.config['SECRET_KEY'] = 'super secret key'` (`app.py:17`) — used to sign the session
  cookie that carries Flask flash messages. Change it to a random value before any real
  deployment.

---

## How to Launch

**Run from the project root.** `app.py` resolves `uploads/` and `word.txt` relative to the
current working directory, and the PDF branch opens `uploads/<file>` with a relative path.

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
.\.venv\Scripts\Activate.ps1
python app.py
```

Expected console output:

```
 * Serving Flask app 'app'
 * Debug mode: off
WARNING: This is a development server. For production, use a production WSGI server.
 * Running on http://127.0.0.1:5000
 * Running on http://<your-lan-ip>:5000
Press CTRL+C to quit
```

- **Port: 5000** — `app.run(host="0.0.0.0", debug=False)` uses Flask's default port
  (`app.py:231-232`). The server listens on **all interfaces**, so it is reachable from
  other machines on the network as well as from `http://127.0.0.1:5000`.
- **Front end = back end.** The UI is a Jinja template rendered by Flask; there is no
  separate static server and no CORS involved. Open `http://127.0.0.1:5000/` in a browser.
- **Production-style start (optional):** `gunicorn app:app --log-file=-` (see `Procfile`) or
  `python -m flask run --host=0.0.0.0` (see `Dockerfile`).

**To stop:** press `Ctrl+C` in the terminal running the app.

**Run the smoke test:**

```powershell
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

---

## Model and Dataset Setup

There is **no model and no dataset** in this project — it is a rule-based web-presence
checker, not a trained model.

| Item | Status |
|---|---|
| Trained model / weights | **Not applicable** — none is used, and none is needed |
| Local reference corpus | **Not in the repository** — the comparison corpus is the live Google result page, fetched per query |
| Training script | **None** — there is nothing to train |
| `word.txt` | Present (44 bytes): the last pasted text from the verified test run, `"The quick brown fox jumps over the lazy dog."` |
| `uploads/` | Present and empty in a fresh clone; uploaded PDFs are written here at runtime |
| `.google-cookie` | Present (950 bytes): the `LWPCookieJar` file used by `googlesearch`; it is a client cookie store, not a model |

The only "external setup" the app needs is a working internet connection and, optionally,
a Google cookie jar in the location `googlesearch` expects (see
[Environment Configuration](#environment-configuration)). If Google blocks the request,
the scan returns no matches rather than an error.

---

## Usage

### Scan pasted text

1. Open `http://127.0.0.1:5000/`.
2. The **Input desk** opens on the *Paste text* tab. Type or paste a passage — the counters
   under the box update live (`N characters` / `N sentences`, split on `". "` exactly as the
   backend does).
3. Press **Scan originality** (or `Ctrl`/`⌘` + `Enter`).
4. A radar overlay appears: *"Each sentence is being quoted into Google (TLD `co.id`, 10
   results, short pause per query). Long texts can take a minute or two — please keep this
   tab open."*
5. The browser is redirected to `/plagiarism/word#hasil` and the **Results** panel renders:
   - the **status stamp** (*Original* / *Minor overlap* / *High overlap*),
   - the **gauge** with the similarity index (e.g. `0.0 %`),
   - **sentences scanned**, **matched sentences**, and the **TLD used**,
   - the list of **matched sentences** with their source links (copy sentence / copy link),
   - the full **sources** list,
   - and an *explainer* restating the four method steps and their honest limits.

Example input used during the verified test run:

```
The quick brown fox jumps over the lazy dog.
```

Result: the request returned `302` to the results page, the page returned `200`, live
Google queries completed in about 3 seconds, **0 matches** were found and the index
rendered as **0.0 %** — i.e. the stamp read *Original*.

### Scan a PDF

1. Click the **Upload PDF** tab.
2. Drop a PDF on the zone (or click it to browse). The client rejects anything that is not
   a `.pdf` or that exceeds 16 MB before anything is uploaded.
3. Press **Scan originality**. The server saves the file to `uploads/` (with
   `secure_filename`) and extracts the text page by page with PyPDF2.
4. The extracted text is split into sentences and processed exactly like pasted text.

### Reading the result

- **Similarity index** = matched sentences ÷ total sentences × 100.
- **Thresholds used by the page**: `0 %` → *Original*, `< 30 %` → *Minor overlap*,
  `≥ 30 %` → *High overlap*.
- **A match means** the exact quoted sentence appeared in the first 10 Google results for
  that sentence's query (after blocked-domain filtering). It does **not** mean the text is
  stolen, and paraphrased or translated passages will not match.

### Edge behaviour worth knowing

- Submitting **both** fields empty produces the flash message *"Please fill the form"*.
- Submitting a **non-PDF** file silently returns to the input desk with no message
  (the server-side branch only handles allowed extensions).
- Only the **first 10 sentences** of a document can ever register a match, because the
  result index is bounded by the 10-result search window.

---

## API Documentation

The project exposes exactly two Flask routes — there is no JSON API, no REST resource and
no authentication. Both routes render the same HTML template.

| Method | Path | Request | Response | Errors |
|---|---|---|---|---|
| `GET` | `/` | none | `200` — the Similarity Radar page (≈10.5 KB of HTML) | — |
| `POST` | `/` | `multipart/form-data` with `text` (string) **and** `file` (file part, may be empty) | `302` → `/plagiarism/word#hasil` when `text` is filled and `file` is empty; `302` → `/plagiarism/#hasil` when a PDF is attached; `302` back to `/` with flash *"Please fill the form"* when both are empty | `400` when the upload exceeds `MAX_CONTENT_LENGTH` (16 MB) |
| `GET` | `/plagiarism/<name>` | `name` = `word` (re-runs the scan on `word.txt`) or an uploaded filename (re-extracts that PDF) | `200` — the results page with the similarity index, matched sentences and sources | `500` if `uploads/<name>` does not exist (e.g. after a restart cleared the folder) |
| `POST` | `/plagiarism/<name>` | `multipart/form-data` with `text` and `file` | `200` — same results page, rendered from the freshly submitted input | same as above |

The `GET|POST /plagiarism/<name>` route also accepts a `POST` body and re-runs the scan
without redirecting — the form on the desk posts to `/`, so in normal use this route is
reached through the `302`.

Flash messages are carried in Flask's signed session cookie, signed with the hard-coded
`SECRET_KEY` in `app.py:17`.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | The virtualenv is not active | `.\.venv\Scripts\Activate.ps1`, then `python app.py` |
| `FileNotFoundError: [Errno 2] No such file or directory: 'uploads/…'` on a PDF scan | The app was started from a different directory | `app.py` opens `uploads/<file>` with a relative path — always start it from the project root |
| Uploaded PDF never appears in the results | The upload was not a `.pdf`, so `allowed_file()` returned `False` and the request silently re-rendered the desk | Use a real PDF; the UI also validates the extension client-side |
| Scan takes minutes | Each sentence triggers **two** `search()` calls with `pause=2` → roughly 4 s per sentence | Scan fewer sentences, or shorten the passage; the pause exists to avoid Google rate-limiting |
| `429`/empty result lists from Google | Google throttled or blocked the scraper | Wait a few minutes, or provide a usable `.google-cookie` in the location `googlesearch` resolves (see [Environment Configuration](#environment-configuration)) |
| Port 5000 already in use | Another Flask app occupies the default port | Stop the other process, or run `python -m flask run --port 5001` (and use that URL) |
| `Address already in use` on Windows | Stale `python.exe` still holding the socket | `Get-Process python | Stop-Process -Force`, then start again |
| "Please fill the form" flash | Both the text box and the file field were empty | Provide one of the two inputs |
| Scan returns 0 matches for text you believe is copied | Paraphrased text, or the matching page is not in the top 10 for the `co.id` Google TLD | The method is exact-phrase only; a paraphrased passage is invisible to it |
| `pip install -r requirements.txt` fails on Python 3.13+ | The pins target the 3.12-era stack (`MarkupSafe==2.1.1`, `zipp==3.10.0`) | Use Python 3.12.1 (the bundled `.venv` already is) |
| `pytest` cannot import `app` | Wrong working directory | Run pytest from the project root |

---

## Limitations

- **Exact-phrase only.** Paraphrased, translated or reformatted text is not detected.
- **Top-10 window.** Only the first 10 Google results per sentence are considered, and
  only the **first 10 sentences** of a document can register a match (the code pairs
  sentence *i* with result *i*).
- **A "match" is not proof of plagiarism.** The same sentence can legitimately appear in
  many documents (quotations, standard wording, licences).
- **Two search calls per sentence** and a 2-second pause make long documents slow
  (roughly 4 s per sentence) and Google rate-limits can break a scan.
- **Blocked-domain list is hard-coded** (`app.py:66-67`) — new social/marketplace domains
  are not filtered, and legitimate academic hosts are not whitelisted.
- **Shared server state**: `word.txt` and `uploads/` are global; two visitors interfere
  with each other, and uploaded files are never cleaned up.
- **No session/history**: results live only in the URL and are lost when the server
  restarts (`word.txt` survives; `uploads/` content may not).
- **PDF text extraction is naive** — scanned/image-only PDFs yield no text, and PyPDF2
  extraction of complex layouts can scramble reading order.
- **No report export** (no PDF/CSV of the result) and no batch/multi-file scan.
- **No API**, so the checker cannot be embedded in another application as-is.
- **Debug server, no TLS, hard-coded secret key** — fine for local use, not for the
  public internet as written.
- **Upstream metadata mismatch**: `project-metadata.json` advertises a TF-IDF / local-corpus
  goal that the code does not implement; the badges in the original README point at
  `plagiarism-checker-flask` while the metadata URL is `plagiarism-check`.

---

## License and Credits

- **Upstream project:** *Plagiarism Checker Flask* by **Regi Apriandi** —
  <https://github.com/regiapriandi012/plagiarism-check> (badge links in the original README
  reference `plagiarism-checker-flask`).
- **License:** MIT — see `LICENSE.md`, *Copyright (c) 2022 Regi Apriandi*. The license and
  original attribution are preserved unchanged.
- **Added later (not part of the upstream release):** the *Similarity Radar* interface —
  the redesigned `templates/index.html`, `static/css/style.css`, `static/js/app.js`, the
  `/plagiarism/<name>` results view with the gauge and stamp, the honest method explainer,
  this `README.md` and `PROJECT_OVERVIEW.md`. The upstream template is kept at
  `templates/index.html.bak`.
- **Third-party dependencies:** Flask, Jinja2, Werkzeug (BSD-3-Clause), PyPDF2 (BSD-3-Clause),
  `google`/`googlesearch` (MIT), beautifulsoup4 (MIT), gunicorn (MIT), pytest (MIT).
  Google is queried as an external service; see Google's terms of service before using
  this at scale.
