# CampusWise (college-faq-chatbot-rag) — Setup & Test Workflow

This document covers **how to install, configure, launch and test the complete project**: the Streamlit RAG
chat application (`app/app.py`, port **8501**), the one-time ChromaDB ingestion (`scripts/ingest.py`), the
evaluation CLIs, and the optional static CampusWise console (`index.html` + `css/` + `js/`, port **8000**).

**Honest scope note up front:** the real chat backend is the **Streamlit app** — there is **no REST API**
(no Flask/FastAPI route, no `/chat` endpoint) and the static console's `js/app.js` contains **no `fetch()`
call**; it shows an offline card and a scripted demo mode. Live answers require a valid **OpenRouter API
key** (used for *both* chat and embeddings) and a populated `chroma_db/`.

---

### 1. Prerequisites

| Requirement | Version / detail | Checked with |
|---|---|---|
| OS | Windows 10/11 (commands below are PowerShell) | `Get-Host` |
| Python | **3.12.1** (already present as `.venv`) | `.\.venv\Scripts\python.exe --version` |
| Streamlit | **1.66.0** (already in `.venv`) | `.\.venv\Scripts\python.exe -m pip show streamlit` |
| ChromaDB | **1.5.9** (already in `.venv`) | `.\.venv\Scripts\python.exe -m pip show chromadb` |
| **OpenRouter API key** | **Required.** Placeholder: `sk-or-v1-<YOUR_KEY>` | <https://openrouter.ai/keys> |
| Internet | Required **only** for the OpenRouter API calls (chat + embeddings) | — |
| Disk | ≈ 500 MB for the venv + a few MB for `chroma_db/` | `Get-PSDrive` |
| Node.js | **Not required** — the UI is plain HTML/CSS/JS, no build step | — |

> The API key is **never** written into this document. Everything below uses placeholders.

Project root (used by every command below):

```powershell
$root = "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"
Set-Location $root
```

---

### 2. Installation and Setup

#### 2.1 The shipped virtual environment (fastest path)

A complete `.venv` already exists in this checkout — verified contents:

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"
.\.venv\Scripts\python.exe --version
.\.venv\Scripts\python.exe -m pip list
```

Key packages actually present (verified):

| Package | Version |
|---|---|
| streamlit | 1.66.0 |
| langchain | 1.4.6 |
| langchain-core | 1.6.12 |
| langchain-community | **0.4.2** |
| langchain-openai | 1.7.2 |
| langchain-chroma | 1.1.0 |
| langchain-text-splitters | 1.1.3 |
| chromadb | 1.5.9 |
| openai | 3.35.1 |
| rank-bm25 | 0.2.2 |
| ragas | 0.3.1 |
| pydantic / pydantic-settings | 2.14.1 / 2.16.1 |

If you ever need to rebuild it from scratch:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

#### 2.2 Configure the API key (`.env`)

The app reads configuration from `.env` via `pydantic-settings`
(`config/settings.py` → `env_file=PROJECT_ROOT / ".env"`).

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"

# Create .env from the shipped template (only needed if .env is missing)
Copy-Item .env.example .env

# Open it and replace the placeholder with your real key
notepad .env
```

` .env` must contain (placeholder values shown):

```dotenv
OPENROUTER_API_KEY=sk-or-v1-<YOUR_OPENROUTER_KEY>
OPENROUTER_SITE_URL=http://localhost:8501
OPENROUTER_APP_NAME=College FAQ Chatbot

LLM_MODEL=openai/gpt-4o-mini
EMBEDDING_MODEL=openai/text-embedding-3-small

RETRIEVAL_TOP_K=5
RELEVANCE_SCORE_THRESHOLD=0.20
FETCH_K=20
LAMBDA_MULT=0.5
ADAPTIVE_K_THRESHOLD=0.45

CHUNK_SIZE=500
CHUNK_OVERLAP=100
ENABLE_QUERY_REWRITING=true
```

> **Note:** a `.env` file already exists in this checkout and already contains a non-placeholder value.
> Replace it with **your own** key; never commit a real key. `.env` is git-ignored.

**How the app decides the key is "missing"** (`app/app.py:121-124`):

