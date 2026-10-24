# Note Sense — Project Overview

*Folder id: `currency-note-recognition-for-visually-impaired` · Upstream: `deveshwar7/Currency-Detector-System-for-visually-impaired-people-using-PYTHON-OPENCV-COMPUTER-VISION`*

---

## Project Summary

| Field | Value |
|---|---|
| **Name** | Note Sense |
| **Folder id** | `currency-note-recognition-for-visually-impaired` |
| **Problem** | A visually impaired person cannot reliably identify an Indian banknote by sight, and cannot read the printed value. Cashiers and family members are often unavailable to help. |
| **Objective** | Identify the denomination of a photographed note **offline**, on a CPU-only machine, with no model download and no network round-trip — and present the result in a voice-first, high-contrast, keyboard-navigable interface. |
| **Primary users** | Visually impaired users handling cash; the caregivers and shop assistants who support them; students studying OpenCV feature matching. |
| **Expected output** | `Detected denomination: Rs. <value>` on the console plus a match-visualisation window; in the web UI, a spoken announcement and the reference gallery. |
| **Architecture style** | Desktop script (OpenCV) + independent static web front end. **No server, no API, no database, no model weights.** |

The repository is the sum of two layers that were never wired together: an OpenCV
feature-matching detector written for a Digital Image Processing mini project, and a
later accessibility-focused web page that presents the same repository's images and audio
honestly instead of pretending to run the detector.

---

## Problem Statement

Banknotes in India carry their value in several places — the numeral on the front, the
numeral on the reverse, and the raised intaglio numerals for the blind — but none of these
are reliably perceivable without sight, and a partially worn note can be ambiguous even for
sighted users. The practical need is:

1. **Decide the denomination of one note quickly** (a shop counter, a till, a wallet).
2. **Do it without a cloud service** — the note is sensitive and connectivity is unreliable.
3. **Do it without a heavy ML stack** — a phone or a low-end laptop should run it.
4. **Hear the answer** — the result must be spoken, not only printed.

An ORB-based matcher satisfies 2–4 naturally: ORB is patent-free, CPU-only, ships inside
`opencv-python`, needs no weights and no GPU, and matching against a handful of reference
photographs is a per-image operation that finishes in seconds.

The web layer then has a second, equally important requirement: **it must not lie**. A page
that showed a random denomination with a confidence bar would be worse than useless for the
target user. So the page states plainly that recognition happens in the local script and
prints nothing it did not actually receive.

---

## Proposed Solution

### 3.1 Detection core (upstream, `Currency Detection using OpenCV in ML/`)

A **reference-photo template matcher**:

- The user photographs a note; the photo is stored as a JPG inside `files/`.
- `detect.py` computes **ORB** keypoints and descriptors for that photo.
- For each of six **reference photographs** it computes the same and **brute-force matches**
  the descriptors with `cv2.BFMatcher().knnMatch(des1, des2, k=2)`.
- Matches that are far better than their runner-up survive **Lowe's ratio test** at `0.789`.
- The reference with the **most surviving matches** wins; its **filename encodes the
  denomination**, so `files/200.jpg` → `200` → `Detected denomination: Rs. 200`.
- `cv2.drawMatchesKnn` + matplotlib render which keypoints actually matched.

There is **no training step and no learned model** — the knowledge is literally the set of
reference photographs, and adding a new denomination means adding one file.

### 3.2 Presentation layer (added later, project root)

`index.html` + `css/style.css` + `js/app.js` implement the accessibility shell:

- Atkinson Hyperlegible typeface, oversized controls, high-contrast palette.
- **Web Speech API** read-aloud of the visible text (never of an invented value).
- A three-step flow (choose photo → identify → result) where step 2 deliberately resolves to
  the *“Requires backend”* state, because the browser cannot run OpenCV.
- A gallery of all 44 images in `files/`, each explicitly labelled by role.
- Playback of the repository's own `audio/*.mp3` announcements (₹20, ₹50, ₹100 only).

---

## Features and Capabilities

### Existing (verified in source)

