---
name: paleo-ml-agent-architecture
overview: Design a staged, end-to-end PALEO architecture that goes from real predator–prey data through ML baselines and evaluation to a game-playing agent in Path of Titans, orchestrated by a Letta bot, with clear phases and risks for a future coding agent.
todos:
  - id: phase-0-setup
    content: Finalize environment assumptions and repo layout, including README and docs/ai_tool_log.md entries for PALEO.
    status: pending
  - id: phase-1-data
    content: Design concrete data ingestion and manifest format for the chosen predator–prey dataset.
    status: pending
  - id: phase-2-models
    content: Specify exact baseline model tasks (labels, metrics) for OpenCV and ResNet-18.
    status: pending
  - id: phase-4-pot-loop
    content: Detail the screen capture region, frame rate, and input mapping assumptions for Path of Titans integration.
    status: pending
  - id: phase-7-letta
    content: Define Letta tool surface (list of callable actions and their I/O schemas) against PALEO.
    status: pending
isProject: false
---

## End-to-end system overview

```mermaid
flowchart LR
  subgraph dataSide [Offline Data & Training]
    serengetiRaw[SerengetiRawData] --> dataIngest[DataIngestion & Cleaning]
    dataIngest --> featureStore[FeatureStore/PreprocessedDatasets]

    featureStore --> classicalBaselines[OpenCV & Heuristic Baselines]
    featureStore --> resnetTraining[ResNet18 Training]

    classicalBaselines --> evalBench[Eval & Metrics]
    resnetTraining --> evalBench

    evalBench --> modelRegistry[ModelRegistry]
  end

  subgraph agentSide [Online Agent & Game]
    modelRegistry --> paleoService[PALEOBackendService]
    paleoService --> decisionModule[InstinctAgentModule]

    subgraph potLoop [Path of Titans Loop]
      screenCapture[ScreenCaptureWorker] --> obsEncoder[ObsEncoder(CV+NN)]
      obsEncoder --> stateAssembler[GameStateAssembler]
      stateAssembler --> decisionModule
      decisionModule --> actionMapper[ActionMapper]
      actionMapper --> potInput[PoTInputController]
    end

    paleoService <--> lettaAgent[LettaLettaAgent]
    lettaAgent <--> wikiRAG[WikiRAG(KnowledgeBase)]
  end
```



- **Data ingestion**: Download a curated subset of Snapshot Serengeti (or similar) and normalize into a local, versioned dataset with labels for species, time, and coarse interaction context (e.g., predator present / prey present / co-occurrence).
- **ML baselines**: On Serengeti data, train (1) simple OpenCV/heuristic detectors and (2) a ResNet-18 classifier. These become the first predator/prey recognition components and ground PALEO’s instinct layer about predator/prey and behavior cues.
- **Training/eval**: Standardized train/val/test splits, metrics (accuracy, F1, confusion matrices, AUROC), experiment logging, and model registry.
- **Agent decision-making**: A lightweight rule-based / RL-backed **Instinct Agent** that consumes Serengeti-derived instinct signals + live game observations and a small set of personality traits (mood, aggressiveness, curiosity, bravery, etc.), then emits high-level actions (e.g., move toward herd, flee predator) and logs its internal chain-of-thought (hidden) plus visible behavior.
- **PoT integration**: A local loop on the same machine that captures screenshots, runs the vision stack, maintains a short-term state buffer, and uses an input controller to send keyboard/mouse/controller events into Path of Titans.
- **Letta integration**: Letta orchestrates PALEO tools and hosts per-dinosaur agents: each dinosaur gets its own Letta agent instance with memory blocks (identity, abilities, current goals, recent experiences) and access to PALEO tools plus a RAG tool over a local snapshot of the Path of Titans wiki.

## Technical stack proposal

### Core languages & environment

