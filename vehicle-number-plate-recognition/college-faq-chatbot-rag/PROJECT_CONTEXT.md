# PROJECT_CONTEXT.md

## Project: College FAQ Chatbot

A Retrieval-Augmented Generation (RAG) chatbot for any college, university or training institute. Answers questions strictly from an institution knowledge base using an OpenAI-compatible LLM endpoint and ChromaDB for vector search.

---

## Architecture Overview

```
User Question
     │
     ▼
Query Normalizer          ← lowercase, punctuation strip, abbreviation expansion
     │
     ▼
Query Rewriter (LLM)      ← converts informal queries to search-friendly form
     │
     ▼
Hybrid Retriever
  ├── Semantic (MMR)  70% ← ChromaDB + OpenAI embeddings via OpenRouter
  └── BM25 Keyword    30% ← in-memory index built from all chunks at startup
     │
     ▼
Adaptive-k Expansion      ← widens search if best score < threshold
     │
     ▼
Relevance Gate            ← refuses if max score < relevance_score_threshold
     │
     ▼
LLM Answer Generation     ← gpt-4o-mini via OpenRouter, temperature=0.0
     │
     ▼
ChatResponse              ← answer + sources + retrieval metadata
```

---

## Project Structure

```
RAG_based_Chatbot/
├── app/
│   └── app.py                   # Streamlit chat UI
├── config/
│   ├── __init__.py
│   └── settings.py              # Pydantic-settings config from .env
├── data/
│   └── knowledge_base.docx      # College knowledge base document
├── scripts/
│   ├── ingest.py                # CLI: ingest documents into ChromaDB
│   ├── evaluate.py              # CLI: run RAGAS evaluation
│   └── evaluate_retrieval.py    # CLI: retrieval smoke-test (7 queries)
├── src/
│   ├── __init__.py
│   ├── chunker.py               # Recursive character splitter with metadata
│   ├── document_loader.py       # .docx parser → LangChain Documents
│   ├── embeddings.py            # OpenAIEmbeddings via OpenRouter
│   ├── factory.py               # create_chatbot() bootstrap function
│   ├── ingestion.py             # Orchestrates load → chunk → embed → store
│   ├── llm.py                   # ChatOpenAI via OpenRouter
│   ├── prompt.py                # System prompt, user template, refusal message
│   ├── query_normalizer.py      # Abbreviation expansion + text cleaning
│   ├── query_rewriter.py        # LLM-based query rewriter (QueryRewriter class)
│   ├── rag_chain.py             # RAGChatbot.ask() — full end-to-end pipeline
│   ├── retriever.py             # DocumentRetriever — hybrid BM25 + MMR
│   ├── vector_store.py          # ChromaDB persistence helpers
│   └── evaluation/
│       ├── __init__.py
│       └── ragas_eval.py        # RAGAS evaluation pipeline
├── chroma_db/                   # ChromaDB persistence (auto-created, gitignored)
├── evaluation_results/          # Evaluation outputs (auto-created, gitignored)
├── .env                         # API key + config (never committed)
├── .env.example                 # Template for .env
├── .gitignore
├── .streamlit/config.toml
├── requirements.txt
├── run.py                       # Convenience Streamlit launcher
└── README.md
```

---

## Completed Features (12 / 12)

### 1. Configuration System (`config/settings.py`)
- Pydantic-settings with BOM-safe `.env` loading (Windows-compatible)
- All pipeline parameters exposed: API keys, models, chunking, retrieval, MMR, adaptive-k, query rewriting toggle
- `EVAL_DIR` path constant for evaluation output

### 2. Document Loader (`src/document_loader.py`)
- Parses `.docx` knowledge base using `python-docx`
- Headings detected by paragraph style or numeric pattern, prepended to section buffers
- Tables converted to Markdown for retrieval
- Outputs LangChain `Document` objects with `section` and `source` metadata

### 3. Chunker (`src/chunker.py`)
- `RecursiveCharacterTextSplitter` — 500 chars / 100 overlap
- Every chunk has section heading prepended to content
- Enriched metadata per chunk: `section`, `filename`, `chunk_id`, `heading`

### 4. Embeddings (`src/embeddings.py`)
- `OpenAIEmbeddings` pointed at OpenRouter's API base with correct auth headers

### 5. Vector Store (`src/vector_store.py`)
- ChromaDB with `build_vector_store`, `ingest_documents` (reset support), `load_vector_store`, `collection_is_empty`
- Knowledge base already ingested (chroma_db/ populated)

### 6. Ingestion Pipeline (`src/ingestion.py` + `scripts/ingest.py`)
- `run_ingestion(reset=False)` — skips if collection already populated
- CLI with `--reset` flag for full re-ingest
- Unicode-safe console output for Windows paths

### 7. LLM Factory (`src/llm.py`)
- `ChatOpenAI` via OpenRouter, `temperature=0.0`, `max_tokens=1024`

### 8. Prompt Module (`src/prompt.py`)
- `build_system_prompt()` — instructs LLM to extract answers from partial context rather than refusing prematurely
- `build_user_prompt()` — injects context + original question
- `build_refusal_message()` — standard out-of-scope response

### 9. Query Normalizer (`src/query_normalizer.py`)
- Lowercase, punctuation stripping, whitespace collapse
- 50+ domain abbreviation expansions: `hod`, `ece`, `eee`, `mech`, `aids`, `aiml`, `dept`, `princi`, etc.

### 10. Query Rewriter (`src/query_rewriter.py`)
- `QueryRewriter` class — LLM-based rewrite to search-optimized form
- `temperature=0.0`, `max_tokens=128`, graceful fallback to original query on error
- Controlled by `enable_query_rewriting` setting

