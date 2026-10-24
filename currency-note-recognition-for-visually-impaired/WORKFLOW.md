# Note Sense (currency-note-recognition-for-visually-impaired) — Setup & Test Workflow

This document covers **how to install, configure, launch and test the complete project**: the OpenCV ORB
recogniser (`Currency Detection using OpenCV in ML/detect.py`), its helper module (`utils.py`), and the
static Note Sense page (`index.html` + `css/style.css` + `js/app.js`, port **8000**).

**Honest scope note up front:**

* **There is no HTTP backend, no API and no model server.** `js/app.js` contains **no `fetch()` call**, no
  `XMLHttpRequest` and no backend URL. Pressing *Identify note* switches the result banner to an honest
  **"Requires backend"** state that explains that recognition happens inside the local OpenCV script and
  shows the exact command to run it.
* **There is no trained model.** The "model" is the set of reference photographs in
  `Currency Detection using OpenCV in ML/files/` (44 JPGs; six of them are the `training_set`).
* **The detector is a desktop GUI script** — it opens OpenCV and matplotlib windows and waits for a key
  press. It **cannot run headless**.
* **The script does not play audio.** `detect.py` builds `audio_file = 'audio/<value>.mp3'` and then
  overwrites it with the literal `"value.mp3"`, and the `playsound(...)` / `gTTS` calls are commented out.
  The **web page** plays the real pre-recorded announcements instead.

---

### 1. Prerequisites

| Requirement | Version / detail | Checked with |
|---|---|---|
| OS | Windows 10/11 (commands below are PowerShell) | `Get-Host` |
| Python | 3.12.1 is present; **the shipped 2020 pins will not build on it** — use the unpinned install in Section 2 | `python --version` |
| opencv-python | ≥ 4.10 (4.13.0 is already installed system-wide here) | `python -c "import cv2; print(cv2.__version__)"` |
| numpy | ≥ 2.0 on 3.12 (2.2.4 already installed) | `python -c "import numpy; print(numpy.__version__)"` |
| matplotlib | ≥ 3.9 (3.11.1 already installed) | `python -c "import matplotlib; print(matplotlib.__version__)"` |
| **playsound** | **Not in `requirements.txt` but imported at the top of `detect.py`** | `python -c "import playsound"` |
| **gTTS** | **Not in `requirements.txt` but imported at the top of `detect.py`** | `python -c "import gtts"` |
| **A display / GUI session** | Required — `utils.display()` calls `cv2.waitKey(0)` and `detect.py` calls `plt.show()` | — |
| Node.js | **Not required** — the page is plain HTML/CSS/JS, no build step | — |
| API keys / network / GPU | **None.** The pipeline is fully offline, CPU-only | — |

Project root (used by every command below):

```powershell
$root = "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired"
Set-Location $root
```

> The detector lives in a **subfolder** that uses relative paths, so it must be launched from inside
> `Currency Detection using OpenCV in ML`.

---

### 2. Installation and Setup

#### 2.1 The detector's dependencies

The dependency file ships **inside the detector folder**:
`Currency Detection using OpenCV in ML\requirements.txt`, pinned to 2020 versions:

```
certifi==2020.6.20
cycler==0.10.0
kiwisolver==1.3.1
matplotlib==3.3.2
numpy==1.19.4
opencv-python==4.4.0.46
Pillow==8.0.1
pyparsing==2.4.7
python-dateutil==2.8.1
six==1.15.0
```

> **These pins will not install on Python 3.12** (`numpy==1.19.4`, `matplotlib==3.3.2`, `Pillow==8.0.1`
> have no 3.12 wheels). Also note that `playsound` and `gTTS` are **missing from this file** even though
> `detect.py` imports both at module level.

**Recommended install (Python 3.12, unpinned modern versions):**

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"

python -m venv .venv
.\.venv\Scripts\Activate.ps1
# If PowerShell blocks the activation script:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

python -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install "opencv-python>=4.10,<5" "numpy>=2.0,<3" "matplotlib>=3.9,<4" "pillow>=10" playsound gTTS
```

Verify:

```powershell
.\.venv\Scripts\python.exe -c "import cv2, numpy, matplotlib, playsound, gtts; print('cv2', cv2.__version__); print('numpy', numpy.__version__); print('matplotlib', matplotlib.__version__); print('playsound + gtts OK')"
```

> **The system Python 3.12.1 already has `cv2` 4.13.0, `numpy` 2.2.4 and `matplotlib` 3.11.1**, but
> **not** `playsound` and **not** `gtts` — verified: `python detect.py` currently fails with
> `ModuleNotFoundError: No module named 'playsound'` (the import on `detect.py` line 4).
> Installing just those two packages is enough to run the detector with the system interpreter:
> ```powershell
> python -m pip install playsound gTTS
> ```

**Legacy path (Python ≤ 3.9, as the upstream file intends):**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install playsound gTTS
```

