from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(data_dir: Path, filename: str) -> list[dict[str, Any]] | dict[str, Any]:
    file_path = data_dir / filename
    if not file_path.exists():
        raise FileNotFoundError(f"Missing data file: {file_path}")
    with file_path.open(encoding="utf-8") as file:
        return json.load(file)
