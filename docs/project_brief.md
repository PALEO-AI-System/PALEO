# Project brief (v0)

Problem:
- Many game NPCs (and assistant agents for players) behave in predictable, reactive ways that lack an interpretable internal state. For dinosaur survival gameplay, we want per-dinosaur agents that connect visual cues to high-level behavioral intent and action choices.

Why it matters:
- For game developers, PALEO provides a behavior-stress-testing tool for level design, resource placement, and balance. For players (especially those with accessibility needs), it can assist with complex survival loops while keeping behavior explainable via thought logs.

Dataset (link + size):
- Snapshot Serengeti (subset of millions of camera-trap images): `https://lila.science/datasets/snapshot-serengeti`
- Kaggle predator vs prey animal image dataset (specific subset TBD): `https://www.kaggle.com/datasets?search=predator+prey+animals`
- Final sample counts and class distributions will be recorded in preprocessing logs.

Core AI function (ML/CV/NLP/Search/Opt):
- Supervised computer vision classifier for behavior/intent from images.
- Letta-based agentic orchestration for perceive → decide → act → remember loops.
- Optional natural-language generation of thought logs for interpretability.

Baseline model:
- Rule-based OpenCV script using simple motion/region heuristics as a fully transparent baseline.
- Learned baseline: ResNet-18 backbone with a fine-tuned behavior-intent classification head.

Agentic AI (Letta): what it perceives → decides → does:
- Perceives: downsampled game screen frames and classifier outputs (e.g., threat level, hunger/need proxies, risk posture).
- Decides: updates per-dinosaur internal state (identity, needs, recent events, risk history), writes natural-language thought logs, and selects a behavior mode (e.g., flee, forage, explore, idle).
- Does: proposes or executes keyboard/mouse actions consistent with the chosen mode; logs outcomes back into Letta memory for future decisions.

Success metrics:
- Classifier: accuracy, macro-F1, confusion matrices across behavior classes.
- Agent: action success rate, decision latency, and qualitative behavior realism judged via scenario-based tests.
- System: clear, interpretable thought logs that align with observed actions in qualitative evaluations.

Required experiments:
- Convergence curves for training/validation loss and accuracy across epochs.
- Hyperparameter sensitivity sweeps (learning rate, augmentation strength, class weighting, backbone variants).
- Baseline comparison table (OpenCV rule baseline vs. ResNet-18 and any improved variants).
- Qualitative examples of success/failure cases with short narrative analysis.

Deliverables:
- Reproducible codebase (fresh-clone runnable pipelines for data, training, and agent loop prototypes).
- Figures/tables for convergence, sensitivity, baselines, and qualitative examples.
- IEEE-style report (≤ 8 pages) plus AI tool usage/disclosure section aligned with course requirements.