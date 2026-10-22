"""End-to-end RAG pipeline with query normalization, rewriting, and strict grounding."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

from langchain_core.messages import HumanMessage, SystemMessage

from config.settings import Settings
from src.llm import build_llm
from src.prompt import build_refusal_message, build_system_prompt, build_user_prompt
from src.query_normalizer import normalize_query
from src.query_rewriter import QueryRewriter
from src.retriever import DocumentRetriever, RetrievalResult

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    answer: str
    sources: list[dict] = field(default_factory=list)
    refused: bool = False
    retrieval: RetrievalResult | None = None
    normalized_query: str = ""
    rewritten_query: str = ""


class RAGChatbot:
    def __init__(
        self,
        retriever: DocumentRetriever,
        settings: Settings,
        rewriter: QueryRewriter | None = None,
    ) -> None:
        self._retriever = retriever
        self._settings = settings
        self._llm = build_llm(settings)
        self._rewriter = rewriter

    def ask(self, question: str) -> ChatResponse:
        original = question.strip()
        if not original:
            return ChatResponse(answer="Please enter a question.", refused=True)

        # --- Step 1: Normalize (cheap, always on) ---
        normalized = normalize_query(original)
        logger.debug("Normalized: %r -> %r", original, normalized)

        # --- Step 2: LLM rewrite (optional, can be disabled in settings) ---
        if self._rewriter and self._settings.enable_query_rewriting:
            rewritten = self._rewriter.rewrite(normalized)
        else:
            rewritten = normalized
        logger.debug("Rewritten:  %r -> %r", normalized, rewritten)

        # --- Step 3: Retrieve with rewritten query ---
        retrieval = self._retriever.retrieve(
            query=original,
            rewritten_query=rewritten,
        )

        if not retrieval.is_relevant:
            return ChatResponse(
                answer=build_refusal_message(self._settings),
                refused=True,
                retrieval=retrieval,
                normalized_query=normalized,
                rewritten_query=rewritten,
            )

        # --- Step 4: Build context and prompt ---
        context = self._retriever.format_context(retrieval.documents)
        # Always use the *original* question for the LLM so the answer sounds natural
        user_prompt = build_user_prompt(context=context, question=original)

        response = self._llm.invoke(
            [
                SystemMessage(content=build_system_prompt(self._settings)),
                HumanMessage(content=user_prompt),
            ]
        )
        answer = response.content.strip()

        if self._is_refusal(answer):
            return ChatResponse(
                answer=build_refusal_message(self._settings),
                sources=self._build_sources(retrieval),
                refused=True,
                retrieval=retrieval,
                normalized_query=normalized,
                rewritten_query=rewritten,
            )

        return ChatResponse(
            answer=answer,
            sources=self._build_sources(retrieval),
            refused=False,
            retrieval=retrieval,
            normalized_query=normalized,
            rewritten_query=rewritten,
        )

    @staticmethod
    def _is_refusal(answer: str) -> bool:
        normalized = answer.lower()
        refusal_markers = (
            "couldn't find",
            "could not find",
            "do not have that information",
            "not in the knowledge base",
            "insufficient context",
            "no information",
            "cannot find",
            "not available in",
        )
        return any(marker in normalized for marker in refusal_markers)

    @staticmethod
    def _build_sources(retrieval: RetrievalResult) -> list[dict]:
        sources: list[dict] = []
        for doc, score in zip(retrieval.documents, retrieval.scores, strict=False):
            sources.append(
                {
                    "section": doc.metadata.get("section", "Unknown"),
                    "heading": doc.metadata.get("heading", ""),
                    "content": doc.page_content[:400],
                    "score": round(score, 4),
                    "chunk_id": doc.metadata.get("chunk_id", "?"),
                }
            )
        return sources