> Linux/macOS: replace `.\.venv\Scripts\Activate.ps1` with `source .venv/bin/activate`.

#### 2.2 Configuration

**There is none.** The code reads no environment variables, no `.env` file, no config file and no
command-line arguments. Everything is hard-coded in `detect.py`:

| Setting | Hard-coded value | Location |
|---|---|---|
| Test image | `files/test_200_1.jpg` | `detect.py:22` (it overrides the `files/test_100_4.jpg` assignment on line 20) |
| Training / reference set | `files/20.jpg`, `files/50.jpg`, `files/100.jpg`, `files/500.jpg`, `files/200.jpg`, `files/test_20_6.jpg` | `detect.py:32` |
| Minimum "good" matches | `max_val = 8` (result printed only when `max_val != 8`, i.e. **strictly more than 8**) | `detect.py:10`, `detect.py:58` |
| Lowe's ratio test | `0.789` (source comment: *"give an arbitrary number"*) | `detect.py:48` |
| Preview scale | `0.4` | `detect.py:25` |
| ORB instance | `cv2.ORB_create()` with default parameters | `detect.py:14` |
| Display window size | `1440 x 900` (hard-coded "MacBook Air" resolution) | `utils.py:171` |

**To test your own photo**, edit one line and drop the file into `files/`:

```python
test_img = read_img('files/my_note.jpg')
```

**Reference images** live in `Currency Detection using OpenCV in ML\files\` — **44 JPGs**:
the denomination references (`10.jpg`, `20.jpg`, `50.jpg`, `100.jpg`, `200.jpg`, `500.jpg`, `2000.jpg`),
extra variants (`10_2.jpg`, `20_2.jpg`, `20_3.jpg`, `100_2.jpg`, `100_3.jpg`, `50_2.jpg`, `50_3.jpg`) and
the `test_*.jpg` photographs.

A second, smaller image set also ships at the project root and is used only by the page's gallery:
`Images\currency_images\` (5 photos: `20_rs`, `50_rs`, `100_rs`, `200_rs`, `500_rs`) and
`Images\testing_images\` (19 photos including `Euro-500.png` and `test_dollar_*.jpg`).

**Audio samples** — `Currency Detection using OpenCV in ML\audio\` contains exactly three files:
`20.mp3`, `50.mp3`, `100.mp3`. There is **no** ₹200 or ₹500 sample.

---

### 3. Launch the Complete Project

#### 3.1 The detector — the only component that produces a denomination

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"
.\.venv\Scripts\python.exe detect.py
```

> **It must be run from inside `Currency Detection using OpenCV in ML`** — `detect.py` does
> `from utils import *` and opens `files/...` with relative paths.

What happens, step by step:

1. A window titled **`original`** appears showing the resized preview. `utils.display()` calls
   `cv2.waitKey(0)` — **press any key** to dismiss it.
2. The console prints the number of "good" matches for each reference image, e.g.
   `0   files/20.jpg   10`.
3. The winning reference and the match count are printed, followed by
   **`Detected denomination: Rs.  <value>`**.
4. A **matplotlib window** shows the matched keypoints (`cv2.drawMatchesKnn`). Close it to end the script.

**Stop:** `Esc` / `q` in the OpenCV window, or `Ctrl+C` in the terminal.

**`run.bat`** (`python detect.py runserver; pause;`) also works — the extra `runserver` word is simply
ignored, because `detect.py` never parses `sys.argv`.

**`try.py`** is an experiment sandbox with a **different, 10-image** `training_set` and its own hard-coded
test image (`files/test_200_3.jpg`). Run it the same way (`python try.py`) if you want to compare.

