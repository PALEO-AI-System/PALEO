# AI Tool Usage Log

## 2026-03-12
- Scaffolded repository structure only (`src/`, `scripts/`, `tests/`).
- Added a minimal runnable "hello pipeline" with no model implementation.
- Added basic unit tests for pipeline behavior.
- Updated `README.md` with reproducible run commands.

## 2026-03-13
- Revised `docs/project_checkin_response.md` for truthful progress reporting and clearer alignment with project scope.
- Added Letta-oriented agent design notes (one agent per dinosaur, memory block usage).
- Chose a concrete first-pass model/data direction for planning (`ResNet-18`, Snapshot Serengeti + Kaggle predator/prey search track).
- Added `pages/index.html` and `pages/project-checkin-1.html` as GitHub Pages-ready placeholders with HTML/CSS/JS scaffolding.
- Verified moved check-in file under `docs/project_checkin1/` and generated a Canvas-ready plain-text submission draft at `docs/project_checkin1/project_checkin1_response.txt`.
- Expanded "Progress So Far" in both check-in response files to explicitly credit documentation/setup artifacts (`context_dump`, brainstorming, project brief, check-in template, course slide deck review, Cursor rules, AI log).
- Added GitHub Actions workflow at `.github/workflows/deploy-pages.yml` to deploy GitHub Pages from the `pages/` directory.
- Upgraded `pages/index.html` into a full themed PALEO dashboard homepage with navigation, repo link, roadmap, and planned-feature placeholders.
- Upgraded `pages/project-checkin-1.html` from placeholder to a complete check-in site with structured sections, planning notes, and experiment artifact placeholders.
- Added `pages/technical.html` to preserve the technical dashboard view as a dedicated tab while converting `pages/index.html` into a user-friendly public homepage.
- Enhanced site-wide nav styling with an animated gradient GitHub repository button and updated tab structure (`Home`, `Technical`, `Check-in 1`).
- Added richer UI features to homepage/check-in pages: dark mode toggle, scroll progress bar, scroll-trigger reveal animations, Google Fonts, and themed image placeholders.
- Performed a second-pass homepage polish (`pages/index.html`) with longer user-facing content flow, additional sections, and expanded image placeholder blocks.
- Rebuilt `pages/technical.html` to match the same modern style system used on Home/Check-in (dark mode, progress bar, reveal animations, and consistent nav hierarchy).
- Added Font Awesome CDN icon library for themed visual elements (leaf, footprint, fossil/bone-like, dinosaur-adjacent motifs) across homepage and technical views.
- Added reusable decorative section-divider components to homepage (`fern frond` and `track trail` SVG motifs) and applied them between major sections for a more premium visual rhythm.
- Applied the same reusable fern/track SVG divider components to `pages/project-checkin-1.html` and `pages/technical.html` for cross-site visual consistency.
- Normalized divider density/spacing across all three pages by softening SVG prominence and harmonizing divider spacing for a cleaner, more premium rhythm.
- Applied a typography micro-pass across Home/Technical/Check-in pages (heading rhythm, paragraph spacing, line-length readability, and list spacing) for a more polished premium finish.
- Added accessibility refinements across all site tabs: stronger keyboard focus states, skip-to-content links, improved muted-text contrast, and reduced-motion fallbacks for animations/reveal effects.
- Added semantic accessibility polish across all pages: explicit primary-nav landmarks, `aria-current` for active tabs, decorative SVG/icon hiding (`aria-hidden`), and improved disabled-link keyboard behavior.
- Added final no-manual-testing accessibility hardening: `aria-pressed` state on color-mode toggles, decorative progress bar marked hidden, and conversion of technical placeholder pseudo-links into non-interactive cards.
- Implemented a combined UX/engineering pass: SEO metadata and canonical tags on all pages, requestAnimationFrame + passive scroll progress updates for smoother performance, richer homepage updates/credibility/quick-action sections, and enhanced micro-interaction polish for cards/buttons/placeholders.
- Performed a portfolio/demo-readiness content pass: tightened homepage value proposition and section copy, streamlined Technical page messaging, and simplified Check-in hero copy for faster scanning.
- Final style consistency pass: aligned heading capitalization/phrasing conventions across Home, Technical, and Check-in pages for one cohesive voice.

