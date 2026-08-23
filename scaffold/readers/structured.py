"""JSON, JSONL, YAML. Flattened to a table when the shape allows it."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

EXTENSIONS = (".json", ".jsonl", ".ndjson", ".yaml", ".yml")


def _read(path: Path):
    if path.suffix.lower() in {".jsonl", ".ndjson"}:
        return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]
    if path.suffix.lower() in {".yaml", ".yml"}:
        import yaml  # optional dep, only needed for yaml
        return yaml.safe_load(path.read_text())
    return json.loads(path.read_text())


def load(path: str | Path, **_) -> pd.DataFrame | dict | list:
    data = _read(Path(path))
    if isinstance(data, list) and data and isinstance(data[0], dict):
        return pd.json_normalize(data)
    if isinstance(data, dict):
        for v in data.values():
            if isinstance(v, list) and v and isinstance(v[0], dict):
                return pd.json_normalize(v)
    return data


def profile(path: str | Path) -> dict:
    path = Path(path)
    data = _read(path)
    out = {"file": path.name, "kind": "structured", "warnings": []}

    if isinstance(data, list):
        out["records"] = len(data)
        keys: set[str] = set()
        for r in data[:200]:
            if isinstance(r, dict):
                keys |= set(r.keys())
        out["keys"] = sorted(keys)
        out["sample"] = data[:3]
        ragged = [k for k in keys if sum(1 for r in data[:200] if isinstance(r, dict) and k in r) < min(len(data), 200)]
        if ragged:
            out["warnings"].append(f"{len(ragged)} keys are missing from some records: {ragged[:5]}")
    elif isinstance(data, dict):
        out["keys"] = sorted(data.keys())
        out["sample"] = {k: data[k] for k in list(data)[:5]}
    return out
