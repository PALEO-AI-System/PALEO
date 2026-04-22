# Chroma Strata skin database (`skin-db/`)

Static files live under **`pages/skin-db/`** next to `chroma-strata.html`. Commit PNGs here and open the lab via GitHub Pages or `python scripts/serve_companion.py` (serves the `pages/` folder).

## AsagiYang — folder and filenames

Put files in **`pages/skin-db/AsagiYang/`** (one folder per skin id).

**Bottom → top draw order** (matches PoT-style stacking for this skin):

| Order | File |
|------|------|
| 1 (bottom) | `AsagiYang_Color1.png` |
| 2 | `AsagiYang_Color2.png` |
| 3 | `AsagiYang_Color3.png` |
| 4 | `AsagiYang_Color4.png` |
| 5 | `AsagiYang_Color5-Pattern1.png`, `-Pattern2.png`, … (one active; tinted by color 5) |
| 6 | `AsagiYang_Color6.png` |
| 7 | `AsagiYang_Details.png` (no tint) |
| 8 | `AsagiYang_Lineart.png` (no tint) |
| 9 (top) | `AsagiYang_Background.png` (no tint) |

Optional: **`AsagiYang_Info.md`** (sidebar text, not a canvas layer).

Add or remove pattern entries in **`manifest.json`** → `"patterns": [ ... ]`. Color **5** tints whichever pattern is selected.

## Tint masks vs separate option PNGs

- **`tintMask`**: one PNG per color slot. **Opaque white** where you want paint; transparent elsewhere. Swatch hex maps predictably to those pixels.
- **`imageOptions`**: separate PNGs per swatch in `manifest.json` when you need painted variants.

## Register a skin

1. Folder: `skin-db/<SkinId>/` (e.g. `AsagiYang/`).
2. `manifest.json` inside that folder.
3. Entry in `skin-db/index.json`.

## Custom colors (browser)

Extra swatches from the color picker are stored in **localStorage** (`chromaStrata_customHex.v1`), keyed by skin path (e.g. `AsagiYang`).
