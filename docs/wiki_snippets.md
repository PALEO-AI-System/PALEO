## Path of Titans wiki snippets (seed)

Lightweight manual snippet dump for key pages. This is *not* a full scrape; it is a curated set of short summaries or quotes that can be:

- Used directly by humans when designing policies.
- Optionally ingested into a future local RAG index.

### Allosaurus (base game carnivore)

- Source: `https://pathoftitans.wiki/dinosaurs/carnivores/allosaurus`
- Role: well-rounded, large terrestrial carnivore with balanced health, damage, and speed.
- Notable mechanics:
  - Access to bleed abilities (e.g., Hatchet Bite) and generalist defensive options.
  - Good land speed allows kiting and repositioning; not the tankiest but rarely “bad” in any category.

### Styracosaurus (base game herbivore)

- Source: `https://pathoftitans.wiki/dinosaurs/herbivores/styracosaurus`
- Role: aggressive ceratopsian frontliner, capable of jousting, ramming, and support playstyles.
- Notable mechanics:
  - Joust: wind-up charge that deals bleed and rewards timing/spacing.
  - Ram: direct, high-impact horn attack.
  - Support tools like Frilled Bond that buff nearby allies’ damage/armor.

### Achillobator (base game raptor)

- Source: `https://pathoftitans.wiki/dinosaurs/carnivores/achillobator`
- Role: medium, pack-oriented raptor with options for lone-hunter builds.
- Notable mechanics:
  - Raptor claw attacks and multi-hit strike abilities.
  - Pack buffs (e.g., Mob Boss–style effects) and solo buffs (e.g., Lone Hunter–style damage boosts).

### Tylosaurus (base game aquatic apex)

- Source: `https://pathoftitans.wiki/dinosaurs/carnivores/tylosaurus`
- Role: apex aquatic ambush predator that dominates in water but is limited on land.
- Notable mechanics:
  - Clamp/drag-style attacks to pull prey into deep water and break bones.
  - Strong water mobility and vision tools; can briefly surge onto shore for opportunistic strikes.

### KTO Pachyrhinosaurus (modded ceratopsian)

- Sources:
  - Description: Path of Titans modded-creature wiki entry (Pachyrhinosaurus, KTO).
  - Stats: `https://guides.gsh-servers.com/path-of-titans/guides/curve-overrides/modded-dinosaurs/kto/path-of-titans-ktopachyrhino`
- Role: thick-nosed ceratopsian “tank” with strong crowd control and group-oriented buffs.
- Notable mechanics:
  - Heavy knockback/ram abilities and bone-break potential.
  - Defensive and stamina-support tools that make it ideal for anchoring a herd and protecting juveniles.

### KTO Yangchuanosaurus (modded carnivore)

- Sources:
  - Description: KTO collection overview page featuring Yangchuanosaurus.
  - Stats: `https://guides.gsh-servers.com/path-of-titans/guides/curve-overrides/modded-dinosaurs/kto/path-of-titans-ktoyang`
- Role: large, armor-light but high-pressure theropod; mid-to-top predator focusing on sustained pressure over hard tanking.
- Notable mechanics:
  - Solid health and combat weight progression; no special armor/venom, relies on raw damage and positioning.
  - Stamina and recovery curves that reward planned engagements and disengages rather than endless sprinting.

### Stamina (mechanic)

- Source (mechanics overview): `https://path-of-titans.fandom.com/wiki/Stamina`
- Role: governs how long a dinosaur can sprint, attack, jump, and swim before needing to rest.
- Notable details:
  - High stamina and recovery reward kiting, repositioning, and extended chases.
  - Low stamina thresholds should trigger disengage/flight behavior in most instincts, especially for fragile species.
  - Some abilities and hides modify stamina drain/recovery, which affects how aggressively an Instinct Agent can play.

### Bleeding (mechanic)

- Source: `https://path-of-titans.fandom.com/wiki/Bleed`
- Role: damage-over-time effect applied by certain attacks (often claws, teeth, or horns) that pressures targets to disengage.
- Notable details:
  - Bleed stacks and can be mitigated by specific hides/abilities or by resting/sleeping.
  - High incoming bleed should make agents value cover, disengage routes, and defensive/emergency actions more.
  - Bleed-heavy predators (e.g., some raptors and horned dinos) gain leverage by landing short, safe hits and waiting.

### Quests & Growth (mechanic)

- Source: `https://path-of-titans.fandom.com/wiki/Quests`
- Role: primary way to earn growth and marks in Adventure mode, directly tied to progression through Hatchling → Adult.
- Notable details:
  - Many quests are low-threat (exploration, collection) and can be prioritized when survival needs (health/stamina/hunger/thirst) are stable.
  - Death at higher growth stages has a bigger effective cost, so Instinct Agents should become more conservative in high-risk fights as they grow.
  - For juveniles, quests near safe areas and groups are preferable to isolated objectives in high-threat regions.

### Status Effects (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Status_Effects`
- Role: umbrella category for ongoing positive/negative effects (bleed, venom, fracture, slow, buffs, etc.) that influence how a dinosaur should behave moment to moment.
- Notable details:
  - Many status effects stack or interact (e.g., bleed + fracture is more dangerous than either alone).
  - Instinct policies should map severe negative effects (heavy bleed, fracture, poison) to more conservative, survival-focused behavior.

### Fracture / Bone Break (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Bone_Break`
- Role: reduces movement capability and escape options, often applied by heavy-impact abilities (horn charges, tail swipes, aquatic grabs).
- Notable details:
  - When fractured, fleeing becomes much harder; agents should avoid committing to long-range chases while at risk of being bone-broken.
  - On offense, species with reliable bone-break tools gain leverage by forcing enemies to fight on bad terms (no sprint, poor maneuvering).

### Venom / Poison (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Venom`
- Role: damage and debuff-over-time effects that can weaken targets gradually rather than through immediate bursts.
- Notable details:
  - Venom often encourages hit-and-run tactics: apply and disengage while the effect works.
  - When afflicted, agents should factor in long-term attrition—seeking safe areas, resting, or friendly support rather than extending fights.

### Hunger & Thirst (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Buffs_and_Debuffs`
- Role: core survival meters that, when low, apply debuffs and eventual damage.
- Notable details:
  - High hunger/thirst should override most non-emergency goals, pushing agents toward food/water even if there is some risk.
  - Long-distance foragers (e.g., large herbivores) benefit from metabolism choices and routes that minimize how often they must cross dangerous territory.

### Marks (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Marks`
- Role: main currency for unlocking abilities, skins, and subspecies; earned via quests and gameplay.
- Notable details:
  - While Instinct Agents don’t need to “spend” marks directly, awareness that certain quests or behaviors yield marks can inform risk/reward (e.g., high-mark quests might justify extra caution).

### Waystones (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Waystones`
- Role: structures used to teleport group members to the leader’s location.
- Notable details:
  - For herd/pack-aware agents, Waystones provide a way to regroup quickly; policies can prefer using them when isolated and in danger.
  - Juveniles or fragile builds might value staying near known Waystone locations as safe regroup points.

### Home Caves (mechanic)

- Source: `https://pathoftitans.fandom.com/wiki/Home_Caves`
- Role: personal housing instances where players can rest, customize, and sometimes avoid danger.
- Notable details:
  - Home Caves can be considered “safe zones” in high-level reasoning—agents might path through them between risky objectives or during downtime.
  - Long-term, Instinct Agents could associate Home Cave proximity with reduced risk and more willingness to engage in nearby quests.

