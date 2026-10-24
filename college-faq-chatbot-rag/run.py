#!/usr/bin/env python3
"""
Convenience launcher for the College FAQ Chatbot.

Usage:
    python run.py

This is equivalent to:
    streamlit run app/app.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> None:
    app_path = Path(__file__).resolve().parent / "app" / "app.py"
    cmd = [sys.executable, "-m", "streamlit", "run", str(app_path)]
    print("Starting College FAQ Chatbot…")
    print(f"Running: {' '.join(cmd)}\n")
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nChatbot stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
