from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict

_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _strip_control_chars(text: str) -> str:
    return _CONTROL_CHARS_RE.sub("", text)


def load_json_file(path: str | Path) -> Dict[str, Any]:
    """
    Load JSON from disk while stripping invalid control characters if needed.
    """
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = _strip_control_chars(text)
        return json.loads(cleaned)
