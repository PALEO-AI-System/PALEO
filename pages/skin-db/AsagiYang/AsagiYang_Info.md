# Asagi — skin lab notes

Drop PNGs next to this file using the names in `manifest.json`. Chroma Strata loads **`skin-db/AsagiYang/`** so assets persist without re-uploading each session.

**Draw order (bottom → top):** Color1 → Color2 → Color3 → Color4 → selected **Color5-Pattern** (tinted by color 5) → Color6 → **Details** → **Lineart** → **Background**. After color 6 there are **no further recolors** — Details, Lineart, and Background are drawn as-is.

**Patterns:** list any number of `AsagiYang_Color5-PatternN.png` files in `manifest.json` → `patterns`. **Randomize (colors only)** keeps the current pattern and shuffles swatches (including pattern tint and eyes).
