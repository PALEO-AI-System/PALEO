# PALEO

PALEO is an AI system that uses computer vision and trained animal behavior
models to power realistic, instinct-driven dinosaur agents in a survival game
environment.

## Minimal Scaffold (v0)

This repository currently provides project structure and a runnable "hello
pipeline" only. Model implementation is intentionally deferred.

## Project Layout

- `src/`: core Python package code
- `scripts/`: runnable entry-point scripts
- `tests/`: basic test coverage for scaffold behavior
- `docs/`: briefs and AI tool disclosure notes

## Reproducible Run Commands

From the repository root:

```bash
python scripts/run_pipeline.py
python -m unittest discover -s tests -p "test_*.py"
```
