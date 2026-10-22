# Note Sense

*Folder id: `currency-note-recognition-for-visually-impaired`*

Note Sense is a voice-first web front end for a classic OpenCV currency-note detector.
The repository ships two things that were never connected to each other:

1. **A real, working desktop recogniser** — `Currency Detection using OpenCV in ML/detect.py`, an
   ORB feature-matching pipeline that identifies an Indian banknote by comparing it against six
   reference photographs and prints `Detected denomination: Rs. <value>`.
2. **A static, accessible web page** (`index.html` + `css/style.css` + `js/app.js`) that lets a
   visually impaired user pick a photo, browse the reference set, and play the project's own
   pre-recorded rupee announcements.

There is **no server, no HTTP API and no model service** in this project. The web page is
deliberately honest about that: pressing *Identify note* does not invent a denomination — it
switches the result banner to a **“Requires backend”** state that explains that recognition only
happens inside the local OpenCV script, and shows the exact command to run it.

> Upstream project: [deveshwar7/Currency-Detector-System-for-visually-impaired-people-using-PYTHON-OPENCV-COMPUTER-VISION](https://github.com/deveshwar7/Currency-Detector-System-for-visually-impaired-people-using-PYTHON-OPENCV-COMPUTER-VISION).
> The Note Sense page and this documentation were added later; the OpenCV code is not ours.

---

## Features

### Implemented and verified by reading the source

| Feature | Where | Status |
|---|---|---|
| ORB keypoint detection + brute-force matching + Lowe's ratio test | `Currency Detection using OpenCV in ML/detect.py` | Implemented, runs locally |
| Denomination print-out (`Detected denomination: Rs. 200`) | `detect.py` | Implemented |
| Match visualisation window (OpenCV + matplotlib) | `detect.py` → `cv2.drawMatchesKnn`, `utils.display()` | Implemented |
| Reusable image-processing helpers (Canny, Sobel, Laplacian, Harris, FFT, contours, gamma, histogram) | `Currency Detection using OpenCV in ML/utils.py` | Implemented (mostly used by `try.py` experiments) |
| Voice-first UI: file picker + drag & drop, local preview, Web Speech read-aloud, keyboard/lightbox navigation | `index.html`, `js/app.js` | Implemented |
| Local backend that serves the page and recognises an uploaded photo (ORB matching, JSON result) | `server.py`, `detector.py` | Implemented |
| Result banner that shows the real detection (denomination, match count, runner-up) and speaks it | `js/app.js` (`detectWithBackend`, `setBanner`) | Implemented |
| Honest "Requires backend" result banner instead of a fabricated prediction when the backend is down | `js/app.js` (`BACKEND_KICKER` / `BACKEND_TITLE` / `BACKEND_BODY`) | Implemented |
| Playback of the repository's real rupee announcements (₹20, ₹50, ₹100) | `Currency Detection using OpenCV in ML/audio/*.mp3` via `<audio>` | Implemented (3 files exist) |
| Reference gallery of all 44 images in `files/`, each labelled *Training reference* / *Hardcoded test image* / *Test photo* / *Reference photo* | `js/app.js` (`FILES`, `TRAINING`, `HARDCODED`, `roleFor()`) | Implemented |

### Not available / not implemented

- **No recognition in the browser.** OpenCV cannot run in the page; the *Identify note* button posts
  the photo to the local backend (`server.py`), and if that backend is not running the banner says so
  instead of inventing a result.
- **No cloud or third-party API.** The only endpoint is the local `POST /api/detect` (see
  [API Documentation](#api-documentation)).
- **No TTS in the pipeline.** `detect.py` imports `gTTS` and `playsound`, but every line that would
  speak the value is commented out — the announcement audio is therefore played by the web page from
  the pre-recorded MP3s, not generated per detection.
- **No ₹200 or ₹500 audio sample.** `audio/` contains only `20.mp3`, `50.mp3` and `100.mp3`, so the
  page offers exactly those three buttons.
- **No trained ML model.** There is no neural network here; the "model" is the set of reference JPEGs
  in `files/`.
- **No webcam capture in the UI.** The chosen photo is previewed locally; it is sent to the local
  backend only when *Identify note* is pressed.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Detector | Python 3, OpenCV (`cv2.ORB_create`, `cv2.BFMatcher`, `cv2.drawMatchesKnn`) |
| Plotting | `matplotlib` (matplotlib.pyplot) — match map window |
| Numerics | `numpy` (used by `utils.py`) |
| Audio (declared, currently unused) | `playsound`, `gtts` |
| UI | Vanilla HTML5 + CSS + ES5 JavaScript — no framework, no build step |
| Accessibility | Web Speech API (`speechSynthesis`) for read-aloud, ARIA roles, focus trap in the lightbox, `prefers-reduced-motion` support |

---

## Prerequisites

- **Windows 10/11** first (commands below are PowerShell); macOS/Linux variants are noted inline.
- **Python 3.8–3.11 recommended.** The pinned `requirements.txt` dates from 2020 (`numpy==1.19.4`,
  `matplotlib==3.3.2`, `Pillow==8.0.1`) and will **not** build on Python 3.12. Use the relaxed
  versions in [Installation](#installation) if you are on 3.12.
- **A display.** `detect.py` calls `utils.display()` (an OpenCV window that waits for a key press)
  and `plt.show()`, so it needs a GUI session. It cannot run headless.
- **No API keys, no network access, no GPU.**
- Node.js is *not* required (the UI is static). Python's standard library `http.server` is enough
  if you want to serve the page over HTTP.

---

## Project Structure

```
currency-note-recognition-for-visually-impaired/
├── index.html                     # Note Sense UI (static, no server)
├── css/style.css                  # UI styles
├── js/app.js                      # UI logic: preview, gallery, lightbox, read-aloud, honest banner
├── project-metadata.json          # Repository metadata (upstream URL, entry point)
├── Images/                        # Extra image sets shipped with the repo
│   ├── currency_images/           # 5 reference note photos (100_rs, 200_rs, 20_rs, 500_rs, 50_rs)
│   └── testing_images/            # 21 test photos (incl. Euro-500.png, test_dollar_*.jpg)
└── Currency Detection using OpenCV in ML/
    ├── detect.py                  # ← MAIN ENTRY POINT (top-level script, hardcoded paths)
    ├── utils.py                   # ← image helpers (read_img, resize_img, display, edge ops…)
    ├── try.py                     # experiment sandbox: same ORB idea with a 10-image training set
    ├── run.bat                    # "python detect.py runserver" (the word "runserver" is ignored by detect.py)
    ├── requirements.txt           # 2020-era pinned deps
    ├── README.md                  # upstream note: "python3 detect.py"
    ├── files/                     # ← REFERENCE SET: 44 JPGs (6 of them used as training refs)
    └── audio/                     # 20.mp3, 50.mp3, 100.mp3 (real pre-recorded announcements)
```

Paths that matter at runtime:

- **Test image (hardcoded):** `files/test_200_1.jpg` — assigned at `detect.py:22` (it overrides the
  `files/test_100_4.jpg` assignment on line 20).
- **Training references:** `files/20.jpg`, `files/50.jpg`, `files/100.jpg`, `files/500.jpg`,
  `files/200.jpg`, `files/test_20_6.jpg` (`detect.py:32`).
- **Audio:** `audio/<denomination>.mp3` (`detect.py:68`, currently overwritten by the literal
  `"value.mp3"` on line 69).

---

## Installation

The detector lives in a subfolder that uses **relative paths**, so the virtual environment can live
either in that folder or in the project root.

### Option A — as the upstream `requirements.txt` intends (Python ≤ 3.9)

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install playsound gTTS
```

```bash
# macOS / Linux
cd "Currency Detection using OpenCV in ML"
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install playsound gTTS
```

> `playsound` and `gTTS` are **not** in `requirements.txt` but they *are* imported at the top of
> `detect.py` (`from playsound import playsound`, `from gtts import gTTS`), so the script fails to
> start without them even though the code that uses them is commented out.

### Option B — Python 3.10/3.11 (recommended for this repo)

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "opencv-python>=4.8,<5" "numpy>=1.24,<2" "matplotlib>=3.7,<4" "pillow>=10" playsound gTTS
```

### Option C — Python 3.12 (the 2020 pins do not build here)

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install "opencv-python>=4.10,<5" "numpy>=2.0,<3" "matplotlib>=3.9,<4" "pillow>=10" playsound gTTS
```

### Serving the Note Sense page

The page needs the local backend, which also serves the static files:

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired"
python server.py
```

Then open <http://127.0.0.1:8000/> and use *Choose a note photo* → *Identify note*.

A plain static server still works for browsing the gallery and the audio samples, but the
*Identify note* button then shows the backend-required notice, because there is no
`/api/detect` behind it:

```powershell
python -m http.server 8000
```

---

## Environment Configuration

**There is none.** The code reads no environment variables, no `.env` file, no config file and no
command-line arguments. Everything is hardcoded in `detect.py`:

| Setting | Hardcoded value | Location |
|---|---|---|
| Test image | `files/test_200_1.jpg` | `detect.py:22` |
| Training set | 6 files under `files/` | `detect.py:32` |
| Minimum good matches | `max_val = 8` | `detect.py:10` |
| Lowe's ratio | `0.789` (source comment: “give an arbitrary number”) | `detect.py:48` |
| Preview scale | `0.4` | `detect.py:25` |
| ORB instance | `cv2.ORB_create()` with default parameters | `detect.py:14` |
| Display window size | `1440 x 900` (hardcoded “MacBook Air” resolution) | `utils.py:171` |

To test your own photo you edit one line — the `test_img = read_img(...)` assignment — and drop the
file into `files/`.

---

## How to Launch

### 1. The detector (the only thing that produces a denomination)

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"
.\.venv\Scripts\Activate.ps1
python detect.py
```

- **Must be run from inside the `Currency Detection using OpenCV in ML` folder** — `detect.py` does
  `from utils import *` and opens `files/...` with relative paths.
- A window titled `original` appears (scaled preview). **Press any key** to dismiss it
  (`utils.display()` calls `cv2.waitKey(0)`).
- The console then prints, per reference image, the number of “good” matches, e.g.
  `0   files/20.jpg   37`, followed by the winner and
  `Detected denomination: Rs. 200`.
- Finally a matplotlib window shows the matched keypoints. Close it to end the script.
- **Stop:** press `Esc`/`q` in the OpenCV window, or `Ctrl+C` in the terminal.

### 2. The Note Sense page (with recognition)

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired"
python server.py
```

- Open <http://127.0.0.1:8000/>.
- **Stop:** `Ctrl+C` in the terminal.

The page posts the chosen photo to `POST /api/detect`; the server runs the same ORB pipeline as
`detect.py` and answers with the denomination, the number of good matches and the runner-up. The
result banner then shows and reads out that denomination.

`detect.py` keeps working on its own, unchanged, for the desktop workflow.

---

## Model and Dataset Setup

**No model download and no training step exist.** The “model” is the set of reference photographs.

| Item | Status | Where the code expects it |
|---|---|---|
| Reference images | **Present** — 44 JPGs in `Currency Detection using OpenCV in ML/files/` | `detect.py:32` lists 6 of them as the training set |
| Test images | **Present** — `files/test_*.jpg` plus `Images/testing_images/` | `detect.py:22` reads `files/test_200_1.jpg` |
| Trained weights / `.h5` / `.pt` | **Does not exist** (and is not needed) | — |
| Audio samples | **Present** — `audio/20.mp3`, `50.mp3`, `100.mp3` | `detect.py:68` expects `audio/<value>.mp3` |
| `Images/currency_images/` | Present but **unused by the code** — a second, smaller set (100/200/20/500/50 ₹) | referenced only by the gallery in `js/app.js` |

**To recognise a new note (e.g. ₹2000):** add `files/2000.jpg` and add its path to the
`training_set` list in `detect.py:32`. No retraining, no weights — just one more reference photo.

---

## Usage

### Using the Note Sense page

1. **Step 1 — Choose a note photo.** Drag a JPG/PNG onto the drop zone or use the big
   *Choose a note photo* button. The page previews it locally; nothing is uploaded.
2. **Step 2 — Identify note.** The *Identify note* button is enabled once a preview shows. Pressing it
   switches the result banner to the honest *“Requires backend — Recognition needs the local OpenCV
   backend”* message (it does **not** print a denomination).
3. **Step 3 — Result.** Use *Read this aloud* to hear the banner text with your system voice.
   Voice guidance can be toggled in the header (*Voice guidance: ON/OFF*, persisted in
   `localStorage` under `notesense:voice`).
4. **Voice section.** *Play ₹20 / ₹50 / ₹100 sample* plays the repository's real MP3 files;
   *Stop* halts playback.
5. **Gallery.** Every image in `files/` is listed with a role label. Click a thumbnail for a
   full-screen lightbox (`←`/`→` to browse, `Esc` to close, *Read caption aloud* for speech).
6. **Method panel.** A collapsible explanation of the ORB → BFMatcher → ratio-0.789 pipeline.

### Using the detector directly

```powershell
cd "Currency Detection using OpenCV in ML"
# point the test image at your own photo
notepad detect.py      # edit the `test_img = read_img('files/....jpg')` line
python detect.py
```

Example console output (**illustrative — the exact match counts depend on your photos**):

```
0   files/20.jpg   11
1   files/50.jpg   14
2   files/100.jpg   9
3   files/500.jpg   12
4   files/200.jpg   96
5   files/test_20_6.jpg   7
files/200.jpg
good matches  96

Detected denomination: Rs.  200
```

If no reference exceeds the threshold of 8 good matches, the script prints `No Matches`.

---

## API Documentation

The repository ships one small local backend, `server.py` (Python standard library only). It serves
the static page and exposes two routes.

### `POST /api/detect`

Multipart upload of one photo.

| Field | Type | Notes |
|---|---|---|
| `photo` | file | JPG/PNG image, max 12 MB (the field may also be named `file`) |

Response `200 OK`:

```json
{
  "ok": true,
  "denomination": "200",
  "label": "Rs. 200",
  "reference": "200.jpg",
  "good_matches": 468,
  "runner_up": "100",
  "runner_up_matches": 31,
  "method": "ORB + brute force matching + Lowe's ratio 0.789",
  "reference_count": 40,
  "counts": { "200": 468, "100": 31 },
  "filename": "my_note.jpg"
}
```

`ok` is `false` when the best denomination does not pass the minimum of 8 good matches; the JSON
then carries a `message` explaining why no denomination is claimed. The matching itself is the
project's own method (ORB → brute-force → Lowe's ratio `0.789`), run over every reference
photograph in `files/` and grouped per denomination by `detector.py`.

### `GET /api/health`

```json
{ "status": "ok", "references": 40 }
```

> For the record: an earlier brief for this documentation mentioned a
> `POST http://127.0.0.1:5000/recognize` upload endpoint. The live endpoint is
> `POST /api/detect` on port 8000 (the port is configurable with `python server.py --port 8080`).

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'playsound'` (or `gtts`) | `detect.py` imports both at module level; they are missing from `requirements.txt` | `pip install playsound gTTS` |
| `ModuleNotFoundError: No module named 'utils'` | Script launched from the wrong working directory | `cd "Currency Detection using OpenCV in ML"` then `python detect.py` |
| `cv2.imread` returns `None` → `error: (-215:AssertionFailed)` | Relative `files/...` path not found (wrong CWD or file missing) | Run from the script folder; confirm `files/test_200_1.jpg` exists |
| `pip install -r requirements.txt` fails on Python 3.12 | 2020-era pins (`numpy==1.19.4`, `matplotlib==3.3.2`, `Pillow==8.0.1`) have no wheels for 3.12 | Use Option B/C above (unpinned modern versions) |
| Nothing happens after the window opens | `utils.display()` blocks on `cv2.waitKey(0)` | Press any key in the OpenCV window |
| `AttributeError: module 'numpy' has no attribute 'int0'` | `utils.harris_edge()` uses the removed `np.int0` (NumPy ≥ 1.24) | Only hit if you call `harris_edge()`; it is not used by `detect.py` |
| Matplotlib window opens behind the terminal | GUI backend | `python -c "import matplotlib; matplotlib.use('TkAgg')"` before running, or close the OpenCV window first |
| Page shows no thumbnails / broken images | Page opened from the wrong folder | Serve the **project root** (`python -m http.server 8000`) — `js/app.js` resolves `Currency%20Detection%20using%20OpenCV%20in%20ML/files/…` relative to the page |
| *Play ₹X sample* shows “Could not open the sample” | Audio path not resolvable | Serve over HTTP from the project root; only `20.mp3`, `50.mp3`, `100.mp3` exist |
| Read-aloud buttons greyed out | Browser has no Web Speech API | Use a current Chrome/Edge/Firefox; the page disables the buttons and says so |
| `No Matches` printed | The photo differs too much from the six references (lighting, angle, crop) | Add a reference photo of that note to `files/` and list it in `training_set` |

---

## Limitations

- **Manual, single-image workflow.** One hardcoded test image per run; no batch mode, no webcam
  pipeline, no video.
- **Six reference images only.** `detect.py` compares against
  `20 / 50 / 100 / 500 / 200 / test_20_6`. Notes not in that set (₹10, ₹2000, ₹10 notes) can never
  be recognised by `detect.py`, even though such photos exist in `files/` and `Images/`.
- **Photographic sensitivity.** ORB + ratio matching is not robust to strong perspective, glare,
  motion blur or partial occlusion. No orientation normalisation, no perspective rectification
  (`try.py` lists “four point transform / warping” as unfinished TODOs).
- **A real bug in the visualisation.** The `good` list drawn by `cv2.drawMatchesKnn` is the one from
  the **last** loop iteration, not from the winning reference, so the match map can disagree with the
  printed denomination.
- **Threshold semantics.** `max_val` starts at 8 and the result is only printed when
  `max_val != 8`, i.e. strictly more than 8 good matches are required.
- **Denomination is parsed from the file name** (`str(training_set[max_pt])[6:-4]`), so a reference
  file with an unexpected name produces a nonsense label.
- **No evaluation, no accuracy report, no test suite** in the repository.
- **The web page cannot detect anything.** It is an accessibility shell around the reference set and
  the audio samples.
- **Old dependency pins** in `requirements.txt` (2020) do not install on modern Python.

---

## License and Credits

- **Upstream project:** [deveshwar7/Currency-Detector-System-for-visually-impaired-people-using-PYTHON-OPENCV-COMPUTER-VISION](https://github.com/deveshwar7/Currency-Detector-System-for-visually-impaired-people-using-PYTHON-OPENCV-COMPUTER-VISION).
  `detect.py`, `utils.py`, `try.py`, `run.bat`, `requirements.txt`, the `files/` image set and the
  `audio/` announcements are upstream work (`detect.py` header: *UE14CS348 Digital Image Processing
  Mini Project — Indian paper currency detection*).
- **Upstream licence:** not stated in the repository (`project-metadata.json` → `"license": "Unknown"`).
  Treat the upstream code as all-rights-reserved unless the upstream author grants otherwise.
- **Added later (not upstream):** the Note Sense web interface — `index.html`, `css/style.css`,
  `js/app.js` — plus this `README.md` and `PROJECT_OVERVIEW.md`. These files do not change or
  redistribute the upstream detector.
- **Third-party assets:** Google Fonts (Atkinson Hyperlegible) are loaded by `index.html` from
  `fonts.googleapis.com`; the page degrades gracefully to system fonts when offline.
