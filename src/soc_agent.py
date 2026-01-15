import asyncio
from typing import Dict, List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel

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
from src.utils.pull_prompt import pull_prompt_async

generate_soc_issue_table = make_generate_soc_issue_table()

async def _get_soc_user_prompt() -> str:
    """
    Fetch the SOC agent user prompt from local registry.
    """
    prompt_template = await pull_prompt_async("soc_agent_user_prompt")
    # prompt_template is a ChatPromptTemplate; render with no vars to get text
    rendered = prompt_template.invoke({})
    # rendered is a ChatPromptValue; grab the first message content
    return rendered.messages[0].content

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


class SocAgentMessage(BaseModel):
    role: str
    content: str


class SocAgentMessageList(BaseModel):
    messages: List[SocAgentMessage]


def _build_soc_agent_messages(user_prompt: str) -> List[Dict[str, str]]:
    payload = SocAgentMessageList(
        messages=[SocAgentMessage(role="user", content=user_prompt)]
    )
    return payload.model_dump(mode="json")["messages"]


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
