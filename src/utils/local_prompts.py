"""
Local prompt management system - replaces LangSmith Hub integration.
All prompts are defined locally in src/prompts/ directory.
"""

import asyncio
import os
from typing import Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_openai import ChatOpenAI


# Get model from environment or use default
DEFAULT_MODEL = "gpt-5.1"


def _get_model():
    """Get the model to use, respecting GLOBAL_MODEL override."""
    model_name = os.getenv("GLOBAL_MODEL", DEFAULT_MODEL)
    return ChatOpenAI(model=model_name, temperature=0)


def pull_prompt(name: str, include_model: bool = False):
    """
    Load a prompt from the local prompts directory.

    Args:
        name: Name of the prompt to load
        include_model: If True, return prompt | model chain

    Returns:
        ChatPromptTemplate or Runnable chain (prompt | model)
    """
    # Import the prompt module
    try:
        from src.prompts import PROMPTS
        prompt_config = PROMPTS.get(name)

        if prompt_config is None:
            raise ValueError(f"Prompt '{name}' not found in local prompts")

        prompt = prompt_config["prompt"]

        if include_model:
            model = _get_model()
            if prompt_config.get("output_parser"):
                return prompt | model | prompt_config["output_parser"]
            return prompt | model

        return prompt

    except ImportError as e:
        raise RuntimeError(f"Failed to load prompts: {e}")


async def pull_prompt_async(name: str, include_model: bool = False):
    """
    Async version of pull_prompt (runs in thread pool to avoid blocking).

    Args:
        name: Name of the prompt to load
        include_model: If True, return prompt | model chain

    Returns:
        ChatPromptTemplate or Runnable chain (prompt | model)
    """
    # Since we're loading from local files (fast), we can just call the sync version
    # but wrap it in to_thread for consistency with the original async API
    return await asyncio.to_thread(pull_prompt, name, include_model)
