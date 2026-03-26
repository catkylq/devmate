from __future__ import annotations

import logging
import re
from pathlib import Path

from devmate.config import AppConfig

logger = logging.getLogger(__name__)


def _slugify(text: str, max_len: int = 48) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text or "learned-skill"


def save_learned_skill(
    config: AppConfig,
    user_input: str,
    created_files: list[str],
) -> str | None:
    if not created_files:
        return None

    skills_root = Path(config.skills.skills_dir).resolve()
    skill_name = _slugify(user_input)
    target_dir = skills_root / skill_name
    target_dir.mkdir(parents=True, exist_ok=True)

    description = (
        "Learned DevMate pattern based on user request. "
        "The agent generated: " + ", ".join(created_files[:10])
    )

    front_matter = (
        "---\n"
        f"name: {skill_name}\n"
        f"description: {description}\n"
        "---\n"
    )

    files_list = "\n".join([f"- {p}" for p in created_files])
    content = (
        front_matter
        + "\n"
        + "# When to use\n"
        + "Use this skill for similar requests that require generating a "
        + "multi-file project.\n\n"
        + "# What to do\n"
        + "- Use `search_knowledge_base` to retrieve internal guidelines.\n"
        + "- Use MCP `search_web` if external best practices are needed.\n"
        + "- Call `create_files` to generate/update all required files.\n\n"
        + "# Generated files in the learned example\n"
        + files_list
        + "\n"
    )

    skill_path = target_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")
    logger.info("Saved learned skill: %s", skill_path)
    return skill_name

