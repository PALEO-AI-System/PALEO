"""Baseline model stubs for PALEO.

These functions do not perform any real computer vision or learning yet.
They only describe what a baseline *would* do and return dummy outputs.
"""

from __future__ import annotations

from typing import List


def run_opencv_baseline(batch: List[str]) -> str:
    """Return a dummy description of an OpenCV-style rule baseline."""
    return f"opencv_rule_baseline(num_examples={len(batch)})"


def run_resnet18_baseline(batch: List[str]) -> str:
    """Return a dummy description of a ResNet-18 classifier baseline."""
    return f"resnet18_classifier_baseline(num_examples={len(batch)})"

