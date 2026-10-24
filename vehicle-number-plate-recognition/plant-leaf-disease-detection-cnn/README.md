# LeafLens — Plant Leaf Disease Detection (CNN)

Folder id: `plant-leaf-disease-detection-cnn` · UI display name: **LeafLens**

LeafLens is a Django web application that presents a plant-leaf disease classification project: a
convolutional neural network that scores a photograph of a single leaf against **fifteen** categories
and reports whether the leaf reads as healthy or diseased, plus the category it belongs to.

What actually ships in this repository is the **web layer plus the training notebook**, not a running
classifier. The Django project serves four server-rendered pages (`/`, `/about`, `/services`,
`/contact`) plus the Django admin, and the `Code.ipynb` notebook contains the complete Keras training
and inference pipeline. **No trained weights, no dataset and no prediction endpoint are included**,
so the on-page scan bench performs local file validation only and then shows an explicit
"requires backend" panel instead of a fabricated diagnosis.

---

## Features

### Implemented and verified in this repository

| Feature | Where | Status |
|---|---|---|
| Django project with 4 server-rendered pages | `home/urls.py`, `home/views.py` | Implemented — all 4 return HTTP 200 |
| Django admin site (`/admin/`) | `model/urls.py` | Implemented (site branding set to "Leaf Desease Admin") |
| SQLite database + migrations | `model/settings.py`, `db.sqlite3` | Implemented — `migrate` runs clean |
| Server-rendered LeafLens UI (hero, bench, method, plates, research notes) | `templates/*.html`, `static/css/style.css` (22 KB) | Implemented |
| Leaf bench: drag-and-drop / file-picker upload, client-side type + 10 MB size validation, preview, rotate ±90°, zoom 0.5×–3×, reset, remove | `static/js/app.js` | Implemented (browser-only checks) |
| Honest "Diagnosis requires the CNN backend" panel with the exact facts (no weights, no route, no label list) | `templates/index.html`, `static/js/app.js` | Implemented |
| Full CNN training + inference pipeline | `Code.ipynb` | Implemented as notebook code (not wired into the web app) |

### Not available / requires external setup

- **No trained CNN weights committed.** `Code.ipynb` ends with `model.save('./cnn_model.h5')`, but no
  `.h5` or weight file is committed to the repository (the file is ~200 MB, above GitHub's per-file
  limit and is a runtime artefact). `train_cnn.py` (a faithful, headless export of the notebook's
  code cells) and `Code.ipynb` produce `cnn_model.h5` + `label_transform.pkl` at the project root;
  `POST /predict` loads them at runtime if present, otherwise it `503`s.
- **No dataset committed.** The notebook reads from `../input/plantdisease` (a *PlantVillage*
  export). The dataset is fetched by `prepare_dataset.py` into that sibling folder and is not
  stored in git.
- **Class names come from the trained model.** The fifteen label strings live in
  `label_transform.pkl` (a `LabelBinarizer` produced during training), so neither the UI nor the
  README invents class names — none are hardcoded here.
- **Prediction route — implemented, gated on the weights.** `POST /predict` exists in
  `home/views.py`; the bench posts the leaf photo there and gets `{"disease","healthy","confidence"}`.
  It returns HTTP `503` when the trained weights are absent/unloadable, and the UI then shows the
  honest "weights not loaded" facts.
- **ML stack installed in the virtualenv.** `tensorflow`, `opencv-python`, `scikit-learn` and
  `matplotlib` are installed alongside Django; CPU training is sufficient and no GPU is required.

---

## Technology Stack

| Layer | Technology | Notes |
|---|---|---|
| Web framework | Django 5.2.18 (installed in `.venv`) | Project package `model`, app `home` |
| Templating | Django templates + `{% static %}` | `templates/base.html` + 4 page templates |
| Frontend | Vanilla HTML5 / CSS / ES5 JavaScript | No framework, no bundler, no CDN JS |
| Styling | `static/css/style.css` (22 KB) + Google Fonts | Cormorant, Fraunces, Inter |
| Database | SQLite via `django.db.backends.sqlite3` | File `db.sqlite3` at project root |
| ML (notebook only) | TensorFlow / Keras, OpenCV, scikit-learn | Only referenced by `Code.ipynb` |
| Python | 3.12.1 (verified in `.venv`) | |

---

## Prerequisites

- **Windows 10/11** with PowerShell 5.1+ (Linux/macOS commands noted in each section).
- **Python 3.12.1** available as `python` on `PATH` (the checked-in `.venv` was built with 3.12.1).
- No Node.js is required — the Django app serves its own CSS/JS.
- Outbound internet access is *not* required to run the app (only Google Fonts are fetched, and
  the page degrades gracefully without them).

