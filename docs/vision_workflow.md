# PALEO vision workflow (target vs shipped)

This is the **mock workflow** from `docs/paleo_brainstorming.md` and `docs/context_dump.md`, written as **what you want** vs **what the repo does today**.

---

## Already implemented (high level)

- **Screen capture:** grabs a region of your monitor (`mss`), optional PNG snapshots.
- **Cheap “vision” today:** frames are turned into **numbers** (brightness, motion), not semantic scene understanding (`src/pot.py` → `frame_to_observation`).
- **Instinct Agent (local rules):** chooses a high-level action from those numbers + species policy (`src/agent.py`, `simulate_instinct_decision` in `src/letta_tools.py`).
- **Thought-shaped output:** JSON thought logs from the rule-based agent (`format_thought_log`), printed or shown in HUD/debug — **not** stored in a live Letta session.
- **Key mapping + input:** high-level action → keys/mouse (`ActionMapper`, `SafeInputController`); real key injection works when enabled (`keyboard` lib).
- **Local HUD / overlay:** companion server, overlay, control-loop script for advice vs control and emergency stop.
- **Letta-shaped surface (offline):** tool **schemas** and **stub** Python implementations (`src/letta_tools.py`, `scripts/show_letta_tools.py`) — no running Letta agent loop wired to the game yet.
- **Light RAG:** keyword lookup over **your** curated `docs/wiki_snippets.md` (`src/wiki_rag.py`), callable as a tool idea (`query_pot_wiki`).

---

## Still to implement (high level)

- **Real vision:** model or UI parsing that knows dinos, HUD bars, threats — not only brightness/motion.
- **Letta runtime:** connect to a real Letta deployment; one **Instinct Agent** per dino identity with **Primal Mind** memory blocks that **persist**.
- **Closed loop:** capture → (vision + RAG + memory) → **Letta** → tool calls → decision → optional keys, on a steady tick with rate limits and safety.
- **Richer game knowledge:** bigger or embedded wiki RAG, structured species/ability sheets beyond snippets.
- **Logging you can trust:** durable run logs, optional replay, aligned with what the HUD shows.

---

## Letta track (your ideas — more detail)

**Perceive and understand screenshots**

- **Today:** the live loop does **not** send images to Letta or to a multimodal model; it sends **derived scalars** only.
- **To build:** on each tick (or every N ticks), pass a **downsampled frame** or **cropped HUD/world regions** into a **vision-capable** model (via Letta or a sidecar vision model whose outputs Letta reads). Define **what** the model must output (tags, JSON: threat, species guesses, bar readings) so the rest stays small and testable.

**RAG (game context)**

- **Today:** `query_snippets` over local markdown snippets; tool spec `query_pot_wiki` exists in the Letta tool list; stubs can call the real function.
- **To build:** expand `wiki_snippets.md` or add embeddings + chunk store; optionally ingest wiki exports you are allowed to use; expose as a **Letta tool** the agent can call when unsure (“what abilities does X usually have?”).

**Think like an animal + thought process output**

- **Today:** rule-based `decide_instinct_action` + `format_thought_log` (JSON with rationale fields).
- **To build:** Letta system prompts + memory that encode **personality**, **needs**, **recent events**; optional **natural-language** inner monologue for the report/HUD, while **structured** JSON stays the contract for the control layer.

**Logging**

- **Today:** prints JSON lines from `run_paleo_control_loop.py`; HUD shows debug payloads; metrics under `results/` for training.
- **To build:** one **append-only** session log (tick, frame id, observation summary, RAG hits, model text, chosen action, keys sent, safety flags); same fields mirrored for Letta traceability.

**Remembering**

- **Today:** no long-term Letta memory; each `simulate_instinct_decision` call is stateless aside from whatever you pass in.
- **To build:** **Primal Mind** blocks in Letta (identity, goals, traits, last fights, water finds, rival species); **short-term buffer** (last few frames’ summaries) either in Letta or in Python passed into each turn.

**Deciding actions and keys**

- **Today:** Instinct rules → action string → `keymap` / `mousemap` → `SafeInputController`.
- **To build:** Letta (or hybrid) outputs **the same** high-level action vocabulary **or** explicit key intents; a **Python safety shim** maps to keys, enforces **advice vs control**, **rate limits**, and **F12** kill switch so the model never bypasses guardrails.

**Actually controlling the keyboard**

- **Today:** implemented and testable (`--mode control --enable-control`).
- **To build:** only enable this path when Letta + vision path is trusted; keep **dry-run** default; document anti-cheat / ToS risks for official servers (`docs/context_dump.md`).

---

## One-line loop (target)

**Capture frame → vision summary (+ optional image to multimodal model) → retrieve wiki/species facts → update Primal Mind in Letta → emit thought log + structured decision → map to keys → execute or advise → log everything.**

For day-to-day tasks, see `TODO.md`.
