# Chroma Strata skin database (`skin-db/`)

Static files live under **`pages/skin-db/`** next to `chroma-strata.html`. Commit PNGs here and open the lab via GitHub Pages or `python scripts/serve_companion.py` (serves the `pages/` folder).

## Asagi (Yang) — exact filenames

Put files in **`pages/skin-db/Yang/AsagiYang/`**:

| File | Role |
|------|------|
| `AsagiYang_Background.png` | Bottom constant |
| `AsagiYang_Color1.png` … `AsagiYang_Color4.png` | Tint masks for colors 1–4 (see below) |
| `AsagiYang_Color5-Pattern1.png` | Pattern variant 1 (tinted by color 5) |
| `AsagiYang_Color5-Pattern2.png` | Pattern variant 2 |
| `AsagiYang_Color5-Pattern3.png` | Pattern variant 3 |
| `AsagiYang_Color6.png` | Eyes (tint mask for color 6) |
| `AsagiYang_Lineart.png` | Lineart constant |
| `AsagiYang_Details.png` | Details constant |
| `AsagiYang_Info.md` | Optional notes (sidebar) |

Add or remove pattern lines in **`manifest.json`** → `"patterns": [ ... ]` (1, 2, 5+ files all work). Color 5 still tints whichever pattern is selected.

## Tint masks vs `Color4-Option1.png`, etc.

- **Tint (`tintMask`)**: one PNG per slot. **Opaque white (`#FFFFFF`)** where you want paint; **transparent** elsewhere. The preview uses your **exact hex** in those pixels (same RGB as the swatch). Mid-**gray** masks will **not** match the swatch exactly (they act like a filter). For predictable “this hex is what I see,” prefer **white**, not light gray.
- **`imageOptions`**: list separate PNGs in `manifest.json` (`"options": ["AsagiYang_Color4-Option1.png", ...]`). Best when each option is hand-painted or non-uniform.

## Register a skin

1. Folder: `skin-db/<Species>/<SkinFolder>/` (e.g. `Yang/AsagiYang/`).
2. `manifest.json` inside that folder.
3. Entry in `skin-db/index.json`.

## Custom colors (browser)

Extra swatches from the color picker are stored in **localStorage** (`chromaStrata_customHex.v1`), not in this folder.
