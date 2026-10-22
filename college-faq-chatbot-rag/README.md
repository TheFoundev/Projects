# CampusWise

CampusWise is the static front-end for a **Retrieval-Augmented Generation (RAG) FAQ assistant** for *any college, university or training institute*. The repository contains two separate surfaces:

1. **The real chat application** — `app/app.py`, a Streamlit app that answers questions strictly from the college knowledge base using OpenAI-compatible hosted models and a local ChromaDB vector store. It runs on **http://localhost:8501**.
2. **CampusWise itself** — `index.html` + `css/style.css` + `js/app.js`, a vanilla-JS console that visualises the assistant's design. **It exposes no HTTP calls of its own**: the repository has *no REST API*, so the page either plays a labelled scripted demo transcript or explains exactly how to start the Streamlit backend.

---

## Features

### Implemented and verified in this repository

| Feature | Where | Status |
|---|---|---|
| Streamlit chat UI with message history, source excerpts, latency and chunk counters | `app/app.py` | Implemented — needs an API key + ingested vector store |
| Grounded RAG pipeline (normalise → optional LLM rewrite → hybrid retrieval → relevance gate → LLM answer) | `src/rag_chain.py` (`RAGChatbot.ask()`) | Implemented |
| Hybrid retrieval: MMR semantic **70 %** + BM25 keyword **30 %**, de-duplicated and re-sorted | `src/retriever.py` (`_hybrid_retrieve()`) | Implemented |
| Adaptive-k expansion when the best score is below `ADAPTIVE_K_THRESHOLD` | `src/retriever.py` (`retrieve()`) | Implemented |
| Relevance gate that refuses instead of inventing an answer | `src/retriever.py` + `src/prompt.py` (`build_refusal_message()`) | Implemented |
| Query normalisation with a 40+ entry abbreviation table (`estd`→`established`, `ece`→`electronics and communication engineering`, …) | `src/query_normalizer.py` | Implemented |
| Optional LLM query rewriter (search-optimised form of the question) | `src/query_rewriter.py` (`QueryRewriter.rewrite()`) | Implemented, toggleable |
| `.docx` knowledge-base loader that detects section headings and converts tables to Markdown | `src/document_loader.py` (`load_docx()`) | Implemented |
| Chunking with heading prepended and enriched metadata (`section`, `heading`, `chunk_id`) | `src/chunker.py` (`chunk_documents()`) | Implemented |
| ChromaDB persistence with collection `college_knowledge_base` | `src/vector_store.py`, `src/ingestion.py` | Implemented — **the store must be created locally** |
| CLI ingestion (`--reset` supported) | `scripts/ingest.py` | Implemented |
| RAGAS evaluation (faithfulness, answer relevancy, context precision, context recall) over 8 ground-truth Q&A pairs | `scripts/evaluate.py`, `src/evaluation/ragas_eval.py` | Implemented — needs API access |
| Retrieval smoke test over 7 establishment-year phrasings | `scripts/evaluate_retrieval.py` | Implemented — needs API access |
| CampusWise static console: chat composer, topic chips, demo playback, JSON/Markdown export, transcript persistence | `index.html`, `js/app.js` | Implemented, static only |
| Honest offline behaviour: every send shows the real backend run steps | `js/app.js` (`buildOfflineCard()`) | Implemented |

### Not available in this repository

- **No HTTP/REST API.** There is no FastAPI/Flask route, no `/chat` or `/ask` endpoint, and `js/app.js` contains **no `fetch()` call**. The only HTTP surface is Streamlit's own web socket/UI protocol on port 8501.
- **No populated vector store.** `chroma_db/` is git-ignored and **is not present in this checkout** — you must run `python scripts/ingest.py` once (it needs the OpenRouter key for the embeddings).
- **No `.env` file.** Only `.env.example` exists; the API key must be supplied by the user.
- **No installed environment.** There is no `.venv` in this project and the heavy LangChain/Streamlit stack is **not installed** on the machine's Python 3.12.1 (`streamlit`, `langchain`, `langchain_core`, `langchain_community`, `langchain_openai`, `langchain_chroma`, `langchain_text_splitters`, `rank_bm25`, `ragas`, `datasets`, `openai` are all absent).
- **No evaluation artefacts.** `evaluation_results/` is git-ignored and empty — no metric values exist until you run the evaluation.

