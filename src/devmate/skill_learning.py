from __future__ import annotations

import logging
import re

from devmate.config import AppConfig
from devmate.skills_paths import resolve_skills_root

logger = logging.getLogger(__name__)


def _slugify(text: str, max_len: int = 48) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    text = re.sub(r"-{2,}", "-", text).strip("-")
    if len(text) > max_len:
        text = text[:max_len].rstrip("-")
    return text or "learned-skill"


def _yaml_quote(text: str) -> str:
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def save_learned_skill(
    config: AppConfig,
    user_input: str,
    created_files: list[str],
) -> str | None:
    if not created_files:
        return None

    skills_root = resolve_skills_root(config)
    skill_name = _slugify(user_input)
    target_dir = skills_root / skill_name
    target_dir.mkdir(parents=True, exist_ok=True)

    description = (
        "Learned DevMate workflow from a completed run. "
        "Generated files: " + ", ".join(created_files[:10])
    )

    front_matter = (
        "---\n"
        f"name: {_yaml_quote(skill_name)}\n"
        f"description: {_yaml_quote(description)}\n"
        "---\n"
    )

    files_list = "\n".join([f"- {p}" for p in created_files])
    content = (
        front_matter
        + "\n"
        + "# When to use\n"
        + "Use this skill when the user asks for something similar to the original "
        + "request (multi-file codegen, same stack or folder layout).\n\n"
        + "# What to do\n"
        + "- Use `search_knowledge_base` for internal guidelines.\n"
        + "- Use MCP `search_web` when external facts are needed.\n"
        + "- Use filesystem tools (`write_file`, `edit_file`) under the workspace; "
        + "do not paste large code in chat.\n\n"
        + "# Reference files from this run\n"
        + files_list
        + "\n"
    )

    skill_path = target_dir / "SKILL.md"
    skill_path.write_text(content, encoding="utf-8")
    logger.info("Saved learned skill: %s", skill_path)
    return skill_name
