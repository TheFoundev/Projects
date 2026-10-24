"""OpenRouter-compatible LLM factory."""

from __future__ import annotations

from langchain_openai import ChatOpenAI

from config.settings import Settings


def build_llm(settings: Settings) -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    return ChatOpenAI(
        model=settings.llm_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        default_headers=settings.openrouter_headers,
        temperature=0.0,
        max_tokens=1024,
    )
