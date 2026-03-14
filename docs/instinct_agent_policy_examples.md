## Instinct Agent policy examples

This document gives concrete examples of how the **Instinct Agent** and its **Primal Mind** might behave, building on the architecture plan. It is intentionally non-exhaustive and meant as a design reference, not a spec.

---

### 1. Combat “skill levels” and learning

- **Base level (rule-based + instincts)**
  - Uses Serengeti-inspired instinct signals (predator presence, herd density, etc.) plus PoT HUD state and fast-facts.
  - Follows species-appropriate rules: avoids clearly bad matchups, respects low stamina/health, prefers safer prey, and uses non-verbal signaling.
  - Looks **believable and often survivable**, but not optimized like a min-maxing PvP player.

- **Improving over time (data + optional RL)**
  - Logs episodes to disk (observations + actions + outcomes) and can be trained/tuned offline.
  - Over time, learns better **tactics**: when to engage/disengage, kiting patterns, stamina management, using terrain, and timing abilities.
  - Could eventually become **genuinely competent** in 1v1s or small skirmishes, bounded by data quantity/quality and environment complexity.

- **Class-scope reality**
  - For PALEO, the target is a **smart, realistic animal** that often survives and behaves coherently, not an esports-level PvP bot.
  - The architecture is future-proofed so more serious learning is possible if you later invest in more data and training.

---

### 2. Threat response modes: fight / flight / freeze

Example rule fragments (to be implemented as code, not prompts):

- **Flight**
  - If `predator_prob` is high AND health is low AND bravery trait is low → select a **FLIGHT** response.
  - Prioritize paths that move toward cover or herd members; de-prioritize chasing damage.

- **Fight**
  - If cornered (no clear escape path) OR stamina is nearly empty AND enemy is close → **FIGHT** response.
  - Prefer high-impact defensive abilities (knockbacks, armor buffs) and calls/emotes that signal aggression.

- **Freeze**
  - If surprised by a large hit from out-of-view and escape routes are unclear → brief **FREEZE** window.
  - After a short delay, transition into **FLIGHT** or **FIGHT** based on updated threat assessment and personality.

---

### 3. Juvenile / growth-aware behavior

Some example rules that use age and growth:

- Smaller predators may:
  - Prefer **juvenile prey** of competitor species when hungry and low-risk.
  - Avoid fully-grown apex adults unless in a herd or with strong terrain advantage.

- Larger territorial species may:
  - Defend nesting/territory areas more aggressively against juveniles of rival species.
  - Show more tolerance toward same-herd juveniles (protective positioning, warning calls).

These rules should read from both:

- PoT HUD / perception (to approximate size/age), and
- The Primal Mind (knowledge of own growth stage and current goals).

---

### 4. Non-verbal behavior and emotes

Actions should include **calls and emotes** as first-class options, not just movement and attacks. Examples:

- **Broadcast / territory calls**
  - When entering a new territory while healthy and confident, emit a broadcast call to signal presence.
  - When low health or alone, reduce aggressive broadcasting to avoid drawing predators.

- **Friendly / social calls**
  - When near known herd members (tracked in Primal Mind) and not in immediate danger, emit friendly calls or social emotes.
  - When meeting an unknown but non-threatening species, use cautious friendly calls instead of immediate approach.

- **Threaten calls**
  - When guarding a carcass or water source and a rival approaches within a threshold distance, use threaten calls prior to attacking.
  - Personality traits (aggressiveness, bravery, morality) modulate how quickly the agent escalates from threaten → attack.

- **Help / distress calls**
  - When health is critically low and nearby allies exist, prefer help calls while attempting to flee.
  - Juveniles may be more likely to emit distress calls earlier in a fight.

- **Chat emotes**
  - Optionally, the agent can trigger chat emotes (e.g. `:dinocry:`) as extra-flavor signals in low-stakes contexts, though these are not core to decision quality.

Species-specific flavor can be layered on top later (e.g., some species using more visual emotes, others relying mostly on calls). For example, some carnivores with distinctive animations might use more head-bob or stretch emotes when asserting presence, while more skittish species lean heavily on Danger/Help calls.

---

### 5.1 Path of Titans–specific growth flavor

Grounding the juvenile behavior in PoT’s growth system:

- **Hatchling / Juvenile**
  - Higher stamina but low health and weight; more likely to:
    - Avoid direct confrontation with adults of most species.
    - Stay near cover and group members when possible.
    - Emit Danger/Help calls earlier when threatened.
  - As hatchlings/juveniles take fewer group slots, the agent in a herd might tolerate more juveniles nearby and prioritize their safety.

- **Adolescent / Sub-adult**
  - Transitional stages where second ability slots may unlock.
  - The agent can become more exploratory/aggressive as stats improve but should still avoid top-tier adult apex matchups.

- **Adult**
  - Full stats and higher group-slot cost.
  - Territorial behavior becomes more pronounced: more Broadcast and Threaten calls around high-value locations (water, quests, carcasses).
  - Death penalties (dropping back to Sub-adult) can factor into risk appetite in the Primal Mind (e.g., “avoid needless high-risk duels when solo”).

---

### 5. Ability-loadout inference examples

High-level patterns for using observed actions to infer ability loadouts:

- Maintain, in the Primal Mind, a **hypothesis set** for each observed enemy: which abilities they might have equipped, based on:
  - Species, life stage, and typical meta builds (from fast-facts and wiki RAG).
  - Abilities already seen during the encounter.
  - Hotbar slot limits (if UI parsing allows).

- Example inferences:
  - If an enemy uses a high-cost mobility ability (e.g., a specific lunge/dash) that occupies a known slot → eliminate mutually exclusive alternatives from the hypothesis set.
  - If multiple defensive abilities are observed, infer that offensive burst abilities are less likely, adjusting threat level accordingly.
  - If an enemy has not used an expected “meta” ability after a long fight, downweight its probability and adjust positioning risk.

These inferences don’t have to be perfect; even coarse reasoning can make the agent feel more **aware and intentional**.

---

### 6. Example “skilled but animal-like” behavior loop

Putting pieces together, an example loop for a mid-sized predator:

1. **Perceive**
   - Sees a lone juvenile competitor species near a water source, plus a distant adult of the same species.
   - Estimates own health/stamina, hunger, and nearby cover.
2. **Update Primal Mind**
   - Logs that it is hungry, alone, mid-growth, and currently in a contested territory.
3. **Decide threat/target**
   - Assesses juvenile as viable prey, adult as potential future threat.
4. **Non-verbal signaling**
   - Emits a low, territorial broadcast toward the water, but no direct threaten call toward the juvenile yet.
5. **Engage**
   - Approaches cautiously, ready to flee if the adult gets too close.
   - Uses an opening ability to quickly injure the juvenile while conserving stamina.
6. **Adapt**
   - If the adult charges, switches to **FLIGHT** mode; if cornered, transitions to **FIGHT** with threaten calls and defensive abilities.

This style of policy is the target: **coherent, grounded in instincts and personality, and capable of becoming more “skilled” as data and training accumulate.**

