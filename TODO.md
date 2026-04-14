# PALEO — what’s next (living checklist)

Use **[x]** for done, **[ ]** for not done. Do not delete completed lines; mark them **[x]** instead.

## Original checklist (restored)

- [x] Fill `docs/project_brief.md` with concrete project scope and dataset.
- [x] Define baseline model and evaluation protocol.
- [x] Implement data loading and preprocessing module in `src/` (`src/data.py`, manifests, splits).
- [x] Implement first baseline training/inference pipeline (`src/training.py`, `scripts/run_pipeline.py`, image scripts).
- [ ] Add experiment tracking (metrics, configs, artifacts) — basic metrics exist; tighten tracking.
- [ ] Produce required experiments and figures for report.

## Test in Path of Titans (short)

1. Start the game; use **borderless or windowed** first (easier than exclusive fullscreen).
2. Run **advice-only** first: `py -3 scripts/run_paleo_control_loop.py --input-source live --full-screen --mode advice --ticks 30`  
   - Watch the printed JSON: actions and keys should change as the screen changes (still rough heuristics).
3. When ready for real keys: same command with `--mode control --enable-control` and **game window focused**.
4. Keep **F12** handy (emergency stop). Start with low `--fps` and few `--ticks`.
5. Optional: `py -3 dist/PALEO.exe` or `py -3 scripts/run_paleo_live.py` for the HUD while you play.

## Screen understanding (plain language)

- [x] **Right now:** the loop turns your screenshot into **simple numbers** (brightness, motion). The **Instinct Agent** only sees those numbers — not “that’s a rex” or “my health bar is low.”
- [ ] **Later — learned vision on your data:** a small **image model** you train on **your** screenshots or labels, to output things like threat / prey / UI state. No official PoT dataset is required.
- [ ] **Later — multimodal Letta path:** send frames or sparse stills to a **vision-capable** Letta/model so the agent reasons about pixels (not implemented in the hot loop yet; needs wiring, rate limits, and cost/size tradeoffs).

## Deferred heavy downloads (when you have disk/bandwidth)

- [ ] Pull and use large Kaggle bundles when ready — see `docs/deferred_large_datasets.md` (optional, not blocking core PALEO).

## Overlay & HUD

- [ ] Iterate on **overlay** UX and readability during real play.
- [ ] **PALEO.exe** (browser Companion HUD) vs **PALEOOverlay.exe** (transparent tk HUD): keep first-run docs and in-HUD copy aligned so the two launchers are not conflated.
- [ ] **Cross-check** the plan vs reality: what the overlay/HUD *should* show vs what is **actually** wired and visible (debug fields, live frame, control preview, API endpoints).
- [ ] Keep **companion HUD** (`serve_companion` / `companion-hud.html`) aligned with the same behaviors where it makes sense.
- [ ] Document (or optionally unify) running **overlay** alongside **advice vs control**: default overlay is advice-only; real OS input stays on `run_paleo_control_loop.py --enable-control` until a single entrypoint exists.

## Core pipeline / agent

- [ ] Replace or augment pixel **heuristics** with a trained **vision** step (even a small classifier on cropped UI).
- [ ] **Path of Titans** hardening: focus, key timing, fewer accidental inputs.
- [ ] **Letta** integration (next big step): real agent session, tools, memory — beyond local stubs (`src/letta_tools.py`).
- [ ] **Agent output → keys/mouse**: same structured actions **Letta** (or any middle tier) emits must map through **`ActionMapper` / `SafeInputController`** with tests and guardrails (schema parity with `simulate_instinct_decision` today).
- [ ] Richer **game context** for the agent (wiki / mechanics — see `src/wiki_rag.py`, `docs/paleo_brainstorming.md`).

## Course / evaluation (from `docs/context_dump.md`)

- [ ] Clear **metrics** and experiments (curves, baselines, qualitative examples) as your class expects.
- [ ] **Report** artifacts when due.

## Older backlog (still useful)

- [ ] Tighten `docs/project_brief.md` vs current repo (keep it matching shipped code).

## Gaps vs docs (nothing “hidden” — if it’s not above, it’s here)

- [ ] **LILA COCO JSON** track for Serengeti (brief mentions “later”).
- [ ] **Unify** Kaggle tabular behavior data with the **same** training path as Serengeti (if you want one joint pipeline).
- [ ] **Abilities / growth / emote** depth from `docs/paleo_brainstorming.md` (agent knows loadouts, calls, growth) — design + data, not built end-to-end.
- [ ] **Multi-dinosaur** / NPC-scale agents (brainstorm); current focus is one Instinct Agent loop.
- [ ] **Distributable install** so “someone else tries it on their dinosaur” is one-command smooth (README + exe path exists; polish as needed).
- [ ] **Windows injection reality**: document admin/focus/antivirus caveats for `keyboard`/`mouse`; smoke-test packaged control on a second machine if you ship `--enable-control`.