```python
if not settings.openrouter_api_key or settings.openrouter_api_key == "your_openrouter_api_key_here":
    raise ValueError("OPENROUTER_API_KEY is not set. ...")
```

The value `your_openrouter_api_key_here` (the `.env.example` placeholder) is treated as **unset**, and the
app shows a red error banner.

**Other settings that matter** (`config/settings.py`):

| Setting | Default | Effect |
|---|---|---|
| `LLM_MODEL` | `openai/gpt-4o-mini` | Chat model on OpenRouter |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | Embedding model on OpenRouter |
| `RETRIEVAL_TOP_K` | `5` | Chunks returned by the retriever |
| `RELEVANCE_SCORE_THRESHOLD` | `0.20` | Below this best score the pipeline **refuses** instead of answering |
| `FETCH_K` | `20` | Candidates fetched before the MMR diversity pass |
| `LAMBDA_MULT` | `0.5` | MMR: 0 = max diversity, 1 = max relevance |
| `ADAPTIVE_K_THRESHOLD` | `0.45` | If the best score is below this, retrieval expands to `FETCH_K` |
| `CHUNK_SIZE` / `CHUNK_OVERLAP` | `500` / `100` | Document chunking |
| `ENABLE_QUERY_REWRITING` | `true` | Enables the LLM query rewriter |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | Hard-coded in `config/settings.py` |

> **Useful trick for testing the failure path without editing `.env`:** real environment variables take
> priority over the `.env` file in `pydantic-settings`. Verified working:
> ```powershell
> $env:OPENROUTER_API_KEY = "your_openrouter_api_key_here"   # forces the "missing key" banner
> Remove-Item Env:\OPENROUTER_API_KEY                        # undo
> ```

#### 2.3 One-time ingestion (creates `chroma_db/`)

`chroma_db/` is git-ignored and **is not present in this checkout** — it must be created once.

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"
.\.venv\Scripts\python.exe scripts\ingest.py
```

Expected output shape (from `scripts/ingest.py`):

```
Ingestion complete:
  Sections parsed : 57
  Chunks indexed  : <N>
  Persist dir     : N:\...\college-faq-chatbot-rag\chroma_db
```

> The "Sections parsed : 57" figure was verified by loading `data/knowledge_base.docx` directly with
> `src/document_loader.load_docx()` in this checkout. The chunk count depends on `CHUNK_SIZE` /
> `CHUNK_OVERLAP`.

Re-ingest from scratch after editing the `.docx`:

```powershell
.\.venv\Scripts\python.exe scripts\ingest.py --reset
```

**Auto-ingestion:** you can skip the manual step. `src/factory.py:31-33` checks
`collection_is_empty(vector_store)` and runs the ingestion automatically, so the **first** launch of the
Streamlit app embeds the document if `chroma_db/` is empty.

---

### 3. Launch the Complete Project

#### 3.1 Backend — the Streamlit chat app on port 8501

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"
.\.venv\Scripts\python.exe -m streamlit run app\app.py --server.port 8501 --server.headless true
```

Expected output (verified in this checkout):

```
  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
```

Open **http://localhost:8501**. Stop with `Ctrl+C`.

**Equivalent convenience launcher** (`run.py` shells out to `streamlit run app/app.py`):

```powershell
.\.venv\Scripts\python.exe run.py
```

> `.streamlit/config.toml` sets `fileWatcherType = "none"` (useful on Windows/network drives) and
> disables usage stats.

#### 3.2 Frontend — the static CampusWise console on port 8000 (optional)

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"
python -m http.server 8000
```

Open **http://localhost:8000**. Stop with `Ctrl+C`.

This page is **fully self-contained**: it shows an *"Offline — Streamlit mode"* badge, an offline card with
the exact backend commands, a **Demo mode** toggle with a scripted 4-turn transcript, and JSON/Markdown
export. It never calls the Streamlit app.

#### 3.3 Ports summary

| Component | Port | Address |
|---|---|---|
| Streamlit chat app (`app/app.py`) | 8501 | `http://localhost:8501` |
| Static CampusWise console (`python -m http.server`) | 8000 | `http://localhost:8000` |
| ChromaDB | — | local files in `chroma_db/` (no port) |
| OpenRouter | 443 | `https://openrouter.ai/api/v1` (outbound only) |