---

## Project Structure

```
plant-leaf-disease-detection-cnn/
├── manage.py                     # Django management entry point (DJANGO_SETTINGS_MODULE=model.settings)
├── model/                        # Django project package
│   ├── settings.py               # INSTALLED_APPS, TEMPLATES DIRS, STATICFILES_DIRS, SQLite config
│   ├── urls.py                   # admin/ + include('home.urls'); admin site branding
│   ├── asgi.py / wsgi.py         # ASGI/WSGI entry points
├── home/                         # Django app
│   ├── views.py                  # index / about / services / contact — render only
│   ├── urls.py                   # path(""), "about", "services", "contact"
│   ├── models.py / admin.py / tests.py   # unchanged Django stubs
│   ├── apps.py                   # HomeConfig
│   └── migrations/               # only __init__.py (no models to migrate)
├── templates/                    # Server-rendered UI
│   ├── base.html                 # Shell: nav, footer, static css/js includes
│   ├── base.html.bak             # Original shell (backup)
│   ├── index.html                # LeafLens home: hero + scan bench + method + plates
│   ├── index.html.bak            # Original home page (backup)
│   ├── about.html                # About page
│   ├── services.html             # Services page
│   └── contact.html              # Contact page (contains the original file-input form)
├── static/
│   ├── css/style.css             # LeafLens stylesheet (22 KB)
│   ├── js/app.js                 # Bench logic: validation, preview, rotate/zoom, backend panel
│   ├── 1.jpg / 2.jpg / 3.jpg     # Original demo photographs used as "plates"
│   ├── img/1.jpg, img/2.jpg, img/3.jpg  # Copies of the same assets
│   └── test.txt                  # Original Django "static page" placeholder
├── Code.ipynb                    # 34-cell Keras notebook: load → label → augment → CNN → train → predict
├── db.sqlite3                    # SQLite database (admin/auth/sessions)
├── LICENSE                       # MIT, (c) 2022 Ghanshyam Prajapati
├── project-metadata.json         # Upstream catalogue metadata
└── .venv/                        # Pre-created virtualenv (Python 3.12.1 + Django 5.2.18)
```

Model/data paths the code expects (all currently **absent**):

| Expected path | Referenced by | Contents |
|---|---|---|
| `../input/plantdisease/` | `Code.ipynb` (`directory_root`) | PlantVillage image folders per class |
| `./cnn_model.h5` | `Code.ipynb` (`model.save`) | Trained Keras weights |
| `./label_transform.pkl` | `Code.ipynb` (`pickle.dump(label_binarizer, ...)`) | Fitted `LabelBinarizer` (class names) |

---

## Installation

A `.venv` with the correct interpreter and Django is already present in this project. Use it:

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\plant-leaf-disease-detection-cnn"
.\.venv\Scripts\Activate.ps1
```

Confirm the environment:

```powershell
python -c "import django, sys; print(sys.version); print('Django', django.get_version())"
```

Expected output: Python `3.12.1` and `Django 5.2.18`.

If you prefer to build the environment yourself (or the bundled `.venv` is missing):

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\plant-leaf-disease-detection-cnn"
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install "Django>=5.0,<6.0"
```

