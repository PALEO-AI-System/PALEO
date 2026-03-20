# Profiles: per-creature visual variants

When adding a **new** creature page under `pages/profiles/`, keep the same JSON fields and `profile-app.js` behavior, but pick a **distinct layout/skin** so you can compare aesthetics over time.

**Convention (recommended):**

- Add a body class on the creature HTML shell, e.g. `theme-profile-<slug-short>`.
- Scope layout overrides in `pages/profiles/css/profiles.css` under that class (hero geometry, card shapes, accent use).
- Do **not** change **KTO Deinosuchus** styling unless explicitly requested; treat `theme-profile-deino` as the reference implementation.

This file is planning-only; the Deinosuchus page ships as the first reference profile.
