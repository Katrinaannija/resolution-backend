"""
Backward-compatible wrapper for prompt retrieval.
Now uses local prompts instead of LangSmith Hub.

This module maintains the same API as before but uses the local prompts module.
"""

from __future__ import annotations

# Import from the new local prompts module
from src.utils.prompts import get_prompt, get_prompt_async


def pull_prompt(name: str, include_model: bool = False):
    """
    Get a prompt by name from the local registry.

    Args:
        name: The prompt name
        include_model: If True, bind the prompt to a ChatOpenAI model

    Returns:
        The prompt template, optionally bound to a model
    """
    return get_prompt(name, include_model=include_model)


async def pull_prompt_async(name: str, include_model: bool = False):
    """
    Async version of pull_prompt for compatibility.

    Args:
        name: The prompt name
        include_model: If True, bind the prompt to a ChatOpenAI model

    Returns:
        The prompt template, optionally bound to a model
    """
    return await get_prompt_async(name, include_model=include_model)

