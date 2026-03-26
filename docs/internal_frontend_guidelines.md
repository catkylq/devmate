---
title: Internal Frontend Guidelines
---

# Internal Frontend Guidelines (for DevMate)

These are internal guidelines used to validate RAG retrieval.

## Styling
- Use plain CSS with clear class names.
- Prefer accessible defaults (high contrast, focus outlines).

## File layout
- `index.html` should reference `styles.css` and `app.js` via relative paths.
- Keep all CSS in `styles.css` and all JS in `app.js`.

## JavaScript expectations
- Do not use blocking alerts for normal flows; use non-blocking UI text instead.
- Keep functions small and avoid global mutable state.

## App behavior
- Render a list of hiking trails with: name, distance_km, difficulty, description.
- Provide a simple search input that filters client-side.