#### 3.2 Frontend — the Note Sense page (static, port 8000)

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired"
python -m http.server 8000
```

Open **http://localhost:8000/**. (Opening `index.html` directly also works in Chrome/Edge, but serving over
HTTP is more reliable for the audio and image paths.) Stop with `Ctrl+C`.

> **Serve from the project root**, not from inside the detector folder — `js/app.js` resolves its assets as
> `Currency%20Detection%20using%20OpenCV%20in%20ML/files/…` and `…/audio/…` relative to the page.

The page and the detector **run independently**; the page never talks to the script. Its *How to run the
recogniser* panel shows both commands.

#### 3.3 Ports summary

| Component | Port | Address |
|---|---|---|
| Note Sense page (`python -m http.server`) | 8000 | `http://localhost:8000/` |
| Detector (`detect.py`) | — | no server; a desktop GUI script |

---

### 4. Test the Project

#### 4.1 Automated / command-line tests

**There is no test suite in this repository** (no `tests/`, no CI). The checks below are direct CLI
invocations.

**Test 1 — the detector starts and prints its per-reference match counts**

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\currency-note-recognition-for-visually-impaired\Currency Detection using OpenCV in ML"
.\.venv\Scripts\python.exe detect.py
```

Expected shape of the console output (six lines, one per reference image, then the winner):

```
0   files/20.jpg   <count>
1   files/50.jpg   <count>
2   files/100.jpg   <count>
3   files/500.jpg   <count>
4   files/200.jpg   <count>
5   files/test_20_6.jpg   <count>
files/<winner>.jpg
good matches  <count>

Detected denomination: Rs.  <value>
```

**Test 2 — the import chain is intact (fast, no GUI)**

```powershell
.\.venv\Scripts\python.exe -c "import utils; print('utils OK'); print(utils.read_img('files/test_20_2.jpg').shape)"
```

Expected: `utils OK` followed by a NumPy shape tuple (the image dimensions, e.g. `(h, w, 3)`).

**Test 3 — the ORB matching arithmetic, without the GUI windows**

This reproduces exactly what `detect.py` computes for a given test image, using the shipped reference set.
Run it from the detector folder:

```powershell
@'
import cv2, os
orb = cv2.ORB_create()
test_img = cv2.imread("files/test_20_2.jpg")
(kp1, des1) = orb.detectAndCompute(test_img, None)
training_set = ["files/20.jpg","files/50.jpg","files/100.jpg","files/500.jpg","files/200.jpg","files/test_20_6.jpg"]
max_val, max_pt = 8, -1
for i, ref in enumerate(training_set):
    img = cv2.imread(ref)
    (kp2, des2) = orb.detectAndCompute(img, None)
    good = [ [m] for (m, n) in cv2.BFMatcher().knnMatch(des1, des2, k=2) if m.distance < 0.789 * n.distance ]
    if len(good) > max_val:
        max_val, max_pt = len(good), i
    print(i, " ", ref, " ", len(good))
if max_val != 8:
    print("Detected denomination: Rs. ", str(training_set[max_pt])[6:-4])
else:
    print("No Matches")
'@ | Set-Content -Path "$env:TEMP\orb_probe.py" -Encoding utf8