- **Language**: Python 3.11+.
- **Environment**: `uv` or `pip + venv` with a pinned `requirements.txt` / `pyproject.toml`.
- **Project layout** (high-level, no code yet):
  - `paleo/data/` – dataset downloading, parsing, and validation.
  - `paleo/models/` – OpenCV rules, ResNet-18 definitions, training loops.
  - `paleo/agent/` – decision logic, policies, simple RL or rule-based agents.
  - `paleo/pot/` – Path of Titans integration (screen capture, input control).
  - `paleo/api/` – service layer exposing ML and agent capabilities as callable functions / HTTP endpoints for Letta.
  - `notebooks/` – exploratory work, visualization.
  - `docs/` – architecture, ai_tool_log, run instructions.

### 1) Data ingestion & dataset management

- **Data sources**: Snapshot Serengeti (or similar camera trap dataset).
- **Libraries**:
  - `requests` or `httpx` – download scripts if needed.
  - `pandas` – metadata tables, filtering, splits.
  - `pyarrow` / `parquet` – efficient local storage of structured labels (optional but recommended).
  - `Pillow` or `opencv-python` – image I/O and basic manipulation.
  - `tqdm` – progress bars for ingestion.
  - `pydantic` / `pydantic-core` – typed configs and validation for dataset manifests.
- **Artifacts**:
  - Local `data/raw/` and `data/processed/` folders (relative paths only).
  - A dataset manifest file (JSON/Parquet) describing image paths, species, and interaction tags.
  - Reproducible script/CLI to regenerate processed datasets.

### 2) ML baselines (OpenCV + ResNet-18)

- **Libraries**:
  - `opencv-python` – color thresholding, motion detection, contour-based heuristics.
  - `torch`, `torchvision` – ResNet-18, transforms, training loop.
  - `scikit-learn` – train/val split, metrics, simple classical baselines (e.g., logistic regression on hand-crafted features).
  - `matplotlib` / `seaborn` – plots, confusion matrices.
  - `wandb` or `mlflow` (optional) – experiment tracking; can be stubbed initially.
- **Models**:
  - **Heuristic baseline**: e.g., simple foreground/background segmentation, bounding box occupancy, crude predator/prey presence flags.
  - **ResNet-18 classifier**: pre-trained on ImageNet, fine-tuned for species classification and/or predator-present vs. not.
- **Packaging**:
  - Models saved as Torch `.pt` files plus a lightweight metadata sidecar (JSON) describing input shape, labels, and version.
  - A small `ModelRegistry` abstraction that loads the latest approved model for a task (e.g., `predator_presence_v1`).

### 3) Training & evaluation pipeline

- **Libraries**:
  - Same as ML baselines (`torch`, `torchvision`, `sklearn`, `pandas`).
  - `hydra-core` or `argparse` – configuration-driven experiments.
- **Capabilities**:
  - Deterministic train/val/test splits based on manifest.
  - Metrics: accuracy, per-class F1, macro/micro F1, confusion matrices, possibly AUROC for binary predator presence.
  - Simple early-stopping training loop for ResNet-18.
  - Experiment logging to disk (`results/experiments/<run_id>/...`).

### 4) Agent decision-making

- **Observation model**:
  - Input: outputs from the Serengeti-trained vision models (predator presence probability, prey/herd density proxies, coarse behavior cues) + basic PoT state (HUD signals such as health, stamina, hunger/thirst, debuffs/buffs parsed via CV, and nearby dino silhouettes/species).
  - Representation: a small `Observation` struct that can be serialized and fed to both the Instinct Agent and Letta tools.
- **Policy / agent logic**:
  - **Phase 1**: rule-based policies conditioned on **personality traits** (e.g., aggressiveness, bravery, curiosity, sociability, morality) and instincts, with explicit **threat response modes** (fight/flight/freeze) and examples such as: if predator probability high and health low and bravery low → flight; if cornered or out of stamina → fight; if surprised by a large hit with unclear escape → brief freeze.
  - **Phase 2 (optional)**: lightweight RL using `stable-baselines3` if we can construct a pseudo-environment over PoT episodes, still conditioned on personality traits.
  - The policy should also encode **growth/juvenile-specific behavior**, e.g., some species being more likely to hunt juveniles of competitor species, or smaller predators preferring juvenile prey for size/safety reasons.
- **Libraries**:
  - `numpy` – feature vectors.
  - `dataclasses` or `pydantic` – typed observations/actions.
  - `stable-baselines3` – optional RL agents (PPO, DQN) if environment abstractions become viable.

