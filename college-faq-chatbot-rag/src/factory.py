"""Factory helpers to bootstrap the chatbot with all enhanced components."""

from __future__ import annotations

import logging

from config.settings import Settings, get_settings
from src.chunker import chunk_documents
from src.document_loader import load_docx
from src.embeddings import build_embeddings
from src.ingestion import run_ingestion
from src.query_rewriter import QueryRewriter
from src.rag_chain import RAGChatbot
from src.retriever import DocumentRetriever
from src.vector_store import collection_is_empty, load_vector_store

logger = logging.getLogger(__name__)


def create_chatbot(settings: Settings | None = None) -> RAGChatbot:
    """Bootstrap the full RAG pipeline.

    Loads the knowledge base, builds BM25 index from live chunks,
    wires the hybrid retriever, and returns a ready-to-use chatbot.
    """
    settings = settings or get_settings()
    embeddings = build_embeddings(settings)
    vector_store = load_vector_store(settings, embeddings)

    # Ingest if the collection is empty
    if collection_is_empty(vector_store):
        logger.info("Vector store is empty — running ingestion...")
        run_ingestion(settings=settings)

    # Load chunks from disk to build the BM25 index
    # (needed for hybrid retrieval — this is a fast in-memory build)
    try:
        documents = load_docx(settings.knowledge_base_path)
        all_chunks = chunk_documents(documents, settings)
        logger.info("Loaded %d chunks for BM25 index.", len(all_chunks))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Could not load chunks for BM25 (%s); hybrid retrieval disabled.", exc)
        all_chunks = []

    retriever = DocumentRetriever(vector_store, settings, all_chunks=all_chunks)

    # Query rewriter (optional — controlled by settings.enable_query_rewriting)
    rewriter = QueryRewriter(settings) if settings.enable_query_rewriting else None

    return RAGChatbot(retriever, settings, rewriter=rewriter)