---

## Technology Stack

| Layer | Technology |
|---|---|
| Chat UI | Streamlit (`app/app.py`) |
| Static front-end | Vanilla HTML5 + CSS + JavaScript (`index.html`, `css/style.css`, `js/app.js`) — no frameworks |
| Orchestration | LangChain ≥ 0.3 (`langchain-core`, `langchain-community`, `langchain-openai`, `langchain-chroma`, `langchain-text-splitters`) |
| Vector store | ChromaDB ≥ 0.5, collection `college_knowledge_base`, persisted in `chroma_db/` |
| Embeddings | `openai/text-embedding-3-small` through the configured OpenAI-compatible endpoint, or a local ONNX model (`EMBEDDING_PROVIDER=local`) |
| Chat model | `openai/gpt-4o-mini` through the configured OpenAI-compatible endpoint, `temperature=0.0`, `max_tokens=1024` |
| Keyword search | `rank_bm25` (in-memory BM25 index built at start-up) |
| Document parsing | `python-docx` |
| Configuration | `pydantic` + `pydantic-settings` (BOM-safe `.env` loading) |
| Evaluation | RAGAS, `datasets`, `pandas`, `plotly` |

---

## Prerequisites

- **Windows 10/11, macOS or Linux.**
- **Python 3.10 or later** (the project targets 3.10+; this machine has 3.12.1).
- **An OpenRouter API key** — <https://openrouter.ai/keys>. It is used for *both* the chat model and the embeddings, so a missing key breaks ingestion as well as chat.
- **~500 MB of free disk** for the virtual environment (Chroma, LangChain, RAGAS, Streamlit) and a few MB for `chroma_db/`.
- **Internet access** to `openrouter.ai` for every query and every embedding call.
- **Microsoft Visual C++ Build Tools** are *not* required — all dependencies have wheels for Python 3.10–3.12.

---

## Project Structure

```
college-faq-chatbot-rag/
├── app/
│   └── app.py                     # REAL entry point: the Streamlit chat application
├── run.py                         # Convenience launcher -> streamlit run app/app.py
├── config/
│   └── settings.py                # Pydantic-settings; every tunable lives here
├── data/
│   └── knowledge_base.docx        # Institution knowledge base (template — replace with your own)
├── src/
│   ├── factory.py                 # create_chatbot(): wires the whole pipeline
│   ├── rag_chain.py               # RAGChatbot.ask() + ChatResponse dataclass
│   ├── retriever.py               # DocumentRetriever: BM25 + MMR hybrid, adaptive-k
│   ├── query_normalizer.py        # normalize_query(): cleanup + abbreviation expansion
│   ├── query_rewriter.py          # QueryRewriter: LLM rewrite of the query
│   ├── document_loader.py         # load_docx(): .docx -> LangChain Documents
│   ├── chunker.py                 # chunk_documents(): RecursiveCharacterTextSplitter
│   ├── embeddings.py              # build_embeddings(): OpenAIEmbeddings via OpenRouter
│   ├── llm.py                     # build_llm(): ChatOpenAI via OpenRouter
│   ├── prompt.py                  # build_system_prompt(), build_user_prompt(), build_refusal_message()
│   ├── vector_store.py            # build/load/ingest Chroma helpers
│   ├── ingestion.py               # run_ingestion(): load -> chunk -> embed -> store
│   └── evaluation/
│       └── ragas_eval.py          # run_ragas_evaluation(), save_evaluation_results()
├── scripts/
│   ├── ingest.py                  # CLI: one-time ingestion into ChromaDB
│   ├── evaluate.py                # CLI: RAGAS evaluation (8 Q&A pairs)
│   └── evaluate_retrieval.py      # CLI: retrieval smoke test (7 queries)
├── index.html                     # CampusWise static front-end
├── css/style.css
├── js/app.js                      # Composer, demo playback, exports (no fetch())
├── .env.example                   # Template with every supported variable
├── requirements.txt
├── .streamlit/config.toml         # fileWatcherType = "none", usage stats off
└── chroma_db/                     # NOT PRESENT - created by scripts/ingest.py
```

