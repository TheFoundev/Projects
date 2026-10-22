"""Embedding factories.

Two backends are supported:

* ``openai`` (default) - OpenAI-compatible embeddings endpoint (OpenRouter).
* ``local``  - local ONNX model executed through fastembed; requires no API key
  and no network access once the model is cached.

The backend is selected with ``EMBEDDING_PROVIDER`` in the environment.
"""

from __future__ import annotations

import logging
from typing import Any

import numpy as np
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from config.settings import Settings

logger = logging.getLogger(__name__)


class LocalFastEmbedEmbeddings(Embeddings):
    """Local embeddings backed by a fastembed ONNX model."""

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5") -> None:
        self.model_name = model_name
        self._model: Any | None = None

    def _get_model(self) -> Any:
        if self._model is None:
            from fastembed import TextEmbedding

            logger.info("Loading local embedding model %s", self.model_name)
            self._model = TextEmbedding(model_name=self.model_name)
        return self._model

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        model = self._get_model()
        vectors = model.embed(list(texts))
        return [np.asarray(v, dtype=np.float32).tolist() for v in vectors]

    def embed_query(self, text: str) -> list[float]:
        model = self._get_model()
        vector = list(model.embed([text]))[0]
        return np.asarray(vector, dtype=np.float32).tolist()


def build_embeddings(settings: Settings) -> Embeddings:
    provider = (settings.embedding_provider or "openai").strip().lower()

    if provider == "local":
        return LocalFastEmbedEmbeddings(settings.local_embedding_model)

    if provider != "openai":
        raise ValueError(
            f"Unknown EMBEDDING_PROVIDER '{provider}'. Use 'openai' or 'local'."
        )

    if not settings.openrouter_api_key:
        raise ValueError(
            "OPENROUTER_API_KEY is not set. Copy .env.example to .env and add your key."
        )

    return OpenAIEmbeddings(
        model=settings.embedding_model,
        openai_api_key=settings.openrouter_api_key,
        openai_api_base=settings.openrouter_base_url,
        default_headers=settings.openrouter_headers,
        check_embedding_ctx_length=False,
    )
