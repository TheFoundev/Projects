"""Load and parse the college knowledge base from a .docx file.

Improvements over v1:
- Headings are kept *attached* to the content that follows them so that
  the chunker can prepend the heading to every chunk, rather than the
  heading being split into an isolated chunk.
- Metadata now includes the filename explicitly.
"""

from __future__ import annotations

import re
from pathlib import Path

from docx import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
from langchain_core.documents import Document as LCDocument


SECTION_PATTERN = re.compile(r"^\d+\.\s+.+")

# Section titles recognised even when the paragraph carries no heading style.
# Kept generic so any institution's knowledge base can use them.
KNOWN_SECTIONS = {
    "Overview",
    "History",
    "Vision",
    "Mission",
    "Vision & Mission",
    "Vision and Mission",
    "Programs",
    "Courses",
    "Admissions",
    "Admission Process",
    "Eligibility",
    "Fees",
    "Tuition Fees",
    "Faculty",
    "Departments",
    "Facilities",
    "Placements",
    "Research",
    "Hostel",
    "Contact",
}


def _paragraph_style_name(paragraph: Paragraph) -> str:
    if paragraph.style and paragraph.style.name:
        return paragraph.style.name
    return ""


def _is_section_heading(text: str, style_name: str) -> bool:
    stripped = text.strip()
    if not stripped:
        return False
    if SECTION_PATTERN.match(stripped):
        return True
    if style_name.lower().startswith("heading"):
        return True
    return stripped in KNOWN_SECTIONS


def _table_to_markdown(table: Table) -> str:
    rows: list[list[str]] = []
    for row in table.rows:
        cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
        if any(cells):
            rows.append(cells)
    if not rows:
        return ""

    header = rows[0]
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join(["---"] * len(header)) + " |",
    ]
    for row in rows[1:]:
        padded = row + [""] * (len(header) - len(row))
        lines.append("| " + " | ".join(padded[: len(header)]) + " |")
    return "\n".join(lines)


def _iter_block_items(document: Document):
    """Yield paragraphs and tables in document order."""
    body = document.element.body
    for child in body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            yield Paragraph(child, document)
        elif tag == "tbl":
            yield Table(child, document)


def load_docx(path: Path) -> list[LCDocument]:
    """Parse a .docx file into LangChain documents with section metadata.

    Each document corresponds to one *section* of the knowledge base.
    The section heading is prepended as the first line of the document
    content so that the chunker can propagate it into every chunk.
    """
    if not path.exists():
        raise FileNotFoundError(f"Knowledge base not found: {path}")

    doc = Document(str(path))
    documents: list[LCDocument] = []
    current_section = "General"
    # Buffer includes the heading as first line
    buffer: list[str] = []

    def flush_buffer() -> None:
        nonlocal buffer
        text = "\n".join(line for line in buffer if line.strip())
        if text.strip():
            documents.append(
                LCDocument(
                    page_content=text.strip(),
                    metadata={
                        "source": path.name,
                        "section": current_section,
                    },
                )
            )
        buffer = []

    for block in _iter_block_items(doc):
        if isinstance(block, Paragraph):
            text = block.text.strip()
            if not text:
                continue
            style = _paragraph_style_name(block)
            if _is_section_heading(text, style):
                flush_buffer()
                current_section = text
                # Include heading as first line of the new section buffer
                # so every chunk in this section starts with the heading.
                buffer.append(text)
            else:
                buffer.append(text)
        elif isinstance(block, Table):
            table_md = _table_to_markdown(block)
            if table_md:
                buffer.append(table_md)

    flush_buffer()
    return documents
