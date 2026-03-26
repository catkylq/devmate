---
title: Internal Project Guidelines
---

# Internal Project Guidelines (for DevMate)

These guidelines are used by the assistant during code generation tests.

## Code generation constraints
- Use deterministic file names as requested by the user.
- Output multiple files if the request is a multi-file project.

## Template hints for "hiking trails website"
- `index.html`: single page that loads styles and scripts.
- `styles.css`: styling for layout, cards, typography.
- `app.js`: fetches/loads static data (mock) and renders trail cards.
- `pyproject.toml` and `main.py` are optional unless explicitly requested.

## UI content expectations
- Include at least 3 sample trails.
- Each trail must include: `name`, `distance_km`, `difficulty`, `description`.

