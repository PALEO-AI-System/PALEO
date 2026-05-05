"""Minimal Letta API helper for PALEO decision calls."""

from __future__ import annotations

import json
from typing import Any, Dict

import requests


def request_letta_decision(
    *,
    base_url: str,
    api_key: str,
    agent_id: str,
    payload: Dict[str, Any],
    timeout_sec: float = 20.0,
) -> Dict[str, Any]:
    """Send one decision request to Letta and normalize response shape.

    Expects either a direct ``{"action": "...", "thought_log": "..."}`` response,
    or a nested structure containing these fields.
    """
    base = base_url.rstrip("/")
    endpoints = [
        f"{base}/v1/agents/{agent_id}/messages",
        f"{base}/v1/agents/{agent_id}/chat/completions",
    ]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    body = {
        "messages": [
            {
                "role": "user",
                "content": json.dumps(payload, separators=(",", ":"), sort_keys=True),
            }
        ],
        "metadata": {"source": "paleo-control-loop"},
    }
    last_error = ""
    for url in endpoints:
        try:
            r = requests.post(url, headers=headers, json=body, timeout=timeout_sec)
            r.raise_for_status()
            data = r.json()
            action = (
                data.get("action")
                or (((data.get("output") or {}).get("action")) if isinstance(data.get("output"), dict) else "")
                or (((data.get("decision") or {}).get("action")) if isinstance(data.get("decision"), dict) else "")
            )
            thought = (
                data.get("thought_log")
                or (((data.get("output") or {}).get("thought_log")) if isinstance(data.get("output"), dict) else "")
                or json.dumps(data, separators=(",", ":"), sort_keys=True)
            )
            if action:
                return {"action": str(action), "thought_log": str(thought), "raw": data, "endpoint": url}
            last_error = f"missing action field in response from {url}"
        except Exception as exc:  # pragma: no cover - runtime network path
            last_error = str(exc)
    raise RuntimeError(f"letta decision request failed: {last_error}")