**Paths the code expects**

| Path | Constant | Present? |
|---|---|---|
| `<root>/data/knowledge_base.docx` | `settings.knowledge_base_path` | Yes |
| `<root>/chroma_db/` | `settings.chroma_persist_dir` | **No** — created by ingestion |
| Collection `college_knowledge_base` | `settings.collection_name` | Created by ingestion |
| `<root>/evaluation_results/` | `EVAL_DIR` in `config/settings.py` | No — created by `save_evaluation_results()` |

---

## Installation

Windows-first, PowerShell:

```powershell
cd "N:\Foundev-Projects\Domain\Artificial Intelligence & Machine Learning\college-faq-chatbot-rag"

# 1. Create and activate the virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# If PowerShell blocks the activation script:
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Install the dependencies (LangChain stack + ChromaDB + Streamlit + RAGAS)
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Linux/macOS: `source .venv/bin/activate`.

> **This checkout has no `.venv` and the heavy dependencies are not installed** on the machine's Python 3.12.1. The commands above were not executed while writing this documentation.

---

## Environment Configuration

All configuration lives in `.env` (loaded by `config/settings.py` with `env_file=PROJECT_ROOT / ".env"` and `env_file_encoding="utf-8-sig"`, so a Windows editor's BOM is tolerated). Copy the template first:

```powershell
Copy-Item .env.example .env
notepad .env
```

| Variable | Default in code | Required | Purpose |
|---|---|---|---|
| `OPENROUTER_API_KEY` | *(empty)* | **Yes** | Authenticates both the chat model and the embeddings. `build_llm()` and `build_embeddings()` raise `ValueError` when it is empty; `app/app.py` refuses to start while the value is still the placeholder |
| `OPENROUTER_SITE_URL` | `http://localhost:8501` | No | Sent as the `HTTP-Referer` header |
| `OPENROUTER_APP_NAME` | `College FAQ Chatbot` | No | Sent as the `X-Title` header |
| `LLM_MODEL` | `openai/gpt-4o-mini` | No | Chat model used through OpenRouter |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | No | Embedding model used through OpenRouter |
| `RETRIEVAL_TOP_K` | `5` | No | Chunks returned per query |
| `RELEVANCE_SCORE_THRESHOLD` | `0.20` | No | Below this maximum score the pipeline refuses |
| `FETCH_K` | `20` | No | Candidates fetched before the MMR diversity pass / adaptive-k expansion |
| `LAMBDA_MULT` | `0.5` | No | MMR trade-off: 0 = maximum diversity, 1 = maximum relevance |
| `ADAPTIVE_K_THRESHOLD` | `0.45` | No | Best-score threshold below which the search widens to `FETCH_K` |
| `CHUNK_SIZE` | `500` | No | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | No | Overlap between consecutive chunks |
| `ENABLE_QUERY_REWRITING` | `true` | No | Turns the LLM query rewriter on/off |
| `OPENROUTER_BASE_URL` | `https://openrouter.ai/api/v1` | No | Base URL of the OpenAI-compatible endpoint used for the chat model (and, with `EMBEDDING_PROVIDER=openai`, for the embeddings) |
| `EMBEDDING_PROVIDER` | `openai` | No | `openai` = remote `/embeddings` endpoint; `local` = local ONNX model via fastembed (no API key needed for embeddings) |
| `LOCAL_EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | No | fastembed model id used when `EMBEDDING_PROVIDER=local` |
| `INSTITUTION_NAME` | `Your College` | No | Name shown in the UI and used in the system prompt — set it to your institution |
| `APP_TITLE` | `FAQ Chatbot` | No | Title shown in the sidebar and page header |

> **Note on a stale table:** the upstream `README.md` in this repository still lists `RELEVANCE_SCORE_THRESHOLD = 0.35`, `CHUNK_SIZE = 800` and `CHUNK_OVERLAP = 150`. The **values actually read by the code** are `0.20`, `500` and `100` (see `config/settings.py` and `.env.example`). This document follows the code.

### Using a non-OpenRouter provider

Any OpenAI-compatible endpoint works by pointing `OPENROUTER_BASE_URL` at it, e.g. Groq:

```dotenv
OPENROUTER_API_KEY=gsk-...
OPENROUTER_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=openai/gpt-oss-120b
```

If that provider serves no `/embeddings` endpoint, switch the embedding backend to the local model (requires `pip install fastembed`):

```dotenv
EMBEDDING_PROVIDER=local
LOCAL_EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
```

After changing the embedding backend, re-index the knowledge base, because vectors from different models are not comparable: `python scripts/ingest.py --reset`.

### Make it yours — three steps

The repository ships **no institution-specific content**. The document in `data/knowledge_base.docx` is a
template with placeholder facts for a fictional college; everything else is driven by configuration.

1. **Drop in your knowledge base.** Replace `data/knowledge_base.docx` with your own Word document
   (or point `KNOWLEDGE_BASE_PATH` at another `.docx`). Use `Heading 1` for top-level sections and
   `Heading 2` for subsections; lists and tables are picked up automatically. Nothing else in the
   code needs to change.
2. **Set your name.** In `.env`:

   ```dotenv
   INSTITUTION_NAME=Your Institute of Technology
   APP_TITLE=FAQ Chatbot
   ```

   `INSTITUTION_NAME` is what the assistant calls itself in the UI and in the system prompt;
   `APP_TITLE` is the window/sidebar title.
3. **Re-index and run.**

   ```bash
   python scripts/ingest.py --reset     # rebuild the vector store from your document
   streamlit run app/app.py             # http://localhost:8501
   ```

Optionally update the ground truth in `src/evaluation/ragas_eval.py` so `scripts/evaluate.py`
scores your document instead of the template.

---

## How to Launch

### 1. One-time ingestion (creates `chroma_db/`)

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\ingest.py
```

