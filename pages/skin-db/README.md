# Chroma Strata skin database (`skin-db/`)

Static files live under **`pages/skin-db/`** next to `chroma-strata.html`. Commit PNGs here and open the lab via GitHub Pages or `python scripts/serve_companion.py` (serves the `pages/` folder).

## AsagiYang — folder and filenames

Put files in **`pages/skin-db/AsagiYang/`** (one folder per skin id).

Optional in **`manifest.json`**:

- **`canvasSize`**: `[3400, 1156]` forces export/preview pixel size (otherwise inferred from Color1 or max image).
- **`tintComposite`**: `"multiply"` tints **colors 1–4, pattern, and color 6** onto the gray base with **multiply** (PoT-style mask stack). Omit or use anything other than `"multiply"` for all–`source-over` tints.
- **`constantsBlend`**: per constant, a [canvas `globalCompositeOperation`](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/globalCompositeOperation) string, e.g. `{ "lineart": "multiply", "infoLayer": "soft-light" }`. PNGs do **not** carry Photoshop blend modes; this reapplies a chosen mode in the browser. Transparent pixels stay transparent; the mode affects how non-transparent pixels combine with what is underneath.
- **`palette`**: `constants.palette` → e.g. `AsagiYang_Palette.png` (reference swatches on canvas). Optional blend via **`constantsBlend.palette`**.
- **`infoLayer`**: top branding / labels PNG. Optional blend (e.g. **`constantsBlend.infoLayer`**: `"soft-light"`). **`infoNotes`**: optional `.md` for the sidebar only.

The Chroma Strata preview **always fits** the wide canvas inside a capped-height panel (no separate zoom modes). The **preview strip is full browser width** above the control panel.

**Bottom → top draw order** (AsagiYang):

| Order | File |
|------|------|
| 1 (bottom) | `AsagiYang_Color1.png` |
| 2 | `AsagiYang_Color2.png` |
| 3 | `AsagiYang_Color3.png` |
| 4 | `AsagiYang_Color4.png` |
| 5 | `AsagiYang_Color5-Pattern1.png` (add more filenames in `"patterns"` if the skin has variants; tinted by color 5) |
| 6 | `AsagiYang_Color6.png` |
| 7 | `AsagiYang_Details.png` |
| 8 | `AsagiYang_Lineart.png` (default blend: **`multiply`** in manifest `constantsBlend`) |
| 9 | `AsagiYang_Background.png` |
| 10 | `AsagiYang_Palette.png` — `constants.palette` |
| 11 (top) | `AsagiYang_Info.png` — `constants.infoLayer` (default **`soft-light`**) |

Optional sidebar: **`AsagiYang_Info.md`** via `constants.infoNotes` (not composited).

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
