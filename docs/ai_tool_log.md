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