### 5) Path of Titans integration (screen-capture + inputs on a single machine)

- **Observation pipeline**:
  - **Screen capture**: `mss` or `pyautogui` for fast, region-specific screen capture.
  - **Preprocessing**: `opencv-python` and `torchvision.transforms` to crop HUD/viewport regions and normalize images.
  - **Model inference**: `torch` models loaded from `ModelRegistry` and run in a low-latency loop, including PoT-specific detectors (HUD parsing, dino silhouettes/species classifiers) if later added.
  - **State buffer**: `collections.deque` or small ring buffer to keep last N observations for smoother decisions and to give Letta short-term episodic context.
  - **Capture cadence**: start with low-rate periodic screenshots (e.g., 1–2 Hz) feeding the same observe → decide → act path, then graduate to a higher-FPS live loop (5–10 Hz) once stable.
- **Action pipeline**:
  - **Input sending**: `pyautogui` or `keyboard` / `mouse` libraries for simulating keypresses and mouse input.
  - **Action abstraction**: high-level actions (`FLEE`, `GRAZE`, `FOLLOW_HERD`, etc.) mapped to low-level key sequences with timing.
- **Process orchestration**:
  - Local runner script that:
    - Binds to a specific monitor/region where PoT is running in windowed/borderless mode.
    - Runs an observe → decide → act loop at a target frequency (e.g., 5–10 Hz) with safety checks.
    - Logs observations, chosen actions, and timestamps to `logs/pot_runs/` for later analysis.

### 6) Letta integration

- **Assumptions**: Letta can call external tools (e.g., via HTTP or Python function tools) and we can expose PALEO functions as those tools.
- **Integration surface**:
  - **Python tool wrapper**: A set of pure functions that Letta can call:
    - **Data/ML tools**: `get_dataset_stats()`, `train_model(config)`, `evaluate_model(run_id)`.
    - **Game tools**: `run_pot_agent(params)`, `get_current_game_state()`, `set_personality_traits(dino_id, traits)`.
    - **Knowledge tools**: `query_pot_wiki(query)` backed by a local RAG index over Path of Titans wiki pages.
  - **Optional HTTP API**: `FastAPI` app exposing a small REST/JSON interface, if Letta prefers HTTP tools.
- **Libraries**:
  - `fastapi` + `uvicorn` (optional) – thin API server.
  - `pydantic` – request/response schemas that mirror Letta tool definitions.

### 7) Knowledge & memory design (Letta + RAG)

- **Long-term factual knowledge**:
  - Local scrape/export of key Path of Titans wiki pages (species, abilities, status effects, controls, emotes).
  - Embedded into a local vector store (e.g., `faiss` or `chromadb`) exposed as a `query_pot_wiki` tool.
- **Per-dinosaur memory blocks (in Letta)**:
  - Identity: species, life stage (hatchling/juvenile/adult), current build/abilities.
  - Personality: mood, aggressiveness, friendliness, curiosity, bravery, morality.
  - Goals: short-term (reach waterhole), medium-term (grow to adult), long-term (hold territory).
  - Recent experience: last N encounters (who, what happened, outcome).
- **Working memory during play**:
  - Small sliding window of recent observations and actions synchronized with the state buffer, for better context in reasoning and post-hoc analysis.

## Phases and milestones (single-session sized)

### Phase 0 – Repo hygiene & scaffolding

- **P0.1**: Confirm and document environment (Python version, env creation, basic `requirements.txt` stub, `README` quickstart, `docs/ai_tool_log.md` note).
- **P0.2**: Establish project layout (`paleo/data`, `paleo/models`, `paleo/agent`, `paleo/pot`, `paleo/api`) and minimal config pattern (YAML or JSON).

### Phase 1 – Dataset ingestion & exploration

- **P1.1**: Implement a small ingestion script to download a tiny subset of Snapshot Serengeti (or load from a manually downloaded archive) into `data/raw`.
- **P1.2**: Normalize metadata into a manifest (e.g., JSONL/Parquet) with columns for image path, species, predator/prey flag, and split; support both synthetic fallback and real Snapshot Serengeti metadata CSVs.
- **P1.3**: Add a simple EDA notebook to inspect label balance and sample images.