.\.venv\Scripts\python.exe "$env:TEMP\orb_probe.py"
```

**Measured results in this environment** (OpenCV 4.13.0, numpy 2.2.4) — reproduced by the writer, so you
can compare your own numbers against them:

| Test image | Winning reference | Good matches | Printed denomination |
|---|---|---|---|
| `files/test_20_2.jpg` | `files/20.jpg` | 28 | `Rs. 20` |
| `files/test_50_2.jpg` | `files/50.jpg` | 17 | `Rs. 50` |
| `files/test_200_1.jpg` **(the hard-coded default)** | `files/100.jpg` | 26 | `Rs. 100` |
| `files/test_100_2.jpg` | `files/test_20_6.jpg` | 15 | `Rs. test_20_6` |

> **Important:** the exact counts and the winner **depend on the OpenCV version** — the ORB implementation
> changed across releases. With the default test image (`files/test_200_1.jpg`) this environment selects
> `files/100.jpg` and prints **`Detected denomination: Rs. 100`**, *not* ₹200. Treat the denomination as
> an observation, not a guarantee, and be aware of the last row: the label is **parsed from the file
> name** (`str(training_set[max_pt])[6:-4]`), so a reference named `test_20_6.jpg` yields the nonsense
> label `test_20_6` — and there is no `audio/test_20_6.mp3`.

**Test 4 — the audio samples exist**

```powershell
Get-ChildItem ".\audio" | Select-Object Name, Length
```

Expected: `20.mp3`, `50.mp3`, `100.mp3` — and nothing else.

#### 4.2 Manual checks in the browser (Note Sense page, http://localhost:8000)

1. The header chip reads **"Requires backend for recognition"**.
2. **Step 1** — drag a JPG/PNG onto the drop zone or press the big *Choose a note photo* button. The page
   previews it locally; **nothing is uploaded** (there is no network call anywhere in `js/app.js`).
3. **Step 2** — press *Identify note* (enabled once a preview shows). The result banner switches to
   *"Requires backend"* / *"Recognition needs the local OpenCV backend"* with the exact command
   (`python detect.py`) — it deliberately **does not print a denomination**.
4. **Step 3** — press *Read this aloud* to hear the banner text with the system voice. The header toggle
   *Voice guidance: ON/OFF* switches this, persisted in `localStorage` under `notesense:voice`.
5. **Voice** section — *Play ₹20 / ₹50 / ₹100 sample* plays the repository's **real** MP3 files
   (`Currency%20Detection%20using%20OpenCV%20in%20ML/audio/<denom>.mp3`); *Stop* halts playback.
   There is deliberately **no** ₹200 or ₹500 button, because those MP3s do not exist.
6. **Gallery** — every image in `files/` is listed with a role label (*Training reference* /
   *Hardcoded test image* / *Test photo* / *Reference photo*). Click a thumbnail for a full-screen
   lightbox (`←`/`→` to browse, `Esc` to close, *Read caption aloud*).
7. **Method panel** — a collapsible explanation of the ORB → BFMatcher → ratio-0.789 pipeline, which
   explicitly notes that the script's audio lines are commented out.
8. **Keyboard check** — tab through the controls; the page is designed for screen-reader and keyboard use.

#### 4.3 Manual checks in the detector window

1. The OpenCV window titled `original` shows the resized test photo; press a key to continue.
2. The terminal shows the six per-reference match counts and the winning reference.
3. The matplotlib window shows the matched keypoints drawn on the test image.
4. Close the matplotlib window — the script exits.

---

### 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'playsound'` (verified in this checkout) | `detect.py` imports `playsound` and `gTTS` at module level; neither is in `requirements.txt` | `python -m pip install playsound gTTS` |
| `ModuleNotFoundError: No module named 'gtts'` | Same cause | `python -m pip install gTTS` |
| `ModuleNotFoundError: No module named 'utils'` | The script was launched from the wrong working directory | `cd "Currency Detection using OpenCV in ML"` then `python detect.py` |
| `pip install -r requirements.txt` fails on Python 3.12 | 2020-era pins (`numpy==1.19.4`, `matplotlib==3.3.2`, `Pillow==8.0.1`) have no 3.12 wheels | Use the unpinned install in Section 2.1 |
| `error: (-215:AssertionFailed) … !_src.empty()` | `cv2.imread` returned `None` — the relative `files/...` path was not found | Run from the detector folder; confirm `files/test_200_1.jpg` exists |
| Nothing happens after the `original` window opens | `utils.display()` blocks on `cv2.waitKey(0)` | Press any key in the OpenCV window |
| `No Matches` printed | No reference exceeded 8 good matches (lighting, angle, crop differ too much) | Add a reference photo of that note to `files/` and list it in `training_set` (`detect.py:32`) |
| The printed denomination is nonsense (e.g. `Rs. test_20_6`) | The label is parsed from the reference **file name** (`str(training_set[max_pt])[6:-4]`) | Rename the reference to the bare denomination (e.g. `20.jpg`) |
| The detected denomination differs from the note in the photo | ORB + a fixed ratio test is version- and photo-sensitive | Compare against Test 3's table; add a clearer reference photo; re-check with a different OpenCV version |
| `AttributeError: module 'numpy' has no attribute 'int0'` | `utils.harris_edge()` uses `np.int0`, removed in NumPy ≥ 1.24 | Only triggered if you call `harris_edge()` — `detect.py` does not. Use `np.int_` in a local edit |
| The matplotlib window opens behind the terminal | GUI backend / window focus | Press `Ctrl+C`, close the OpenCV window first, or force a backend: `python -c "import matplotlib; matplotlib.use('TkAgg')"` |
| The page shows broken thumbnails / no images | The page was served from the wrong folder | Serve the **project root** (`python -m http.server 8000`) — `js/app.js` resolves `Currency%20Detection%20using%20OpenCV%20in%20ML/files/…` relative to the page |
| *Play ₹X sample* shows "Could not open the sample" | The audio path is not resolvable, or the file does not exist | Serve over HTTP from the project root; only `20.mp3`, `50.mp3`, `100.mp3` exist |
| Read-aloud buttons are greyed out | The browser has no Web Speech API | Use a current Chrome/Edge/Firefox; the page disables the buttons and says so |
| The script runs but no audio is heard | **By design** — `playsound(audio_file)` and the `gTTS` lines are commented out, and `audio_file` is overwritten with the literal `"value.mp3"` | Play the announcements from the web page instead |