Expected output (from `scripts/ingest.py`):

```
Ingestion complete:
  Sections parsed : <n>
  Chunks indexed  : <n>
  Persist dir     : ...\chroma_db
```

Use `python scripts\ingest.py --reset` to delete the collection and re-ingest from scratch (needed after editing the `.docx`).

### 2. The Streamlit chat application — port 8501

```powershell
# Option A - convenience launcher (equivalent to the command below)
python run.py

# Option B - direct
.\.venv\Scripts\Activate.ps1
streamlit run app\app.py
```

Open **http://localhost:8501**. Stop with `Ctrl+C`.

### 3. The CampusWise static console (no port requirement)

```powershell
python -m http.server 8000
```

Open **http://localhost:8000** — or just open `index.html` directly; the page uses relative paths only. Stop the server with `Ctrl+C`.

### How the front-end reaches the backend

**It doesn't.** CampusWise is a static page with no `fetch()` call. `index.html` states: *"No REST API - Streamlit only"* and *"This repository exposes no HTTP endpoints for the chat, so this page does not pretend to call one."* Pressing **Send** in live mode renders a card with the four real run steps; switching on **Demo mode** plays a scripted 4-turn transcript that is labelled as sample data on every bubble.

The live chat experience is the Streamlit app on port 8501 — open it in a second tab/window.

