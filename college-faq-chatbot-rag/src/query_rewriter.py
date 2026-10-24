"""LLM-based query rewriter for the RAG pipeline.

Rewrites informal or ambiguous user questions into clean, search-friendly
queries that improve semantic retrieval accuracy.

Example rewrites
----------------
"in which year the institution start"  -> "When was the college established?"
"fees for cse"                          -> "CSE tuition fee"
"hostel available?"                     -> "hostel facilities"
"""

from __future__ import annotations

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from config.settings import Settings

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a search-query optimizer for a college FAQ chatbot.

Your ONLY job: rewrite the user's question into a clean, concise, search-friendly query.

Rules:
- Fix spelling and grammar.
- Expand abbreviations (e.g. "dept" -> "department", "estd" -> "established").
- Preserve the original intent exactly — do NOT change the topic.
- Output ONLY the rewritten query. No explanation, no punctuation beyond the query itself.
- If the question is already clear and well-formed, return it unchanged.

Examples:
User: in which year the institution start
Output: When was the college established?

User: fees for cse
Output: CSE tuition fee

User: hostel available?
Output: hostel facilities

User: how many faculty in cse dept
Output: number of faculty in CSE department

User: naac grade of college
Output: NAAC accreditation grade of the institution

User: who is hod of ece
Output: head of department of ECE

User: placement highest package
Output: highest placement package
"""


class QueryRewriter:
    """Rewrite a user query into a search-optimized form using an LLM."""

    def __init__(self, settings: Settings) -> None:
        self._llm = ChatOpenAI(
            model=settings.llm_model,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base=settings.openrouter_base_url,
            default_headers=settings.openrouter_headers,
            temperature=0.0,
            max_tokens=128,
        )

    def rewrite(self, query: str) -> str:
        """Return a rewritten, search-friendly version of *query*.

        Falls back to the original query on any error to avoid breaking
        the retrieval pipeline.
        """
        if not query or not query.strip():
            return query

        try:
            response = self._llm.invoke(
                [
                    SystemMessage(content=_SYSTEM_PROMPT),
                    HumanMessage(content=query.strip()),
                ]
            )
            rewritten = response.content.strip()
            if rewritten:
                logger.debug("Query rewrite: %r -> %r", query, rewritten)
                return rewritten
        except Exception as exc:  # noqa: BLE001
            logger.warning("Query rewriter failed (%s); using original query.", exc)

        return query
