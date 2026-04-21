# Asagi (Yang) — skin lab notes

Drop PNGs next to this file using the names in `manifest.json`. Chroma Strata loads this folder from `skin-db/` so you do not re-upload assets each session.

**Pipeline (draw order):** background → colors 1–4 (tint masks) → selected pattern tinted with color 5 → color 6 (eyes) → lineart → details.

**Patterns:** `AsagiYang_Color5-Pattern1.png` … (add as many as you want in `manifest.json` → `patterns`); **Randomize (colors only)** keeps the current pattern and shuffles palette indices (including pattern tint and eyes).