---

## Model and Dataset Setup

| Item | Status | Where it goes |
|---|---|---|
| `data/knowledge_base.docx` | **In the repo** (template knowledge base) | Read by `src/document_loader.py` → LangChain Documents |
| `chroma_db/` | **Missing** (git-ignored) | Created by `python scripts/ingest.py`; the app loads the persisted collection from it |
| Collection `college_knowledge_base` | **Missing** | Created on first ingestion |
| `OPENROUTER_API_KEY` | **Missing** (only `.env.example`) | `.env` in the project root |
| `evaluation_results/` | **Missing** (git-ignored) | Created by `save_evaluation_results()` when you run `scripts/evaluate.py` |

**Ingestion behaviour** — `create_chatbot()` in `src/factory.py` checks `collection_is_empty(vector_store)` and runs `run_ingestion()` automatically when the collection is empty, so the first launch of the Streamlit app will embed the document if you skipped the manual step. `run_ingestion(reset=False)` skips work when the collection is already populated.

**Evaluation ground truth** — `src/evaluation/ragas_eval.py` contains 8 Q&A pairs derived directly from the knowledge base (establishment year 2001, NAAC Grade 'B+' 2021, Example State University affiliation, vision, 42 CSE faculty, contact e-mail, "no MBA programme mentioned", highest package 35.0 LPA from Globex Technologies).

---

## Usage

### The Streamlit app (the real assistant)

1. Open <http://localhost:8501>. The sidebar shows **Knowledge Base** status (document name, chunk count, vectors in DB) and **Retrieval Config** (embedding model, collection name, `Hybrid (BM25 + MMR)`, top-K). If the key is missing, a red banner reads *"Failed to initialise chatbot — OPENROUTER_API_KEY is not set…"*.
2. Type a question, e.g. *"When was the college established?"*, or pick one from the suggestion chips in the CampusWise page.
3. The answer is followed by a **Sources Used** list (unique section headings) and, if **Show source excerpts** is enabled, a collapsible expander with the first 350 characters of each retrieved chunk and its relevance score.
4. A thin status line shows the retrieval latency and the number of chunks retrieved.
5. Toggle **Show relevance scores** to display the numeric score per source.
6. **Clear chat history** resets the conversation.

Example behaviours (grounded in the knowledge base):

| Question | Expected behaviour |
|---|---|
| "When was the college established?" | Answer from the knowledge base (2012) |
| "What is the NAAC grade?" | Answer from the knowledge base (Grade 'A', 2020) |
| "How many CSE faculty are there?" | Answer from the knowledge base (49) |
| "What is the placement highest package?" | Answer from the knowledge base (35.0 LPA) |
| "Who is the Prime Minister of India?" | Polite refusal — out of scope |

### The CampusWise static console

1. Open <http://localhost:8000>. The masthead badge reads **"Offline - Streamlit mode"**.
2. Pick a topic chip (Admissions, Hostel life, Placements, Branches, Timings, Contact) or type a question.
3. Press **Send** in live mode → the thread shows an *offline card* containing the exact commands: `python -m venv .venv`, `Copy-Item .env.example .env` + `OPENROUTER_API_KEY=sk-or-v1-…`, `python scripts/ingest.py`, `streamlit run app/app.py` → `http://localhost:8501`. Each command has a **Copy** button.
4. Switch **Demo mode** on (or press **Play demo conversation**) → a scripted 4-turn transcript plays back with a persistent banner *"Demo transcript - sample data, not live model output"*; each assistant bubble carries a **Demo** badge and a retrieval panel with demo scores.
5. **Export JSON** / **Export Markdown** download the thread; the JSON marks every demo turn with `"demo": true` and a note that it is scripted sample data.
6. The **Knowledge** tab explains the pipeline (hybrid retrieval, MMR, adaptive-k, relevance gate) and the **About** tab explains what is real and what is demo.

