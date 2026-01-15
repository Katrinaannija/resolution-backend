import asyncio
from typing import Dict, List, Optional

from dotenv import load_dotenv

load_dotenv()

from langchain.agents import create_agent
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_openai import ChatOpenAI

from src.tools.document_store import (
    get_all_document_details,
    list_documents,
    retrieve_document,
    write_court_issues_json,
)
from src.tools.soc_issue_table import make_generate_soc_issue_table
from src.utils.local_prompts import pull_prompt_async

generate_soc_issue_table = make_generate_soc_issue_table()

# Prompt name for local prompts
SOC_AGENT_USER_PROMPT_NAME = "soc_agent_user_prompt"

# Fallback if the prompt cannot be loaded
DEFAULT_SOC_AGENT_USER_MESSAGE = (
    "Generate the structured statement of claim issues JSON by analysing the "
    "statement of claim, statement of defence, and the document table. Use "
    "generate_soc_issue_table to build the JSON and persist it with "
    "write_court_issues_json so downstream agents can consume it. Report once "
    "the issues file has been saved. Don't generate invalid characters, line breaks, or other non-JSON characters."
)


async def _get_soc_user_prompt() -> str:
    """
    Fetch the SOC agent user prompt from local prompts.
    Falls back to the hardcoded default if the prompt doesn't exist.
    """
    try:
        prompt_template = await pull_prompt_async(SOC_AGENT_USER_PROMPT_NAME)
        # prompt_template is a ChatPromptTemplate; render with no vars to get text
        rendered = prompt_template.invoke({})
        # rendered is a ChatPromptValue; grab the first message content
        return rendered.messages[0].content
    except Exception:
        # Prompt not found or other error – use fallback
        return DEFAULT_SOC_AGENT_USER_MESSAGE

MODEL_NAME = "gpt-5.1"

_soc_agent: Optional[Runnable] = None
_soc_agent_lock = asyncio.Lock()


async def _ensure_soc_agent_loaded() -> Runnable:
    """
    Lazily construct and cache the SOC agent, fetching prompts asynchronously to
    avoid blocking the event loop during imports.
    """
    global _soc_agent
    if _soc_agent is not None:
        return _soc_agent

    async with _soc_agent_lock:
        if _soc_agent is not None:
            return _soc_agent

        soc_system_prompt = await pull_prompt_async("soc_system_prompt")
        orchestrator_model = ChatOpenAI(model=MODEL_NAME)
        _soc_agent = create_agent(
            model=orchestrator_model,
            tools=[
                list_documents,
                retrieve_document,
                get_all_document_details,
                generate_soc_issue_table,
                write_court_issues_json,
            ],
            system_prompt=soc_system_prompt.messages[0].prompt.template,
        )
        return _soc_agent


def _build_soc_agent_messages(user_prompt: str) -> List[Dict[str, str]]:
    return [{"role": "user", "content": user_prompt}]


async def agent(config: RunnableConfig | None = None) -> Runnable:
    """
    LangGraph entrypoint - returns the compiled SOC agent runnable.
    """
    return await _ensure_soc_agent_loaded()


def run_soc_agent(user_prompt: Optional[str] = None):
    """
    Execute the SOC agent synchronously to regenerate the issues file.
    """
    prompt = user_prompt or DEFAULT_SOC_AGENT_USER_MESSAGE
    return asyncio.run(run_soc_agent_async(prompt))


async def run_soc_agent_async(user_prompt: Optional[str] = None):
    """
    Async wrapper around the SOC agent execution for orchestrator compatibility.
    """
    prompt = user_prompt or await _get_soc_user_prompt()
    soc_agent = await _ensure_soc_agent_loaded()
    return await soc_agent.ainvoke({"messages": _build_soc_agent_messages(prompt)})

# result = agent.invoke({
#     "messages": [
#         {"role": "user", "content": "From the given files generate statement of claim issues json and give path to the file"}
#     ]
# })

# print(result["messages"][-1].content)

# python -m src.soc_agent