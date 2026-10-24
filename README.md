# PlateSight — vehicle-number-plate-recognition

Automatic Number Plate Recognition (ANPR) for cars and other vehicles, implemented as a **Streamlit app** running a custom-trained **YOLOv5** plate detector, plus **PlateSight**, a static browser console that documents the model, stages images for the app, and exposes the bundled sample gallery. Detection runs inside the Streamlit process; the browser console is an honest preview and never fabricates bounding boxes or plate text.

> **What "recognition" means here:** the app **detects and localises** number-plate regions with YOLOv5 and renders annotated images. It does **not** read plate characters — `app.py` never calls Tesseract or any OCR library. The metadata goal ("Plate localisation, OCR cleanup with regex and CSV log.") describes the *upstream* project's intent; the OCR half is not wired up in this code.

| | |
| --- | --- |
| **Folder id** | `vehicle-number-plate-recognition` |
| **UI display name** | PlateSight — ANPR Operator Console |
| **Entry point** | `app.py` (Streamlit) |
| **Upstream author** | Prateek Ralhan (MIT, 2022), extending [mftnakrsu's YOLO+OCR work](https://github.com/mftnakrsu/Automatic_Number_Plate_Recognition_YOLO_OCR) |
| **Weights** | `model/last.pt` — 14,378,245 bytes, present in this repository |
| **Runtime settings** | `conf = 0.5`, `iou = 0.45`, inference `size = 640` |
| **Port** | 8501 (Streamlit default; Docker maps `-p 8501:8501`) |

---

## Features

**Implemented and verified in code**

| Capability | Where |
| --- | --- |
| Streamlit app with centred layout and expanded sidebar | `app.py:13` — `st.set_page_config(page_title="Auto NPR", page_icon="✨", layout="centered", initial_sidebar_state="expanded")` |
| Custom YOLOv5 model loading, cached per session | `app.py:20` — `instantiate_model()` with `@st.cache(persist=True, …)` |
| Hub-based model resolution (no local YOLOv5 package needed) | `app.py:22` — `torch.hub.load("ultralytics/yolov5", "custom", path="model/last.pt", force_reload=True)` |
| Confidence / IoU / input size configuration | `app.py:24-26` — `model.conf = 0.5`, `model.iou = 0.45`; `model(img, size=640)` |
| Image upload (PNG, JPG, BMP, JPEG) | `app.py:50` — `st.file_uploader(..., type=["png","jpg","bmp","jpeg"])` |
| Annotated result rendering and in-app preview | `app.py:63-72` — `results.render()`, `st.image(final_image, caption=…)` |
| Annotated image download (per-extension MIME) | `app.py:73-106` — `st.download_button` for `.jpg/.jpeg/.png/.bmp` |
| Live webcam detection | `app.py:112-137` — `cv2.VideoCapture(0)` in a frame loop |
| On-screen success feedback | `app.py:28-31` — `download_success()` (`st.balloons()` + `st.success`) |
| Banner artwork on page and sidebar | `app.py:33-46` — `static/main_banner.png`, `static/banner_top.png`, `static/banner_bottom.png` |
| PlateSight static console (3 tabs) | `index.html` + `js/app.js` + `css/style.css` |
| Browser image intake with type/empty-file validation | `js/app.js` — `acceptFile()`, `showError()`, `formatBytes()` |
| Original-file download from the console | `js/app.js` — `downloadPreview()` (via `URL.createObjectURL`) |
| Sample gallery over the real `uploads/` images | `js/app.js` — `SAMPLES[]` (7 entries), `renderSamples()` |
| Lightbox viewer with keyboard navigation | `js/app.js` — `openLightbox()`, `stepLightbox()`, `initLightbox()` |
| Copy-to-clipboard for run commands | `js/app.js` — `copyText()` + `.copy-btn[data-copy]` |
| Tab persistence | `js/app.js` — `localStorage["platesight-tab"]` |
| Docker image | `Dockerfile` — `FROM python:3.7`, `CMD ["streamlit","run","app.py"]` |
| Heroku-style Procfile + `setup.sh` | `Procfile` — `web: sh setup.sh && streamlit run app.py` |

**Present in the repo but not wired into `app.py`**

- `utils/helper.py` — `filter_text(rectangle_size, ocr_result, region_threshold)` (area-filters OCR results) and `save_results(text, csv_filename, folder_path)` (appends one column to a CSV). These are OCR-side helpers; **`app.py` never imports them**, and no Tesseract call exists anywhere in the code.
- `models/` and `utils/` (remaining files) — a **vendored copy of the Ultralytics YOLOv5 sources** (`common.py`, `yolo.py`, `experimental.py`, `tf.py`, `yolov5{n,s,m,l,x}.yaml`, `datasets.py`, `augmentations.py`, `loss.py`, …). The app does **not** import them; `torch.hub` fetches its own copy of YOLOv5 at runtime.
- `project-metadata.json` — catalogue metadata for this project (id, stack, goal, license, entry point). It is descriptive, not read by the app.

**Not available**

- **No OCR / character recognition.** No Tesseract, no `pytesseract`, no plate-text output of any kind.
- **No REST/HTTP API.** There is no endpoint, no JSON response, and no way to get detection results from a script over HTTP.
- **No training pipeline in-repo.** No dataset, no `train.py`, no config for a training run. The shipped checkpoint was trained elsewhere; its training data and procedure are not documented in this repository.
- **No structured/multi-vehicle output.** Only the rendered image is persisted; no JSON, no CSV log, no per-detection confidence list.
- **No authentication, no multi-user isolation.** `uploads/` and `downloads/` are shared directories.

## Technology Stack

| Layer | Technology | Version in `requirements.txt` |
| --- | --- | --- |
| UI framework | Streamlit | `streamlit==1.9.0` |
| Detector | YOLOv5 (custom checkpoint) loaded through `torch.hub` | via `torch==1.8.1` / `torchvision==0.9.1` |
| Deep learning | PyTorch | `torch==1.8.1` |
| Vision | OpenCV (webcam capture, colour conversion) | `opencv-python==4.5.5.64` |
| Imaging | Pillow (open, render, save, download) | `Pillow==9.1.0` |
| Numerics | NumPy (`np.squeeze` on rendered frames) | `numpy==1.21.6` |
| Hub loader | `torch.hub` → GitHub `ultralytics/yolov5` | — (network access at first run) |
| Browser console | Vanilla HTML5 / CSS / ES5-compatible JavaScript (no framework, no build step) | — |
| Deployment | Docker (`python:3.7`), Heroku-style `Procfile` + `runtime.txt` | `python-3.7.13` |
| Not used | Tesseract / pytesseract / any OCR engine | — (not installed, not called) |

`requirements.txt` is a full `pip freeze` (115 files were recorded at download time, `project-metadata.json`), so it also pins the Jupyter/Notebook stack (`notebook==6.4.11`, `jupyterlab-pygments==0.2.2`, `ipykernel==6.13.0`, …) that the app never imports.

## Prerequisites

| Requirement | Detail |
| --- | --- |
| **Python 3.7–3.10** | `torch==1.8.1`, `torchvision==0.9.1` and `streamlit==1.9.0` have no wheels for Python 3.11+. The Dockerfile and `runtime.txt` both target 3.7. |
| **Internet access on first run** | `torch.hub.load("ultralytics/yolov5", …)` downloads the YOLOv5 repository from GitHub, and `force_reload=True` re-fetches it on every session start. |
| **Disk space** | ~3–4 GB for the pinned wheels (torch 1.8.1 is the bulk) plus the 14 MB checkpoint. |
| **Working directory** | `app.py` uses **relative** paths (`model/last.pt`, `static/…`, `uploads/`, `downloads/`), so it must be started from the project root. |
| **Webcam** (optional) | Only for the *Live Video Feed* branch; needs camera permission in the browser/OS. |
| **Docker** (optional) | For the containerised path. |
| **Linux/macOS caveat** | `pywin32==304` and `pywinpty==2.0.5` are Windows-only and have no Linux/macOS wheels — see [Installation](#installation). |

## Project Structure

```
vehicle-number-plate-recognition/
├── app.py                       # Streamlit app — the only executable entry point
├── index.html                   # PlateSight console markup (3 tabs: Analyze / Samples / About)
├── css/
│   └── style.css                # PlateSight styling
├── js/
│   └── app.js                   # PlateSight behaviour (intake, samples, lightbox, copy, tabs)
├── model/
│   └── last.pt                  # Custom YOLOv5 checkpoint (14,378,245 bytes) — PRESENT
├── static/
│   ├── banner_top.png           # Sidebar banner, loaded at app import time
│   ├── banner_bottom.png        # Sidebar footer banner
│   └── main_banner.png          # Main page banner
├── uploads/                     # 7 sample input images (Cars18/23/65/72/78/9.png, test.jpg)
├── downloads/                   # 7 annotated outputs (output_Cars18.png … output_test.jpg)
├── models/                      # Vendored YOLOv5 sources (common.py, yolo.py, tf.py, *.yaml) — unused by app.py
├── utils/                       # Vendored YOLOv5 helpers + helper.py (OCR helpers, unused by app.py)
├── .github/
│   └── FUNDING.yml              # Sponsorship config only
├── requirements.txt             # Pinned pip freeze (torch 1.8.1, streamlit 1.9.0, …)
├── Dockerfile                   # python:3.7 image → streamlit run app.py
├── Procfile                     # web: sh setup.sh && streamlit run app.py
├── runtime.txt                  # python-3.7.13
├── setup.sh                     # Writes ~/.streamlit/{credentials,config}.toml for headless hosting
├── project-metadata.json        # Catalogue metadata (stack, goal, license, entry)
└── LICENSE                      # MIT — Copyright (c) 2022 Prateek Ralhan
```

**Paths the code actually reads or writes**

| Path | Mode | Reference |
| --- | --- | --- |
| `model/last.pt` | read | `app.py:22` |
| `static/main_banner.png`, `static/banner_top.png`, `static/banner_bottom.png` | read | `app.py:33-35` |
| `uploads/<uploaded name>` | write | `app.py:37,53` |
| `downloads/output_<uploaded name>` | write | `app.py:38,57,67` |
| `uploads/*.png`, `uploads/*.jpg` | read (browser) | `js/app.js` — `SAMPLES[]` |

## Installation

### A — Windows (PowerShell), the pinned environment

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\vehicle-number-plate-recognition"

py -3.9 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks the activation script, allow it for the current session:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### B — Linux / macOS (the same pins, minus the Windows-only packages)

`requirements.txt` contains `pywin32==304` and `pywinpty==2.0.5`, which have no wheels outside Windows and will make `pip install -r requirements.txt` fail. Install only what the app imports:

```bash
cd vehicle-number-plate-recognition
python3.9 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install torch==1.8.1 torchvision==0.9.1 streamlit==1.9.0 opencv-python==4.5.5.64 Pillow==9.1.0 numpy==1.21.6
```

### C — Docker (no local Python needed)

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\vehicle-number-plate-recognition"
docker build -f Dockerfile -t app:latest .
```

The image is `python:3.7` and installs the full `requirements.txt` at build time.

### D — Open-source licence check before redistribution

`models/` and `utils/` contain Ultralytics' YOLOv5 sources, but **no separate licence file for them is included in this repository** (`LICENSE` covers only Prateek Ralhan's MIT work). Verify Ultralytics' terms before redistributing those folders.

## Environment Configuration

**The application code reads no environment variables, no `.env` file and no config file.** There is nothing to configure in the app itself — the only settings are the hard-coded runtime values in `app.py`:

| Setting | Value | Location |
| --- | --- | --- |
| Model path | `model/last.pt` | `app.py:22` |
| Confidence threshold | `0.5` | `app.py:24` |
| IoU threshold | `0.45` | `app.py:25` |
| Inference size | `640` | `app.py:63`, `app.py:126` |
| Hub repository | `ultralytics/yolov5` (forced reload) | `app.py:22` |
| Streamlit page | title `Auto NPR`, icon `✨`, centred, sidebar expanded | `app.py:13-18` |

**Optional — Streamlit theme.** Upstream's README asks for a local `.streamlit/config.toml` (the directory does not exist in this repo; create it if you want the custom theme):

```powershell
New-Item -ItemType Directory -Path ".streamlit" -Force
```

```toml
[theme]
primaryColor="#ffb5b5"
backgroundColor="#132743"
secondaryBackgroundColor="#407088"
textColor="#ffb5b5"
```

**Hosting configuration (not used locally).** `setup.sh` — invoked by the `Procfile` — writes `~/.streamlit/credentials.toml` and `~/.streamlit/config.toml` with `headless = true`, `port = $PORT` and `enableCORS = false`; `Dockerfile` sets `ENV PORT 8501`. `runtime.txt` pins `python-3.7.13`.

## How to Launch

### 1. The Streamlit app (the real product)

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Open **http://localhost:8501**. The server prints `You can now view your Streamlit app in your browser.`; the first start also downloads the YOLOv5 hub repository.

To expose it on the network instead of localhost only:

```powershell
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

**Stop it** with `Ctrl+C` in the terminal that is running it (or close that terminal). `Ctrl+C` triggers Streamlit's shutdown and releases port 8501.

### 2. The PlateSight console (static, optional)

The console is a plain static page — no build step, no server needed.

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\vehicle-number-plate-recognition"
python -m http.server 8000
```

Then open **http://localhost:8000/**. Serving over HTTP matters: opening `index.html` directly via `file://` breaks the relative `uploads/…` sample images, and the console itself prints that hint when the first sample fails to load.

### 3. Docker

```powershell
docker build -f Dockerfile -t app:latest .
docker run -p 8501:8501 app:latest
```

Open **http://localhost:8501/**. Stop it with `Ctrl+C`, then `docker stop <container-id>`; list running containers with `docker ps`.

### 4. Heroku-style (as configured in the repo)

```bash
# The platform runs: web: sh setup.sh && streamlit run app.py
```

`setup.sh` generates the headless Streamlit config from `$PORT` before the app starts.

### How the front end reaches the back end

It does not — and that is deliberate. The browser console has **no network call to any model**: pressing **Detect plates** reveals the exact commands to run the Streamlit app instead. The only back end in this repository is the Streamlit process itself, which serves its own page on port 8501 and runs inference in-process.

## Model and Dataset Setup

**What exists in the repository**

| Item | Status | Detail |
| --- | --- | --- |
| `model/last.pt` | **Present** | 14,378,245 bytes. A custom-trained YOLOv5 checkpoint for number-plate detection. |
| Sample inputs | **Present** | `uploads/` — `Cars18.png` (357,119 B), `Cars23.png` (661,699 B), `Cars65.png` (351,201 B), `Cars72.png` (716,719 B), `Cars78.png` (718,522 B), `Cars9.png` (186,756 B), `test.jpg` (419,406 B). |
| Sample outputs | **Present** | `downloads/` — the annotated results for the six `Cars*` images and `test.jpg`, produced by the app. |
| Banner artwork | **Present** | `static/` — three PNGs, loaded at app import time. |

**What is missing**

- **No training dataset.** The images used to train `model/last.pt` are not in this repository, and the training procedure (epochs, augmentation, train/val split, evaluation metrics) is not documented here. `models/datasets.py` and `models/augmentations.py` are YOLOv5's generic loaders, not a configured dataset.
- **No training script and no training config.** `models/hyp.scratch.yaml` is not present either, so the checkpoint cannot be reproduced or fine-tuned from this repository alone.
- **No evaluation artefact.** There is no committed precision/recall report, no confusion matrix, and no benchmark table for the detector. The `downloads/` images are qualitative examples, not a measured evaluation.

**What the code expects**

`app.py:22` loads the checkpoint with

```python
torch.hub.load("ultralytics/yolov5", "custom", path="model/last.pt", force_reload=True)
```

so the *runtime* requirements are: (1) the file at `model/last.pt` relative to the working directory, and (2) network access to GitHub so `torch.hub` can fetch the `ultralytics/yolov5` repository (the `force_reload=True` flag re-fetches it on every session start, so the first launch of a session is the slow one).

**No weights download link is provided**, because the weights are already committed — there is nothing to download.

## Usage

### A — Streamlit app: detect plates in an uploaded image

1. Start the app: `streamlit run app.py`, then open **http://localhost:8501**.
2. In the sidebar, keep the activity type on **Upload Image** (the default). The page shows the main banner and the two sidebar banners.
3. In the sidebar uploader, choose a file — **PNG, JPG, BMP or JPEG** (the uploader's `type=[...]` list is the only accepted set; other formats are rejected by the browser).
4. The file is written to `uploads/<name>`, loaded with Pillow, and passed to the model as `model(img, size=640)`. A spinner ("Working... 💫") is shown while the detector runs.
5. `results.render()` draws the bounding boxes; the annotated frame is written to `downloads/output_<name>` and displayed with the caption *"This is how your final image looks like 😉"*.
6. Click **Download Output Image 📷** to save the annotated image. The download's MIME type follows the *input* extension (`image/jpg`, `image/jpeg`, `image/png`, `image/bmp`), and a balloons animation plus a success message confirm the download.

*Example input:* `uploads/Cars18.png` (a road scene with a car) → the app produces `downloads/output_Cars18.png` with a box around the plate region.

### B — Streamlit app: live webcam detection

1. Switch the sidebar activity type to **Live Video Feed**.
2. Tick **Start Web-Camera ✅**.
3. OpenCV opens device `0`, reads frames in a loop, runs the detector on each frame at `size=640`, and streams the annotated frames back into the Streamlit image placeholder. The first frames take a moment while the model warms up.
4. Untick the checkbox to stop. (Note: the app releases the camera only on that path, so a browser tab that is closed mid-stream can leave the device busy until the process exits.)

### C — PlateSight console (browser, no inference)

1. Open the console (`index.html` over HTTP, e.g. `python -m http.server 8000`).
2. The **Analyze** tab shows a status strip with the real values from the code — `model/last.pt` (14,378,245 bytes), `CONF 0.5`, `IOU 0.45`, `INFER SIZE 640` — and a warning that inference runs inside the Streamlit app, not in this page.
3. Drop an image on the **Drop image here** zone (or click it, or press Enter). The console validates the type and the size, shows name/size/type metadata, and previews the image locally.
4. Click **Detect plates**. Because there is no REST API, the console reveals the run panel with the exact commands and the five steps to reproduce the detection in the Streamlit app, plus a "copy" button.
5. **Download preview** saves the original file (unchanged) via a blob URL; **Clear** resets the intake.
6. The **Samples** tab lists the seven real images from `uploads/`; clicking one opens the lightbox (arrow keys / Esc / backdrop click all work).
7. The **About model** tab records the detector settings, the inference pipeline, the fact that OCR is not implemented, the real deployment options, the pinned dependency versions, and provenance.

### D — Using the detector from your own Python script

There is no public API, but the model object is a normal YOLOv5 object, so you can drive it directly:

```python
import torch
from PIL import Image

model = torch.hub.load("ultralytics/yolov5", "custom", path="model/last.pt", force_reload=True)
model.eval()
model.conf = 0.5
model.iou = 0.45

results = model(Image.open("uploads/Cars18.png"), size=640)
results.render()
for det in results.xyxy[0]:
    x1, y1, x2, y2, conf, cls = det.tolist()
    print(f"box=({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f}) conf={conf:.3f} class={cls}")
```

This mirrors what `app.py` does; it is not an endpoint, just the same object.

## API Documentation

**This project exposes no HTTP API.** There is no REST endpoint, no request/response contract, and no JSON output — verified across `app.py`, `js/app.js` and the vendored `models/`/`utils/` sources.

| Surface | Method / path | Purpose | Notes |
| --- | --- | --- | --- |
| Streamlit app | `GET http://localhost:8501/` | Serves the Streamlit UI | Streamlit's own internal websocket protocol (`/_stcore/stream`, `/st-websocket`) handles the session. This is framework behaviour, not a project API, and it is not a stable integration contract. |
| PlateSight console | `GET http://localhost:8000/` (static) | Serves `index.html`, `css/`, `js/`, `uploads/` | Read-only static files. No dynamic routes. |

Anything you want to automate must go through the Python object returned by `torch.hub.load(...)`, as shown in [Usage → D](#usage).

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `ERROR: Could not find a version that satisfies the requirement torch==1.8.1` | `torch==1.8.1` has no wheels for Python 3.11+ | Use Python 3.7–3.10 (`py -3.9 -m venv .venv`). |
| `pip install -r requirements.txt` fails on `pywin32` / `pywinpty` | Windows-only packages | On Linux/macOS install the reduced list from [Installation → B](#installation). |
| `st.cache` deprecation / `st.cache_data` warnings | Newer Streamlit installed | Keep `streamlit==1.9.0` (as pinned), or migrate `@st.cache` → `@st.cache_resource` in `app.py:20` and `@st.cache` → `@st.cache_data` in `app.py:28`. |
| `FileNotFoundError: …/static/main_banner.png` | App started from the wrong directory — all paths are relative | `cd` to the project root before `streamlit run app.py`. |
| `FileNotFoundError: …/uploads/…` or `…/downloads/…` | Output directories missing | `mkdir uploads`, `mkdir downloads` in the project root. Both exist in the repo as shipped. |
| Hub download fails / hangs at start | No GitHub access, or a proxy is required | Check connectivity to `github.com`; set `HTTPS_PROXY` if you are behind a proxy. `force_reload=True` re-downloads the YOLOv5 repo on every session start, so the first launch of each session pays this cost. |
| Webcam branch shows nothing / camera busy | `cv2.VideoCapture(0)` cannot open the device | Close other apps using the camera, grant OS/browser camera permission, and confirm device `0` is a camera. A previous tab left the device held can also block it — restart the app. |
| `NameError: name 'img_BGR' is not defined` in the live feed | The first `cap.read()` returned `success == False`, so the render branch never assigned `img_BGR` | Restart the app once the camera is available. This is an upstream code path, not a configuration issue. |
| Container exits immediately / port not reachable | Streamlit in a container must run headless and bind the port | Run with `docker run -p 8501:8501 app:latest`; for a custom port add `--server.port` / `--server.address 0.0.0.0`. |
| Sample thumbnails broken in the console | Page opened via `file://` | Serve over HTTP: `python -m http.server 8000` and open `http://localhost:8000/`. |
| `downloads/output_Cars18.png` will not open in some viewers | The app saves JPEG-encoded bytes into a `.png`-named file (`app.py:67` uses `format="JPEG"`) | Rename to `.jpg`, or open with Pillow/browsers, which sniff the content. |
| No download button appears | The button is only rendered for `.jpg/.jpeg/.png/.bmp` inputs | Use one of those extensions. |
| `uploads/` and `downloads/` keep growing | The app never deletes uploaded files | Clear them manually. |
| Port 8501 already in use | Another Streamlit app is running | `streamlit run app.py --server.port 8502` and browse to `http://localhost:8502`, or stop the other process. |

## Limitations

- **No OCR.** `app.py` never calls Tesseract or any OCR library, and `utils/helper.py` (`filter_text()`, `save_results()`) is not imported by the app. The system **localises** plates; it does not read them. Any "recognition" claim in the catalogue metadata (`project-metadata.json` → `"stack": "Python; OpenCV; Tesseract"`, `"goal": "Plate localisation, OCR cleanup with regex and CSV log."`) is aspirational relative to this code.
- **No API and no structured output.** Results exist only as a rendered image; there is no JSON/CSV of detections, no confidence list, no programmatic access.
- **No reproducible training.** The dataset, hyperparameters and evaluation behind `model/last.pt` are absent, so the checkpoint's accuracy is unknown and it cannot be retrained from this repository.
- **No measured performance.** No precision/recall, mAP, or benchmark table is committed; `downloads/` holds qualitative examples only.
- **Only the last rendered frame is written.** The loop at `app.py:65-67` writes every frame to the same path, so multi-vehicle scenes produce a single image with all boxes drawn, and per-object crops are not available.
- **The saved file's format does not match its extension** (JPEG bytes in a `.png` file), which trips strict consumers.
- **The live-feed path is CPU-only and unthrottled** — inference runs on every captured frame with no GPU path, no FPS cap, and no frame skipping.
- **The webcam loop does not terminate cleanly.** `cap.release()` is only called on the "checkbox off" branch; a closed tab mid-stream can hold the device.
- **Old stack.** Streamlit 1.9.0, Torch 1.8.1 and Python 3.7 are all end-of-life, and `requirements.txt` is a full freeze that pulls in an unnecessary Jupyter toolchain.
- **No production hygiene.** No authentication, no per-session isolation (shared `uploads/`/`downloads/`), no request limits, no log retention policy, no HTTPS configuration.
- **The browser console cannot detect anything.** It is a documentation and staging surface; it explicitly refuses to fabricate boxes or plate text.
- **The vendored YOLOv5 sources are unused** and carry no bundled licence file — a redistribution question, not a code problem.

## License and Credits

**Upstream project — MIT.** `LICENSE`: *"MIT License — Copyright (c) 2022 Prateek Ralhan"*. The original repository is [prateekralhan/Streamlit-based-Automatic-Number-Plate-Recognition](https://github.com/prateekralhan/Streamlit-based-Automatic-Number-Plate-Recognition) (see `project-metadata.json` → `repository`).

**The Streamlit implementation is an extended implementation of** [mftnakrsu/Automatic_Number_Plate_Recognition_YOLO_OCR](https://github.com/mftnakrsu/Automatic_Number_Plate_Recognition_YOLO_OCR), credited in the upstream README.

**YOLOv5** is Ultralytics' work. `models/` and `utils/` contain a vendored copy of those sources; no separate licence file for them ships in this repository — check Ultralytics' terms before redistributing.

**Added later by this project team (not upstream):** the `PlateSight` operator console (`index.html`, `css/style.css`, `js/app.js`), the `README.md` and `PROJECT_OVERVIEW.md` documentation, and the `project-metadata.json` catalogue entry. The upstream Streamlit app, its dependencies, the sample images and the `model/last.pt` checkpoint remain the original author's work under MIT.