### Running the evaluations

```powershell
# RAGAS evaluation over the 8 ground-truth pairs -> evaluation_results/
python scripts\evaluate.py
python scripts\evaluate.py --output-dir .\my_eval_results

# Retrieval smoke test over 7 establishment-year phrasings
python scripts\evaluate_retrieval.py
```

---

## API Documentation

**There is no HTTP API in this repository.** No FastAPI/Flask application, no route handlers, no `/chat`/`/ask` endpoint, and no `fetch()` call in `js/app.js`. CampusWise's own footer states *"No REST API - Streamlit only"*.

The real programmatic interfaces are:

### 1. Python API

```python
from config.settings import get_settings
from src.factory import create_chatbot

chatbot = create_chatbot(get_settings())      # boots embeddings, vector store, BM25 index, rewriter
response = chatbot.ask("When was the college established?")

response.answer            # str   - the final answer text
response.refused           # bool  - True when the relevance gate or the LLM refused
response.sources           # list[dict] - {"section", "heading", "content", "score", "chunk_id"}
response.retrieval         # RetrievalResult | None - documents, scores, is_relevant, latency_ms
response.normalized_query  # str   - after normalize_query()
response.rewritten_query   # str   - after the optional LLM rewrite
```

### 2. CLI entry points

| Command | Function | Output |
|---|---|---|
| `python run.py` / `streamlit run app/app.py` | Streamlit chat UI | http://localhost:8501 |
| `python scripts/ingest.py [--reset]` | `run_ingestion()` | Chunk/section counts, persist dir |
| `python scripts/evaluate.py [--output-dir DIR]` | `run_ragas_evaluation()` + `save_evaluation_results()` | CSV, JSON and a Plotly HTML dashboard in `evaluation_results/` |
| `python scripts/evaluate_retrieval.py` | Retrieval smoke test | Pass/fail per query |

### 3. The contract the static UI states (for a future HTTP wrapper)

The knowledge base is chunked and embedded; a hypothetical service would need to accept a question and return a `ChatResponse`-shaped object. The CampusWise demo transcript mirrors exactly that shape (`answer`, `sources[{section, score}]`, `refused`) — but **no such service is implemented**.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Red banner *"Failed to initialise chatbot — OPENROUTER_API_KEY is not set"* | `.env` missing or still contains the placeholder `your_openrouter_api_key_here` | `Copy-Item .env.example .env`, paste the real key, restart the app |
| `ValueError: OPENROUTER_API_KEY is not set` from `build_llm()` / `build_embeddings()` | Same as above, raised deeper in the stack | Same fix |
| Sidebar shows *"Not Loaded"* and no chunk/vector counts | The vector store is empty and ingestion failed (usually a network/auth problem to OpenRouter) | `python scripts\ingest.py` and read the error |
| `python scripts\ingest.py` fails on the embedding call | OpenRouter rejected the key, or no internet access | Verify the key at <https://openrouter.ai/keys>; check `OPENROUTER_SITE_URL`/`OPENROUTER_APP_NAME` are valid URLs |
| Every answer is the refusal message | The relevance gate rejected the retrieval (`RELEVANCE_SCORE_THRESHOLD` too high) or the query was too vague | Lower `RELEVANCE_SCORE_THRESHOLD` in `.env` to e.g. `0.10`, or use a more specific question; check the retrieval diagnostics printed to the console |
| `ModuleNotFoundError: No module named 'streamlit'` (or `langchain_*`) | Dependencies not installed, or the venv is not active | `.venv\Scripts\Activate.ps1` then `pip install -r requirements.txt` |
| `ModuleNotFoundError: No module named 'datasets'` | `ragas` pulls `datasets`; an incomplete install | `pip install -r requirements.txt` again (or `pip install datasets`) |
| RAGAS evaluation crashes while importing `ragas` | Known `ragas` / `langchain-community` version friction | Pin `ragas` to the version in `requirements.txt` (`>=0.2.0`) and align `langchain-community`; the environment note in `PROJECT_CONTEXT.md` records this friction |
| Streamlit prints a "missing ScriptRunContext" warning | Streamlit run without a context (e.g. imported from a plain script) | Always launch via `streamlit run app\app.py` or `python run.py` |
| CampusWise "Send" only shows the offline card | Expected — there is no REST API to call | Start the Streamlit app and use http://localhost:8501, or switch on Demo mode |
| Port 8501 already in use | Another Streamlit app is running | `streamlit run app\app.py --server.port 8502` |
| Answers cite the wrong section | BM25/MMR ranking mismatch | Raise `RETRIEVAL_TOP_K` or `LAMBDA_MULT`; inspect the diagnostics block printed by `_log_retrieval()` |
| `.env` changes are ignored | `.env` is read at start-up only | Restart the Streamlit app |
| Unicode/emoji garbling in the console | Windows console code page | `chcp 65001` in PowerShell, or `python -X utf8 …` |