---

### 4. Test the Project

#### 4.1 Automated / command-line tests

**Test 1 — the service starts and serves HTTP 200**

```powershell
# (with the Streamlit app running in another window)
curl.exe -s -o NUL -w "HTTP %{http_code}`n" http://localhost:8501/
```

Expected — verified: `HTTP 200`.

**Test 2 — configuration loads and the knowledge base is readable**

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from config.settings import get_settings; s=get_settings(); print('kb:', s.knowledge_base_path.name, s.knowledge_base_path.exists()); print('collection:', s.collection_name); print('top_k:', s.retrieval_top_k); print('llm:', s.llm_model, '| emb:', s.embedding_model)"
```

Expected (verified):

```
kb: knowledge_base.docx True
collection: college_knowledge_base
top_k: 5
llm: openai/gpt-4o-mini | emb: openai/text-embedding-3-small
```

**Test 3 — the document parses into sections**

```powershell
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0,'.'); from src.document_loader import load_docx; from config.settings import get_settings; print('sections:', len(load_docx(get_settings().knowledge_base_path)))"
```

Expected — verified: `sections: 57`.

**Test 4 — the "missing key" failure path (red banner)**

```powershell
$env:OPENROUTER_API_KEY = "your_openrouter_api_key_here"
# start the app, open http://localhost:8501, read the banner
# afterwards:
Remove-Item Env:\OPENROUTER_API_KEY
```

Expected: the page shows a red **"⚠️ Failed to initialise chatbot"** banner containing
*"OPENROUTER_API_KEY is not set. Open the .env file and replace the placeholder with your real API key,
then restart the app."* and no chat input is usable.

**Test 5 — retrieval smoke test (7 establishment-year phrasings)**

```powershell
Set-Location "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"
.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py
```

Expected: a PASS/FAIL table ending with a line like
`RESULTS: 7/7 queries passed  (100.0% accuracy)`. This script needs a valid API key **and** a populated
`chroma_db/` (it embeds on first run via `create_chatbot`).

> **Not executed in this checkout** — it makes live billed OpenRouter embedding calls.

**Test 6 — RAGAS evaluation (currently broken in this venv)**

```powershell
.\.venv\Scripts\python.exe scripts\evaluate.py
```

Expected in the current environment — **verified failure**:

```
ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
```

Cause: `ragas 0.3.1` → `ragas/llms/base.py` does
`from langchain_community.chat_models.vertexai import ChatVertexAI`, but that module was **removed** in
the installed `langchain-community 0.4.2`.

**Two ways around it:**

*Option A — no dependency change (recommended):* use the retrieval smoke test (Test 5) instead.

*Option B — pin `langchain-community` back:*

```powershell
.\.venv\Scripts\python.exe -m pip install "langchain-community==0.3.20"
```

> Verified with `pip install --dry-run`: this fix resolves the import, but pip will also **downgrade**
> `langchain` 1.4.6 → 0.3.30, `langchain-core` 1.6.12 → 0.3.86,
> `langchain-text-splitters` 1.1.3 → 0.3.11 and `langsmith` → 0.3.45, and add `dataclasses-json`,
> `marshmallow`, `mypy-extensions`, `typing-inspect`. **Do this in a throw-away venv or re-create `.venv`
> afterwards** — the shipped stack is known-good for the app itself.

#### 4.2 Manual checks in the browser (Streamlit app, http://localhost:8501)

1. **Sidebar → Knowledge Base.** With a valid key and an ingested store it reads
   **"Status: 🟢 Loaded"**, the document name (`knowledge_base.docx`), a chunk count and a vector count.
   Without a key it reads **"Status: 🔴 Not Loaded"**.
2. **Sidebar → Retrieval Config** shows the embedding model, the ChromaDB collection
   (`college_knowledge_base`), the retrieval mode (`Hybrid (BM25 + MMR)`) and `Top-K: 5`.
