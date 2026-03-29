from __future__ import annotations

import logging
import sys


def configure_logging(level: int = logging.INFO) -> None:
    # Improve Windows terminal readability for Chinese logs.
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream is not None and hasattr(stream, "reconfigure"):
            try:
                stream.reconfigure(encoding="utf-8", errors="replace")
            except Exception:  # noqa: BLE001 - keep logging setup robust
                pass

    # Force basic config to ensure logs appear in container/CLI.
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        force=True,
    )