### 11. Hybrid Retriever (`src/retriever.py`)
- `DocumentRetriever` — MMR semantic (70%) + BM25 keyword (30%)
- `RetrievalResult` dataclass with documents, scores, latency, relevance flag
- Adaptive-k: expands to `fetch_k` candidates if best score < `adaptive_k_threshold`
- Structured diagnostics printed to stdout on every retrieval call
- `format_context()` formats retrieved chunks for LLM prompt

### 12. RAG Chain (`src/rag_chain.py`)
- `RAGChatbot.ask(question)` — full pipeline: normalize → rewrite → retrieve → relevance gate → generate → refusal detection
- `ChatResponse` dataclass: `answer`, `sources`, `refused`, `retrieval`, `normalized_query`, `rewritten_query`
- Source metadata included for UI display

### 13. Factory (`src/factory.py`)
- `create_chatbot(settings)` — single entry point used by both the UI and the evaluation pipeline
- Bootstraps: embeddings → vector store → auto-ingest if empty → load chunks for BM25 → `DocumentRetriever` → `QueryRewriter` → `RAGChatbot`

### 14. Streamlit UI (`app/app.py`)
- Full chat interface with persistent message history
- Sidebar: source excerpts toggle, relevance scores toggle, clear chat button
- `@st.cache_resource` chatbot init — loaded once per session
- API key validation with user-friendly error banner
- Custom CSS for chat message and source block styling

### 15. RAGAS Evaluation (`src/evaluation/ragas_eval.py` + `scripts/evaluate.py`)
- 8 ground-truth Q&A pairs covering: establishment year, NAAC grade, affiliation, vision, faculty count, contact email, out-of-scope question, placement package
- Metrics: `faithfulness`, `answer_relevancy`, `context_precision`, `context_recall`
- Saves: timestamped CSV, JSON, interactive Plotly HTML dashboard, summary JSON
- **Evaluation pipeline uses `create_chatbot(settings)` — identical production path to the Streamlit UI** (final task completed in this session)

### 16. Retrieval Smoke Test (`scripts/evaluate_retrieval.py`)
- 7 test queries for establishment-year topic
- Keyword-hit pass/fail scoring, latency measurement, formatted table output

---

## Key Configuration Defaults (`.env` / `settings.py`)

| Variable | Default | Notes |
|---|---|---|
| `LLM_MODEL` | `openai/gpt-4o-mini` | Via OpenRouter |
| `EMBEDDING_MODEL` | `openai/text-embedding-3-small` | Via OpenRouter |
| `RETRIEVAL_TOP_K` | `5` | Chunks returned per query |
| `RELEVANCE_SCORE_THRESHOLD` | `0.20` | Minimum score before refusing |
| `FETCH_K` | `20` | MMR candidate pool size |
| `LAMBDA_MULT` | `0.5` | MMR diversity/relevance balance |
| `ADAPTIVE_K_THRESHOLD` | `0.45` | Triggers wider search if best score below this |
| `CHUNK_SIZE` | `500` | Characters per chunk |
| `CHUNK_OVERLAP` | `100` | Overlap between chunks |
| `ENABLE_QUERY_REWRITING` | `true` | LLM query rewrite before retrieval |

---

## Running the Project

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set API key in .env
#    OPENROUTER_API_KEY=sk-or-v1-...

# 3. Ingest knowledge base (one-time)
python scripts/ingest.py

# 4. Launch chatbot
python run.py
# or: streamlit run app/app.py

# 5. Run RAGAS evaluation
python scripts/evaluate.py

# 6. Run retrieval smoke test
python scripts/evaluate_retrieval.py
```

---

## Remaining Task

### Fix: `ragas` / `langchain-community` version incompatibility

**Status:** Pre-existing environment issue — not a code bug.

**Symptom:**
```
ModuleNotFoundError: No module named 'langchain_community.chat_models.vertexai'
```

**Cause:** `ragas==0.4.3` hard-imports `langchain_community.chat_models.vertexai`, which was removed in `langchain-community==0.4.x`.

**Impact:** `scripts/evaluate.py` (RAGAS evaluation) cannot run. The chatbot UI and all other scripts are unaffected.

**Fix (choose one):**

```bash
# Option A — upgrade ragas (preferred, gets latest fixes)
pip install "ragas>=0.2.6,<0.5.0"

# Option B — downgrade langchain-community to a version that still has vertexai
pip install "langchain-community==0.3.20"

# Option C — pin both to known-compatible versions
pip install "ragas==0.2.6" "langchain-community==0.3.20"
```

After fixing, run:
```bash
python scripts/evaluate.py
```

Expected output:
```
Running RAGAS evaluation (this may take a few minutes)...

Evaluation complete.
Results saved to: evaluation_results/ragas_results_<timestamp>.csv

Average scores:
  faithfulness: 0.xxx
  answer_relevancy: 0.xxx
  context_precision: 0.xxx
  context_recall: 0.xxx
```

---

## Session History

| Session | Work Done |
|---|---|
| Session 1 (Jul 9) | Built entire project: config, loader, chunker, embeddings, vector store, ingestion, LLM, prompt, query normalizer, query rewriter, hybrid retriever, RAG chain, factory, Streamlit UI, RAGAS evaluation skeleton, retrieval smoke test, README |
| Session 2 (Jul 10) | Recovered project state; fixed evaluation pipeline — replaced manual `RAGChatbot` construction with `create_chatbot(settings)` so evaluation uses the identical production path as the UI; removed dead imports |

---

*Last updated: 2026-07-10*
