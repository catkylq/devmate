from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from langchain_core.tracers.context import tracing_v2_enabled
from langsmith import Client as LangSmithClient

from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver

from devmate.config import AppConfig
from devmate.llm import make_chat_model
from devmate.mcp_client import load_mcp_tools
from devmate.rag import maybe_ingest, search_knowledge_base
from devmate.skills import build_skill_sources
from devmate.skill_learning import save_learned_skill
from devmate.skills_paths import project_root

logger = logging.getLogger(__name__)


class FileSpec(BaseModel):
    path: str = Field(..., description="File path relative to project root.")
    content: str = Field(..., description="Full content to write.")


class CreateFilesInput(BaseModel):
    files: list[FileSpec]


def build_rag_tool(config: AppConfig) -> Any:
    @tool("search_knowledge_base")
    def search_knowledge_base_tool(
        query: str,
        top_k: int = 4,
    ) -> list[dict[str, Any]]:
        """Search internal docs and return relevant chunks."""
        return search_knowledge_base(config=config, query=query, top_k=top_k)

    return search_knowledge_base_tool


def _workspace_root(config: AppConfig, *, project_root_path: Path) -> Path:
    return (project_root_path / config.app.workspace_dir).resolve()


def build_search_web_fallback_tool() -> Any:
    @tool("search_web")
    def search_web_fallback(
        query: str,
        max_results: int = 5,
    ) -> list[dict[str, Any]]:
        """Fallback web-search tool when MCP server is unavailable."""
        logger.warning(
            "MCP search_web unavailable, fallback returns no results. query=%s max_results=%s",
            query,
            max_results,
        )
        return []

    return search_web_fallback


async def build_tools(config: AppConfig) -> tuple[list[Any], list[str]]:
    try:
        await asyncio.to_thread(maybe_ingest, config, docs_dir="docs")
    except Exception as e:  # noqa: BLE001 - keep agent available when Qdrant is down
        logger.warning(
            "Skip RAG ingestion because Qdrant is unavailable: %s",
            e,
        )
    mcp_tools = await load_mcp_tools(config)
    if not any(getattr(t, "name", "") == "search_web" for t in mcp_tools):
        mcp_tools = [*mcp_tools, build_search_web_fallback_tool()]
    rag_tool = build_rag_tool(config)
    return [*mcp_tools, rag_tool], []


async def run_agent_once(config: AppConfig, user_input: str) -> dict[str, Any]:
    project_root_path = project_root()
    tools, _file_writes_unused = await build_tools(config)

    langsmith_client: LangSmithClient | None = None
    api_key = config.langsmith.langchain_api_key.strip()
    if api_key and not api_key.lower().startswith("your_"):
        langsmith_client = LangSmithClient(api_key=api_key)

    # tracing_v2_enabled will log tool calls and chain steps to LangSmith.
    workspace_root = _workspace_root(config, project_root_path=project_root_path)

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

    def should_expect_file_writes() -> bool:
        keywords = (
            "构建",
            "创建",
            "生成",
            "项目",
            "网站",
            "build",
            "create",
            "generate",
            "project",
            "website",
            "app",
        )
        lowered = user_input.lower()
        return any(k in lowered for k in keywords)

    def hiking_checklist_already_satisfied() -> bool:
        """For re-runs: workspace may already contain the hiking site from a prior run."""
        base = workspace_root / "hiking_agent"
        required = (
            "index.html",
            "styles.css",
            "app.js",
            "README.md",
            "main.py",
            "pyproject.toml",
        )
        return all((base / name).is_file() for name in required)

    def assert_expected_writes_or_raise() -> None:
        if not should_expect_file_writes() or learned_files:
            return
        lowered = user_input.lower()
        if ("徒步" in user_input or "hiking" in lowered) and hiking_checklist_already_satisfied():
            logger.info(
                "No new files this run; hiking_agent outputs already present (checklist OK)."
            )
            return
        raise RuntimeError("NO_FILE_WRITE_DETECTED: agent did not write any files.")

    system_prompt = (
        "You are DevMate, an AI coding assistant.\n"
        "You MUST follow this workflow:\n"
        "1) Use `search_knowledge_base` to read internal guidelines.\n"
        "2) Use MCP tool `search_web` for best practices.\n"
        "3) Create or overwrite files using filesystem tools (`write_file`, `edit_file`).\n"
        "4) If a skill matches (see Skills section in system context), read its full "
        "`SKILL.md` with `read_file` then apply it.\n"
        "5) After tool calls, summarize and list written paths.\n"
        "\n"
        "Important:\n"
        "- Do not output large code blocks directly; write files via tools.\n"
        "- Never create `requirements.txt`; use `pyproject.toml` for dependencies.\n"
        "- Keep CSS in `styles.css` and JS in `app.js`.\n"
        "- For website project requests, include executable `main.py` and `pyproject.toml`.\n"
        "- If the request is about hiking/徒步 website, write files under `workspace/hiking_agent/`.\n"
        "- Avoid using `execute` unless absolutely necessary.\n"
    )

    skill_sources = build_skill_sources(config, project_root=project_root_path)
    backend = FilesystemBackend(root_dir=project_root_path, virtual_mode=True)
    checkpointer = MemorySaver()
    agent = create_deep_agent(
        model=make_chat_model(config),
        tools=list(tools),
        backend=backend,
        skills=skill_sources,
        system_prompt=system_prompt,
        checkpointer=checkpointer,
        interrupt_on={
            "write_file": False,
            "edit_file": False,
            "read_file": False,
            "execute": False,
        },
        debug=False,
        name="devmate",
    )

    if config.langsmith.langchain_tracing_v2 and langsmith_client is not None:
        with tracing_v2_enabled(
            project_name="devmate",
            client=langsmith_client,
        ) as cb:
            result = await agent.ainvoke(
                {"messages": [{"role": "user", "content": user_input}]},
                config={"configurable": {"thread_id": "devmate"}},
            )
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
            learned_files = created_files
            assert_expected_writes_or_raise()
            try:
                save_learned_skill(
                    config=config,
                    user_input=user_input,
                    created_files=learned_files,
                )
            except Exception:  # noqa: BLE001
                logger.exception("Failed to save learned skill")

            return {
                "result": result,
                "run_url": run_url,
                "share_url": share_url,
            }

    result = await agent.ainvoke(
        {"messages": [{"role": "user", "content": user_input}]},
        config={"configurable": {"thread_id": "devmate"}},
    )

    after_files = list_workspace_files()
    created_files = sorted(after_files - before_files)
    learned_files = created_files
    assert_expected_writes_or_raise()
    try:
        save_learned_skill(
            config=config,
            user_input=user_input,
            created_files=learned_files,
        )
    except Exception:  # noqa: BLE001
        logger.exception("Failed to save learned skill")

    return {"result": result, "run_url": "", "share_url": ""}
