# PlateSight (vehicle-number-plate-recognition) — Setup & Test Workflow

### 1. Prerequisites

- **OS**: Windows (PowerShell)
- **Python**: `runtime.txt` specifies Python 3.7; context is 3.12.1. **Old pins may not install on Python 3.12** (see deps). A conda/env with Python 3.7 is safer for exact pins.
- **Webcam** (optional): For webcam branch in `app.py` (`cv2.VideoCapture(0)`).
- **Internet**: **Required on first run** — `torch.hub.load("ultralytics/yolov5","custom", path="model/last.pt")` will fetch YOLOv5 repo if not cached.
- **Node.js**: v22.15.0 (static landing page only)

### 2. Installation and Setup

From `N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\vehicle-number-plate-recognition\`:

#### Option A: Full pinned install (may be problematic on Python 3.12)
```powershell
py -3.7 -m venv .venv37  # preferred per runtime.txt
.\.venv37\Scripts\Activate.ps1
pip install -r requirements.txt
```
Note: `requirements.txt` is a 105-line freeze including Windows-only packages (`pywin32`, `pywinpty`) and full Jupyter stack.

#### Option B: Reduced runtime install (often works better)
```powershell
py -3.7 -m venv .venv37
.\.venv37\Scripts\Activate.ps1
pip install torch==1.8.1 torchvision==0.9.1
pip install streamlit==1.9.0 opencv-python==4.5.5.64 Pillow==9.1.0 numpy==1.21.6
```

**Ground truth:**
- Weights shipped: `model/last.pt` (14.4 MB custom YOLOv5 plate detector).
- Sample images: `uploads/` (7), outputs: `downloads/`.
- Static banners: `static/`.
- `app.py` is Streamlit backend/app. Vendored YOLOv5 in `utils/` and `models/` (not imported by `app.py`).
- Inference is **detection only** (no OCR).
- No tests, no training script/dataset.

### 3. Launch the Complete Project

#### Component 1: Streamlit app (primary backend/UI) — port 8501
```powershell
streamlit run app.py
```
Open [http://localhost:8501/](http://localhost:8501/). On first run with internet, YOLOv5 repo may be downloaded via `torch.hub`. Supports image upload and webcam branch (`cv2.VideoCapture(0)`). **Detection only.**

#### Component 2: Static landing page (optional)
```powershell
py -m http.server 8000
```
Open [http://localhost:8000/](http://localhost:8000/). `index.html` + `js/` provide image intake/docs; inference runs in **Streamlit** (no `fetch()` to API in static files).

#### Component 3: Docker (optional)
`Dockerfile`, `Procfile`, `setup.sh` present for container/deployment.

### 4. Test the Project

**Automated tests:** None.

**Manual verification:**
| Component | How to test | Expected |
|---|---|---|
| Streamlit app | `streamlit run app.py` | App loads at `:8501`. Loads custom weights from `model/last.pt` via torch.hub (may fetch YOLOv5 first time). |
| Image upload | Upload sample from `uploads/` | Detections rendered (bounding boxes). **No OCR/plate text extraction**. |
| Webcam | Use webcam branch if available | Uses `cv2.VideoCapture(0)` (requires webcam/camera perms). |
| Static page | Serve HTTP on `:8000` | Landing page loads; points to Streamlit/docs. |

### 5. Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `torch.hub.load` fails on first run | No internet/cache | Connect to internet; allow YOLOv5 repo download. Cached in torch hub cache after first run. |
| Old deps install errors on Python 3.12 | Pins target Python 3.7 | Use Python 3.7 env. Or use reduced install with compatible versions. |
| `cv2.VideoCapture(0)` fails | No webcam/permissions/drivers | Use image upload instead. |
| Streamlit version issues | `streamlit==1.9.0` old | Use compatible environment; avoid upgrading torch/streamlit arbitrarily. |
| Windows-specific packages | `pywin32`/`pywinpty` in freeze | May be unnecessary for core detection; can skip if not needed. |

### 6. Verification Checklist

- [ ] Python 3.7 env created/activated (recommended) or attempted reduced install
- [ ] Weights present: `model/last.pt` exists
- [ ] Installed deps (full or reduced)
- [ ] Launched Streamlit: `streamlit run app.py` at `http://localhost:8501/`
- [ ] Tested with sample image from `uploads/` — detections appear (no OCR expected)
- [ ] (Optional) Tested webcam if available
- [ ] (Optional) Served static page on `:8000`
