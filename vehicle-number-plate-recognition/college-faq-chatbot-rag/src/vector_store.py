"""Persistent ChromaDB vector store management."""

from __future__ import annotations

from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from config.settings import Settings


def build_vector_store(
    settings: Settings,
    embedding: Embeddings,
) -> Chroma:
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    return Chroma(
        collection_name=settings.collection_name,
        embedding_function=embedding,
        persist_directory=str(settings.chroma_persist_dir),
    )


def ingest_documents(
    vector_store: Chroma,
    chunks: list[Document],
    *,
    reset: bool = False,
    settings: Settings | None = None,
    embedding=None,
) -> int:
    if reset:
        # Capture attributes before deleting
        collection_name = (
            settings.collection_name
            if settings
            else vector_store._collection_name
        )
        embedding_fn = embedding or vector_store._embedding_function
        persist_dir = (
            str(settings.chroma_persist_dir)
            if settings
            else vector_store._persist_directory
        )

        try:
            vector_store.delete_collection()
        except Exception:
            pass

        # Re-create fresh collection
        vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_fn,
            persist_directory=persist_dir,
        )

    ids = [f"chunk_{chunk.metadata.get('chunk_id', idx)}" for idx, chunk in enumerate(chunks)]
    vector_store.add_documents(documents=chunks, ids=ids)
    return len(chunks)


def load_vector_store(
    settings: Settings,
    embedding: Embeddings,
) -> Chroma:
    return build_vector_store(settings, embedding)


def collection_is_empty(vector_store: Chroma) -> bool:
    try:
        return vector_store._collection.count() == 0
    except Exception:
        return True
