from __future__ import annotations

import json
import re
from typing import Any, Dict

from langchain_core.messages import BaseMessage


_CONTROL_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def _strip_control_chars(text: str) -> str:
    return _CONTROL_CHARS_RE.sub("", text)


def coerce_prompt_output(output: Any) -> Dict[str, Any]:
    """
    Normalize prompt outputs into a dict, handling LangChain message objects.
    """
    if isinstance(output, BaseMessage):
        output = output.content
    if isinstance(output, dict):
        return output
    if isinstance(output, str):
        text = output.strip()
        if not text:
            return {}
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError:
            cleaned = _strip_control_chars(text)
            if cleaned != text:
                try:
                    parsed = json.loads(cleaned)
                except json.JSONDecodeError:
                    return {"text": cleaned}
                return parsed if isinstance(parsed, dict) else {"value": parsed}
            return {"text": text}
        return parsed if isinstance(parsed, dict) else {"value": parsed}
    if isinstance(output, list):
        return {"items": output}
    return {"value": output}
