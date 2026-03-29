from __future__ import annotations

import logging
from pathlib import Path

from devmate.config import AppConfig

logger = logging.getLogger(__name__)


def build_skill_sources(config: AppConfig, *, project_root: Path) -> list[str]:
    """
    Build deepagents skill source paths (POSIX, relative to FilesystemBackend root).

    Order: extra_skill_dirs first, then skills_dir (later wins for same skill name).
    See: https://docs.langchain.com/oss/python/deepagents/skills
    """
    root = project_root.resolve()
    sources: list[str] = []

    for rel in config.skills.extra_skill_dirs:
        skills_path = (root / rel).resolve()
        if not skills_path.exists():
            logger.warning("Extra skills dir does not exist: %s", skills_path)
            continue
        rel_posix = skills_path.relative_to(root).as_posix().strip("/")
        sources.append(f"/{rel_posix}/")

    main = (root / config.skills.skills_dir).resolve()
    if main.exists():
        rel_posix = main.relative_to(root).as_posix().strip("/")
        sources.append(f"/{rel_posix}/")
    else:
        logger.warning("Skills dir does not exist: %s", main)

    if not sources:
        logger.warning("No skill sources found; agent will run without skills.")
    return sources
