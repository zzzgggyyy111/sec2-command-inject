"""Pytest bootstrap: put the repository root on sys.path."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ROOT_TEXT = str(ROOT)

if ROOT_TEXT not in sys.path:
    sys.path.insert(0, ROOT_TEXT)