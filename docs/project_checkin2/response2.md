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

- **Machine learning:** Train a **predator vs non-predator** ResNet-18 on a nearly 10k-image balanced **Snapshot Serengeti** set, then **fine-tune on 300 labeled Path of Titans screenshots** to adapt to game-domain visuals (domain shift reduction). `1e-4` was the best accuracy-oriented choice on Serengeti and stayed strong on the 300-image PoT validation split, but the agent version shifted toward predator recall because missed predators are more harmful in-game than false alarms.
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
- Serengeti split: **6,529 training images** and **2,142 validation images** from the existing manifest split.
- Domain adaptation dataset: **300 manually labeled Path of Titans screenshots** (`predator` / `non_predator`).
- Path of Titans split: **240 training screenshots** and **60 validation screenshots** from the 300-image set.
- Verification set: **10 Path of Titans test images** (manual + filename-based labels).
- Source: LILA page `https://lila.science/datasets/snapshot-serengeti`; Dryad link in `docs/project_brief.md`; Kaggle links there for secondary data.
- Data modality: **Images** + **CSV metadata** now; **text** for wiki/RAG; gameplay frames later.
- Approximate size: Full Serengeti is huge; the repo is built around **small, reproducible subsets** (`--max-records`, `--max-images`).
- Preprocessing plan: `prepare_data` → JSONL manifest + splits + `predator_label`; download JPEGs to `data/processed/serengeti_images/`; train/eval with the image scripts above.

If you are collecting your own data, also include:

- Collection method: Optional **your own gameplay screenshots** if wildlife transfer is not enough.
- Annotation plan: **Light manual labels** only if needed.
- Ethical considerations: **Public/permitted data**, no personal data in captures, **disclose AI use**, and **no unfair online cheating**—private testing and advisor-style use first.

## 7. Evaluation Plan

- What metrics will you use? For images: **accuracy**, **F1**, **confusion matrix**, plus **predator recall/precision** at multiple inference thresholds (safety-first target is high predator recall). For the agent: **does the loop run**, **thought text matches behavior**, **latency**, and **safe control** (kill switch works).
- What baseline methods or comparison methods will you use? **Rule/heuristic** screen signals and OpenCV-style baselines in code; **no-training** majority baseline from `run_experiments.py`; **trained** ResNet runs vs those.
- How will you determine whether the project is successful? **Reproducible scripts**, honest metrics, a **working live capture + keyboard path**, and—once Letta is in—**clear multi-step behavior** that feels like a creature, not a single if-statement.

Examples may include accuracy, F1 score, mAP,  success rate, latency, user satisfaction, robustness, or other task-specific metrics.

## 8. Current Progress

- **Live game feed:** **Working**—`run_paleo_live.py`, `serve_companion.py` + `companion-hud.html`, and `run_paleo_overlay.py` use **live screen capture** (`README.md`).
- **Keyboard output:** **Working in prototype**—`run_paleo_control_loop.py` can run **advice-only** or **control** with **`--enable-control`** and an **F12** emergency stop (`README.md`). This is the path for “hold W to walk” style tests once the game window is focused.
- **Agent loop in code:** **Instinct Agent** decisions, **Primal Mind** state, thought formatting, and PoT-style key mapping exist in `src/agent.py`, `src/pot.py`, with **`simulate_dino.py`** to sample scenarios and **`run_pipeline.py`** for a one-shot integrated demo.
- **Training / data path (wildlife):** Manifest pipeline (`prepare_data`), image download, **ResNet fine-tune** (`train_serengeti_images`), **eval** (`evaluate_serengeti_images`), and **experiment sweep + JSON outputs** (`run_experiments.py`) are in the repo; results appear under `results/experiments/` **after you run them locally** (not committed).
- **Latest model update:** Fine-tuned checkpoint from 300 PoT screenshots (`epoch=15`) with LR sweep. The accuracy pick is `lr=1e-4` (`0.767` validation accuracy on the 60-image split). The agent safety pick is `lr=3e-5` with predator class weight `3.0` and threshold `0.20`, which improves 10-image predator recall from `0.571` to `0.714` while keeping holdout accuracy at `0.70`.
- **False-negative mitigation now supported:** configurable predator threshold in inference and threshold-sweep eval output to select a recall-prioritized operating point.
- **Main gap:** **Letta** is still **stub / schema** level (`letta_tools.py`, `show_letta_tools.py`)—not the live “brain in the middle” yet.
- **Not done yet:** I have **not** fully tested **PALEO while actually playing Path of Titans** (focused game window, real in-game screen, simple movement like **holding W**). That is the next practical check.

Supporting evidence (screenshots, sample outputs, training curves, tables or visualizations):  
HUD/overlay screenshots optional; metrics JSON under `results/experiments/` when training scripts are run; `unittest` under `tests/` for pipeline and data pieces.

## 9. Next-Step Plan

- What will be completed next? **Wire Letta** as the real decision layer (session + memory + tools), not just stubs.
- What experiments will be run? **Play Path of Titans with PALEO running**: confirm **live capture sees the game**, **advice mode** looks sane, then **control mode** smoke tests (e.g. **walk forward**) with **low FPS** and **kill switch** ready.
- What improvements will be made? More **in-game** hours, tighter **metrics** for class work, and clearer **report figures** from saved runs.
- What timeline do you expect for the next milestones? **Soon:** Letta hookup + first successful **in-PoT** capture/control trial; **after that:** richer behavior and report polish.
