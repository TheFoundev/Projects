"""Split loaded documents into retrieval-ready chunks.

Improvements over v1:
- Smaller default chunk size (500 chars / 100 overlap) for tighter retrieval.
- Every chunk inherits the section heading from its parent document.
- Enriched metadata: section, filename, chunk_id, heading, char_start.
"""

from __future__ import annotations

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from config.settings import Settings


def chunk_documents(documents: list[Document], settings: Settings) -> list[Document]:
    """Split *documents* into overlapping chunks with enriched metadata."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=settings.chunk_size,
        chunk_overlap=settings.chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""],
        length_function=len,
    )

    all_chunks: list[Document] = []
    global_index = 0

    for doc in documents:
        raw_chunks = splitter.split_text(doc.page_content)
        section = doc.metadata.get("section", "General")
        source = doc.metadata.get("source", "knowledge_base.docx")

        # Derive a short heading from the section name
        heading = section.strip()

        for raw_text in raw_chunks:
            # Prepend heading to every chunk so the LLM always sees context
            if heading and not raw_text.startswith(heading):
                chunk_text = f"{heading}\n{raw_text}"
            else:
                chunk_text = raw_text

            chunk = Document(
                page_content=chunk_text,
                metadata={
                    "section": section,
                    "filename": source,
                    "chunk_id": global_index,
                    "heading": heading,
                    **{k: v for k, v in doc.metadata.items()
                       if k not in ("section", "source")},
                },
            )
            all_chunks.append(chunk)
            global_index += 1

    return all_chunks
