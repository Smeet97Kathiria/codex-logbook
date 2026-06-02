"""Codex Logbook"""

import importlib.metadata

try:
    __version__ = importlib.metadata.version("codex-logbook")
except importlib.metadata.PackageNotFoundError:
    # Fallback for development mode
    __version__ = "0.1.0"

__all__ = ["__version__"]
