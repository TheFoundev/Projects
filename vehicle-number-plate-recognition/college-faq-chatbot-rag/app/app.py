from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st

from config.settings import get_settings
from src.factory import create_chatbot
from src.rag_chain import ChatResponse

settings = get_settings()

st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout="centered",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
        .stChatMessage { padding: 0.5rem 0; }
        .source-label {
            font-size: 0.78rem;
            color: #6b7280;
            margin-top: 0.25rem;
        }
        .source-block {
            border-left: 3px solid #3b82f6;
            padding-left: 0.6rem;
            margin-bottom: 0.5rem;
            font-size: 0.82rem;
            color: #374151;
        }
        .sources-used-header {
            font-size: 0.80rem;
            font-weight: 600;
            color: #374151;
            margin-top: 0.5rem;
            margin-bottom: 0.15rem;
        }
        .sources-used-item {
            font-size: 0.78rem;
            color: #6b7280;
            padding-left: 0.4rem;
            line-height: 1.6;
        }
        .stat-line {
            font-size: 0.76rem;
            color: #9ca3af;
            margin-top: 0.3rem;
            margin-bottom: 0.1rem;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# Rendering helpers

def _unique_section_labels(sources: list[dict]) -> list[str]:
    seen: set[str] = set()
    labels: list[str] = []
    for src in sources:
        heading = src.get("heading", "").strip()
        section = src.get("section", "").strip()
        label = heading if heading and heading != section else section
        if label and label not in seen:
            seen.add(label)
            labels.append(label)
    return labels


def _render_sources_used(sources: list[dict]) -> None:
    """Bulleted Sources Used list. No page numbers (source is .docx)."""
    labels = _unique_section_labels(sources)
    if not labels:
        return
    items_html = "".join(
        f"<div class='sources-used-item'>• {label}</div>" for label in labels
    )
    st.markdown(
        f"<div class='sources-used-header'>Sources Used</div>{items_html}",
        unsafe_allow_html=True,
    )


def _render_sources(sources: list[dict], include_scores: bool, key_prefix: str = "") -> None:
    """Full excerpts in a collapsible expander."""
    with st.expander(f"📄 {len(sources)} source excerpt(s) used", expanded=False):
        for i, src in enumerate(sources, start=1):
            score_tag = f" · score: {src['score']:.3f}" if include_scores else ""
            st.markdown(
                f"<div class='source-label'><strong>Source {i}</strong> · {src['section']}{score_tag}</div>"
                f"<div class='source-block'>{src['content'][:350]}…</div>",
                unsafe_allow_html=True,
            )


def _render_answer_stats(response: ChatResponse) -> None:
    """Latency + chunk count after every non-refused answer."""
    if response.retrieval is None:
        return
    latency = response.retrieval.latency_ms
    chunk_count = len(response.retrieval.documents)
    st.markdown(
        f"<div class='stat-line'>"
        f"⏱ {latency:.0f} ms &nbsp;·&nbsp; 📦 {chunk_count} chunks retrieved"
        f"</div>",
        unsafe_allow_html=True,
    )


@st.cache_resource(show_spinner=False)
def load_chatbot():
    settings = get_settings()
    if not settings.openrouter_api_key or settings.openrouter_api_key == "your_openrouter_api_key_here":
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Open the .env file and replace the placeholder with your real API key, then restart the app."
        )

    chatbot = create_chatbot(settings)

    try:
        chunk_count = len(chatbot._retriever._all_chunks)
    except Exception:
        chunk_count = "N/A"

    try:
        vector_count = chatbot._retriever._vector_store._collection.count()
    except Exception:
        vector_count = "N/A"

    kb_info = {
        "document_name": Path(settings.knowledge_base_path).name,
        "chunk_count": chunk_count,
        "vector_count": vector_count,
        "embedding_model": (
            settings.local_embedding_model
            if settings.embedding_provider.lower() == "local"
            else settings.embedding_model
        ),
        "collection_name": settings.collection_name,
        "retrieval_mode": "Hybrid (BM25 + MMR)",
        "top_k": settings.retrieval_top_k,
    }

    return chatbot, kb_info


