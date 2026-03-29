from __future__ import annotations

import argparse
import logging
import asyncio

from devmate.agent import run_agent_once
from devmate.config import AppConfig, load_config
from devmate.logging_setup import configure_logging

logger = logging.getLogger(__name__)


async def _async_main(prompt: str) -> None:
    config: AppConfig = load_config()
    result = await run_agent_once(config, prompt)
    share_url = result.get("share_url") or ""
    if share_url:
        logger.info("LangSmith share link: %s", share_url)
    run_url = result.get("run_url") or ""
    if run_url:
        logger.info("LangSmith run URL: %s", run_url)

    logger.info("Agent finished.")

    # Important: keep logs concise (but enough for evaluation).
    agent_result = result.get("result")
    if isinstance(agent_result, dict):
        if "output" in agent_result:
            logger.info("Agent output: %s", agent_result.get("output"))
        else:
            logger.info("Agent result keys: %s", list(agent_result.keys()))
    else:
        logger.info("Agent response type: %s", type(agent_result).__name__)


def main() -> None:
    configure_logging()

    parser = argparse.ArgumentParser(prog="devmate")
    parser.add_argument(
        "--prompt",
        type=str,
        default="我想构建一个展示附近徒步路线的网站项目。",
        help="User request for the coding assistant.",
    )
    args = parser.parse_args()

    asyncio.run(_async_main(args.prompt))


if __name__ == "__main__":
    main()
