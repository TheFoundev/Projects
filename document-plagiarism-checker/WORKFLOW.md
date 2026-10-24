# Similarity Radar (document-plagiarism-checker) — Setup & Test Workflow

**Folder id:** `document-plagiarism-checker`
**UI name:** Similarity Radar
**Stack:** Flask 2.2.2 · Jinja2 3.1.2 · Werkzeug 2.2.2 · PyPDF2 2.11.1 · `google` 3.0.0 (imports as `googlesearch`) · gunicorn 20.1.0 · pytest 7.0.1
**Entry point:** `app.py` (single-file Flask app; no build step, no front-end framework, no JavaScript bundler)

**What it actually is:** a server-rendered web app that splits your text (pasted or extracted
from a PDF) into sentences, quotes each sentence verbatim into a live Google search
(TLD `co.id`, 10 results, 2-second pause), filters out social/marketplace domains, and reports
a similarity index of `matched sentences ÷ total sentences × 100`. It is a *web-presence*
measure, not a semantic/TF-IDF comparison — there is no local corpus and no API key.

**Runtime surfaces:**

| Surface | Kind | Port | Needs internet? |
|---|---|---|---|
| `app.py` → `/` and `/plagiarism/<name>` | Flask web app (server-rendered HTML) | 5000 | **Yes** — every scan queries Google |
| `python -m pytest -q` | Automated smoke test | n/a | No |

---

### 1. Prerequisites

- **Windows 10/11** with PowerShell (all commands below are Windows PowerShell).
- **Python 3.12.1** — the bundled `.venv` was created with it and every pinned package
  installs cleanly on 3.12. The pins (`MarkupSafe==2.1.1`, `zipp==3.10.0`) target the
  3.12-era stack; do **not** use Python 3.13+.
- **An internet connection** — mandatory for any scan. `app.py` calls
  `googlesearch.search(query, tld="co.id", num=10, stop=10, pause=2)` for every sentence.
- **No Node.js, no database, no API key, no Google Custom Search credentials.**
- **Optional:** Docker Desktop, if you prefer the container path.
- **Free disk space:** negligible (< 100 MB); the `.venv` is already present.

Environment variable that matters (read by the `googlesearch` library, not by this repo):

| Variable | Effect |
|---|---|
| `HOME` | Location of the `.google-cookie` cookie jar → `os.path.join(HOME, ".google-cookie")` |
| `USERHOME` | Fallback for `HOME` (note: the library spells it `USERHOME`, **not** `USERPROFILE`) |
| *(fallback)* | If neither is set, the jar resolves to the **current working directory** → `<cwd>\.google-cookie`. On a typical Windows shell neither `HOME` nor `USERHOME` is set, so this is the branch that actually runs — **the file is created by the library on the first successful Google request; no `.google-cookie` ships with the repository.** Set `HOME` to a writable path if you want the jar kept out of the project folder |

**Hard-coded settings in `app.py` (change by editing the file, not by environment):**

| Setting | Value | Line |
|---|---|---|
| Upload size cap | `MAX_CONTENT_LENGTH = 16 * 1000 * 1000` (16 MB) | `app.py:16` |
| Session signing key | `SECRET_KEY = 'super secret key'` | `app.py:17` |
| Allowed upload extension | `{'pdf'}` only | `app.py:9`, `app.py:19-21` |
| Search TLD / results / pause | `co.id` / `10` / `2` s | `app.py:55`, `app.py:109` |
| Blocked domains | LinkedIn, YouTube, Instagram, Facebook, Twitter, Reddit, Tokopedia, Bukalapak, Shopee, Blibli | `app.py:66-67` |

> **`SECRET_KEY` is a development placeholder.** It is committed in source and signs the
> Flask session cookie that carries flash messages. Do not deploy this as-is; generate a
> random value before any real use.

---

### 2. Installation and Setup

