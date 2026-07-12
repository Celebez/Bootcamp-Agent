"""Fixture pytest bersama."""
import sys
from pathlib import Path

# Pastikan root repo ada di sys.path (pytest default tidak selalu demikian)
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
