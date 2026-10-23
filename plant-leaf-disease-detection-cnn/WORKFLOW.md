# LeafLens (plant-leaf-disease-detection-cnn) — Setup & Test Workflow

### 1. Prerequisites

- **OS:** Windows (PowerShell)
- **Python:** 3.12.1
- **Node:** v22.15.0 (not required)
- **Environment:** `.venv` present with Django 5.2 installed
- **Ports:** Django dev server `8001` (127.0.0.1:8001)
- **Critical missing artifacts (no inference):**
  - `cnn_model.h5` — **missing**
  - `label_transform.pkl` — **missing**
  - PlantVillage dataset — **missing**
- **Training reference:** `Code.ipynb` shows `model.save('./cnn_model.h5')` (not present)

### 2. Installation and Setup

#### Step 1: Open the project directory
```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\plant-leaf-disease-detection-cnn"
```

#### Step 2: Use the existing virtual environment
```powershell
.\.venv\Scripts\Activate.ps1
```
Django is installed in `.venv`. No `requirements.txt` is present — if recreating env, install at minimum:
```powershell
pip install django
```

#### Step 3: Apply migrations and verify
```powershell
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py check
```
Expected: `System check identified no issues (0 silenced).`

### 3. Launch the Complete Project

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\plant-leaf-disease-detection-cnn"
.\.venv\Scripts\python.exe manage.py runserver 127.0.0.1:8001
```
Open: [http://127.0.0.1:8001/](http://127.0.0.1:8001/)

Routes (from `home/urls.py`): `/`, `/about`, `/services`, `/contact` (all render-only).

### 4. Test the Project

#### Automated checks (verified)
```powershell
.\.venv\Scripts\python.exe manage.py check
# OK

# Tests (stub only)
.\.venv\Scripts\python.exe manage.py test
```
`home/tests.py` is untouched stub.

#### Manual UI tests
1. `/` — LeafLens homepage loads with hero, "Scan a leaf" bench UI. Note badge states "Requires CNN backend".
2. Upload/preview image in browser (client-side preview only). "Analyze" button remains disabled/indicates backend required.
3. `/about`, `/services`, `/contact` — all return 200 with templates.
4. Static assets load (CSS/JS/images from `static/`).

#### Inference status
No prediction endpoint/views exist that load a model. The UI is a preview interface only. To enable inference you must add a trained `cnn_model.h5` and `label_transform.pkl`, implement loading/inference in Django views, and update routes/templates accordingly.

### 5. Troubleshooting

| Issue | Cause | Fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'django'` | Wrong env | Activate `.venv` or install Django. |
| Port already in use | 8001 taken | Use different port: `runserver 127.0.0.1:8002`. |
| Static files not loading | Missing `STATICFILES_DIRS` in dev? | Settings configured for static; ensure run from project root. |
| Model inference not working | Missing artifacts | Train using `Code.ipynb` or obtain `cnn_model.h5` and `label_transform.pkl`. |

### 6. Verification Checklist

- [ ] Activated `.venv` with Django 5.2
- [ ] Ran `manage.py migrate` and `manage.py check` (no issues)
- [ ] Started server on 127.0.0.1:8001
- [ ] Verified all 4 routes return 200
- [ ] Confirmed no CNN model files present
- [ ] Confirmed UI labels backend requirement
- [ ] Ran `manage.py test` (stub)
- [ ] Reviewed `Code.ipynb` for training reference