| # | Capability | Implementation |
|---|---|---|
| F1 | ORB keypoint + descriptor extraction | `detect.py:14` `orb = cv2.ORB_create()`, `orb.detectAndCompute(img, None)` |
| F2 | Brute-force 2-nearest-neighbour matching | `detect.py:41-42` `cv2.BFMatcher().knnMatch(des1, des2, k=2)` |
| F3 | Lowe's ratio filter (0.789) | `detect.py:47-49` `if m.distance < 0.789 * n.distance` |
| F4 | Winner selection with a minimum-match floor (8) | `detect.py:10`, `51-54` |
| F5 | Denomination derived from the winning file name | `detect.py:65` `note = str(training_set[max_pt])[6:-4]` |
| F6 | Match visualisation | `detect.py:63` `cv2.drawMatchesKnn(...)` + `plt.imshow(img3), plt.show()` |
| F7 | On-screen preview window before matching | `detect.py:25-26` → `utils.display()` (`cv2.waitKey(0)`) |
| F8 | Broad image-processing toolbox (Canny, Sobel, Laplacian, Harris, FFT, contours, gamma, histogram equalisation) | `utils.py` — `canny_edge`, `sobel_edge`, `sobel_edge2`, `laplacian_edge`, `find_contours`, `harris_edge`, `fourier`, `gamma_correction`… |
| F9 | Voice-first accessible UI with read-aloud | `js/app.js` `speak()` / `stopSpeaking()`, `localStorage` key `notesense:voice` |
| F10 | Honest “Requires backend” result state | `js/app.js` `BACKEND_KICKER`, `BACKEND_TITLE`, `BACKEND_BODY` |
| F11 | Real pre-recorded announcements | `audio/20.mp3`, `50.mp3`, `100.mp3` played through `<audio id="sample-audio">` |
| F12 | Reference gallery with per-image role labels | `js/app.js` `FILES`, `TRAINING`, `HARDCODED`, `roleFor()` |
| F13 | Accessible lightbox (focus trap, `Esc`/arrows) | `js/app.js` `openLightbox`, `closeLightbox`, `renderLightbox`, keydown handler |

### Future / not implemented

- No webcam capture, no video loop, no batch directory processing.
- No OCR of the printed numeral, no perspective rectification of a tilted note.
- No HTTP backend (no `/recognize`-style endpoint exists).
- No per-detection text-to-speech (the `gTTS`/`playsound` calls in `detect.py` are commented out).
- No accuracy benchmark, no unit tests, no CI.

---

## System Architecture

Two **independent** components that share files but not a runtime:

```
┌──────────────────────────────┐        ┌──────────────────────────────────────────────┐
│  Note Sense web UI (static)  │        │  OpenCV detector (desktop script)            │
│  index.html / css / js/app.js│        │  detect.py + utils.py                        │
│  • local file preview        │        │  • reads hardcoded files/test_200_1.jpg      │
│  • Web Speech read-aloud     │        │  • ORB descriptors                           │
│  • gallery + lightbox        │        │  • BFMatcher + Lowe ratio 0.789              │
│  • plays audio/*.mp3         │        │  • prints "Detected denomination: Rs. …"      │
│  • "Requires backend" banner │        │  • opens match map window                    │
└──────────────┬───────────────┘        └───────────────────┬──────────────────────────┘
               │                                            │
               │ reads (static assets)                      │ reads (image files)
               ▼                                            ▼
    Currency Detection using OpenCV in ML/files/*.jpg   files/*.jpg  (44 images)
    Currency Detection using OpenCV in ML/audio/*.mp3   audio/*.mp3  (3 files)
```

- **No HTTP client** exists in `js/app.js` — the page never contacts a server.
- **No server** exists in the repository — `detect.py` is a top-level script.
- The shared dependency is the **file system**: both components read the same `files/` and
  `audio/` directories relative to their own location.