### Phase 2 – Baseline models on Serengeti

- **P2.1**: Implement an OpenCV-based heuristic baseline that flags predator presence from simple pixel heuristics; evaluate on a small split.
- **P2.2**: Implement a minimal ResNet-18 training script (ImageNet-pretrained) for species or predator presence classification; save a trained checkpoint.
- **P2.3**: Implement a basic evaluation script generating accuracy/F1/confusion matrix, saving results to disk.

### Phase 3 – Model registry & inference API

- **P3.1**: Implement a lightweight `ModelRegistry` that can list/load the latest model by task name from `models/`.
- **P3.2**: Implement a pure-Python prediction function that, given an image (path or array), returns predator/prey probabilities using the latest model.
- **P3.3**: Wrap prediction in a small local CLI/utility script (no service yet) to sanity-check performance.

### Phase 4 – PoT observation loop (read-only)

- **P4.1**: Implement a `ScreenCaptureWorker` to grab frames from a specified region where PoT will run; verify FPS and save sample frames.
- **P4.2**: Implement an `ObsEncoder` that runs the Serengeti-trained ResNet-18 on captured frames (or cropped HUD regions) and outputs a compact observation struct including Serengeti-inspired instinct features (predator/prey/threat) plus PoT HUD state.
- **P4.3**: Log encoded observations to disk over a short test session to validate latency and stability.

### Phase 5 – Agent decision logic (no control yet)

- **P5.1**: Implement a simple rule-based Instinct Agent that takes a stream of observations + a fixed personality profile for one dinosaur and proposes high-level actions (but only logs them, does not send inputs yet).
- **P5.2**: Run offline simulations on recorded observation logs to tune thresholds and rules.

### Phase 5.5 – Multi-agent & personality layer (optional, small)

- **P5.5.1**: Define a compact personality schema (e.g., 5–7 numeric traits) and store it per dinosaur in Letta memory.
- **P5.5.2**: Allow the Instinct Agent to be instantiated for multiple dinosaurs (even if you only drive one in-game at first), each with its own Letta memory block and personality.

### Phase 6 – PoT action integration (control loop)

- **P6.1**: Implement an `ActionMapper` from high-level actions to sequences of key/mouse events tailored to PoT controls.
- **P6.2**: Implement a safe control loop that reads observations in real-time, calls the policy, and sends inputs to PoT, including an emergency stop mechanism (hotkey) to disable AI control.
- **P6.3**: Instrument logging of episodes (actions + screenshots) for later debugging.

### Phase 7 – Letta integration (tool layer)

- **P7.1**: Define a small set of PALEO capabilities as Letta tools (at least: run dataset stats, train a model with a config, run a short PoT agent session, query the PoT wiki, and set/get dinosaur personality traits and goals).
- **P7.2**: Implement a Python tool wrapper module or `FastAPI` service exposing these capabilities with clear schemas, suitable for one Letta agent per dinosaur.
- **P7.3**: Create a Letta workflow prompt/flow that orchestrates a full mini pipeline (e.g., inspect dataset, train small model, spawn a juvenile dino agent with traits X, run 2-minute PoT session in advisor or control mode).

### Phase 8 – Iteration & extension

- **P8.1**: Add more robust metrics (e.g., calibration, precision/recall at different thresholds) and dataset curation tools.
- **P8.2**: Explore simple RL training over scripted scenarios if a PoT-like environment can be abstracted.
- **P8.3**: Tighten real-time performance (batching, GPU usage, asynchronous loops) once correctness is solid.

## Key unknowns, risks, and info to gather

### Dataset-related

- **Licensing & usage constraints**: Confirm Snapshot Serengeti (or chosen dataset) license permits local ML training and publication of derived models for non-commercial research/experimentation.
- **Data format & availability**: Verify how images and labels are distributed (e.g., separate metadata CSV vs. API) and whether subsets can be easily downloaded.
- **Label granularity**: Ensure predator/prey or interaction labels can be derived from available annotations; otherwise, define a mapping from species labels to predator/prey categories.

### ML transferability

