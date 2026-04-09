#!/usr/bin/env python3
"""Compatibility shim for the installed kb command."""
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from kb.cli.main import cli_entry


if __name__ == "__main__":
    cli_entry()
