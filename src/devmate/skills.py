from __future__ import annotations

import logging
from pathlib import Path

from langchain_skills import SkillTool

from devmate.config import AppConfig

logger = logging.getLogger(__name__)


def build_skill_tool(config: AppConfig) -> SkillTool:
    skills_dir = Path(config.skills.skills_dir)
    if not skills_dir.exists():
        logger.warning("Skills dir does not exist: %s", skills_dir)
    # SkillTool will discover all SKILL.md under `directories`.
    return SkillTool(directories=str(skills_dir))