- **Domain gap**: Camera trap photos vs. Path of Titans visuals are very different domains; the Serengeti-trained models may not transfer directly.
  - Plan to gather a small PoT-specific dataset (screenshots with manual labels) to fine-tune or calibrate models.

### PoT integration & OS constraints

- **Anti-cheat / TOS**: Confirm whether PoT permits automation tools that simulate input; ensure the project stays within community and legal norms.
- **Input libraries**: On Windows, confirm which of `pyautogui`, `keyboard`, or other libraries work reliably in full-screen/borderless mode and whether administrator privileges are required.
- **Performance**: Screen capture + NN inference may be CPU/GPU intensive. Need to benchmark to ensure the loop can maintain acceptable FPS without making PoT unplayable.

### Letta APIs and orchestration

- **Tool definition format**: Confirm current Letta version, how Python/HTTP tools are specified, and any serialization constraints on inputs/outputs.
- **Long-running jobs**: Clarify how Letta prefers to handle long-running actions (like a 30-minute training run or extended PoT session) – synchronous vs. async, progress updates, and cancellation.

### System design & safety

- **Safety & control**: Define clear user overrides (keyboard hotkey, on-screen toggle) so the AI can be instantly disabled in-game.
- **Logging & replay**: Decide on a standard log schema so that episodes can be replayed or at least re-analyzed from saved frames + actions.
- **Resource management**: GPU vs. CPU allocation when running PoT and models on the same box; may require configurable frame rate or dynamic quality.

## Information you should gather before building

- **Dataset**: Exact dataset choice and link; license terms; how to obtain a small test subset; label schema for predator/prey.
- **PoT details**: Game settings (windowed vs. fullscreen), keybinds, whether any modding/API hooks exist, and any community guidance on automation.
- **Hardware**: Target machine specs (GPU model, RAM, CPU) to tune the real-time inference loop.
- **Letta**: Version, preferred integration style (in-process Python vs. HTTP tools), and examples of long-running tool orchestration.
- **Project constraints**: Any limits on external services (e.g., can we use wandb or is everything local-only?).


## Alignment addendum (from context_dump & brainstorming)

This section pins down a few explicit requirements that were previously only implied or missing:

- **Local-only control & server policy**
  - PALEO must run as a **local screen-watching + input-sending process**, *not* injected into the PoT client or shipped as a mod.
  - On **official/anti-cheat servers**, the default is **advisor mode only** (no automated inputs), with any full-control experiments restricted to **private/community servers you own and run** where such automation is allowed.

- **Fast-facts table alongside RAG**
  - In addition to the wiki RAG vector store, maintain a small **fast-facts table** (e.g., JSON/CSV) mapping `species → {diet, size tier, threat tier, typical role, key abilities}` for cheap, deterministic lookups inside the Instinct Agent.

- **Single Instinct Agent MVP**
  - Phase 1 scope is **one dinosaur + one Instinct Agent with one Primal Mind** (per-dino memory block) end-to-end: Serengeti instincts → PoT perception → decisions → (advisor/control) actions.
  - Multi-agent support (many dinos at once) remains an explicit **stretch goal** after the single-agent loop is robust.

- **Ability-loadout inference**
  - The Instinct Agent should perform **ability-loadout inference**: from observed enemy actions and limited hotbar slots, maintain hypotheses over what abilities a nearby dinosaur likely has equipped and update threat estimates accordingly.

- **Non-verbal behavior in the action set**
  - The high-level action space must explicitly include **non-verbal behaviors** (calls, emotes, body-language postures) such as broadcast/friendly/threaten/help calls, emote-wheel animations, and idle/defensive postures, not just movement and combat actions.

- **Primal Mind terminology**
  - The structured per-dinosaur memory (identity, personality traits, goals, recent experiences) is referred to consistently as the dinosaur’s **Primal Mind**, with the acting controller called the **Instinct Agent**, matching `docs/lexicon.md`.

- **Live feed preference**
  - The default PoT observation loop targets a **live, throttled capture stream** (e.g., 3–10 FPS region-based screen capture) rather than sporadic manual screenshots, with room to later explore incorporating audio as an additional signal if a safe/local capture path is available.

