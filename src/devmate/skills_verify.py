from __future__ import annotations

import argparse
import logging
import re
from pathlib import Path

from devmate.config import load_config
from devmate.skills import build_skill_sources
from devmate.skills_paths import project_root, resolve_skills_root

logger = logging.getLogger(__name__)

_FRONT_MATTER_RE = re.compile(
    r"^---\s*\n(?P<fm>.*?)\n---\s*\n",
    re.DOTALL | re.MULTILINE,
)
_NAME_RE = re.compile(r"^name:\s*(.+)\s*$", re.MULTILINE)
_DESC_RE = re.compile(r"^description:\s*(.+)\s*$", re.MULTILINE | re.DOTALL)


def _parse_skill_md(path: Path) -> tuple[str | None, str | None]:
    text = path.read_text(encoding="utf-8")
    m = _FRONT_MATTER_RE.match(text)
    if not m:
        return None, None
    fm = m.group("fm")
    name_m = _NAME_RE.search(fm)
    desc_m = _DESC_RE.search(fm)
    name = name_m.group(1).strip().strip("\"'") if name_m else None
    desc = desc_m.group(1).strip().strip("\"'") if desc_m else None
    return name, desc


def _iter_skill_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("SKILL.md"))


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(
        description="Verify Agent Skills layout (SKILL.md + YAML frontmatter).",
    )
    parser.add_argument(
        "--config",
        default="config.toml",
        help="Path to config.toml",
    )
    args = parser.parse_args()

    config = load_config(args.config)
    root = project_root()
    sources = build_skill_sources(config, project_root=root)

    logger.info("DeepAgents skill sources (backend-relative): %s", sources)

    ok = True
    for rel in config.skills.extra_skill_dirs:
        base = (root / rel).resolve()
        for skill_md in _iter_skill_files(base):
            name, desc = _parse_skill_md(skill_md)
            if not name or not desc:
                logger.error("Invalid SKILL.md (missing name/description): %s", skill_md)
                ok = False
                continue
            logger.info("OK %s | name=%s", skill_md.relative_to(root), name)

    learned_root = resolve_skills_root(config)
    if learned_root.exists():
        for skill_md in _iter_skill_files(learned_root):
            name, desc = _parse_skill_md(skill_md)
            if not name or not desc:
                logger.error("Invalid SKILL.md: %s", skill_md)
                ok = False
            else:
                logger.info("OK %s | name=%s (learned)", skill_md.relative_to(root), name)

    if not ok:
        raise SystemExit(1)
    logger.info("Skills verification passed.")


if __name__ == "__main__":
    main()