```mermaid
flowchart TD
    subgraph UI["Note Sense web UI (static, no server)"]
        A[Open index.html] --> B[Step 1: choose / drop a photo]
        B --> C[Local preview via URL.createObjectURL]
        C --> D[Step 2: press Identify note]
        D --> E["Result banner: Requires backend (honest state)"]
        E --> F[Read this aloud via Web Speech API]
        G[Gallery: 44 images in files/] --> H[Lightbox with role labels]
        I[Play rupee sample] --> J["audio/20.mp3, 50.mp3, 100.mp3"]
    end

    subgraph DET["detect.py (OpenCV, local)"]
        K[read_img files/test_200_1.jpg] --> L[orb.detectAndCompute -> kp1, des1]
        M[training_set of 6 reference JPGs] --> N[orb.detectAndCompute -> kp2, des2]
        L --> O[BFMatcher.knnMatch k=2]
        N --> O
        O --> P[Lowe ratio test m.distance < 0.789 * n.distance]
        P --> Q["best reference (must exceed 8 good matches)"]
        Q --> R["note = path[6:-4] -> 'Detected denomination: Rs. …'"]
        Q --> S[cv2.drawMatchesKnn + matplotlib window]
    end

    E -. "same files/ folder; no runtime link" .- M
    J -. "same audio/ folder" .- U[detect.py audio/<note>.mp3 (commented out)]
```

---

## Complete Project Workflow

### 6.1 Detection workflow (`detect.py`)

1. **Import & globals.** `from utils import *` pulls in `cv2`, `numpy`, `matplotlib.pyplot` and the
   helpers. `max_val = 8`, `max_pt = -1`, `max_kp = 0`, and a single `cv2.ORB_create()` instance
   are created.
2. **Pick the test photo.** `test_img = read_img('files/test_200_1.jpg')` (line 22 — it supersedes
   the `files/test_100_4.jpg` assignment on line 20). `read_img()` is a thin `cv2.imread` wrapper.
3. **Preview.** `original = resize_img(test_img, 0.4)` then `display('original', original)` opens an
   OpenCV window scaled to a hardcoded 1440×900 screen and **blocks** until a key is pressed
   (`utils.display()` → `cv2.waitKey(0)`).
4. **Describe the test photo.** `(kp1, des1) = orb.detectAndCompute(test_img, None)` → oriented
   FAST keypoints + rotated BRIEF descriptors.
5. **Describe every reference.** For each of the six paths in `training_set`,
   `cv2.imread` → `orb.detectAndCompute(train_img, None)` → `(kp2, des2)`.
6. **Match.** `bf = cv2.BFMatcher()`; `all_matches = bf.knnMatch(des1, des2, k=2)` returns, for each
   test descriptor, the two nearest reference descriptors.
7. **Filter.** For every `(m, n)` pair, keep `m` if `m.distance < 0.789 * n.distance` (Lowe's
   ratio). The surviving list is `good`.
8. **Score and track the leader.** If `len(good) > max_val`, update `max_val`, `max_pt` and
   `max_kp`. The per-reference counts are printed as they go.
9. **Decide.** If `max_val != 8` (i.e. strictly more than 8 good matches), print the winning path,
   the number of good matches, and:
   `note = str(training_set[max_pt])[6:-4]` → `files/200.jpg` becomes `200` → prints
   `Detected denomination: Rs.  200`.
10. **Visualise.** `cv2.drawMatchesKnn(test_img, kp1, train_img, max_kp, good, 4)` then
    `plt.imshow(img3), plt.show()`.
11. **Else** print `No Matches`.
12. **Audio (disabled).** `audio_file = 'audio/{}.mp3'.format(note)` is immediately overwritten by
    `audio_file = "value.mp3"`, and the `playsound` / `gTTS` calls are commented out — the script
    never speaks the result.

### 6.2 Web-page workflow (`js/app.js`)

1. `init()`-equivalent IIFE runs on load: `syncVoiceUI()`, `buildGallery()`, `setNowPlaying(...)`.
2. Voice preference is restored from `localStorage["notesense:voice"]`; if the browser has no Web
   Speech API, the toggle and the read-aloud buttons are disabled and labelled accordingly.
3. **Step 1** — `acceptFile(file)` validates `file.type` starts with `image/`, creates an object URL
   and renders the preview; a failed image load calls `resetPhoto()`.
4. **Step 2** — clicking *Identify note* sets `banner[data-state] = "backend-required"` and writes
   `BACKEND_KICKER` / `BACKEND_TITLE` / `BACKEND_BODY` into the banner, then scrolls to it.
5. **Step 3** — *Read this aloud* concatenates the banner's kicker/title/body and speaks it.
6. **Voice** — the play buttons set `audio.src = "Currency%20Detection%20using%20OpenCV%20in%20ML/audio/<denom>.mp3"`;
   an `error` event shows the expected path.
