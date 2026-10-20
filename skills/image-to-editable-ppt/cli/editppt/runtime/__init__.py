"""Deterministic runtime modules behind the public editppt CLI."""

from __future__ import annotations

import sys
from pathlib import Path

# Runtime modules import their siblings by bare module name (for example
# ``from deck_run_state import ...``) because ``cli.py`` executes
# ``runtime/main.py`` as a script through ``runpy`` after inserting the runtime
# directory into ``sys.path``. When callers import the package normally instead
# (``import editppt.runtime.<module>``) that directory is absent, so every
# sibling import raises ModuleNotFoundError. Register it here so both the CLI
# entry point and package imports resolve the same modules.
_RUNTIME_DIR = str(Path(__file__).resolve().parent)
if _RUNTIME_DIR not in sys.path:
    sys.path.insert(0, _RUNTIME_DIR)
