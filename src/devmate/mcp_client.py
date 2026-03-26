from __future__ import annotations

from typing import Any

from langchain_mcp_adapters.client import MultiServerMCPClient

from devmate.config import AppConfig


async def load_mcp_tools(config: AppConfig) -> list[Any]:
    client = MultiServerMCPClient(
        {
            config.mcp.server_name: {
                # Must use Streamable HTTP transport (not SSE/stdio).
                "transport": "streamable_http",
                "url": config.mcp.url,
            }
        }
    )
    tools = await client.get_tools()
    return list(tools)

