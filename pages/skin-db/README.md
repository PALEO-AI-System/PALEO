# Chroma Strata skin database (`skin-db/`)

Static files live under **`pages/skin-db/`** next to [`chroma-strata.html`](../chroma-strata.html). Commit PNGs here and open the lab via GitHub Pages or `python scripts/serve_companion.py` (serves the `pages/` folder).

## Layout: species → skin

Each **species** folder holds shared line art / base color masks, and one subfolder per **skin** variant.

| Species | Shared files (same folder as the skin subfolders) | Example skin folder |
|--------|-----------------------------------------------------|---------------------|
| `Yang/` | `Yang_Color1.png`, `Yang_Color6.png`, `Yang_Lineart.png` | `Yang/AsagiYang/` |
| `Sin/` | `Sin_Color1.png`, `Sin_Lineart.png` | `Sin/PastelSin/` |
| `Tuojian/` | `SunsetTuojian_Color1.png`, `SunsetTuojian_Lineart.png` | `Tuojian/SunsetTuojian/` |
| `Wiehen/` | `Wiehen_Color1.png`, `Wiehen_Color6.png`, `Wiehen_Lineart.png` | `Wiehen/SolsticeWiehen/`, `Wiehen/SeismicWiehen/`, … |

In **`manifest.json`**, paths to those shared PNGs use **`../`** from the skin folder (e.g. `"mask": "../Wiehen_Color1.png"`). A skin may also reference another skin’s file when you intentionally share an asset (for example, **Seismic** can point `"details"` at `../SolsticeWiehen/SolsticeWiehen_Details.png` while still using species-level **`Wiehen_Color1.png` / `Wiehen_Color6.png`** for tints). Avoid duplicating large PNGs when a single shared file is enough.

## `manifest.json` conventions

- **`canvasSize`**: `[w, h]` forces export/preview size (otherwise inferred from the color 1 mask or largest loaded image).
- **`constantsBlend`**: per constant, a canvas `globalCompositeOperation` string (e.g. `{ "lineart": "multiply", "infoLayer": "soft-light" }`).
- **Color slots 1–6** (slot **5** tints the selected **pattern** PNGs listed in `"patterns"`). Omit a slot if the skin does not use it.
- **`constants`**: `background`, `lineart`, `details`, `palette`, `infoLayer`; optional **`infoNotes`** `.md` filename for sidebar copy when wired in the page.
- **`defaults`** (optional but recommended): `gender` (`"male"` or `"female"`), `patternIndex`, and per-gender slot indices, e.g. `"male": { "1": 0, "2": 1, … }`, `"female": { … }`. Indices are into the **effective** palette for that gender (manifest palette plus any user-added custom colors for that gender).
- **Gendered palettes**: `palette` = male options. **`femalePalette`** = female options when present (independent from male). The lab shows one set at a time based on the gender control.

**Bottom → top draw order** (same as Chroma Strata compose): color masks **1–4** → pattern (5) → color **6** (if present) → **details** → **lineart** → **background** → **palette** → **infoLayer**.

### Palette ordering (authoring)

When you list multiple swatches in `palette` / `femalePalette`, a useful convention is **ROYGBIV-like hue order**, then **darker → lighter**, then **less saturated → more saturated** within similar hues. This keeps the in-browser pill lists predictable after edits.

## Register a skin

1. Folder: `skin-db/<Species>/<SkinId>/` (e.g. `Yang/AsagiYang/`).
2. `manifest.json` inside that folder; shared assets beside the species folder’s skin subfolders.
3. Entry in `skin-db/index.json` with **`path`** = `"Species/SkinId"`.
4. Optional: add a short `*SkinId*_Info.md` in the skin folder for notes; reference it from `infoNotes` if you use an info layer PNG.

## Custom colors and DevKit export (browser)

- Extra swatches from the color picker are stored in **localStorage** under **`chromaStrata_customHex.v1`**, keyed by **skin path → gender (`male` / `female`) → slot (`"1"`–`"6"`)**. Male and female custom lists are **separate**: adding a custom color in one gender does not add it to the other.
- The **Unreal-style DevKit import** block in Chroma Strata is regenerated from the **current skin’s** male/female manifest palettes **plus** those gender-scoped custom colors (deduplicated, merged in order: manifest first, then customs). It updates when you add or remove a custom color or change skin/gender.