## 2026-03-14
- Filled out `docs/project_brief.md` using project-checkin details (problem, datasets, models, metrics, experiments, deliverables).
- Added scaffold modules `src/config.py` and `src/data.py` with non-I/O stubs for data configuration and dataset/batch placeholders.
- Updated `src/pipeline.py` to call the new config/data stubs while keeping behavior as a non-model "hello pipeline".
- Extended `tests/test_pipeline.py` to assert presence of new pipeline summary fields.
- Added `src/baselines.py` with stubbed OpenCV and ResNet-18 baseline interfaces and surfaced an OpenCV baseline descriptor via `run_pipeline()`.
- Added `src/training.py` with a stub `TrainingConfig` and dummy convergence curves; extended `run_pipeline()` and tests to surface summary training stats without any real model code.
- Added `src/agent.py` with an `AgentState`, stub decision rule, and formatted thought log, then surfaced `agent_action` and `thought_log` summaries from `run_pipeline()`.
- Created `docs/lexicon.md` and defined canonical terminology for Instinct Agent and Primal Mind, referenced from `docs/project_brief.md` and enforced via `.cursor/rules/00-project.mdc`.
- Updated `.cursor/rules/00-project.mdc`: reinforced short/simple replies and one-action-at-a-time when user leads development; avoid task dumps.
- Replaced data stubs with real manifest-oriented ingestion utilities in `src/data.py` (directory setup, deterministic split assignment, CSV-to-JSONL normalization, synthetic fallback, summary stats).
- Expanded `src/config.py` with concrete `DataConfig`, `PotConfig`, and `LettaConfig` for reproducible local setup and PoT/Letta assumptions.
- Implemented baseline task specs and baseline contracts in `src/baselines.py` (OpenCV-style rule baseline metrics + ResNet-18 model builder when torch is available).
- Upgraded `src/training.py` with reproducible training config/output handling and metrics persistence to `results/experiments/.../metrics.json`.
- Reworked `src/agent.py` to canonical Instinct Agent + Primal Mind terminology, including personality traits, observation struct, and structured thought logs.
- Added `src/pot.py` for Path of Titans runtime assumptions, screen-capture worker scaffold, and high-level action key mapping.
- Added `src/letta_tools.py` defining Letta tool schemas (dataset stats, train/eval, run agent, wiki query, personality updates) plus local stubs.
- Added `src/model_registry.py` for lightweight model registry metadata handling.
- Added scripts `scripts/prepare_data.py` and `scripts/show_letta_tools.py` for reproducible data prep and Letta tool introspection.
- Rewrote `README.md` with concrete environment setup and run commands.
- Added `requirements.txt` listing standard dependencies for PALEO phases.
- Added/updated tests in `tests/test_pipeline.py` and `tests/test_components.py` for end-to-end summary checks and component-level contracts.
- Implemented manifest join: `consensus_data.csv` + `all_images.csv` on `CaptureEventID` to populate `image_path` (full Snapshot Serengeti image URLs).
- Tuned predator label mapping to match actual `consensus_data.csv` species strings (e.g., `lionFemale`, `hyenaSpotted`).
- Rerun `prepare_data.py` on `data/raw/dryad/consensus_data.csv` and confirmed `data/manifests/serengeti_manifest.jsonl` contains non-empty `image_path` URLs.
- Updated `README.md` and `docs/project_brief.md` to reflect Dryad CSV exports as the current input source (derived from Snapshot Serengeti), while noting the future switch to LILA COCO JSON for full CV training.

## 2026-03-19
- Locked three Kaggle datasets in `docs/project_brief.md`: animal-behaviour, animal-behavior-prediction, Dinosaur Tactical Action Dataset (on-theme synthetic tactics for Instinct Agent alignment).
- Noted in project brief: `animal-behavior-prediction` deferred locally due to large (~16 GB) download; animal-behaviour + dinosaur-tactical-action-dataset used first.
- Added `data/raw/kaggle/animal-behavior-prediction/README.txt` placeholder for deferred Kaggle download.
- Adjusted `.gitignore` so `data/**` stays ignored but `data/raw/kaggle/animal-behavior-prediction/README.txt` can be committed.

