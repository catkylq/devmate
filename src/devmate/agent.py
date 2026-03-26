from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Iterable

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.tools import tool
from pydantic import BaseModel, Field

from langgraph.graph import MessagesState, StateGraph, START
from langgraph.prebuilt import ToolNode, tools_condition
from langchain_core.tracers.context import tracing_v2_enabled
from langsmith import Client as LangSmithClient

from devmate.config import AppConfig
from devmate.llm import make_chat_model
from devmate.mcp_client import load_mcp_tools
from devmate.rag import maybe_ingest, search_knowledge_base
from devmate.skills import build_skill_tool
from devmate.skill_learning import save_learned_skill

logger = logging.getLogger(__name__)


class FileSpec(BaseModel):
    path: str = Field(..., description="File path relative to project root.")
    content: str = Field(..., description="Full content to write.")


class CreateFilesInput(BaseModel):
    files: list[FileSpec]


def project_root() -> Path:
    # Deprecated: file generation root is controlled by
    # config.app.workspace_dir.
    return Path(__file__).resolve().parents[2]


def build_create_files_tool(config: AppConfig) -> Any:
    root = Path(config.app.workspace_dir).resolve()

    @tool("create_files", args_schema=CreateFilesInput)
    def create_files(files: list[FileSpec]) -> list[str]:
        """Create or overwrite multiple files in the project workspace."""
        written: list[str] = []
        for f in files:
            rel = f.path.replace("\\", "/").lstrip("/")
            dest = (root / rel).resolve()
            if root not in dest.parents and dest != root:
                raise ValueError(
                    "Refusing to write outside project root: " + f.path
                )
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f.content, encoding="utf-8")
            written.append(rel)
        return written

    return create_files


def build_rag_tool(config: AppConfig) -> Any:
    @tool("search_knowledge_base")
    def search_knowledge_base_tool(
        query: str,
        top_k: int = 4,
    ) -> list[dict[str, Any]]:
        """Search internal docs and return relevant chunks."""
        return search_knowledge_base(config=config, query=query, top_k=top_k)

    return search_knowledge_base_tool


async def build_tools(config: AppConfig) -> list[Any]:
    await asyncio.to_thread(maybe_ingest, config, docs_dir="docs")
    mcp_tools = await load_mcp_tools(config)
    rag_tool = build_rag_tool(config)
    create_files_tool = build_create_files_tool(config)
    skill_tool = build_skill_tool(config)
    return [*mcp_tools, rag_tool, create_files_tool, skill_tool]


def build_agent_graph(config: AppConfig, tools: Iterable[Any]) -> Any:
    llm = make_chat_model(config)
    tool_list = list(tools)

    async def acall_model(state: MessagesState) -> dict[str, Any]:
        response = await llm.bind_tools(tool_list).ainvoke(state["messages"])
        return {"messages": response}

    builder = StateGraph(MessagesState)
    builder.add_node("call_model", acall_model)
    builder.add_node("tools", ToolNode(tool_list))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    return builder.compile()


async def run_agent_once(config: AppConfig, user_input: str) -> dict[str, Any]:
    tools = await build_tools(config)
    graph = build_agent_graph(config, tools)

    langsmith_client: LangSmithClient | None = None
    api_key = config.langsmith.langchain_api_key.strip()
    if api_key and not api_key.lower().startswith("your_"):
        langsmith_client = LangSmithClient(api_key=api_key)

    # tracing_v2_enabled will log tool calls and chain steps to LangSmith.
    workspace_root = Path(config.app.workspace_dir).resolve()

    def list_workspace_files() -> set[str]:
        if not workspace_root.exists():
            return set()
        out: set[str] = set()
        for path in workspace_root.rglob("*"):
            if not path.is_file():
                continue
            rel = path.relative_to(workspace_root).as_posix()
            out.add(rel)
        return out

    before_files = list_workspace_files()

    system_prompt = (
        "You are DevMate, an AI coding assistant.\n"
        "You MUST follow this workflow:\n"
        "1) Use `search_knowledge_base` to read internal guidelines.\n"
        "2) Use MCP tool `search_web` for best practices.\n"
        "3) Create or overwrite files by calling `create_files`.\n"
        "4) If a suitable skill exists, use it from SkillTool.\n"
        "5) After tool calls, summarize and list written paths.\n"
        "\n"
        "Important:\n"
        "- Do not output large code blocks directly; call `create_files`.\n"
        "- Keep CSS in `styles.css` and JS in `app.js`.\n"
    )

    if config.langsmith.langchain_tracing_v2 and langsmith_client is not None:
        with tracing_v2_enabled(
            project_name="devmate",
            client=langsmith_client,
        ) as cb:
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_input),
            ]
            state = await graph.ainvoke({"messages": messages})
            final_content = getattr(state["messages"][-1], "content", "")
            result = {"output": final_content}
            run_url = ""
            share_url = ""
            try:
                run_url = cb.get_run_url()
                if cb.latest_run is not None:
                    share_url = langsmith_client.share_run(cb.latest_run.id)
            except Exception:  # noqa: BLE001
                logger.exception("Failed to generate LangSmith share link")

            after_files = list_workspace_files()
            created_files = sorted(after_files - before_files)
            try:
                save_learned_skill(
                    config=config,
                    user_input=user_input,
                    created_files=created_files,
                )
            except Exception:  # noqa: BLE001
                logger.exception("Failed to save learned skill")

            return {
                "result": result,
                "run_url": run_url,
                "share_url": share_url,
            }

    # If LangSmith is not configured, just run the agent.
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_input),
    ]
    state = await graph.ainvoke({"messages": messages})
    final_content = getattr(state["messages"][-1], "content", "")
    result = {"output": final_content}

    after_files = list_workspace_files()
    created_files = sorted(after_files - before_files)
    try:
        save_learned_skill(
            config=config,
            user_input=user_input,
            created_files=created_files,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to save learned skill")

    return {"result": result, "run_url": "", "share_url": ""}

