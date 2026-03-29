from __future__ import annotations

import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from devmate.config import AppConfig

logger = logging.getLogger(__name__)


def _candidate_mcp_urls(primary_url: str) -> list[str]:
    urls: list[str] = []

    def _add(url: str) -> None:
        if url and url not in urls:
            urls.append(url)

    _add(primary_url)

    # Common local fallback addresses.
    _add("http://127.0.0.1:8000/mcp")
    _add("http://localhost:8000/mcp")

    # Common docker-compose service address fallback.
    _add("http://devmate-mcp-search:8000/mcp")
    _add("http://devmate-mcp-search:3000/mcp")
    return urls


async def load_mcp_tools(config: AppConfig) -> list[Any]:
    """加载 MCP 工具，若失败则返回空列表（允许 Agent 降级运行）。"""
    for url in _candidate_mcp_urls(config.mcp.url):
        try:
            client = MultiServerMCPClient(
                {
                    config.mcp.server_name: {
                        "transport": "streamable_http",
                        "url": url,
                    }
                }
            )
            tools = await client.get_tools()
            logger.info("Loaded %d MCP tools from %s", len(tools), url)
            return list(tools)
        except Exception as e:
            logger.warning("Failed MCP tools load from %s: %s", url, e)
            continue

    logger.error(
        "Failed to load MCP tools from all candidates. configured=%s",
        config.mcp.url,
        exc_info=True,
    )
    return []  # 降级：返回空工具列表，不影响其他功能
