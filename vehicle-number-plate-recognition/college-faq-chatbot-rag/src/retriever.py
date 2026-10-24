"""Enhanced retriever: hybrid BM25+MMR semantic, adaptive-k, diagnostics logging."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from langchain_chroma import Chroma
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document

from config.settings import Settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------

@dataclass
class RetrievalResult:
    documents: list[Document]
    scores: list[float]
    is_relevant: bool
    rewritten_query: str = ""
    latency_ms: float = 0.0
    diagnostics: list[dict] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Diagnostics printer
# ---------------------------------------------------------------------------

def _log_retrieval(query: str, result: RetrievalResult) -> None:
    """Print a structured diagnostics block for every retrieval call."""
    sep = "=" * 70
    lines = [
        sep,
        "RETRIEVAL DIAGNOSTICS",
        f"  Original query   : {query}",
        f"  Rewritten query  : {result.rewritten_query or '(unchanged)'}",
        f"  Chunks returned  : {len(result.documents)}",
        f"  Latency          : {result.latency_ms:.1f} ms",
        f"  Is relevant      : {result.is_relevant}",
    ]
    for i, (doc, score) in enumerate(zip(result.documents, result.scores), 1):
        meta = doc.metadata
        lines.append(
            f"  [{i}] score={score:.4f} | chunk_id={meta.get('chunk_id','?')} "
            f"| section={meta.get('section','?')} | heading={meta.get('heading','?')}"
        )
        lines.append(f"       {doc.page_content[:120].replace(chr(10), ' ')}")
    lines.append(sep)

    output = "\n".join(lines)
    logger.info(output)
    print(output)


# ---------------------------------------------------------------------------
# Main retriever
# ---------------------------------------------------------------------------

class DocumentRetriever:
    """Hybrid (BM25 + MMR semantic) retriever with adaptive-k and diagnostics."""

    def __init__(
        self,
        vector_store: Chroma,
        settings: Settings,
        all_chunks: list[Document] | None = None,
    ) -> None:
        self._vector_store = vector_store
        self._settings = settings
        self._all_chunks = all_chunks or []
        self._bm25: BM25Retriever | None = None

        if self._all_chunks:
            self._bm25 = BM25Retriever.from_documents(
                self._all_chunks,
                k=settings.retrieval_top_k,
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(self, query: str, rewritten_query: str = "") -> RetrievalResult:
        """Retrieve chunks using hybrid search + adaptive-k expansion.

        Parameters
        ----------
        query:
            The original user query (used only for diagnostics / logging).
        rewritten_query:
            The search-optimized query sent to the vector store.
            Falls back to *query* when empty.
        """
        search_query = rewritten_query or query
        t0 = time.perf_counter()

        docs, scores = self._hybrid_retrieve(search_query, k=self._settings.retrieval_top_k)

        # Adaptive-k: widen the search if the best score is too low
        best_score = max(scores) if scores else 0.0
        if best_score < self._settings.adaptive_k_threshold and len(docs) < self._settings.fetch_k:
            logger.info(
                "Adaptive-k triggered (best=%.4f < %.4f); expanding to fetch_k=%d",
                best_score,
                self._settings.adaptive_k_threshold,
                self._settings.fetch_k,
            )
            docs, scores = self._hybrid_retrieve(search_query, k=self._settings.fetch_k)

        latency_ms = (time.perf_counter() - t0) * 1000
        is_relevant = bool(scores) and max(scores) >= self._settings.relevance_score_threshold

        result = RetrievalResult(
            documents=docs,
            scores=scores,
            is_relevant=is_relevant,
            rewritten_query=rewritten_query,
            latency_ms=latency_ms,
        )
        _log_retrieval(query, result)
        return result

    # ------------------------------------------------------------------
    # Context formatter
    # ------------------------------------------------------------------

    def format_context(self, documents: list[Document]) -> str:
        if not documents:
            return ""
        blocks: list[str] = []
        for index, doc in enumerate(documents, start=1):
            section = doc.metadata.get("section", "Unknown")
            heading = doc.metadata.get("heading", "")
            label = heading if heading and heading != section else section
            blocks.append(
                f"[Source {index} | Section: {label}]\n{doc.page_content.strip()}"
            )
        return "\n\n---\n\n".join(blocks)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _semantic_retrieve(self, query: str, k: int) -> list[tuple[Document, float]]:
        """MMR-based semantic retrieval with post-hoc scoring."""
        fetch_k = max(k * 2, self._settings.fetch_k)
        try:
            mmr_docs = self._vector_store.max_marginal_relevance_search(
                query,
                k=k,
                fetch_k=fetch_k,
                lambda_mult=self._settings.lambda_mult,
            )
            # Retrieve scores post-hoc via a broader similarity search
            scored = self._vector_store.similarity_search_with_relevance_scores(
                query, k=fetch_k
            )
            score_map: dict[str, float] = {d.page_content[:80]: s for d, s in scored}
            pairs: list[tuple[Document, float]] = []
            for doc in mmr_docs:
                key = doc.page_content[:80]
                pairs.append((doc, score_map.get(key, 0.0)))
            return pairs
        except Exception as exc:  # noqa: BLE001
            logger.warning("MMR search failed (%s); falling back to similarity search.", exc)
            return self._vector_store.similarity_search_with_relevance_scores(query, k=k)

    def _bm25_retrieve(self, query: str, k: int) -> list[tuple[Document, float]]:
        """BM25 keyword retrieval with rank-based synthetic scores."""
        if self._bm25 is None:
            return []
        self._bm25.k = k
        try:
            docs = self._bm25.invoke(query)
            pairs: list[tuple[Document, float]] = []
            n = max(len(docs) - 1, 1)
            for rank, doc in enumerate(docs):
                # Rank 0 -> 0.75, last rank -> 0.50
                score = max(0.5, 0.75 - rank * (0.25 / n))
                pairs.append((doc, score))
            return pairs
        except Exception as exc:  # noqa: BLE001
            logger.warning("BM25 retrieval failed (%s).", exc)
            return []

    def _hybrid_retrieve(self, query: str, k: int) -> tuple[list[Document], list[float]]:
        """Merge semantic (70%) + BM25 (30%), de-duplicate, sort by combined score."""
        semantic_pairs = self._semantic_retrieve(query, k)

        if self._bm25 is not None:
            bm25_pairs = self._bm25_retrieve(query, k)
        else:
            bm25_pairs = []

        # Weighted merge keyed on first 120 chars of page content
        merged: dict[str, tuple[Document, float]] = {}

        for doc, score in semantic_pairs:
            key = doc.page_content[:120]
            merged[key] = (doc, score * 0.7)

        for doc, score in bm25_pairs:
            key = doc.page_content[:120]
            if key in merged:
                existing_doc, existing_score = merged[key]
                merged[key] = (existing_doc, existing_score + score * 0.3)
            else:
                merged[key] = (doc, score * 0.3)

        sorted_items = sorted(merged.values(), key=lambda x: x[1], reverse=True)[:k]
        documents = [item[0] for item in sorted_items]
        scores = [item[1] for item in sorted_items]
        return documents, scores
