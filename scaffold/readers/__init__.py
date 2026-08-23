"""File readers, one per kind, all returning the same shape.

Adding support for a new file type means dropping a module in here that exposes
`EXTENSIONS`, `profile(path)` and `load(path, **kw)`. Nothing else changes.

If you meet a file type with no reader, write one and save it here. The scaffold
is meant to grow.
"""
from __future__ import annotations

import importlib
import pkgutil
from pathlib import Path

_REGISTRY: dict[str, str] = {}


def _discover() -> None:
    if _REGISTRY:
        return
    for mod in pkgutil.iter_modules(__path__):
        if mod.name.startswith("_"):
            continue
        m = importlib.import_module(f"{__name__}.{mod.name}")
        for ext in getattr(m, "EXTENSIONS", ()):
            _REGISTRY[ext.lower()] = m.__name__


def reader_for(path: str | Path):
    """Return the reader module for a file, or None if we don't have one yet."""
    _discover()
    ext = Path(path).suffix.lower()
    name = _REGISTRY.get(ext)
    return importlib.import_module(name) if name else None


def supported() -> dict[str, str]:
    _discover()
    return dict(sorted(_REGISTRY.items()))