## 2026-03-20
- Added `src/kaggle_ingest.py` to stream-count rows and list columns for every CSV under `data/raw/kaggle/`.
- Added `scripts/kaggle_stats.py` (text or `--json`) for quick verification of local Kaggle extracts without loading full files.
- Added `scripts/download_serengeti_images.py` to pull a deterministic small subset of `https://...` URLs from `serengeti_manifest.jsonl` into `data/processed/serengeti_images/`.
- Documented both flows in `README.md`; added `tests/test_kaggle_ingest.py` + `tests/fixtures/kaggle_sample.csv`.
- Ran `scripts/kaggle_stats.py` locally (Dino tactical 630k rows; `abp_accel.csv` ~14.6M rows) and successfully fetched two Snapshot Serengeti JPEGs via `scripts/download_serengeti_images.py`.
- Added `data/raw/kaggle/animal-behaviour/README.txt` + `.gitignore` un-ignore for that README; attempted Kaggle CLI download — blocked without `~/.kaggle/kaggle.json` on this machine (user must add API token or manual unzip).
- User chose to defer large local Kaggle downloads (deleted partial zip); clarified in README that sttaseen animal-behaviour ≠ deferred ~16 GB ABP dataset; raw extracts can be deleted after keeping small `results/` / processed artifacts.
- Added `docs/deferred_large_datasets.md` and linked it from `docs/project_brief.md` + `README.md` for explicit “large downloads TODO later” tracking.
- Ran `scripts/kaggle_stats.py` against existing local CSVs only (no new downloads): dino tactical 630k rows; `abp_accel.csv` ~14.6M rows.
- Wired local Kaggle inventory into `run_pipeline()` via `summarize_kaggle_for_pipeline()` (fast: skips full row scan for very large CSVs); added Letta tool `get_kaggle_local_inventory` + `scripts/kaggle_stats.py --quick`.
- Raised `KAGGLE_PIPELINE_ROW_COUNT_MAX_FILE_BYTES` to 100 MB so medium Kaggle CSVs (e.g. dino tactical) get full row counts in `run_pipeline` while huge accel-scale files stay deferred.
- Earlier `run_pipeline` check: manifest ~334k records; with a 12 MB threshold both local Kaggle CSVs deferred; 100 MB threshold targets tactical counts + accel deferred.
- Added `src/serengeti_image_paths.py` (shared naming with download script), `src/image_training.py` (ResNet-18 disk fine-tune on predator labels), `scripts/train_serengeti_images.py`, and `tests/test_serengeti_image_paths.py`; README section for JPEG training workflow.

## 2026-03-19
- Added `scripts/serve_companion.py`: localhost static server for `pages/` plus `/api/hud`, `/api/species`, `/api/metrics` wired to `simulate_instinct_decision` and optional `results/experiments/default_run/metrics.json`.
- Added `pages/companion-hud.html`: Path of Titans–themed local companion HUD (vitals, thought log JSON, rationale, fast facts); documented `file://` limitation.
- Linked Companion HUD from `pages/index.html` and `pages/technical.html`; documented run command in `README.md`.
- `companion-hud.html`: static / GitHub Pages mode with banner + offline preview heuristic when `/api/*` is unavailable; clarified live vs preview in `README.md`.
- `companion-hud.html`: expandable “Run the real Instinct Agent” instructions with copy-to-clipboard for terminal command and local URL; explains browsers cannot launch Python.
- `companion-hud.html`: fully spelled-out steps (terminal, full command, full local URL in prose + copy row); live URL sync updates both prose and code when already on localhost.
- Added **PALEO Profiles** under `pages/profiles/`: dark-themed mini-wiki (`index.html` dashboard + `kto-deinosuchus.html` profile) with JSON-driven content, full KTODeino curve dumps (attributes / multipliers / combat from NexLink seed), wiki-style abilities & skins, local-only loadout + skin-note tools (localStorage + JSON export), and paleontology section; linked **Profiles** from main site nav and documented in `README.md`.
- Profiles dashboard: expandable note clarifying **GitHub Pages works without** `serve_companion.py` (local server is for Companion HUD `/api/*`); **Fandom preferred** over Alderon modding portal for up-to-date tables (e.g. base playables like Kaiwhekea); KTO Deinosuchus provenance + external links reordered to match.
- Profiles **KTO Deinosuchus v2**: sticky **Contents** TOC; hero with **group slot** callout + **mod/curve IDs**; **adult-tier** ability stats (split **Bite / 90° / 180°** + utilities); NexLink **official curve link** + collapsible **curve key** lists; **core vitals** cards only; horizontal **slot layout** rail; **skin showcase** with rarity borders + Steam image fallback; **in-game gallery** (Steam PoT shots) vs **paleo media** dropdown; **visual loadout** (icon picker modal); **pattern lab** (male/female + per-region swatches, localStorage); subspecies cards with images; collapsible trivia/loadout/lab/paleo/curves; `media/kto-deinosuchus/README.md` for user assets.
- Profiles **Deinosuchus UX pass**: **centered full-width hero banner**; **sticky horizontal section tabs** under site nav (replaces in-page Contents list); **paleontology** outer block **collapsed by default**; **Font Awesome** column icons + extra numeric columns (bleed, bone-break, speed, mult, splinters) on abilities table; **pattern lab** skin **dropdown** + **preview thumb**; hero **class / curve prefix / copy control** row above group slot (dropped internal-key pill); `modIdToCopy` + hint in JSON; added `docs/profiles_future_styles.md` for per-creature style variants later; README links that doc from the Profiles blurb.
- Profiles: KTO Deinosuchus `modIdToCopy` set to `UGC_M_43G76JQ0NR_SK` (user-supplied mod ID).
