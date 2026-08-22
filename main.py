"""Standalone entrypoint for PBIRS Mailer."""

import sys
from importlib import import_module
from pathlib import Path


def _load_main():
    """Load the src-layout package even when the project is not installed."""
    source_dir = Path(__file__).resolve().parent / "src"
    source_path = str(source_dir)
    if source_path not in sys.path:
        sys.path.insert(0, source_path)
    return import_module("pbirs_mailer.cli").main


if __name__ == "__main__":
    raise SystemExit(_load_main()())