The repository already ships a working virtualenv (`.venv`, Python 3.12.1, all pins
installed). **Use it as-is:**

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
.\.venv\Scripts\Activate.ps1
```

If PowerShell refuses to run the activation script, allow it for the current session and retry:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Confirm the interpreter and the key packages:

```powershell
python --version
python -m pip list
```

Expected: `Python 3.12.1` and `Flask 2.2.2`, `PyPDF2 2.11.1`, `google 3.0.0`,
`gunicorn 20.1.0`, `pytest 7.0.1`.

**To rebuild the environment from scratch** (only if `.venv` is missing or broken):

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Runtime directories and files the app expects** (all relative to the working directory):

```powershell
# uploads/ already exists and holds a sample PDF (cek.pdf) — the app writes here.
Test-Path .\uploads
Test-Path .\uploads\cek.pdf
Get-ChildItem .\uploads
```

- `uploads/` — where uploaded PDFs are saved (`UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')`, `app.py:7-8`).
- `word.txt` — scratch file holding the last pasted text (`app.py:30`, `app.py:104`).
- `templates/index.html` — the Jinja template; `templates/index.html.bak` is the preserved original upstream template.
- `static/css/style.css`, `static/js/app.js` — the radar gauge, tabs, counters, drag-and-drop and copy buttons.

**Optional — Docker path** (uses the pinned `python:3.8.2` image from the `Dockerfile`):

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
docker build -t similarity-radar .
docker run --rm -p 5000:5000 similarity-radar
```

**There is no configuration file and no `.env`.** Nothing to edit for a local run.

---

### 3. Launch the Complete Project

**You must start the app from the project root.** `app.py` resolves `uploads/` and
`word.txt` against `os.getcwd()`, and the PDF branch re-opens the file with the *relative*
path `uploads/<file>` (`app.py:88`, `app.py:193`). Starting from any other directory breaks
PDF scans.

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

- **Port 5000** — `app.run(host="0.0.0.0", debug=False)` (`app.py:231-232`) uses Flask's
  default port and binds **all interfaces**, so the app is also reachable from other
  machines on your LAN.
- **Front end = back end.** The UI is a Jinja template rendered by Flask. There is no
  separate static server, no CORS, no build step.
- **Open:** <http://127.0.0.1:5000/>
- **Stop:** `Ctrl+C` in the terminal running the app.

**Production-style starts (optional, same code):**

```powershell
# From the Procfile
gunicorn app:app --log-file=-
# From the Dockerfile
python -m flask run --host=0.0.0.0
```

**Typical first-run flow (for reference):**

1. Open <http://127.0.0.1:5000/> — the *Input desk* opens on the **Paste text** tab.
2. Paste a passage. The live counters under the box update (`N characters` / `N sentences`),
   split on `". "` exactly as the backend does.
3. Press **Scan originality** (or `Ctrl`/`⌘` + `Enter`).
4. A scanning overlay appears: *"Each sentence is being quoted into Google (TLD `co.id`,
   10 results, short pause per query). Long texts can take a minute or two — please keep
   this tab open."*
5. The browser is redirected to `/plagiarism/word#hasil` and the **Results** panel renders:
   the status stamp (*Original* / *Minor overlap* / *High overlap*, thresholds 0 % / < 30 % /
   ≥ 30 %), the SVG gauge with the similarity index, the counts of sentences scanned and
   sentences matched, the TLD used, the matched sentences with their source links, and the
   full sources list.

**PDF mode:** switch to the **Upload PDF** tab, drop a `.pdf` on the zone (or click to
browse), press **Scan originality**. The client rejects non-PDF files and files over 16 MB
before uploading. The server saves the file to `uploads/` via `secure_filename` and
extracts text page by page with PyPDF2.

---

### 4. Test the Project

#### 4a. Automated test (pytest) — the only automated suite in this project

`test_app.py` contains exactly one test: it asserts that `GET /` returns HTTP 200.

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker"
.\.venv\Scripts\Activate.ps1
python -m pytest -q
```

Expected result:

```
.                                                                        [100%]
1 passed, 127 warnings in 0.71s
```

(The warnings are `ast.Str`/`ast.NameConstant` deprecation notices emitted by the pinned
`pytest 7.0.1` / `Werkzeug 2.2.2` on Python 3.12 — they are harmless and are not failures.)

**Important:** pytest must be run from the project root, otherwise `from app import app`
fails to resolve.

#### 4b. HTTP route tests (manual, against the running server)

Start the server first (Section 3), then in a **second** PowerShell window exercise each
route.

| # | Method | Path | Example input | Expected output |
|---|---|---|---|---|
| 1 | `GET` | `/` | *(none)* | `200 OK`, ~10.5 KB of HTML containing the *Similarity Radar* page, the input desk and the radar gauge markup |
| 2 | `POST` | `/` | `multipart/form-data` with `text="The quick brown fox jumps over the lazy dog."` and an **empty** `file` part | `302` redirect to `/plagiarism/word#hasil`; the text is written to `word.txt` |
| 3 | `GET` | `/plagiarism/word` | *(none)* | `200 OK` — re-runs the scan over the stored `word.txt` and renders the results page (index + matched sentences + sources). Requires internet |
| 4 | `POST` | `/` | `multipart/form-data` with an **empty** `text` field and `file` = `uploads/cek.pdf` | `302` to `/plagiarism/cek.pdf#hasil`; the PDF is saved to `uploads/` and its text extracted with PyPDF2 |
| 5 | `GET` | `/plagiarism/cek.pdf` | *(none)* | `200 OK` — results page for the uploaded PDF, provided `uploads/cek.pdf` still exists |
| 6 | `POST` | `/` | both `text` and `file` **empty** | `302` back to `/` with the flash message *"Please fill the form"* |