---

## Limitations

- **No REST API.** Any other front-end (mobile, Slack, a website) cannot talk to this assistant without someone writing a wrapper.
- **No bundled vector store.** `chroma_db/` is git-ignored, so a fresh clone always needs an ingestion step (and an OpenRouter key) before the first answer.
- **Single document.** The knowledge base is one `.docx`; there is no web crawling, no multi-document routing, no incremental update path other than `--reset`.
- **English only, no multilingual support**, and the abbreviation table is hand-curated for this domain.
- **Answer quality depends on the hosted models.** `gpt-4o-mini` via OpenRouter means answers are only as good as the provider's routing, and the app cannot run offline.
- **Retrieval scores are not calibrated probabilities** — they are a blend of a relevance score and a rank-derived BM25 score, so the `0.20` threshold is a heuristic.
- **The BM25 index is rebuilt in memory on every start-up**, which costs a few seconds on a larger corpus.
- **No conversation memory**: each question is answered independently; follow-up pronouns ("What about the fees?") are handled only by the query normaliser, not by a conversational model.
- **The static CampusWise console is a demonstration surface.** Its demo transcript is scripted sample data and is labelled as such everywhere.
- **The upstream README's configuration table is out of date** (see the note in [Environment Configuration](#environment-configuration)); this document follows the code.

---

## License and Credits

### Upstream project

**College FAQ Chatbot (College FAQ RAG Chatbot)** — upstream repository `https://github.com/aishwarya-nagothu/College-FAQ-RAG-Chatbot` (as recorded in `project-metadata.json`). The upstream project does **not** ship a licence file, and `project-metadata.json` records `"license": "Unknown"` — treat the upstream code's licence as unspecified and confirm with the authors before redistribution.

The knowledge base document `data/knowledge_base.docx` is a **template** with placeholder facts for a fictional college; replace it with your own institutional document. Any document you drop in is a factual institutional record, not a redistributable dataset with a declared licence — verify before sharing it outside the organisation.

### Added later (this front-end)

The **CampusWise** UI — `index.html`, `css/style.css`, `js/app.js` — plus this documentation were added on top of the upstream RAG application. They are not authored by the upstream maintainers. The static console contains no model, no inference code and no third-party JavaScript libraries.

### Third-party components used by the upstream application

- **LangChain** (MIT) — orchestration, splitters, Chroma integration, BM25 retriever.
- **ChromaDB** (Apache-2.0) — local vector store.
- **OpenRouter** (commercial API) — hosts the `openai/gpt-4o-mini` and `openai/text-embedding-3-small` models.
- **RAGAS** (Apache-2.0) — evaluation metrics.
- **Streamlit** (Apache-2.0) — chat UI framework.
- **Your own knowledge base** — the document the assistant answers from; the shipped file is a template.
