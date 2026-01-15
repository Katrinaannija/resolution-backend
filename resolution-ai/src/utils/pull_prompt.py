from __future__ import annotations

import asyncio
import os
from typing import Optional

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langsmith import Client

load_dotenv()

GLOBAL_MODEL_ENV_KEY = "GLOBAL_MODEL"
_DEFAULT_MODEL_NAME = "NONE"

_cached_model_name: Optional[str] = None
_cached_model: Optional[ChatOpenAI] = None
_cached_client: Optional[Client] = None


def _get_target_model_name() -> Optional[str]:
    target_model = os.getenv(GLOBAL_MODEL_ENV_KEY, _DEFAULT_MODEL_NAME)
    if not target_model or target_model.upper() == _DEFAULT_MODEL_NAME:
        return None
    return target_model


def _get_or_create_global_model() -> Optional[ChatOpenAI]:
    global _cached_model_name, _cached_model

    target_model = _get_target_model_name()
    if target_model is None:
        _cached_model = None
        _cached_model_name = None
        return None

    if _cached_model is None or target_model != _cached_model_name:
        _cached_model = ChatOpenAI(model=target_model, temperature=0)
        _cached_model_name = target_model

    return _cached_model


def patched_pull_prompt(client: Client, name: str, include_model: bool = False):
    override_model = _get_or_create_global_model()
    should_bind_override = include_model and override_model is not None

    prompt = Client.pull_prompt(
        client,
        name,
        include_model=include_model and not should_bind_override,
    )

    if should_bind_override:
        return prompt | override_model

    return prompt


def pull_prompt(name: str, include_model: bool = False):
    global _cached_client

    if _cached_client is None:
        _cached_client = Client()

    return patched_pull_prompt(_cached_client, name, include_model=include_model)


async def pull_prompt_async(name: str, include_model: bool = False):
    """Async-friendly wrapper that fetches prompts without blocking the event loop."""
    return await asyncio.to_thread(
        pull_prompt,
        name,
        include_model,
    )