Concrete PowerShell invocations for the same checks:

```powershell
# 1 — index page
Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -UseBasicParsing | Select-Object StatusCode, @{n='Bytes';e={$_.RawContentLength}}

# 2 — paste-text scan (expect a 302 to /plagiarism/word)
try {
  Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method POST `
    -Body @{ text = "The quick brown fox jumps over the lazy dog."; file = "" } `
    -MaximumRedirection 0 -UseBasicParsing
} catch {
  $_.Exception.Response.Headers["Location"]
}

# 6 — empty submission (expect a 302 back to / plus the flash text)
Invoke-WebRequest -Uri "http://127.0.0.1:5000/" -Method POST `
  -Body @{ text = ""; file = "" } -MaximumRedirection 0 -UseBasicParsing -ErrorAction SilentlyContinue
```

**Expected values to look for in the results page:**

- The similarity index rendered in the gauge, formatted to one decimal (`0.0` when nothing matched).
- The status stamp: *Original* (0 %), *Minor overlap* (< 30 %), *High overlap* (≥ 30 %).
- The number of sentences scanned and the number matched.
- The matched-sentence list, each entry with its source URL and *Copy sentence* / *Copy link* buttons.

**Reference verified behaviour:** a single-sentence paste of *"The quick brown fox jumps over
the lazy dog."* produced a `302` to the results page, the page returned `200`, the live
Google queries completed in roughly 3 seconds, **0 matches** were found and the index
rendered as **0.0 %** (status *Original*).

#### 4c. Manual / browser checks

- [ ] The *Paste text* tab and the *Upload PDF* tab both toggle, and the choice survives a page reload (`localStorage["radarInputMode"]`).
- [ ] The character and sentence counters update live while typing.
- [ ] Dragging a non-PDF file onto the drop zone is rejected client-side before any upload.
- [ ] A PDF larger than 16 MB is rejected client-side; a PDF over the limit that reaches the server returns `400`.
- [ ] The *Copy sentence* / *Copy link* buttons put the text on the clipboard.
- [ ] `Ctrl`/`⌘` + `Enter` triggers the scan.
- [ ] Uploading a file that is not a PDF returns to the input desk **with no message** (the server-side branch silently ignores disallowed extensions).

#### 4d. What is *not* tested here

- There is **no** test for `/plagiarism/<name>`, no test for the PDF branch, and no test
  that exercises Google. `test_app.py` is a single smoke test of `GET /`.
- CI (`.github/workflows/python-app.yml` and friends) runs the same single test plus
  CodeQL / dependency-review / Docker publish jobs.

---

### 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'flask'` | Virtualenv not active | `.\.venv\Scripts\Activate.ps1`, then `python app.py` |
| `.\.venv\Scripts\Activate.ps1` is blocked by policy | PowerShell execution policy | `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass`, then retry |
| `FileNotFoundError: ... 'uploads/...'` during a PDF scan | App started from the wrong directory — `app.py` opens `uploads/<file>` with a **relative** path | Always `cd` to the project root before `python app.py` |
| Uploaded PDF never appears in the results | The file was not a `.pdf`, so `allowed_file()` returned `False` and the request silently re-rendered the desk | Use a real PDF; the UI validates the extension client-side too |
| Scan takes minutes | Each sentence triggers **two** `search()` calls with `pause=2` → roughly **4 s per sentence** | Scan fewer sentences or shorten the passage; the pause exists to avoid Google rate-limiting |
| `429` / empty result lists | Google throttled or blocked the scraper | Wait a few minutes, then retry. To point the cookie jar somewhere writable, set `HOME` (e.g. `$env:HOME = "$env:USERPROFILE"`) — otherwise it is created at `<cwd>\.google-cookie` on the first successful request |
| Port 5000 already in use | Another Flask app holds the port | Stop it, or run `python -m flask run --port 5001` and use that URL |
| `Address already in use` on Windows | A stale `python.exe` still holds the socket | `Get-Process python | Stop-Process -Force`, then start again |
| Flash message *"Please fill the form"* | Both the text box and the file field were empty | Provide exactly one of the two inputs |
| Scan returns 0 matches for text you believe is copied | The method is exact-phrase only, and the matching page may not be in the top 10 for the `co.id` TLD | Paraphrased text is invisible to this method by design |
| `pip install -r requirements.txt` fails on Python 3.13+ | The pins target the 3.12-era stack | Use Python 3.12.1 (the bundled `.venv` already is) |
| `pytest` reports `ModuleNotFoundError: No module named 'app'` | Wrong working directory | Run pytest from the project root |
| `413 Request Entity Too Large` | PDF over the 16 MB cap | Raise `MAX_CONTENT_LENGTH` at `app.py:16`, or upload a smaller file |
| `500` on `GET /plagiarism/<name>` | `uploads/<name>` no longer exists (e.g. the folder was cleared) | Re-upload the PDF through the form |
| Page loads but the results panel is empty | Google returned no results (throttled or blocked) — the app does not error, it just reports no matches | See the `429` row above |