7. **Gallery** — `buildGallery()` creates one `<button>` per entry of the hardcoded `FILES` array
   (44 names), tagging the six training references (`.is-training`) and the hardcoded test image
   (`.is-hardcoded`); each opens the lightbox.
8. **Lightbox** — `renderLightbox(index)` swaps the image/caption/role, arrow keys page through,
   `Esc` closes, and focus is restored to the triggering thumbnail.

**Error handling:** the page has no network errors to handle because it performs no network
calls. Its only failure modes are handled explicitly — unsupported file type, broken preview,
missing audio file, missing Web Speech API.

---

## Machine Learning or Algorithm Explanation

> This project contains **no trained model**. It uses a classical computer-vision algorithm
> (**ORB feature matching**) with a nearest-neighbour ratio test. There is no training data, no
> loss function and no evaluation in the repository.

### 7.1 ORB — Oriented FAST + Rotated BRIEF

`cv2.ORB_create()` produces a detector + descriptor in one object (the source comment notes it is
“an alternative to SIFT”, which is patent-free and CPU-only):

- **Detector (FAST):** finds *corners* — pixels brighter/darker than a circular ring of 16
  neighbours. FAST is fast because it can early-exit on the first disqualifying pixel.
- **Orientation:** the intensity centroid of the patch around each keypoint gives a dominant
  gradient direction, so the descriptor is rotation-invariant.
- **Descriptor (rBRIEF):** the orientation is used to steer a *rotated* BRIEF sampling pattern, and
  the 256 sampled intensity pairs are compared in a cascaded fashion for speed.

The result is a list of keypoints (`kp`: position, size, angle, response) and a
`des` array of binary descriptors (one 256-bit string per keypoint).

### 7.2 Brute-force matching with `k = 2`

`cv2.BFMatcher()` with ORB descriptors compares **every** test descriptor against **every**
reference descriptor (Hamming distance on the binary strings) and returns the two nearest for each
query. The second-nearest is what makes the ratio test possible.

### 7.3 Lowe's ratio test at 0.789

```python
for (m, n) in all_matches:
    if m.distance < 0.789 * n.distance:
        good.append([m])
```

A match is kept only if the best candidate is **at least ~21 % better** than the runner-up
(`1 − 0.789 ≈ 0.211`). This rejects *ambiguous* points — texture that looks similar to several
places on the reference note — which is exactly the failure mode of texture-matching approaches.
The source itself calls `0.789` “an arbitrary number”, i.e. it is a hand-tuned constant, not a
learned parameter.

### 7.4 Winner-takes-all voting

The number of surviving matches is a vote for that reference. Because the test photo and the
reference are photographs of the *same physical design* (same printing, same guilloche, same
portrait), the keypoints are largely repeatable, so the correct reference accumulates far more
consistent matches than the wrong ones.

The decision rule is `len(good) > max_val` with `max_val` initialised to **8**, so a reference
must produce **more than 8** good matches to be accepted — otherwise the script prints
`No Matches`.

### 7.5 Deriving the label from the filename

```python
note = str(training_set[max_pt])[6:-4]   # 'files/200.jpg' -> '200'
```

The denomination is *not* read from the image; it is sliced out of the winning reference path
(`'files/'` is 6 characters, `'.jpg'` is 4). Elegant, and also the main fragility: a reference file
named anything else yields a wrong label.

### 7.6 Complexity

Let `n` = test keypoints, `m` = reference keypoints:

- Descriptor extraction: `O(n)` and `O(m)`.
- BF matching: `O(n·m)` descriptor comparisons per reference — with a few hundred keypoints per
  photo and six references this is milliseconds to a few hundred milliseconds.
- Memory: `O(n + m)` descriptors of 256 bits each.

No GPU, no network, no model file. That is precisely why this stack suits an offline,
low-resource assistive tool.

### 7.7 What is *not* here

- No CNN/transfer learning (the upstream metadata mentions "CNN" as a stack keyword, but no neural
  network exists in this repository).
- No training, no validation split, no reported accuracy.
- No mouth/face analysis, no OCR, no orientation rectification.

---

## File-by-File Code Guide

