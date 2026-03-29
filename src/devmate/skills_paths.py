from __future__ import annotations

from pathlib import Path

from devmate.config import AppConfig


def project_root() -> Path:
    """Package layout: src/devmate -> project root."""
    return Path(__file__).resolve().parents[2]


def resolve_skills_root(config: AppConfig) -> Path:
    return (project_root() / config.skills.skills_dir).resolve()
