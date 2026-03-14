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