---

### 6. Verification Checklist

**Prerequisites and environment**

- [ ] Windows 10/11 and PowerShell are available.
- [ ] Python 3.12.1 is the interpreter in use (`python --version`).
- [ ] The working directory is `N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\document-plagiarism-checker`.
- [ ] The machine has a working internet connection (required for every scan).
- [ ] `.venv\Scripts\Activate.ps1` completes without a policy error.
- [ ] `python -m pip list` shows `Flask 2.2.2`, `PyPDF2 2.11.1`, `google 3.0.0`, `gunicorn 20.1.0`, `pytest 7.0.1`.

**Files and directories the app depends on**

- [ ] `app.py` exists and is the entry point.
- [ ] `templates\index.html` exists (`templates\index.html.bak` preserved as the original).
- [ ] `static\css\style.css` and `static\js\app.js` exist.
- [ ] `uploads\` exists and is writable (`Test-Path .\uploads` → `True`).
- [ ] `word.txt` exists in the project root.

**Launch**

- [ ] `python app.py` starts without a traceback.
- [ ] The console shows `Running on http://127.0.0.1:5000`.
- [ ] `http://127.0.0.1:5000/` opens the Similarity Radar page in a browser.
- [ ] `Ctrl+C` stops the server cleanly.

**Automated test**

- [ ] `python -m pytest -q` runs from the project root.
- [ ] The result is `1 passed` (warnings about `ast.Str` deprecation are acceptable).
- [ ] The `test_app.py` test asserts `GET /` → 200.

**Route tests (against the running server)**

- [ ] `GET /` → `200` with the radar page HTML.
- [ ] `POST /` with text only → `302` to `/plagiarism/word#hasil`.
- [ ] `GET /plagiarism/word` → `200` with a similarity index rendered.
- [ ] `POST /` with `uploads/cek.pdf` → `302` to `/plagiarism/cek.pdf#hasil`, and the file appears in `uploads\`.
- [ ] `GET /plagiarism/cek.pdf` → `200` with PDF-derived results.
- [ ] `POST /` with both fields empty → `302` back to `/` and the flash *"Please fill the form"*.

**Manual UI checks**

- [ ] The Paste text / Upload PDF tabs toggle and persist across reload.
- [ ] Character and sentence counters update live.
- [ ] A non-PDF file and a >16 MB file are rejected client-side.
- [ ] Copy sentence / Copy link write to the clipboard.
- [ ] `Ctrl`/`⌘` + `Enter` starts a scan.

**Security note (read before any shared deployment)**

- [ ] The hard-coded `SECRET_KEY = 'super secret key'` at `app.py:17` is understood to be a
      development-only value and has been replaced with a random secret before any
      non-local deployment.
- [ ] The app is not exposed to the public internet as shipped: it is the Flask development
      server, it binds `0.0.0.0`, it has no authentication, and `word.txt` / `uploads/` are
      shared global state across all visitors.
