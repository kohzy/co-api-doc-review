"""Shared test setup: put the skill's scripts on the import path."""
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / ".claude" / "skills" / "doc-quality" / "scripts"
FIXTURES = REPO / "tests" / "fixtures"

if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
