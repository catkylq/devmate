from __future__ import annotations

import logging
from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from devmate.config import AppConfig

logger = logging.getLogger(__name__)


async def load_mcp_tools(config: AppConfig) -> list[Any]:
    """加载 MCP 工具，若失败则返回空列表（允许 Agent 降级运行）。"""
    try:
        client = MultiServerMCPClient(
            {
                config.mcp.server_name: {
                    "transport": "streamable_http",
                    "url": config.mcp.url,
                }
            }
        )
        tools = await client.get_tools()
        logger.info("Loaded %d MCP tools from %s", len(tools), config.mcp.url)
        return list(tools)
    except Exception as e:
        logger.error("Failed to load MCP tools from %s: %s", config.mcp.url, e, exc_info=True)
        return []   # 降级：返回空工具列表，不影响其他功能