| Path | Role | Key symbols / details |
|---|---|---|
| `index.html` | Note Sense UI markup | 3-step layout, `#drop-zone`, `#note-photo`, `#identify-btn`, `#result-banner` (`data-state`), `#sample-audio`, `#gallery-grid`, `#lightbox`; loads `css/style.css` and `js/app.js`; Google Fonts *Atkinson Hyperlegible* |
| `css/style.css` | UI styling | High-contrast palette, oversized buttons, `prefers-reduced-motion` handling |
| `js/app.js` | UI logic (ES5 IIFE) | `BASE`, `FILES_DIR`, `AUDIO_DIR`, `TRAINING`, `HARDCODED`, `FILES` (44 names), `roleFor()`, `speak()`, `stopSpeaking()`, `acceptFile()`, `resetPhoto()`, `buildGallery()`, `openLightbox()`, `renderLightbox()`, `copyText()`, `BACKEND_BODY` |
| `Currency Detection using OpenCV in ML/detect.py` | **Main detector** | `max_val`/`max_pt`/`max_kp`, `orb = cv2.ORB_create()`, `test_img = read_img('files/test_200_1.jpg')`, `training_set` (6 paths), `bf.knnMatch(des1, des2, k=2)`, ratio test `0.789`, `note = str(...)[6:-4]`, `cv2.drawMatchesKnn` |
| `Currency Detection using OpenCV in ML/utils.py` | Image helpers | `read_img`, `resize_img`, `img_to_gray`, `img_to_gaussian_gray`, `img_to_neg`, `binary_thresh`, `adaptive_thresh`, `sobel_edge`, `sobel_edge2`, `canny_edge`, `laplacian_edge`, `find_contours`, `median_blur`, `dilate_img`, `close`, `harris_edge`, `histogram`, `fourier`, `display` (1440×900 window, `cv2.waitKey(0)`) |
| `Currency Detection using OpenCV in ML/try.py` | Experiment sandbox | Same ORB idea with a **10-image** training set (`20/50/100/500/100/200/2000/10/20_3/10_3`); large blocks of commented-out contour/warp code; TODOs: four-point transform, warping, webcam input |
| `Currency Detection using OpenCV in ML/requirements.txt` | 2020-era pins | `opencv-python==4.4.0.46`, `numpy==1.19.4`, `matplotlib==3.3.2`, `Pillow==8.0.1` + transitive pins |
| `Currency Detection using OpenCV in ML/run.bat` | Windows launcher | `python detect.py runserver` — the extra word is ignored by `detect.py` (no argument parsing) |
| `Currency Detection using OpenCV in ML/README.md` | Upstream note | “To run do `python3 detect.py`” |
| `Currency Detection using OpenCV in ML/files/` | **Reference + test set** | 44 JPGs: `20.jpg`, `50.jpg`, `100.jpg`, `200.jpg`, `500.jpg`, `2000.jpg`, `10.jpg`, plus `*_2/_3` variants and `test_*` photos |
| `Currency Detection using OpenCV in ML/audio/` | Announcements | `20.mp3`, `50.mp3`, `100.mp3` (no 200/500 clip) |
| `Images/currency_images/` | Secondary reference set | `100_rs.jpg`, `200_rs.jpg`, `20_rs.jpg`, `500_rs.jpg`, `50_rs.jpg` (+ `100_rs (2).jpg`) — **not read by the code** |
| `Images/testing_images/` | Extra test photos | 21 images incl. `Euro-500.png`, `test_dollar_1.jpg`, `test_dollar_100.jpg` |
| `project-metadata.json` | Repo metadata | upstream URL, `entry: "Currency Detection using OpenCV in ML/detect.py"`, `license: "Unknown"` |

---

## Data Flow

### 9.1 Detection data flow

