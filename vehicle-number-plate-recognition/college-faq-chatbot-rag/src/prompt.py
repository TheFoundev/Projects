"""Prompt templates for the college FAQ chatbot.

The system prompt has been made less rigid so the LLM can extract answers
from partial context matches instead of refusing unnecessarily.

Everything institution-specific is injected from :class:`config.settings.Settings`,
so the same code serves any college, university or training institute.
"""

from __future__ import annotations

from config.settings import Settings


def build_refusal_message(settings: Settings) -> str:
    """The message shown when the knowledge base cannot answer a question."""
    return (
        "I'm sorry, but I couldn't find that information in the knowledge base. "
        "Please rephrase your question or contact the institution directly for "
        "assistance."
    )


def build_system_prompt(settings: Settings) -> str:
    """The grounding instructions handed to the chat model."""
    return f"""You are the official FAQ assistant for {settings.institution_name}.

Your goal is to help students and visitors get accurate information about the institution.

Guidelines:
1. Answer using the provided context excerpts from the knowledge base.
2. If the context contains relevant information — even partially — extract and present it clearly.
3. Do NOT use your own general knowledge, internet information, or assumptions.
4. If the context genuinely contains NO information related to the question, respond with:
   "{build_refusal_message(settings)}"
5. When the answer is partially present, give what you can find and note if details are limited.
6. Keep answers concise, accurate, and helpful.
7. For faculty or roster questions, only mention people explicitly listed in the context.
8. Numbers, dates, and statistics must come directly from the context — do not guess.
"""


def build_user_prompt(context: str, question: str) -> str:
    """The per-question prompt that carries the retrieved context."""
    return f"""Context from the institution knowledge base:
{context}

Question: {question}

Instructions:
- Answer using ONLY the context above.
- If the context contains the answer or partial information, extract and present it.
- Only refuse if the context contains absolutely no relevant information.
"""