3. Ask **"When was the college established?"** → the answer states **2001**.
   (Verified directly in the knowledge base: *"Sample College of Engineering was established in 2001
   under the Example Education Trust…"*.)
4. Ask **"What is the NAAC grade?"** → the answer states **Grade 'B+' (2021)**.
   (Verified in the knowledge base: *"NAAC: Accredited with Grade 'B+' (2021)."*)
5. Ask **"What is the placement highest package?"** → **35.0 LPA**
   (verified in the knowledge base: the 2023-2027 row shows `671 placed | 97% | 35.0`).
6. Ask an out-of-scope question, e.g. **"Who is the Prime Minister of India?"** → a **polite refusal**
   (`response.refused = True`, `build_refusal_message()` in `src/prompt.py`), not an invented answer.
7. Each non-refused answer is followed by a **Sources Used** list and, with *Show source excerpts*
   enabled, a collapsible expander with the first 350 characters of each retrieved chunk.
8. A status line shows the retrieval latency (ms) and the number of chunks retrieved.
9. Toggle **Show relevance scores** to see the numeric score per source.
10. **Clear chat history** resets the conversation.

#### 4.3 Manual checks in the static console (http://localhost:8000)

1. The masthead badge reads **"Offline — Streamlit mode"** and the footer states
   *"No REST API — Streamlit only"*.
2. Press **Send** in live mode → an *offline card* with the exact commands
   (`python -m venv .venv`, `Copy-Item .env.example .env`, `python scripts\ingest.py`,
   `streamlit run app\app.py` → `http://localhost:8501`), each with a **Copy** button.
3. Switch **Demo mode** on (or press **Play demo conversation**) → a scripted 4-turn transcript plays back
   with a *"Demo transcript — sample data, not live model output"* banner; each assistant bubble carries a
   **Demo** badge.
4. **Export JSON** / **Export Markdown** download the thread; the JSON marks demo turns with
   `"demo": true`.
5. The **Knowledge** tab explains hybrid retrieval, MMR, adaptive-k and the relevance gate.

---

### 5. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Red banner **"Failed to initialise chatbot"** | `OPENROUTER_API_KEY` empty or still the placeholder `your_openrouter_api_key_here` | Edit `.env`, replace the placeholder with a real key, **restart** the Streamlit app |
| `ValueError: OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key.` (from `src/embeddings.py`) | Same cause, raised during ingestion | Same fix |
| `ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'` when running `scripts\evaluate.py` | `ragas 0.3.1` vs `langchain-community 0.4.2` (verified) | Use `scripts\evaluate_retrieval.py`, or `pip install "langchain-community==0.3.20"` (see Test 6 / Option B) |
| Every answer is the refusal message | The relevance gate rejected the retrieval (`RELEVANCE_SCORE_THRESHOLD = 0.20` too high), or the question was too vague | Lower `RELEVANCE_SCORE_THRESHOLD` to `0.10` in `.env`, or ask a more specific question; watch the retrieval diagnostics printed to the console |
| `scripts\ingest.py` fails on the embedding call | OpenRouter rejected the key, or no internet access | Verify the key at <https://openrouter.ai/keys>; confirm `OPENROUTER_SITE_URL` / `OPENROUTER_APP_NAME` are valid URLs; retry |
| Sidebar shows **"Not Loaded"** and no chunk/vector counts | The vector store is empty and ingestion failed | Run `.\.venv\Scripts\python.exe scripts\ingest.py` and read the error |
| Answers are stale after editing the `.docx` | The persisted Chroma collection was not refreshed | `.\.venv\Scripts\python.exe scripts\ingest.py --reset` |
| Port 8501 already in use | Another Streamlit app is running | `--server.port 8502` and open `http://localhost:8502` |
| `chroma_db/` was created but the app shows 0 vectors | Partial ingestion | Delete `chroma_db/` and re-run `scripts\ingest.py --reset` |
| CampusWise "Send" only shows the offline card | **Expected** — there is no REST API to call | Use the Streamlit app on 8501, or switch the console to Demo mode |
| `streamlit: command not found` | The venv is not on PATH | Use `.\.venv\Scripts\python.exe -m streamlit run app\app.py` |
| `python: No module named 'streamlit'` | Wrong interpreter | Use `.\.venv\Scripts\python.exe` explicitly |
| `403 / 401` from OpenRouter in the console | Bad or exhausted key | Re-check the key and the account's credits |

**Known limitations to state honestly**

* **No REST API.** The only HTTP surface is Streamlit's own protocol on port 8501; the static console
  cannot be wired to it without writing new code.
* **Requires a paid/external service** (OpenRouter) for both chat and embeddings — the app cannot answer
  anything offline.
* `chroma_db/` is **git-ignored and absent** from the checkout; ingestion is mandatory before the first
  answer.
* `scripts\evaluate.py` (RAGAS) is **broken** in the shipped venv; the fix downgrades the whole LangChain
  stack.
* There is **no automated test suite** — the checks above are manual.

---

### 6. Verification Checklist

Tick each box only once **you** have observed the result.

**Environment and configuration**

- [ ] `.\.venv\Scripts\python.exe --version` prints `Python 3.12.1`
- [ ] `.\.venv\Scripts\python.exe -m pip show streamlit` reports `1.66.0`
- [ ] `.\.venv\Scripts\python.exe -m pip show chromadb` reports `1.5.9`
- [ ] `.env` exists, contains `OPENROUTER_API_KEY=sk-or-v1-…` (your own key, **not** the placeholder)
- [ ] `.env` contains no leftover `your_openrouter_api_key_here` value

**Ingestion**

- [ ] `.\.venv\Scripts\python.exe scripts\ingest.py` completes and prints "Ingestion complete:"
- [ ] The output shows `Sections parsed : 57`
- [ ] `Test-Path .\chroma_db` returns `True` and the folder is non-empty
- [ ] Running `scripts\ingest.py --reset` re-creates the collection without errors

**Backend**

- [ ] The Streamlit app starts and logs `Local URL: http://localhost:8501`
- [ ] `curl.exe -s -o NUL -w "HTTP %{http_code}" http://localhost:8501/` returns `HTTP 200`
- [ ] The sidebar shows **Status: 🟢 Loaded** with a document name, chunk count and vector count
- [ ] The sidebar shows the collection name `college_knowledge_base`, `Hybrid (BM25 + MMR)` and `Top-K: 5`
- [ ] "When was the college established?" returns an answer containing **2001**
- [ ] "What is the NAAC grade?" returns an answer containing **Grade 'A'** and **2020**
- [ ] "What is the placement highest package?" returns an answer containing **35.0**
- [ ] "Who is the Prime Minister of India?" produces a **refusal**, not an invented answer
- [ ] Each answered question shows a **Sources Used** list and the latency/chunk counter line
- [ ] Toggling **Show relevance scores** reveals the numeric score per source
- [ ] **Clear chat history** empties the conversation
- [ ] Starting the app with `$env:OPENROUTER_API_KEY = "your_openrouter_api_key_here"` shows the red
      **"Failed to initialise chatbot"** banner, and the banner disappears after the env var is removed

**Evaluation scripts**

- [ ] `.\.venv\Scripts\python.exe scripts\evaluate_retrieval.py` prints a PASS/FAIL table for the 7 queries
- [ ] (Only if you applied Option B) `.\.venv\Scripts\python.exe scripts\evaluate.py` runs without the
      `langchain_community.chat_models.vertexai` ImportError and writes to `evaluation_results\`

**Static console**

- [ ] `python -m http.server 8000` starts and `http://localhost:8000` loads the CampusWise page
- [ ] The masthead badge reads "Offline — Streamlit mode"
- [ ] Pressing **Send** shows the offline card with the backend commands and Copy buttons
- [ ] **Demo mode** plays a scripted transcript whose banner says "Demo transcript — sample data, not live model output"
- [ ] **Export JSON** downloads a file in which demo turns carry `"demo": true`

**Cleanup**

- [ ] The Streamlit app and the static server were stopped with `Ctrl+C`
- [ ] `Remove-Item Env:\OPENROUTER_API_KEY -ErrorAction SilentlyContinue` was run if you used the override
- [ ] Ports 8501 and 8000 are free
      (`Get-NetTCPConnection -LocalPort 8501,8000 -ErrorAction SilentlyContinue` returns nothing)
