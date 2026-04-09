import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if os.environ.get("KB_TEST_INSTALLED_PACKAGE") != "1" and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
