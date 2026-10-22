"""Orchestrate document loading, chunking, and vector store ingestion."""

from __future__ import annotations

from config.settings import Settings, get_settings
from src.chunker import chunk_documents
from src.document_loader import load_docx
from src.embeddings import build_embeddings
from src.vector_store import build_vector_store, collection_is_empty, ingest_documents


def run_ingestion(*, reset: bool = False, settings: Settings | None = None) -> dict:
    settings = settings or get_settings()

    documents = load_docx(settings.knowledge_base_path)
    chunks = chunk_documents(documents, settings)
    embeddings = build_embeddings(settings)
    vector_store = build_vector_store(settings, embeddings)

    if reset or collection_is_empty(vector_store):
        count = ingest_documents(
            vector_store,
            chunks,
            reset=reset,
            settings=settings,
            embedding=embeddings,
        )
    else:
        count = vector_store._collection.count()

    return {
        "sections": len(documents),
        "chunks": count,
        "persist_dir": str(settings.chroma_persist_dir),
    }
