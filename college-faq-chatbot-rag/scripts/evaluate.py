#!/usr/bin/env python3
"""Run RAGAS evaluation and save results."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.evaluation.ragas_eval import run_ragas_evaluation, save_evaluation_results  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate RAG chatbot with RAGAS")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to save evaluation artifacts",
    )
    args = parser.parse_args()

    print("Running RAGAS evaluation (this may take a few minutes)...")
    df = run_ragas_evaluation()
    output_path = save_evaluation_results(df, args.output_dir)

    print("\nEvaluation complete.")
    print(f"Results saved to: {output_path}")
    print("\nAverage scores:")
    for col in df.columns:
        if col not in {"question", "contexts", "ground_truth", "answer"}:
            print(f"  {col}: {df[col].mean():.3f}")


if __name__ == "__main__":
    main()