if "messages" not in st.session_state:
    st.session_state.messages = []
if "responses" not in st.session_state:
    st.session_state.responses = []
if "init_error" not in st.session_state:
    st.session_state.init_error = None

chatbot = None
kb_info: dict = {}

if st.session_state.init_error is None:
    with st.spinner("🔄 Loading knowledge base… (first run may take a moment)"):
        try:
            chatbot, kb_info = load_chatbot()
        except Exception as exc:
            st.session_state.init_error = str(exc)

with st.sidebar:
    st.title(f"{settings.app_icon} {settings.institution_name}")
    st.caption(f"{settings.app_title} · RAG")
    st.divider()

    st.subheader("🗂️ Knowledge Base")
    if kb_info:
        st.markdown("**Status:** 🟢 Loaded")
        st.markdown(f"**Document:** `{kb_info['document_name']}`")
        st.markdown(f"**Chunk Count:** {kb_info['chunk_count']}")
        st.markdown(f"**Vectors in DB:** {kb_info['vector_count']}")
    else:
        st.markdown("**Status:** 🔴 Not Loaded")

    st.divider()

    st.subheader("⚙️ Retrieval Config")
    if kb_info:
        st.markdown("**Embedding Model:**")
        st.caption(kb_info["embedding_model"])
        st.markdown(
            f"**Vector Database:** ChromaDB  \n"
            f"`{kb_info['collection_name']}`"
        )
        st.markdown(f"**Retrieval Mode:** {kb_info['retrieval_mode']}")
        st.markdown(f"**Top-K:** {kb_info['top_k']}")

    st.divider()

    st.subheader("🔧 Settings")
    show_sources = st.toggle("Show source excerpts", value=True)
    show_scores = st.toggle("Show relevance scores", value=False)

    st.divider()

    if st.button("🗑️ Clear chat history", use_container_width=True):
        st.session_state.messages = []
        st.session_state.responses = []
        st.rerun()

    st.divider()

    st.subheader("ℹ️ About")
    st.markdown(
        f"Answers questions about **{settings.institution_name}** using a RAG pipeline "
        "grounded strictly on the institution knowledge base. "
        "Questions outside the knowledge base are politely declined."
    )

st.title(f"{settings.app_icon} {settings.institution_name} {settings.app_title}")
st.caption(
    f"Ask me anything about {settings.institution_name} — admissions, faculty, "
    "departments, placements, facilities, and more."
)
st.divider()

if st.session_state.init_error:
    st.error(f"⚠️ **Failed to initialise chatbot**\n\n{st.session_state.init_error}", icon="🚨")
    st.stop()

assistant_idx = 0
for msg in st.session_state.messages:
    avatar = "🧑‍💻" if msg["role"] == "user" else settings.app_icon
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            resp = st.session_state.responses[assistant_idx] if assistant_idx < len(st.session_state.responses) else None
            if resp and not resp.refused:
                _render_answer_stats(resp)
                if resp.sources:
                    _render_sources_used(resp.sources)
                    if show_sources:
                        _render_sources(resp.sources, show_scores, key_prefix=f"hist_{assistant_idx}")
            assistant_idx += 1

if prompt := st.chat_input(f"Ask a question about {settings.institution_name}…"):
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user", avatar="🧑‍💻"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar=settings.app_icon):
        with st.spinner("Thinking…"):
            try:
                response: ChatResponse = chatbot.ask(prompt)
            except Exception as exc:
                err = f"⚠️ Error generating response: `{exc}`"
                st.error(err)
                st.session_state.messages.append({"role": "assistant", "content": err})
                st.session_state.responses.append(None)
                st.stop()

        st.markdown(response.answer)

        if not response.refused:
            _render_answer_stats(response)
            if response.sources:
                _render_sources_used(response.sources)
                if show_sources:
                    _render_sources(response.sources, show_scores, key_prefix=f"new_{len(st.session_state.responses)}")

    st.session_state.messages.append({"role": "assistant", "content": response.answer})
    st.session_state.responses.append(response)
