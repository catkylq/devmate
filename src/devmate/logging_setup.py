from __future__ import annotations

import logging


def configure_logging(level: int = logging.INFO) -> None:
    # Force basic config to ensure logs appear in container/CLI.
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

