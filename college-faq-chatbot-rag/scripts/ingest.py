#!/usr/bin/env python3
"""Ingest the knowledge base into ChromaDB."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.ingestion import run_ingestion  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest college knowledge base into ChromaDB")
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete existing collection and re-ingest from scratch",
    )
    args = parser.parse_args()

    result = run_ingestion(reset=args.reset)
    print("Ingestion complete:")
    print(f"  Sections parsed : {result['sections']}")
    print(f"  Chunks indexed  : {result['chunks']}")
    # Print persist_dir without throwing on Unicode paths
    try:
        print(f"  Persist dir     : {result['persist_dir']}")
    except UnicodeEncodeError:
        print(f"  Persist dir     : [path with Unicode characters]")


if __name__ == "__main__":
    main()