There is **no `requirements.txt`** in this project — Django is the only dependency of the web app.
The notebook additionally needs `tensorflow`, `opencv-python`, `scikit-learn`, `numpy` and
`matplotlib`, which are deliberately *not* installed by default (see
[Model and Dataset Setup](#model-and-dataset-setup)).

Linux / macOS equivalent:

```bash
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\plant-leaf-disease-detection-cnn"
python3 -m venv .venv
source .venv/bin/activate
pip install "Django>=5.0,<6.0"
```

---

## Environment Configuration

There is **no `.env` file and no environment variable is read by this project.** `model/settings.py`
is the single source of configuration, and it currently holds development defaults:

| Setting | Value in `model/settings.py` | Note |
|---|---|---|
| `SECRET_KEY` | `django-insecure-9j%385vx$9#hu9#7y5u^(r3b=gg+q$%fvay-)@5=p!ngqf=2xb` | Committed dev key — rotate before any real deployment |
| `DEBUG` | `True` | Development only |
| `ALLOWED_HOSTS` | `[]` | Empty: only `localhost`/`127.0.0.1` are accepted |
| `DATABASES['default']['NAME']` | `BASE_DIR / 'db.sqlite3'` | SQLite file at project root |
| `STATIC_URL` | `'static/'` | Served by the dev server |
| `STATICFILES_DIRS` | `[BASE_DIR / "static"]` | Collected by `collectstatic` |
| `TEMPLATES['DIRS']` | `[BASE_DIR / "templates"]` | Project-level template directory |

---

## How to Launch

Django's development server is used. **Port 8001** is the port this project was verified on.

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\plant-leaf-disease-detection-cnn"
.\.venv\Scripts\Activate.ps1
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

Then open **http://127.0.0.1:8001/** in a browser.

Verified behaviour of that command:

| URL | Result |
|---|---|
| `http://127.0.0.1:8001/` | 200 — LeafLens home page |
| `http://127.0.0.1:8001/about` | 200 — About page |
| `http://127.0.0.1:8001/services` | 200 — Services page |
| `http://127.0.0.1:8001/contact` | 200 — Contact page |
| `http://127.0.0.1:8001/static/css/style.css` | 200 — 22 KB stylesheet |
| `http://127.0.0.1:8001/admin/` | Django admin login page (create a superuser first) |

The frontend and the backend are the **same process**: Django renders the HTML and serves
`static/css/style.css` and `static/js/app.js` itself. There is no separate static server and no
CORS configuration is involved.

Useful commands:

```powershell
python manage.py check          # system check — expected: no issues
python manage.py createsuperuser  # optional, for /admin/
python manage.py collectstatic --noinput  # optional, to gather assets into staticfiles/
```

**To stop:** press `Ctrl+C` in the terminal running `runserver`.

Linux / macOS equivalent:

```bash
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

---

## Model and Dataset Setup

### What exists in the repository

- `Code.ipynb` — the complete training and inference pipeline (34 cells):
  - `convert_image_to_array(image_dir)` reads a file with OpenCV, resizes to 256×256 and returns a
    Keras image array.
  - The loader walks `../input/plantdisease/<plant>/<disease>/*.jpg` and takes at most **200 images
    per class**.
  - `LabelBinarizer` maps folder names to class indices and is pickled to `label_transform.pkl`.
  - Inputs are scaled as `np.array(image_list, dtype=np.float16) / 225.0`.
  - The split is `train_test_split(..., test_size=0.2, random_state=42)`.
  - Augmentation via `ImageDataGenerator(rotation_range=25, width_shift_range=0.1,
    height_shift_range=0.1, shear_range=0.2, zoom_range=0.2, horizontal_flip=True, fill_mode="nearest")`.
  - The network is a Keras `Sequential` CNN over a `(256, 256, 3)` input:
    `Conv2D(32) → BN → MaxPool(3×3) → Dropout(0.25) → Conv2D(64) → BN → Conv2D(64) → BN →
    MaxPool(2×2) → Dropout(0.25) → Conv2D(128) → BN → Conv2D(128) → BN → MaxPool(2×2) →
    Dropout(0.25) → Flatten → Dense(1024) → BN → Dropout(0.5) → Dense(n_classes) → softmax`.
  - Optimizer `Adam(learning_rate=1e-3, decay=1e-3/25)`, loss `binary_crossentropy`,
    `EPOCHS = 25`, `BS = 32`, `steps_per_epoch = len(x_train) // BS`.
  - Output: `model.save('./cnn_model.h5')`, then `load_model("./cnn_model.h5")` and
    `model.predict()` with `np.argmax` over `label_binarizer.classes_`.
- `static/1.jpg`, `static/2.jpg`, `static/3.jpg` — the demo photographs shipped with the original project.

### What is missing, and where the code expects it

| Missing artefact | Path the code expects | Consequence |
|---|---|---|
| Training images (PlantVillage) | `../input/plantdisease/` | The notebook's data-loading cell cannot run |
| Trained weights | `./cnn_model.h5` | No inference is possible |
| Fitted label encoder (class names) | `./label_transform.pkl` | The 15 category names cannot be recovered |
| ML runtime | `tensorflow`, `keras`, `opencv-python`, `scikit-learn`, `matplotlib` | The notebook cannot be executed |

### Making the bench live (all steps implemented in this repo)

1. **ML stack** — installed in `.venv` alongside Django: `tensorflow`, `opencv-python`,
   `scikit-learn`, `matplotlib`.
2. **Dataset** — the 15-class PlantVillage export (Pepper / Potato / Tomato, ~20.6 k images) is
   fetched from Hugging Face (`manoela/plantvillage`) into `../input/plantdisease/PlantVillage/` by
   `prepare_dataset.py` (Kaggle requires auth, so the HF mirror is used). Run it once:
   `python prepare_dataset.py`.
3. **Train** — run `python train_cnn.py` (a faithful, headless export of `Code.ipynb`) to produce
   `cnn_model.h5` and `label_transform.pkl` at the project root. `25` epochs, ~2 min/epoch on CPU.
4. **Predict route** — **done.** `POST /predict` is implemented in `home/views.py`
   (`home/predictor.py` loads the model once and caches it). It accepts a multipart `leaf_image`,
   decodes with OpenCV (BGR, matching training), resizes to 256×256, normalises by `/225.0`, and
   returns `{"disease": "<class>", "healthy": bool, "confidence": 0.0–1.0}`. It `503`s when the
   weights are absent.
5. **Frontend** — **done.** `static/js/app.js` now posts the selected leaf to `/predict` and renders
   the real class, healthy/diseased and confidence into the result panel. If the backend `503`s
   (weights not loaded yet), the honest amber "weights not loaded" facts panel is shown instead.
   The bench still performs the browser-side file checks first.

Until step 3 has produced the trained weights, the bench posts to `/predict`, receives `503`, and
falls back to the "weights not loaded" panel. **No disease name or confidence percentage is ever
fabricated** — a real prediction only appears once the model answers.

---

## Usage

1. Start the server (`python manage.py runserver 127.0.0.1:8001`) and open
   `http://127.0.0.1:8001/`.
2. The hero states plainly: *"Preview interface — the trained model backend is not part of this
   repository."*
3. Scroll to **"The bench → Scan a leaf"**.
4. **Load a photograph.** Either drag a file onto the drop zone or click it to browse.
   - Accepted types: `image/*` MIME or the extensions `jpg, jpeg, png, webp, gif, bmp`.
   - Maximum size: **10 MB** (checked in the browser only).
   - A rejected file produces an inline error, e.g.
     *“tomato.jpg is 12.4 MB — the bench limit is 10 MB. This is a browser-side check only.”*
     or *“notes.txt is not an image the bench can read. Use JPG, PNG, WEBP, GIF or BMP.”*
   - The file is **never uploaded** — the preview uses `URL.createObjectURL()` so the photo stays in
     your browser.
5. **Inspect it.** Use the toolbar: rotate left / right (90° steps), zoom in / out (0.5×–3×), reset
   view, and remove the image.
6. **Press "Analyze leaf."** The bench posts the photo to `POST /predict`. If the trained weights
   are loaded it renders the class, healthy/diseased and confidence in the result panel; if the
   weights are not available (HTTP `503`) it shows the amber "weights not loaded" facts panel.
7. The **"What the result will show"** panel intentionally renders an empty skeleton — class,
   healthy/diseased and confidence rows are placeholders, not sample predictions.
8. Browse the remaining pages via the header nav:
   - **About** — project background.
   - **Services** — how the classifier is meant to be used.
   - **Contact** — contact form scaffold (the original `action_page.php` file-input form is retained).
9. Optional: visit `/admin/` after `python manage.py createsuperuser` to reach the Django admin.

---

## API Documentation

This project is a server-rendered Django application. Its only JSON endpoint is the prediction
route documented below. The complete set of HTTP routes in `model/urls.py` + `home/urls.py` is:

| Method | Path | View function (`home/views.py`) | Request | Response | Errors |
|---|---|---|---|---|---|
| GET | `/` | `index` | none | `200` HTML — LeafLens home page. Renders `templates/index.html` with `context = {"variable": "this is sent"}` | 500 on template errors |
| GET | `/about` | `about` | none | `200` HTML — `templates/about.html` | 500 on template errors |
| GET | `/services` | `services` | none | `200` HTML — `templates/services.html` | 500 on template errors |
| GET | `/contact` | `contact` | none | `200` HTML — `templates/contact.html` | 500 on template errors |
| GET | `/admin/` | Django admin | session cookie | `200` HTML admin, or `302` to `/admin/login/` | 302 redirect when unauthenticated |
| GET | `/static/<path>` | `django.contrib.staticfiles` | none | `200` — CSS/JS/images from `static/` | `404` if the file is missing |
| POST | `/predict` | `predict` (`home/views.py`) | multipart `leaf_image` file | `200` JSON `{"disease": "<class>", "healthy": bool, "confidence": 0.0–1.0}` | `503` when the trained model is not loaded; `400` when no file is sent |

`POST /predict` is **implemented**. The bench posts the selected leaf photo to it (multipart field
`leaf_image`), the view decodes the image with OpenCV, runs it through the CNN loaded from
`cnn_model.h5`, and returns the predicted class, a `healthy` flag and the confidence. It answers
`503` when `cnn_model.h5` / `label_transform.pkl` are absent or fail to load (e.g. before
`Code.ipynb` / `train_cnn.py` have produced the trained weights), in which case the UI shows the
honest "weights not loaded" facts.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'django'` | The virtualenv is not active | Run `.\.venv\Scripts\Activate.ps1`, then `python -c "import django; print(django.get_version())"` |
| `python` resolves to a different interpreter | Another Python is first on `PATH` | Use the full path `.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001` |
| `Error: That port is already in use` | Port 8001 is taken | Use another port: `python manage.py runserver 127.0.0.1:8011`, or stop the other process (`Get-NetTCPConnection -LocalPort 8001 \| Select-Object OwningProcess`) |
| `DisallowedHost` / page loads but assets 404 | `ALLOWED_HOSTS` is empty and `DEBUG=False` | For local work keep `DEBUG = True`; for a real deployment set `ALLOWED_HOSTS` explicitly |
| Static files return 404 | Running from the wrong directory | `runserver` must be started from the folder containing `manage.py` |
| `ImportError: No module named 'home'` | `manage.py` not invoked from project root | `cd` to the project root first |
| The bench says "Diagnosis requires the CNN backend" | Expected behaviour | There is no model in this repository — see [Model and Dataset Setup](#model-and-dataset-setup) |
| `Code.ipynb` fails with `ModuleNotFoundError: tensorflow` | ML stack is not installed | `pip install tensorflow opencv-python scikit-learn matplotlib` (optional; not required by the web app) |
| `FileNotFoundError: '../input/plantdisease'` | Dataset absent | Download a PlantVillage export and place it there, or edit `directory_root` in the notebook |
| `Bad Request` on `/admin/` | `ALLOWED_HOSTS` empty with `DEBUG=False` | Same as above |

---

## Limitations

- **Inference is implemented but weight-gated.** `POST /predict` classifies a leaf once
  `cnn_model.h5` / `label_transform.pkl` are present on disk (produced by `train_cnn.py`). Without
  them the endpoint `503`s and the UI shows the honest "weights not loaded" facts — no prediction is
  ever invented.
- **No weights, dataset or label list are committed** to git: the model is ~200 MB (above GitHub's
  per-file limit) and the dataset is fetched by `prepare_dataset.py`, so none of these large
  artefacts live in the repository. The 15 class names come from the trained `label_transform.pkl`.
- **Single-process dev server.** `runserver` is not for production; `DEBUG=True` and a committed
  `SECRET_KEY` must not be deployed as-is.
- **No authentication on the public pages.** Only the Django admin has auth; the 4 content pages are
  public and read-only.
- **No persistent upload storage.** The uploaded image is read from the request stream and discarded
  (not written to disk); browser preview transforms (rotate/zoom) are CSS only and are not applied
  to the pixels sent to the model.
- **No tests.** `home/tests.py` is the untouched Django stub.
- **Heavy ML dependencies are intentionally excluded** from the project environment to keep the web
  app installable on Python 3.12.

---

## License and Credits

**Upstream project (unchanged):** MIT License — Copyright (c) 2022 Ghanshyam Prajapati.
Upstream repository: `https://github.com/Ghanshyam89/Plant-Leaf-Disease-Detection-using-Deep-Learning`
(`project-metadata.json` → `repository`). The Django project (`model/`, `home/`, `manage.py`,
`db.sqlite3`), the original `Code.ipynb` and the demo images in `static/` originate from that
project and retain its MIT terms.

**Added later (this documentation pass and the UI redesign):** the LeafLens interface
(`templates/base.html`, `templates/index.html` and the `static/` assets), the `.bak` backups of the
original templates (`templates/index.html.bak`, `templates/base.html.bak`), and this README /
`PROJECT_OVERVIEW.md`. These additions are UI and documentation work layered on top of the upstream
code; **no ownership of the original third-party code is claimed**.

> Note: `templates/about.html`, `templates/services.html` and `templates/contact.html` still contain
> the original upstream placeholder bodies ("This is About ka body", etc.). They were left
> untouched; only `index.html` and `base.html` were redesigned.

The upstream README describes the work as a **simulation study**: a CNN trained on samples from
fifteen categories that "provides minimum error during training and better accuracy in
classification". No accuracy figure is claimed here, because no trained model and no evaluation
output are committed to this repository.
