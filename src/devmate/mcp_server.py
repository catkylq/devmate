from __future__ import annotations

import os
import logging

import httpx
from mcp.server.fastmcp import FastMCP

from devmate.config import AppConfig, load_config

logger = logging.getLogger(__name__)


def build_mcp_server(config: AppConfig) -> FastMCP:
    mcp = FastMCP(config.mcp.server_name)

    @mcp.tool()
    async def search_web(query: str, max_results: int = 5) -> list[dict]:
        """Search the web with Tavily.

        Args:
            query: Search query.
            max_results: Maximum number of results.
        """
        tavily_url = "https://api.tavily.com/search"
        payload = {
            "api_key": config.search.tavily_api_key,
            "query": query,
            "max_results": max_results,
        }

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(tavily_url, json=payload)
            resp.raise_for_status()
            data = resp.json()

        results = data.get("results") or []
        simplified: list[dict] = []
        for item in results[:max_results]:
            simplified.append(
                {
                    "title": item.get("title"),
                    "url": item.get("url"),
                    "content": item.get("content"),
                    "score": item.get("score"),
                }
            )
        return simplified

    return mcp


def main() -> None:
    config = load_config()
    mcp = build_mcp_server(config)
    logger.info(
        "Starting MCP Search Server on %s%s (name=%s)",
        config.mcp.host,
        f":{config.mcp.port}",
        config.mcp.server_name,
    )
    # FastMCP v2+ removed host/port/path kwargs from `run()`; configure via env vars.
    os.environ["FASTMCP_HOST"] = config.mcp.host
    os.environ["FASTMCP_PORT"] = str(config.mcp.port)
    os.environ["FASTMCP_STREAMABLE_HTTP_PATH"] = config.mcp.path

    mcp.run(
        transport="streamable-http",
    )


if __name__ == "__main__":
    main()

