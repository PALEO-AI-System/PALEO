# Chroma Strata skin database (`skin-db/`)

Static files live under **`pages/skin-db/`** next to `chroma-strata.html`. Commit PNGs here and open the lab via GitHub Pages or `python scripts/serve_companion.py` (serves the `pages/` folder).

## Layout: species → skin

Each **species** folder holds shared line art / base color masks, and one subfolder per **skin** variant.

| Species | Shared files (same folder as the skin subfolders) | Example skin folder |
|--------|-----------------------------------------------------|---------------------|
| `Yang/` | `Yang_Color1.png`, `Yang_Color6.png`, `Yang_Lineart.png` | `Yang/AsagiYang/` |
| `Sin/` | `Sin_Color1.png`, `Sin_Lineart.png` | `Sin/PastelSin/` |
| `Tuojian/` | `SunsetTuojian_Color1.png`, `SunsetTuojian_Lineart.png` | `Tuojian/SunsetTuojian/` |
| `Wiehen/` | `Wiehen_Color1.png`, `Wiehen_Color6.png`, `Wiehen_Lineart.png` | `Wiehen/SolsticeWiehen/`, `Wiehen/SeismicWiehen/`, … |

In **`manifest.json`**, paths to those shared PNGs use **`../`** from the skin folder (e.g. `"mask": "../Wiehen_Color1.png"`). **Seismic** reuses Solstice’s details layer via `"details": "../SolsticeWiehen/SolsticeWiehen_Details.png"` (no duplicate file).

## `manifest.json` conventions

- **`canvasSize`**: `[w, h]` forces export/preview size (otherwise inferred from the color 1 mask or largest loaded image).
- **`constantsBlend`**: per constant, a canvas `globalCompositeOperation` string (e.g. `{ "lineart": "multiply", "infoLayer": "soft-light" }`).
- **Color slots 1–6** (slot **5** tints the selected **pattern** PNGs listed in `"patterns"`). Omit a slot if the skin does not use it.
- **`constants`**: `background`, `lineart`, `details`, `palette`, `infoLayer`; optional **`infoNotes`** `.md` filename for sidebar copy when wired in the page.

**Bottom → top draw order** (same as Chroma Strata compose): color masks **1–4** → pattern (5) → color **6** (if present) → **details** → **lineart** → **background** → **palette** → **infoLayer**.

## Register a skin

1. Folder: `skin-db/<Species>/<SkinId>/` (e.g. `Yang/AsagiYang/`).
2. `manifest.json` inside that folder; shared assets beside the species folder’s skin subfolders.
3. Entry in `skin-db/index.json` with **`path`** = `"Species/SkinId"`.

## Custom colors (browser)

Extra swatches from the color picker are stored in **localStorage** (`chromaStrata_customHex.v1`), keyed by skin path (e.g. `Yang/AsagiYang`).