**Known limitations to state honestly**

* **Manual, single-image workflow** — one hard-coded test image per run; no batch mode, no webcam
  pipeline, no video.
* **Six reference images only** (`20 / 50 / 100 / 500 / 200 / test_20_6`). Notes outside that set
  (₹10, ₹2000) can never be recognised by `detect.py`, even though photos for them exist in `files/`.
* **Photographic sensitivity** — ORB + ratio matching is not robust to strong perspective, glare, motion
  blur or partial occlusion. `try.py` still lists "four point transform / warping" as an unfinished TODO.
* **A real bug in the visualisation** — the `good` list drawn by `cv2.drawMatchesKnn` is the one from the
  **last** loop iteration, not from the winning reference, so the match map can disagree with the printed
  denomination.
* **Threshold semantics** — `max_val` starts at 8 and the result is printed only when `max_val != 8`,
  i.e. strictly more than 8 good matches are required.
* **The web page cannot detect anything** — it is an accessibility shell around the reference set and the
  audio samples.
* **No evaluation, no accuracy report and no test suite** exist in the repository.
* **Old dependency pins** in `requirements.txt` (2020) do not install on modern Python.

---

### 6. Verification Checklist

Tick each box only once **you** have observed the result.

**Environment**

- [ ] `python --version` reports your Python version
- [ ] `python -c "import cv2; print(cv2.__version__)"` succeeds (4.13.0 in this checkout)
- [ ] `python -c "import numpy; print(numpy.__version__)"` succeeds (2.2.4 in this checkout)
- [ ] `python -c "import matplotlib; print(matplotlib.__version__)"` succeeds (3.11.1 in this checkout)
- [ ] `python -c "import playsound"` succeeds — it is **not** in `requirements.txt`
- [ ] `python -c "import gtts"` succeeds — it is **not** in `requirements.txt`
- [ ] `Get-ChildItem ".\Currency Detection using OpenCV in ML\audio"` lists exactly `20.mp3`, `50.mp3`, `100.mp3`
- [ ] `Get-ChildItem ".\Currency Detection using OpenCV in ML\files" -Filter *.jpg` lists the 44 reference images

**Detector**

- [ ] `python detect.py` starts **from inside** `Currency Detection using OpenCV in ML`
- [ ] An OpenCV window titled `original` appears and closes when you press a key
- [ ] The terminal prints six lines, one per reference image, with a "good matches" count
- [ ] The winning reference file name is printed, followed by `good matches  <count>`
- [ ] `Detected denomination: Rs.  <value>` is printed
- [ ] A matplotlib window shows the matched keypoints and closes the script
- [ ] Test 3 (the GUI-free ORB probe) prints the same counts as the GUI run for the same test image
- [ ] You have compared your counts against the reference table in Test 3 and noted any differences
      (OpenCV version differences are expected)

**Note Sense page**

- [ ] `python -m http.server 8000` starts **from the project root** and `http://localhost:8000/` loads
- [ ] The header chip reads "Requires backend for recognition"
- [ ] Choosing a photo shows a local preview and uploads nothing (verified in DevTools → Network: no request)
- [ ] *Identify note* shows the "Requires backend / Recognition needs the local OpenCV backend" banner
      and **no** denomination
- [ ] *Read this aloud* speaks the banner text (Web Speech API)
- [ ] *Play ₹20 sample*, *Play ₹50 sample* and *Play ₹100 sample* each play their MP3
- [ ] The gallery lists every image in `files/` with a role label, and the lightbox opens with
      `←`/`→`/`Esc`
- [ ] The *Method* panel explains the ORB → BFMatcher → ratio-0.789 pipeline

**Cleanup**

- [ ] The static server was stopped with `Ctrl+C`
- [ ] Port 8000 is free
      (`Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue` returns nothing)
