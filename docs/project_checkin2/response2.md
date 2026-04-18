# Project-Checkin-2/2

## 1. Project Title

PALEO (with Primal Mind)

## 2. Team Information

- Team name: World's Finest
- Team members: Laura Wetherhold, Alexus Aguirre Arias

## 3. Problem to Solve

- What the problem is: In dinosaur survival games, NPCs often feel stale: few real behaviors, little sense of individuality, and combat that does not grow with you. PALEO targets **agentic dinosaurs**—each one can have its own **personality and thresholds**, read **your screen**, form **thoughts and a plan**, and **drive the keyboard** so the loop can run autonomously (for example sitting back while your dinosaur walks or fights). A stretch idea is **quest-only autopilot**; the main goal is **believable animal-like behavior** (tension, disputes, relationships) on creatures that were real animals, not just scripted bots.
- Why it is important: That would make the world feel **more realistic and immersive**, give you **NPCs that can actually fight or react** instead of cardboard targets, and let you **practice combat against dinosaurs that get tougher over time** instead of always the same pattern.
- Who is affected or who would benefit from a solution: **Players** who want richer worlds and sparring partners; **developers** who want to stress-test AI and design; anyone who cares about **explainable, per-creature** behavior instead of one global NPC script.

## 4. AI Functions to Be Developed

- **Machine learning:** Train a small **predator vs non-predator** image model on **Snapshot Serengeti** (manifest + local JPEGs). The repo has `scripts/prepare_data.py`, `scripts/download_serengeti_images.py`, `scripts/train_serengeti_images.py`, `scripts/evaluate_serengeti_images.py`, and `scripts/run_experiments.py` (including a no-training baseline and several training configs). `scripts/run_pipeline.py` also runs a **tiny end-to-end demo** that includes a short ResNet training step on a synthetic batch (for wiring, not full-scale training).
- **Computer vision:** **Live screenshots** from the monitor (`mss`), simple frame stats for the **Instinct Agent**, plus HUD/overlay paths so you can **see** what the loop is doing. Game frames are the long-term target; wildlife images are the current training stand-in.
- **Search:** **RAG-style** lookup over game/wiki text via `src/wiki_rag.py` so decisions can be grounded in mechanics later.

**Please be specific about what your AI system is expected to do:**  
**Letta** is the planned **main agent layer**: memory, reasoning, and choosing what to do next. Today the repo implements the **Python side** (screen input, local **Instinct Agent** + **Primal Mind** state, thought text, key actions, and **Letta-shaped tools** in `src/letta_tools.py` as **stubs**). The missing middle step is a **real Letta session** wired into that loop.

## 5. Use of Agentic AI

- Will the system plan multi-step actions? **Yes**—tick-by-tick **perceive → think → (optional) act**, with state carried forward.
- Will it call tools or external APIs? **Designed to**—tool schemas exist for Letta; right now they are **local stubs**, not a live hosted agent.
- Will it reason over memory or context? **Yes**—**Primal Mind** holds personality, goals, and recent context so choices are not one-off.
- Will it coordinate multiple AI modules? **Yes**—screen signals, optional classifier, wiki/RAG, and action mapping are meant to meet in the **agent** layer.
- Will it make decisions autonomously based on feedback? **Partly today**—there is **advice mode** and **guarded control** with an **emergency stop** (`README.md` / `run_paleo_control_loop.py`); full autonomy waits on Letta + more in-game testing.

## 6. Dataset(s)

- Dataset name: **Snapshot Serengeti** (via **Dryad CSV** workflow in `README.md`); optional **Kaggle** packs later (`docs/deferred_large_datasets.md`).
- Source: LILA page `https://lila.science/datasets/snapshot-serengeti`; Dryad link in `docs/project_brief.md`; Kaggle links there for secondary data.
- Data modality: **Images** + **CSV metadata** now; **text** for wiki/RAG; gameplay frames later.
- Approximate size: Full Serengeti is huge; the repo is built around **small, reproducible subsets** (`--max-records`, `--max-images`).
- Preprocessing plan: `prepare_data` → JSONL manifest + splits + `predator_label`; download JPEGs to `data/processed/serengeti_images/`; train/eval with the image scripts above.

If you are collecting your own data, also include:

- Collection method: Optional **your own gameplay screenshots** if wildlife transfer is not enough.
- Annotation plan: **Light manual labels** only if needed.
- Ethical considerations: **Public/permitted data**, no personal data in captures, **disclose AI use**, and **no unfair online cheating**—private testing and advisor-style use first.

## 7. Evaluation Plan

- What metrics will you use? For images: **accuracy**, **F1** (especially **predator class** if labels are imbalanced), confusion matrix from `evaluate_serengeti_images.py`. For the agent: **does the loop run**, **thought text matches behavior**, **latency**, and **safe control** (kill switch works).
- What baseline methods or comparison methods will you use? **Rule/heuristic** screen signals and OpenCV-style baselines in code; **no-training** majority baseline from `run_experiments.py`; **trained** ResNet runs vs those.
- How will you determine whether the project is successful? **Reproducible scripts**, honest metrics, a **working live capture + keyboard path**, and—once Letta is in—**clear multi-step behavior** that feels like a creature, not a single if-statement.

Examples may include accuracy, F1 score, mAP,  success rate, latency, user satisfaction, robustness, or other task-specific metrics.

## 8. Current Progress

- **Live screen feed:** **Working**—`run_paleo_live.py`, `serve_companion.py` + `companion-hud.html`, and `run_paleo_overlay.py` use **live screen capture** (`README.md`).
- **Keyboard output:** **Working in prototype**—`run_paleo_control_loop.py` can run **advice-only** or **control** with **`--enable-control`** and an **F12** emergency stop (`README.md`). This is the path for “hold W to walk” style tests once the game window is focused.
- **Agent loop in code:** **Instinct Agent** decisions, **Primal Mind** state, thought formatting, and PoT-style key mapping exist in `src/agent.py`, `src/pot.py`, with **`simulate_dino.py`** to sample scenarios and **`run_pipeline.py`** for a one-shot integrated demo.
- **Training / data path (wildlife):** Manifest pipeline (`prepare_data`), image download, **ResNet fine-tune** (`train_serengeti_images`), **eval** (`evaluate_serengeti_images`), and **experiment sweep + JSON outputs** (`run_experiments.py`) are in the repo; results appear under `results/experiments/` **after you run them locally** (not committed).
- **Main gap:** **Letta** is still **stub / schema** level (`letta_tools.py`, `show_letta_tools.py`)—not the live “brain in the middle” yet.
- **Not done yet:** I have **not** fully tested **PALEO while actually playing Path of Titans** (focused game window, real in-game screen, simple movement like **holding W**). That is the next practical check.

Supporting evidence (screenshots, sample outputs, training curves, tables or visualizations):  
HUD/overlay screenshots optional; metrics JSON under `results/experiments/` when training scripts are run; `unittest` under `tests/` for pipeline and data pieces.

## 9. Next-Step Plan

- What will be completed next? **Wire Letta** as the real decision layer (session + memory + tools), not just stubs.
- What experiments will be run? **Play Path of Titans with PALEO running**: confirm **live capture sees the game**, **advice mode** looks sane, then **control mode** smoke tests (e.g. **walk forward**) with **low FPS** and **kill switch** ready.
- What improvements will be made? More **in-game** hours, tighter **metrics** for class work, and clearer **report figures** from saved runs.
- What timeline do you expect for the next milestones? **Soon:** Letta hookup + first successful **in-PoT** capture/control trial; **after that:** richer behavior and report polish.