```mermaid
flowchart TD
    A["files/test_200_1.jpg (hardcoded)"] -->|cv2.imread via read_img| B[test_img BGR]
    B -->|resize_img 0.4| C["display('original') -> OpenCV window, waitKey(0)"]
    B -->|orb.detectAndCompute| D["kp1, des1 (test keypoints + descriptors)"]

    E["training_set (6 reference JPGs)"] -->|cv2.imread| F[train_img]
    F -->|orb.detectAndCompute| G["kp2, des2"]

    D --> H["BFMatcher().knnMatch(des1, des2, k=2)"]
    G --> H
    H --> I{"m.distance < 0.789 * n.distance ?"}
    I -->|yes| J["good.append([m])"]
    I -->|no| K[discard ambiguous match]
    J --> L{"len(good) > max_val ?"}
    L -->|yes| M[max_val = len(good); max_pt = i; max_kp = kp2]
    L -->|no| N[print per-reference count]
    M --> N
    N --> O{"max_val != 8 ?"}
    O -->|no| P["print 'No Matches'"]
    O -->|yes| Q["note = training_set[max_pt][6:-4]"]
    Q --> R["print 'Detected denomination: Rs. <note>'"]
    R --> S["cv2.drawMatchesKnn -> img3"]
    S --> T[plt.imshow(img3); plt.show()]
```

### 9.2 Web-UI data flow

```mermaid
flowchart LR
    subgraph Browser
        U1[User picks JPG/PNG] --> U2[acceptFile: type check]
        U2 --> U3[URL.createObjectURL preview]
        U3 --> U4[Identify note]
        U4 --> U5["Banner: 'Requires backend'"]
        U5 --> U6[speechSynthesis.speak]
        U7[files/*.jpg on disk] --> U8[buildGallery: 44 buttons]
        U8 --> U9[Lightbox: captions + role labels]
        U10[audio/*.mp3 on disk] --> U11[HTMLAudioElement playback]
    end
    U5 -.->|no fetch() call exists| X[(No server / no API)]
```

---

## Example Execution

**Illustrative walkthrough** — the console text below is representative of the code's output
format; the exact match counts depend on the photographs used and have not been measured in this
environment.

**Scenario.** The user wants to identify a ₹200 note. They drop `note_200.jpg` into
`Currency Detection using OpenCV in ML/files/` and edit `detect.py:22` to
`test_img = read_img('files/note_200.jpg')`.

**Step 1 — run.**

```powershell
cd "Currency Detection using OpenCV in ML"
python detect.py
```

**Step 2 — preview window.** A window named `original` shows the photo scaled to 40 %. The script
waits for a key press.

**Step 3 — per-reference match counts.**

```
0   files/20.jpg   11
1   files/50.jpg   14
2   files/100.jpg   9
3   files/500.jpg   12
4   files/200.jpg   96
5   files/test_20_6.jpg   7
```

**Step 4 — verdict.**

```
files/200.jpg
good matches  96

Detected denomination: Rs.  200
```

**Step 5 — visualisation.** A matplotlib window opens showing the matched keypoints between the
test photo and `files/200.jpg`.

**Step 6 — announcing it in the web page.** In Note Sense the user opens the *Voice* section and
presses *Play ₹20 / ₹50 / ₹100 sample*. There is **no ₹200 clip in the repository**, so the page
correctly offers no ₹200 button and says so in the note under the audio row.

**Failure variant.** If the photograph is heavily tilted or the note is not one of the six
references, every count stays below the floor and the script prints `No Matches` — the honest
outcome, rather than a guess.

---

## Dependencies and External Services

| Dependency | Why it matters | Source |
|---|---|---|
| `opencv-python` | ORB detector + descriptor, `BFMatcher`, `drawMatchesKnn`, `imread`, `resize`, `imshow`, Canny/Sobel/Laplacian/Harris in `utils.py` | PyPI |
| `numpy` | Array plumbing in `utils.py` (`np.float32`, `np.ones`, `np.fft`) | PyPI |
| `matplotlib` | `plt.imshow(img3)` match map; `plt.show()`; also `histogram()` / `fourier()` helpers | PyPI |
| `playsound` | Imported by `detect.py` (playback currently commented out) | PyPI |
| `gtts` | Imported by `detect.py` (TTS currently commented out) | PyPI + Google Translate TTS endpoint at call time |
| `Pillow` | Pinned in `requirements.txt` (matplotlib stack) | PyPI |
| Python Tk/Qt GUI | `cv2.imshow` + `plt.show()` need a desktop session | OS-provided |
| Google Fonts | `index.html` loads *Atkinson Hyperlegible* from `fonts.googleapis.com` | CDN (optional; page degrades to system fonts) |
| Web Speech API | Read-aloud in the browser | Browser-provided (Chrome/Edge/Firefox) |

