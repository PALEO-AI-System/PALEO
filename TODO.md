# PALEO — what’s next (living checklist)

Use **[x]** for done, **[ ]** for not done. Do not delete completed lines; mark them **[x]** instead.

## Original checklist (restored)

- [x] Fill `docs/project_brief.md` with concrete project scope and dataset.
- [x] Define baseline model and evaluation protocol.
- [x] Implement data loading and preprocessing module in `src/` (`src/data.py`, manifests, splits).
- [x] Implement first baseline training/inference pipeline (`src/training.py`, `scripts/run_pipeline.py`, image scripts).
- [ ] Add experiment tracking (metrics, configs, artifacts) — basic metrics exist; tighten tracking.
- [x] Produce required experiments and figures for report. (Completed via recent metrics/figure commits and presentation updates.)

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
- [ ] Overlay command-only settings audit pass: expose remaining useful CLI-only options in overlay UI (or explicitly document why they stay CLI-only), including advanced runtime toggles.
- [ ] Overlay -> Companion HUD live sync channel: wire shared runtime state/events so overlay and browser Companion HUD update the same agent-state stream in real time.

## Core pipeline / agent

- [ ] Replace or augment pixel **heuristics** with a trained **vision** step (even a small classifier on cropped UI).
- [x] Add explicit PoT HUD parser pass using confirmed mapping in `docs/pot_hud_reference.md` (health red bar, stamina white bar hidden-at-full edge case, hunger/thirst icons, ability and buff/debuff lanes).
- [ ] HUD ROI calibration pass v2: tune normalized ROI boxes per resolution/UI scale using `scripts/calibrate_pot_hud.py` overlays, then lock per-profile presets.
- [ ] HUD value calibration set expansion: collect more gameplay-only screenshots (exclude menu/skin/abilities pages) and retune confidence thresholds for hunger/thirst/health/stamina.
- [ ] Full supervised HUD-value model training: build labeled HUD dataset (health/stamina/hunger/thirst targets) and train/evaluate a dedicated model to replace or augment rule-based parsing in `parse_pot_hud`.
- [ ] **Path of Titans** hardening: focus, key timing, fewer accidental inputs.
- [ ] **Letta** integration (next big step): real agent session, tools, memory — beyond local stubs (`src/letta_tools.py`).
- [ ] Letta image upload guardrail: enforce <=5MB per image (resize/compress to JPEG/WebP and chunk/fallback policy before upload).
- [ ] **Letta Code MemFS setup:** configure a MemFS-backed Letta Code instance for PALEO so the Instinct Agent/Primal Mind can use fast ephemeral memory during local runs (with a clear switch path to persistent storage later).
- [ ] **Agent output → keys/mouse**: same structured actions **Letta** (or any middle tier) emits must map through **`ActionMapper` / `SafeInputController`** with tests and guardrails (schema parity with `simulate_instinct_decision` today).
- [ ] **Audio events from sound:** capture short audio windows, extract lightweight features, classify a few event types (e.g., roar/combat/quiet), then feed flags into the agent observation.
- [ ] **Voice commands (later):** mic capture + speech-to-text (text output), then map spoken commands into a safe subset of actions (pause, switch mode/species, hold/flee) through the same `ActionMapper` path.
- [ ] **Discord loop telemetry (optional):** post perceive/think/remember/decide/act tick summaries to a Discord channel via webhook for remote monitoring/debug.
- [ ] Richer **game context** for the agent (wiki / mechanics — see `src/wiki_rag.py`, `docs/paleo_brainstorming.md`).

## Course / evaluation (from `docs/context_dump.md`)

- [x] Clear **metrics** and experiments (curves, baselines, qualitative examples) as your class expects. (Recent check-in/presentation commits include corrected metrics, ablation coverage, and confusion matrices.)
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