**External services: none required for detection.** The detector is fully offline. The only
network-dependent behaviour is the optional Google Fonts stylesheet in the web page and the
`gTTS` call that is commented out.

---

## Current Limitations and Future Improvements

### Current limitations

1. **Single hardcoded test image.** No CLI argument, no folder batch mode, no webcam.
2. **Six reference notes only** (`20, 50, 100, 500, 200, test_20_6`); ₹10 and ₹2000 photos exist
   in `files/` but are not in the training list, so they can never be returned.
3. **Visualisation bug.** `drawMatchesKnn` is called with the `good` list of the *last* loop
   iteration while `max_kp` belongs to the *winning* iteration — the drawn matches may not
   correspond to the printed denomination.
4. **Threshold constant.** `0.789` is hand-tuned and hardcoded; no sensitivity analysis exists.
5. **Floor semantics.** `max_val = 8` + `if max_val != 8` means “strictly more than 8”, which is
   easy to misread.
6. **Label comes from the file name**, so renaming a reference breaks the output.
7. **No perspective/rotation normalisation.** A tilted or cropped note degrades matching sharply;
   `try.py` lists the four-point transform as an unfinished TODO.
8. **No accuracy measurement, no tests, no CI.**
9. **Web UI cannot detect.** It is a presentation layer only.
10. **Pinned dependencies date from 2020** and do not install on Python 3.12; `utils.harris_edge()`
    uses the removed `np.int0` on modern NumPy.

### Suggested improvements

- CLI: `python detect.py --image path --refs files/` and a `--batch` directory mode.
- Add the remaining denominations as references; add a `--learn` mode that copies a new photo into
  `files/` and appends it to `training_set`.
- Perspective rectification (four-point transform) before ORB, as already sketched in `try.py`.
- Fix the `good`/`max_kp` pairing so the visualisation matches the verdict.
- Turn the ratio threshold into a CLI flag and report the top-2 candidates.
- Optionally add a thin local HTTP wrapper (`POST /recognize`) if a browser-side flow is wanted —
  this does not exist today.
- Ties back to the accessibility goal: speak the denomination from the script itself
  (`gTTS`/`playsound` are already imported) and add the missing ₹200/₹500 clips.
- Add a golden-image regression test that asserts the detected denomination for a fixed photo.

---

## Learning Outcomes

By studying this repository you learn:

1. **Feature-based image matching without learning.** ORB (FAST + rBRIEF) gives you a detector and
   a binary descriptor that works on CPU, has no weights and no licensing encumbrance — the
   reference-photo template matcher is a complete, deployable classifier.
2. **Why the ratio test matters.** `knnMatch(k=2)` + `m.distance < 0.789 * n.distance` is the
   cheapest way to discard ambiguous matches; without it, every reference receives a large,
   meaningless count and the “winner” is noise.
3. **Absolute vs. relative thresholds.** Counting good matches per reference is a *relative*
   comparison (robust to image quality); the `> 8` floor is an *absolute* guard against declaring
   a winner when nothing matched at all.
4. **Label semantics from filenames.** Encoding the class in the reference file name is elegant for
   a handful of classes and brittle beyond that — a real lesson in data/model separation.
5. **Classic CV toolboxes.** `utils.py` is a compact catalogue: Canny, Sobel, Laplacian, Harris,
   adaptive thresholding, morphological close, contour extraction, gamma correction, histogram
   equalisation and the FFT magnitude spectrum.
6. **Cost/benefit of classical vs. deep methods.** No GPU, no download, no training set, seconds of
   latency — versus the fragility to viewpoint, lighting and occlusion.
7. **Accessibility engineering.** A page can be genuinely useful *without* doing the AI: large
   type, Web Speech read-aloud, keyboard navigation, focus management, `prefers-reduced-motion` — and
   above all, **refusing to fabricate a prediction**. The “Requires backend” panel is a design
   decision as much as a technical one.
8. **Honest documentation of an ML-adjacent system.** Distinguishing *implemented*, *not
   implemented* and *requires external setup* — and stating which model files, weights or
   dependencies are actually missing — is a core engineering skill in applied vision.
9. **Reproducibility hygiene.** Pinning vs. modernising dependencies, relative-path scripts, and
   why a script must be launched from its own directory.
