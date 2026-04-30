/**
 * PALEO Profiles — creature page (KTO Deinosuchus profile + future JSON-driven profiles).
 */
(function () {
  "use strict";

  const slug = document.body.dataset.slug;
  if (!slug) return;

  const root = document.getElementById("profile-root");
  if (!root) return;

  const LS_LOADOUT = `paleo-profiles:v1:loadout:${slug}`;
  const LS_PRESETS = `paleo-profiles:v1:loadout-presets:${slug}`;
  const LS_PALETTE = `paleo-profiles:v1:skin-palette:${slug}`;
  const LS_GENDER = `paleo-profiles:v1:gender:${slug}`;
  const LS_SKIN_LAB = `paleo-profiles:v1:skin-lab-pick:${slug}`;

  function el(tag, cls, html) {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  }

  function slugify(s) {
    return String(s)
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-|-$/g, "");
  }

  function stars(n, max) {
    const full = "★".repeat(n);
    const empty = "☆".repeat(Math.max(0, max - n));
    return `<span class="stars" aria-label="${n} of ${max}">${full}${empty}</span>`;
  }

  function readJson(key, fallback) {
    try {
      const v = localStorage.getItem(key);
      if (!v) return fallback;
      return JSON.parse(v);
    } catch {
      return fallback;
    }
  }

  function writeJson(key, obj) {
    localStorage.setItem(key, JSON.stringify(obj));
  }

  function rarityCss(r) {
    const m = {
      Common: "rarity-common",
      Uncommon: "rarity-uncommon",
      Rare: "rarity-rare",
      Legendary: "rarity-legendary",
    };
    return m[r] || "rarity-common";
  }

  function statDisp(v) {
    if (v === null || v === undefined) return "—";
    return String(v);
  }

  function speedMultDisp(v) {
    if (v === null || v === undefined) return "—";
    return `×${v}`;
  }

  function renderStarsBlock(data) {
    const r = data.ratings;
    const max = r.scaleMax || 5;
    const row = el("div", "star-row");
    Object.entries(r).forEach(([k, v]) => {
      if (k === "scaleMax" || typeof v !== "number") return;
      const item = el("div", "star-item");
      item.innerHTML = `<strong>${k.replace(/([A-Z])/g, " $1").trim()}</strong>${stars(v, max)}`;
      row.appendChild(item);
    });
    return row;
  }

  function skinFallbackSrc(data, index) {
    const shots = data.gameGallery || [];
    if (!shots.length) return "";
    return shots[index % shots.length].src;
  }

  function clamp01(v) {
    return Math.max(0, Math.min(1, v));
  }

  function renderPips(value, label) {
    const wrap = el("div", "agent-pips");
    const fill = Math.round(clamp01(value) * 10);
    const row = el("div", "agent-pip-row");
    for (let i = 0; i < 10; i++) {
      const pip = el("span", `agent-pip ${i < fill ? "on" : "off"}`);
      row.appendChild(pip);
    }
    wrap.appendChild(el("span", "agent-pip-label", label));
    wrap.appendChild(row);
    return wrap;
  }

  function renderTraitBar(value, label) {
    const item = el("div", "agent-trait-item");
    item.appendChild(el("div", "agent-trait-head", `<span>${label}</span><strong>${Math.round(clamp01(value) * 100)}%</strong>`));
    const track = el("div", "agent-trait-track");
    const fill = el("div", "agent-trait-fill");
    fill.style.width = `${Math.round(clamp01(value) * 100)}%`;
    track.appendChild(fill);
    item.appendChild(track);
    return item;
  }

  const AGENT_SPECIES_OPTIONS = [
    { id: "allosaurus", label: "Allosaurus", role: "generalist carnivore", note: "Balanced land hunter; flanks and repositions." },
    { id: "styracosaurus", label: "Styracosaurus", role: "aggressive frontliner", note: "Horned herbivore; thrives in direct pressure." },
    { id: "achillobator", label: "Achillobator", role: "pack raptor", note: "Fast medium carnivore; pack or lone-hunter style." },
    { id: "tylosaurus", label: "Tylosaurus", role: "apex aquatic", note: "Water apex; strong ambush and drag control." },
    { id: "kto_pachyrhinosaurus", label: "KTO Pachyrhino", role: "tank support", note: "Defensive ceratopsian with strong group value." },
    { id: "kto_yangchuanosaurus", label: "KTO Yangchuanosaurus", role: "bruiser carnivore", note: "Sustained pressure and positioning focus." },
  ];

  const AGENT_ARCHITECTURE = {
    agent_name: "PALEO Instinct Agent",
    agent_id: "agent-4c9b0339-20de-4f22-8897-7eb4ba8f8258",
    conversation_id: "conv-82a63dd9-55fe-43be-b564-4723125db844",
    description: "Instinct-driven dinosaur AI for Path of Titans.",
    tools: [
      "query_pot_wiki",
      "simulate_instinct_decision",
      "set_personality_traits",
      "get_species_fast_facts",
      "get_dataset_stats",
      "run_pot_agent",
      "get_kaggle_local_inventory",
    ],
    system_prompt: [
      "You are the PALEO Instinct Agent.",
      "Perceive -> think -> remember -> decide -> act.",
      "Use calls, body language, and structured decisions.",
      "Never speak normally.",
    ],
    memory_blocks: [
      { name: "dinosaur", chars: 1847, limit: 5000, summary: "Species identity, traits, survival priorities, and class context." },
      { name: "persona", chars: 862, limit: 5000, summary: "Behavioral instructions and survival style." },
      { name: "primal_mind", chars: 1940, limit: 10000, summary: "Recent experiences, decisions, allies, rivals, and territory memory." },
      { name: "species_knowledge", chars: 3314, limit: 10000, summary: "Species roles, mechanics, calls, and survival heuristics." },
      { name: "paleo_behavior_spec_merged", chars: 5139, limit: 100000, summary: "Merged exhaustive behavior reference." },
      { name: "paleo_context_strategy", chars: 572, limit: 100000, summary: "Hybrid memory + retrieval guidance." },
    ],
    archival_memory: [
      "No dedicated archival block is currently engaged.",
      "Older conversation history remains retrievable through conversation search.",
    ],
    live_state: {
      species: "allosaurus",
      lifeStage: "adult",
      goal: "survive_and_explore",
      traits: {
        aggressiveness: 0.5,
        friendliness: 0.5,
        curiosity: 0.6,
        bravery: 0.5,
        morality: 0.5,
      },
      loop: ["Perceive", "Think", "Remember", "Decide", "Act"],
      state: {
        predator_probability: 0.3,
        prey_density: 0.5,
        health: 0.8,
        stamina: 0.7,
        hunger: 0.4,
        thirst: 0.3,
      },
    },
  };

  function renderAgentVisualTab(root) {
    const agent = AGENT_ARCHITECTURE.live_state;
    const sections = [
      { id: "agent-avatar", label: "Avatar card" },
      { id: "agent-hud", label: "Live HUD" },
      { id: "agent-scene", label: "Animated scene" },
      { id: "agent-arch", label: "Architecture" },
    ];
    buildSubnav(sections);

    const hero = el("section", "profile-section agent-visual-hero");
    hero.appendChild(el("h1", "profile-title", "PALEO Agent"));
    hero.appendChild(el("p", "profile-intro", "A presentation view of the instinct agent: three ways to show identity, survival state, and the perceive → think → remember → decide → act loop."));

    const speciesSwitcher = el("div", "agent-species-switcher");
    AGENT_SPECIES_OPTIONS.forEach((sp, i) => {
      const btn = el("button", `agent-species-chip ${i === 0 ? "active" : ""}`);
      btn.type = "button";
      btn.dataset.species = sp.id;
      btn.innerHTML = `<strong>${sp.label}</strong><span>${sp.role}</span>`;
      speciesSwitcher.appendChild(btn);
    });
    hero.appendChild(speciesSwitcher);

    const loop = el("div", "agent-loop-rail");
    agent.loop.forEach((step, i) => {
      const chip = el("span", `agent-loop-chip ${i === 0 ? "active" : ""}`, step);
      loop.appendChild(chip);
    });
    hero.appendChild(loop);
    root.appendChild(hero);

    const avatar = el("section", "profile-section agent-tab-panel");
    avatar.id = "agent-avatar";
    avatar.appendChild(el("h2", null, "Avatar card"));
    const card = el("div", "agent-avatar-card");
    const vis = el("div", "agent-avatar-visual");
    vis.innerHTML = `<div class="agent-shadow"></div><div class="agent-body"></div><div class="agent-head"></div><div class="agent-tail"></div>`;
    card.appendChild(vis);
    const cardBody = el("div", "agent-avatar-body");
    cardBody.appendChild(el("div", "eyebrow", "Instinct agent"));
    cardBody.appendChild(el("h3", null, `${agent.species.toUpperCase()} · ${agent.lifeStage}`));
    cardBody.appendChild(el("p", null, `Goal: ${agent.goal}`));
    cardBody.appendChild(renderTraitBar(agent.traits.aggressiveness, "Aggressiveness"));
    cardBody.appendChild(renderTraitBar(agent.traits.friendliness, "Friendliness"));
    cardBody.appendChild(renderTraitBar(agent.traits.curiosity, "Curiosity"));
    cardBody.appendChild(renderTraitBar(agent.traits.bravery, "Bravery"));
    cardBody.appendChild(renderTraitBar(agent.traits.morality, "Morality"));
    card.appendChild(cardBody);
    avatar.appendChild(card);
    root.appendChild(avatar);

    const hud = el("section", "profile-section agent-tab-panel");
    hud.id = "agent-hud";
    hud.appendChild(el("h2", null, "Live HUD"));
    const hudGrid = el("div", "agent-hud-grid");
    Object.entries(agent.state).forEach(([key, value]) => {
      const box = el("div", "agent-hud-box");
      box.appendChild(el("span", "qf-label", key.replace(/_/g, " ")));
      box.appendChild(el("strong", "agent-hud-value", `${Math.round(value * 100)}%`));
      box.appendChild(renderPips(value, ""));
      hudGrid.appendChild(box);
    });
    hud.appendChild(hudGrid);
    const decision = el("div", "agent-decision-card");
    decision.innerHTML = `<h3>Decision bias</h3><p>Low threat, moderate hunger, good stamina: hold position or explore before committing to forage or hunt.</p>`;
    hud.appendChild(decision);
    root.appendChild(hud);

    const scene = el("section", "profile-section agent-tab-panel");
    scene.id = "agent-scene";
    scene.appendChild(el("h2", null, "Animated scene"));
    const stage = el("div", "agent-scene-stage");
    const sky = el("div", "agent-scene-sky");
    const ground = el("div", "agent-scene-ground");
    const dino = el("div", "agent-scene-dino");
    dino.innerHTML = `<div class="agent-scene-aurora"></div><div class="agent-scene-head"></div><div class="agent-scene-body"></div><div class="agent-scene-tail"></div>`;
    stage.appendChild(sky);
    stage.appendChild(ground);
    stage.appendChild(dino);
    scene.appendChild(stage);
    scene.appendChild(el("p", "muted", "A stylized motion scene for presentation slides — calm stance, alert head, subtle tail sway, and a clear silhouette."));
    root.appendChild(scene);

    const arch = el("section", "profile-section agent-tab-panel");
    arch.id = "agent-arch";
    arch.appendChild(el("h2", null, "Architecture"));
    const archGrid = el("div", "agent-arch-grid");
    const identityCard = el("div", "agent-arch-card");
    identityCard.appendChild(el("h3", null, AGENT_ARCHITECTURE.agent_name));
    identityCard.appendChild(el("p", null, AGENT_ARCHITECTURE.description));
    identityCard.appendChild(el("p", "muted", `Agent ID: ${AGENT_ARCHITECTURE.agent_id}`));
    identityCard.appendChild(el("p", "muted", `Conversation: ${AGENT_ARCHITECTURE.conversation_id}`));
    archGrid.appendChild(identityCard);

    const promptCard = el("div", "agent-arch-card");
    promptCard.appendChild(el("h3", null, "System prompt"));
    const promptList = el("ul", "agent-arch-list");
    AGENT_ARCHITECTURE.system_prompt.forEach((line) => promptList.appendChild(el("li", null, line)));
    promptCard.appendChild(promptList);
    archGrid.appendChild(promptCard);

    const toolsCard = el("div", "agent-arch-card");
    toolsCard.appendChild(el("h3", null, "Tools"));
    const toolsList = el("div", "agent-tool-cloud");
    AGENT_ARCHITECTURE.tools.forEach((tool) => toolsList.appendChild(el("span", "agent-tool-chip", tool)));
    toolsCard.appendChild(toolsList);
    archGrid.appendChild(toolsCard);

    const memoryCard = el("div", "agent-arch-card");
    memoryCard.appendChild(el("h3", null, "Memory blocks"));
    const memoryList = el("div", "agent-memory-list");
    AGENT_ARCHITECTURE.memory_blocks.forEach((m) => {
      const row = el("div", "agent-memory-row");
      row.appendChild(el("strong", null, `${m.name} · ${m.chars}/${m.limit}`));
      row.appendChild(el("p", null, m.summary));
      memoryList.appendChild(row);
    });
    memoryCard.appendChild(memoryList);
    archGrid.appendChild(memoryCard);

    const archiveCard = el("div", "agent-arch-card");
    archiveCard.appendChild(el("h3", null, "Archival memory"));
    const archiveList = el("ul", "agent-arch-list");
    AGENT_ARCHITECTURE.archival_memory.forEach((line) => archiveList.appendChild(el("li", null, line)));
    archiveCard.appendChild(archiveList);
    archGrid.appendChild(archiveCard);

    arch.appendChild(archGrid);
    root.appendChild(arch);

    const switcher = hero.querySelector(".agent-species-switcher");
    if (switcher) {
      switcher.addEventListener("click", (e) => {
        const btn = e.target.closest("button[data-species]");
        if (!btn) return;
        switcher.querySelectorAll("button").forEach((b) => b.classList.toggle("active", b === btn));
        const picked = AGENT_SPECIES_OPTIONS.find((x) => x.id === btn.dataset.species);
        if (!picked) return;
        cardBody.querySelector("h3").textContent = `${picked.label.toUpperCase()} · ${agent.lifeStage}`;
        cardBody.querySelectorAll("p")[0].textContent = `Goal: ${picked.role}`;
        decision.querySelector("p").textContent = `${picked.label} perspective: ${picked.note}`;
      });
    }

    return true;
  }

  function thIcon(label, iconClass) {
    const th = document.createElement("th");
    th.className = "th-stat-icon";
    th.title = label;
    th.innerHTML = `<i class="${iconClass}" aria-hidden="true"></i><span class="th-stat-lbl">${label}</span>`;
    return th;
  }

  async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      return true;
    } catch {
      try {
        const ta = document.createElement("textarea");
        ta.value = text;
        ta.style.position = "fixed";
        ta.style.left = "-9999px";
        document.body.appendChild(ta);
        ta.select();
        const ok = document.execCommand("copy");
        ta.remove();
        return ok;
      } catch {
        return false;
      }
    }
  }

  function wrapDetails(summaryText, innerNodes, open) {
    const det = document.createElement("details");
    det.className = "profile-details";
    if (open) det.open = true;
    const s = document.createElement("summary");
    s.textContent = summaryText;
    det.appendChild(s);
    const body = el("div", "profile-details-body");
    innerNodes.forEach((n) => body.appendChild(n));
    det.appendChild(body);
    return det;
  }

  async function fetchCurveText(url) {
    try {
      const r = await fetch(url, { cache: "no-cache" });
      return r.ok ? await r.text() : `HTTP ${r.status}`;
    } catch {
      return "Could not load file.";
    }
  }

  function openAbilityPicker(title, options, currentId, onPick) {
    const backdrop = el("div", "picker-backdrop");
    const modal = el("div", "picker-modal");
    modal.setAttribute("role", "dialog");
    modal.setAttribute("aria-modal", "true");
    modal.setAttribute("aria-label", title);
    modal.appendChild(el("h3", "picker-title", title));
    const grid = el("div", "picker-grid");
    const none = el("button", "picker-tile picker-clear", "Clear slot");
    none.type = "button";
    none.addEventListener("click", () => {
      onPick("");
      backdrop.remove();
    });
    grid.appendChild(none);
    options.forEach((ab) => {
      const b = el("button", "picker-tile");
      b.type = "button";
      if (ab.id === currentId) b.classList.add("picker-tile-active");
      if (ab.icon) {
        const img = document.createElement("img");
        img.src = ab.icon;
        img.alt = "";
        b.appendChild(img);
      }
      b.appendChild(el("span", "picker-tile-label", ab.name));
      b.addEventListener("click", () => {
        onPick(ab.id);
        backdrop.remove();
      });
      grid.appendChild(b);
    });
    modal.appendChild(grid);
    const close = el("button", "picker-close", "Close");
    close.type = "button";
    close.addEventListener("click", () => backdrop.remove());
    modal.appendChild(close);
    backdrop.addEventListener("click", (e) => {
      if (e.target === backdrop) backdrop.remove();
    });
    backdrop.appendChild(modal);
    document.body.appendChild(backdrop);
  }

  async function init() {
    root.classList.add("loading");
    if (slug === "agent-visual") {
      renderAgentVisualTab(root);
      root.classList.remove("loading");
      return;
    }

    let data;
    try {
      const res = await fetch(`data/${slug}.json`, { cache: "no-cache" });
      data = await res.json();
    } catch {
      root.innerHTML = `<div class="error-banner" role="alert">Could not load profile data for <code>${slug}</code>.</div>`;
      root.classList.remove("loading");
      return;
    }

    document.title = `${data.displayName} | PALEO Profiles`;

    const sections = [
      { id: "vitals", label: "Core vitals" },
      { id: "slots", label: "Ability slots" },
      { id: "description", label: "Description" },
      { id: "paleo", label: "Paleontology" },
      { id: "subspecies", label: "Subspecies" },
      { id: "abilities", label: "Abilities" },
      { id: "skins", label: "Skins" },
      { id: "gallery", label: "Gallery (in-game)" },
      { id: "trivia", label: "Trivia" },
      { id: "loadout", label: "Loadout lab" },
      { id: "skin-lab", label: "Pattern / colors" },
      { id: "curves", label: "Server curves" },
      { id: "sources", label: "Sources" },
    ];

    buildSubnav(sections);

    /* —— Hero —— */
    const top = el("section", "profile-top");
    const banner = el("div", "profile-hero-banner");
    banner.style.backgroundImage = `linear-gradient(180deg, rgba(7,9,14,0.88) 0%, transparent 38%, rgba(7,9,14,0.55) 100%), url(${JSON.stringify(data.heroImage)})`;
    top.appendChild(banner);
    if (data.heroImageCaption) {
      top.appendChild(el("p", "hero-caption-banner muted", `<small>${data.heroImageCaption}</small>`));
    }

    const heroMain = el("div", "profile-hero-below");
    heroMain.appendChild(el("div", "eyebrow", `${data.modTeam} · ${data.game}`));
    heroMain.appendChild(el("h1", "profile-title", data.displayName));
    heroMain.appendChild(el("p", "profile-intro", data.intro || data.description.gameplay));
    heroMain.appendChild(renderStarsBlock(data));

    const quick = el("div", "quick-facts");
    quick.innerHTML = `
      <div class="qf-item"><span class="qf-label">Nicknames</span><span class="qf-val">${data.nicknames.slice(0, 4).join(", ")}</span></div>
      <div class="qf-item"><span class="qf-label">Species flavors</span><span class="qf-val">${data.taxon.speciesEpithets.join(", ")}</span></div>
      <div class="qf-item"><span class="qf-label">Category</span><span class="qf-val">${data.classification.diet}</span></div>
    `;
    heroMain.appendChild(quick);

    const mid = data.modIdentifiers || {};
    const curvePh = (mid.curvePrefix || "").trim() || "—";
    const modId = (mid.modIdToCopy || "").trim();
    const metaRow = el("div", "hero-meta-row");
    const clsBox = el("div", "meta-block");
    clsBox.innerHTML = `<span class="qf-label">Class</span><span class="qf-val">${data.classification.class}</span>`;
    metaRow.appendChild(clsBox);
    const curveBox = el("div", "meta-block meta-curve");
    curveBox.innerHTML = `<span class="qf-label">Curve prefix</span><span class="qf-val font-mono">${curvePh}</span>`;
    metaRow.appendChild(curveBox);
    const copyWrap = el("div", "meta-copy");
    const copyBtn = el("button", "copy-mod-btn");
    copyBtn.type = "button";
    copyBtn.innerHTML = modId
      ? '<i class="fa-regular fa-copy" aria-hidden="true"></i> Copy mod ID'
      : '<i class="fa-regular fa-copy" aria-hidden="true"></i> Copy curve prefix';
    copyBtn.title =
      (mid.modIdHint || "").replace(/</g, "") || (modId ? "Copy mod / workshop identifier" : "No mod ID in JSON yet — copies curve prefix");
    const copyFlash = el("span", "copy-flash", "");
    copyWrap.appendChild(copyBtn);
    copyWrap.appendChild(copyFlash);
    copyBtn.addEventListener("click", async () => {
      const text = modId || (curvePh !== "—" ? curvePh : "");
      if (!text) return;
      const ok = await copyToClipboard(text);
      copyFlash.textContent = ok ? "Copied" : "Copy blocked";
      setTimeout(() => {
        copyFlash.textContent = "";
      }, 1600);
    });
    metaRow.appendChild(copyWrap);
    heroMain.appendChild(metaRow);

    const gs = data.classification.groupSlotSize;
    const groupBanner = el("div", "group-slot-hero");
    groupBanner.innerHTML = `<span class="gsl">Group slot size</span><span class="gsn">${gs}</span><span class="gsd">Players per group quota for this playable — critical for roster planning.</span>`;
    heroMain.appendChild(groupBanner);

    const modStrip = el("div", "mod-strip");
    modStrip.innerHTML = `<span class="mod-pill note">${(mid.workshopNote || "").replace(/</g, "&lt;")}</span>`;
    heroMain.appendChild(modStrip);

    top.appendChild(heroMain);
    root.appendChild(top);

    /* Core vitals */
    const vit = el("section", "profile-section");
    vit.id = "vitals";
    vit.appendChild(el("h2", null, "Core vitals"));
    vit.appendChild(el("p", "muted", data.curveTierNote || ""));
    const ca = data.coreAdult || {};
    const vitalGrid = el("div", "vital-cards");
    [
      ["Max health", ca.maxHealth],
      ["Max stamina", ca.maxStamina],
      ["Combat weight", ca.combatWeight],
      ["Armor", ca.armor],
      ["Max hunger", ca.maxHunger],
      ["Max thirst", ca.maxThirst],
      ["Carry capacity", ca.carryCapacity],
    ].forEach(([k, v]) => {
      const card = el("div", "vital-card");
      card.innerHTML = `<span class="vk">${k}</span><span class="vv">${statDisp(v)}</span>`;
      vitalGrid.appendChild(card);
    });
    vit.appendChild(vitalGrid);
    root.appendChild(vit);

    /* Slot layout */
    const sl = el("section", "profile-section");
    sl.id = "slots";
    sl.appendChild(el("h2", null, "Ability slots (layout)"));
    sl.appendChild(el("p", "muted", "Slot counts per region — similar to Fandom creature pages, shown as a horizontal strip."));
    const rail = el("div", "slot-layout-rail");
    (data.slotLayoutWiki || []).forEach((row) => {
      const cell = el("div", "slot-layout-cell");
      const c = row.count;
      cell.innerHTML = `<span class="sl-name">${row.slot}</span><span class="sl-count ${c ? "sl-has" : "sl-zero"}">${c}</span>`;
      rail.appendChild(cell);
    });
    sl.appendChild(rail);
    root.appendChild(sl);

    /* Description */
    const desc = el("section", "profile-section");
    desc.id = "description";
    desc.appendChild(el("h2", null, "Description"));
    desc.appendChild(el("p", "lead", data.description.gameplay));
    if (data.marksEconomy) {
      const m = data.marksEconomy;
      desc.appendChild(
        el(
          "p",
          "muted",
          `Marks economy (wiki estimate): skins ~<strong>${m.skinsTotalMarks.toLocaleString()}</strong> · abilities ~<strong>${m.abilitiesTotalMarks.toLocaleString()}</strong> · combined ~<strong>${m.combinedMarks.toLocaleString()}</strong>. ${m.source}`
        )
      );
    }
    root.appendChild(desc);

    /* Paleo */
    const paleo = data.paleontology;
    const paleoInner = [];
    paleoInner.push(el("p", "lead", paleo.summary));
    paleoInner.push(el("p", null, paleo.size));
    paleoInner.push(el("h3", null, "Fossil record"));
    paleoInner.push(el("p", null, paleo.fossilRecord));
    paleoInner.push(el("h3", null, "Further reading"));
    const refUl = document.createElement("ul");
    paleo.papers.forEach((p) => {
      const li = document.createElement("li");
      li.innerHTML = `<em>${p.cite}</em><br/><span class="muted">${p.note}</span>`;
      refUl.appendChild(li);
    });
    paleoInner.push(refUl);
    if (paleo.collections && paleo.collections.length) {
      paleoInner.push(el("h3", null, "Museums"));
      const cUl = document.createElement("ul");
      paleo.collections.forEach((t) => cUl.appendChild(el("li", null, t)));
      paleoInner.push(cUl);
    }
    const pm = (data.paleoMedia || []).map((im, i) => {
      const fig = document.createElement("figure");
      fig.className = "paleo-fig";
      const img = document.createElement("img");
      img.src = im.src;
      img.alt = im.caption || "";
      img.loading = "lazy";
      const cap = el("figcaption", null, `${im.caption}${im.credit ? ` — ${im.credit}` : ""}`);
      fig.appendChild(img);
      fig.appendChild(cap);
      return fig;
    });
    const paleoMediaBlock = wrapDetails("Paleontology images (real-world)", pm, false);
    paleoInner.push(paleoMediaBlock);
    const paleoSec = el("section", "profile-section");
    paleoSec.id = "paleo";
    paleoSec.appendChild(wrapDetails("Paleontology (real world)", paleoInner, false));
    root.appendChild(paleoSec);

    /* Subspecies */
    const subSec = el("section", "profile-section");
    subSec.id = "subspecies";
    subSec.appendChild(el("h2", null, "Subspecies & variants"));
    subSec.appendChild(el("p", "muted", data.taxon.note));
    const subGrid = el("div", "subspecies-grid");
    (data.subspecies || []).forEach((s) => {
      const card = el("article", "subspecies-card");
      const im = el("div", "subspecies-img");
      im.style.backgroundImage = `url(${JSON.stringify(s.image)})`;
      card.appendChild(im);
      card.appendChild(el("h3", null, s.label));
      card.appendChild(el("p", null, s.blurb));
      subGrid.appendChild(card);
    });
    subSec.appendChild(subGrid);
    root.appendChild(subSec);

    /* Abilities */
    const abSec = el("section", "profile-section");
    abSec.id = "abilities";
    abSec.appendChild(el("h2", null, "Abilities"));
    const ban = el("div", "curve-link-banner");
    ban.innerHTML = `<p><a href="${data.curvesOfficialUrl}" target="_blank" rel="noopener noreferrer" class="curve-official-link">Authoritative KTODeino curves on NexLink (updated host guide) →</a></p>
      <p class="muted">Numbers in-table are the <strong>5th growth index</strong> from that seed. Scroll to <strong>Server curves</strong> for pasteable <code>Game.ini</code> blocks for server owners.</p>`;
    abSec.appendChild(ban);
    const tbl = el("div", "table-wrap");
    const table = document.createElement("table");
    table.className = "profile-table abilities-table";
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    trh.appendChild(el("th", "th-abil-icon", ""));
    trh.appendChild(el("th", null, "Ability"));
    trh.appendChild(el("th", null, "Slot"));
    trh.appendChild(el("th", "th-desc", "Description"));
    trh.appendChild(thIcon("Marks", "fa-solid fa-coins"));
    trh.appendChild(thIcon("Damage", "fa-solid fa-crosshairs"));
    trh.appendChild(thIcon("Cooldown (s)", "fa-regular fa-clock"));
    trh.appendChild(thIcon("Stamina", "fa-solid fa-bolt"));
    trh.appendChild(thIcon("Bleed", "fa-solid fa-droplet"));
    trh.appendChild(thIcon("Bone-break %", "fa-solid fa-bone"));
    trh.appendChild(thIcon("Break amount", "fa-solid fa-arrow-up-right-dots"));
    trh.appendChild(thIcon("Speed", "fa-solid fa-gauge-high"));
    trh.appendChild(thIcon("Speed mult", "fa-solid fa-arrow-trend-up"));
    trh.appendChild(thIcon("Splinters", "fa-solid fa-shapes"));
    trh.appendChild(el("th", null, "Detail"));
    trh.appendChild(el("th", null, "Curves"));
    thead.appendChild(trh);
    table.appendChild(thead);
    const tb = document.createElement("tbody");
    (data.abilityTable || []).forEach((a) => {
      const tr = document.createElement("tr");
      const iconTd = document.createElement("td");
      if (a.icon) {
        const img = document.createElement("img");
        img.src = a.icon;
        img.className = "abil-icon";
        img.alt = "";
        iconTd.appendChild(img);
      } else iconTd.textContent = "—";
      tr.appendChild(iconTd);
      const nameTd = document.createElement("td");
      const sn = document.createElement("strong");
      sn.textContent = a.name;
      nameTd.appendChild(sn);
      tr.appendChild(nameTd);
      tr.appendChild(el("td", null, a.slot));
      tr.appendChild(el("td", null, a.description));
      tr.appendChild(el("td", "num", a.marks === 0 ? "Free" : String(a.marks)));
      const st = a.stats;
      if (st) {
        tr.appendChild(el("td", "num", statDisp(st.damage)));
        tr.appendChild(el("td", "num", statDisp(st.cooldown)));
        tr.appendChild(el("td", "num", statDisp(st.stamina)));
        tr.appendChild(el("td", "num", statDisp(st.bleed)));
        tr.appendChild(el("td", "num", statDisp(st.boneBreakChance)));
        tr.appendChild(el("td", "num", statDisp(st.boneBreakAmount)));
        tr.appendChild(el("td", "num", statDisp(st.speed)));
        tr.appendChild(el("td", "num", speedMultDisp(st.speedMultiplier)));
        tr.appendChild(el("td", "num", statDisp(st.splinter)));
        tr.appendChild(el("td", "abil-detail", st.detail || "—"));
      } else {
        for (let i = 0; i < 9; i++) tr.appendChild(el("td", "num", "—"));
        tr.appendChild(el("td", "abil-detail", "—"));
      }
      const ckTd = document.createElement("td");
      if (a.curveKeys && a.curveKeys.length) {
        const det = document.createElement("details");
        const sm = document.createElement("summary");
        sm.textContent = `${a.curveKeys.length} keys`;
        det.appendChild(sm);
        const pre = document.createElement("pre");
        pre.className = "curve-key-list";
        pre.textContent = a.curveKeys.join("\n");
        det.appendChild(pre);
        ckTd.appendChild(det);
      } else ckTd.textContent = "—";
      tr.appendChild(ckTd);
      tb.appendChild(tr);
    });
    table.appendChild(tb);
    tbl.appendChild(table);
    abSec.appendChild(tbl);
    root.appendChild(abSec);

    /* Skins showcase */
    const skSec = el("section", "profile-section");
    skSec.id = "skins";
    skSec.appendChild(el("h2", null, "Skins"));
    skSec.appendChild(el("p", "muted", "Visual board (Fandom-style). Images cycle generic PoT Steam shots until you add per-skin files under media/. Rarity border colors follow your spec."));
    const skGrid = el("div", "skin-showcase-grid");
    (data.skins || []).forEach((skin, i) => {
      const src = skin.image || skinFallbackSrc(data, i);
      const card = el("article", `skin-showcase-card ${rarityCss(skin.rarity)}`);
      const thumb = el("div", "skin-showcase-thumb");
      thumb.style.backgroundImage = `linear-gradient(180deg, transparent 50%, rgba(0,0,0,0.75)), url(${JSON.stringify(src)})`;
      card.appendChild(thumb);
      card.appendChild(el("span", "skin-rarity-tag", skin.rarity));
      card.appendChild(el("h3", "skin-showcase-name", skin.name));
      card.appendChild(el("p", "skin-showcase-marks", skin.marks === 0 ? "Free" : `${skin.marks.toLocaleString()} marks`));
      skGrid.appendChild(card);
    });
    skSec.appendChild(skGrid);
    root.appendChild(skSec);

    /* Gallery in-game */
    const gSec = el("section", "profile-section");
    gSec.id = "gallery";
    gSec.appendChild(el("h2", null, "Gallery (in-game / PoT)"));
    gSec.appendChild(el("p", "muted", "Real-world paleo art lives under Paleontology. This strip is for on-brand Path of Titans imagery — swap in your own KTO Deino captures via media/ + JSON."));
    const gg = el("div", "gallery-game-grid");
    (data.gameGallery || []).forEach((g) => {
      const fig = document.createElement("figure");
      fig.className = "gallery-game-item";
      const im = document.createElement("img");
      im.src = g.src;
      im.alt = g.caption || "";
      im.loading = "lazy";
      fig.appendChild(im);
      fig.appendChild(el("figcaption", null, g.caption));
      gg.appendChild(fig);
    });
    gSec.appendChild(gg);
    root.appendChild(gSec);

    /* Trivia */
    const trivBody = [];
    const ul = document.createElement("ul");
    (data.trivia || []).forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      ul.appendChild(li);
    });
    trivBody.push(ul);
    const trivSec = el("section", "profile-section");
    trivSec.id = "trivia";
    trivSec.appendChild(wrapDetails("Trivia", trivBody, false));
    root.appendChild(trivSec);

    /* Loadout lab */
    const loadoutBody = [];
    loadoutBody.push(
      el(
        "p",
        "muted",
        "Tap a slot tile, then choose an ability icon — matches horizontal slot thinking from in-game. Saved locally; export JSON to move presets."
      )
    );
    const slotConfig = data.loadoutSlotConfig || [];
    const loadoutRail = el("div", "loadout-rail");
    const selects = readJson(LS_LOADOUT, {});
    const tableAb = data.abilityTable || [];

    function optsForSlot(sc) {
      return tableAb.filter(
        (a) => a.loadoutGroup && sc.groups.some((g) => g === a.loadoutGroup)
      );
    }

    function refreshRail() {
      loadoutRail.innerHTML = "";
      slotConfig.forEach((sc) => {
        const idSel = selects[sc.id] || "";
        const ab = tableAb.find((x) => x.id === idSel);
        const tile = el("button", "loadout-slot-tile");
        tile.type = "button";
        if (ab && ab.icon) {
          const img = document.createElement("img");
          img.src = ab.icon;
          img.alt = "";
          tile.appendChild(img);
        } else tile.appendChild(el("span", "loadout-slot-empty", "+"));
        tile.appendChild(el("span", "loadout-slot-label", sc.label));
        const opts = optsForSlot(sc);
        tile.addEventListener("click", () =>
          openAbilityPicker(sc.label, opts, idSel, (picked) => {
            selects[sc.id] = picked;
            writeJson(LS_LOADOUT, selects);
            refreshRail();
          })
        );
        loadoutRail.appendChild(tile);
      });
    }
    refreshRail();
    loadoutBody.push(loadoutRail);

    const actions = el("div", "loadout-actions");
    const saveBtn = el("button", "primary", "Save loadout");
    saveBtn.type = "button";
    const clr = el("button", null, "Clear all");
    clr.type = "button";
    const ex = el("button", null, "Export JSON");
    ex.type = "button";
    const imBtn = el("button", null, "Import…");
    imBtn.type = "button";
    const file = document.createElement("input");
    file.type = "file";
    file.accept = "application/json";
    file.style.display = "none";
    saveBtn.addEventListener("click", () => writeJson(LS_LOADOUT, selects));
    clr.addEventListener("click", () => {
      slotConfig.forEach((sc) => {
        selects[sc.id] = "";
      });
      writeJson(LS_LOADOUT, selects);
      refreshRail();
    });
    ex.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(selects, null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `paleo-loadout-${slug}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    });
    imBtn.addEventListener("click", () => file.click());
    file.addEventListener("change", () => {
      const f = file.files && file.files[0];
      if (!f) return;
      const r = new FileReader();
      r.onload = () => {
        try {
          Object.assign(selects, JSON.parse(String(r.result)));
          writeJson(LS_LOADOUT, selects);
          refreshRail();
        } catch { /* ignore */ }
      };
      r.readAsText(f);
      file.value = "";
    });
    actions.appendChild(saveBtn);
    actions.appendChild(clr);
    actions.appendChild(ex);
    actions.appendChild(imBtn);
    actions.appendChild(file);
    loadoutBody.push(actions);

    const presetRow = el("div", "loadout-presets");
    const pname = document.createElement("input");
    pname.type = "text";
    pname.placeholder = "Preset name";
    pname.className = "preset-input";
    const psave = el("button", "primary", "Save preset");
    psave.type = "button";
    const psel = document.createElement("select");
    psel.className = "preset-select";
    function refPreset() {
      const pr = readJson(LS_PRESETS, {});
      psel.innerHTML = "";
      psel.appendChild(new Option("Load preset…", ""));
      Object.keys(pr).forEach((k) => psel.appendChild(new Option(k, k)));
    }
    refPreset();
    psave.addEventListener("click", () => {
      const n = (pname.value || "").trim();
      if (!n) return;
      const pr = readJson(LS_PRESETS, {});
      pr[n] = { ...selects };
      writeJson(LS_PRESETS, pr);
      refPreset();
    });
    psel.addEventListener("change", () => {
      const n = psel.value;
      if (!n) return;
      const pr = readJson(LS_PRESETS, {});
      if (pr[n]) Object.assign(selects, pr[n]);
      writeJson(LS_LOADOUT, selects);
      refreshRail();
      psel.value = "";
    });
    presetRow.appendChild(pname);
    presetRow.appendChild(psave);
    presetRow.appendChild(psel);
    loadoutBody.push(presetRow);

    const loadSec = el("section", "profile-section");
    loadSec.id = "loadout";
    loadSec.appendChild(wrapDetails("Loadout lab (visual slots)", loadoutBody, false));
    root.appendChild(loadSec);

    /* Skin color lab */
    const labBody = [];
    labBody.push(
      el("p", "muted", "Pick a skin from the list (placeholder art uses the same shots as the skin board until you add per-skin files). Toggle sex, then click swatches per region to cycle palette indices (0–5). Values save per skin.")
    );
    const pickerRow = el("div", "skin-lab-picker-row");
    const skinLabSelect = document.createElement("select");
    skinLabSelect.className = "skin-lab-select";
    skinLabSelect.setAttribute("aria-label", "Skin to edit");
    (data.skins || []).forEach((skin, i) => {
      skinLabSelect.appendChild(new Option(`${skin.name} (${skin.rarity})`, String(i)));
    });
    let skinLabIdx = Number(readJson(LS_SKIN_LAB, 0)) || 0;
    if (skinLabIdx < 0 || skinLabIdx >= (data.skins || []).length) skinLabIdx = 0;
    skinLabSelect.value = String(skinLabIdx);
    skinLabSelect.addEventListener("change", () => {
      writeJson(LS_SKIN_LAB, Number(skinLabSelect.value) || 0);
      renderSkinLab();
    });
    const labPreview = el("div", "skin-lab-preview");
    labPreview.appendChild(el("span", "skin-lab-preview-rarity", ""));
    labPreview.appendChild(el("span", "skin-lab-preview-name", ""));
    pickerRow.appendChild(skinLabSelect);
    pickerRow.appendChild(labPreview);
    labBody.push(pickerRow);

    const genderRow = el("div", "gender-toggle");
    let gender = readJson(LS_GENDER, "male");
    const maleB = el("button", gender === "male" ? "gender-btn active" : "gender-btn", "Male");
    const femB = el("button", gender === "female" ? "gender-btn active" : "gender-btn", "Female");
    maleB.type = "button";
    femB.type = "button";
    maleB.addEventListener("click", () => {
      gender = "male";
      writeJson(LS_GENDER, "male");
      maleB.classList.add("active");
      femB.classList.remove("active");
      renderSkinLab();
    });
    femB.addEventListener("click", () => {
      gender = "female";
      writeJson(LS_GENDER, "female");
      femB.classList.add("active");
      maleB.classList.remove("active");
      renderSkinLab();
    });
    genderRow.appendChild(maleB);
    genderRow.appendChild(femB);
    labBody.push(genderRow);

    const labHost = el("div", "skin-lab-host");
    labBody.push(labHost);

    function paletteState() {
      return readJson(LS_PALETTE, {});
    }

    function renderSkinLab() {
      labHost.innerHTML = "";
      const skins = data.skins || [];
      let idx = Number(skinLabSelect.value) || 0;
      if (idx < 0 || idx >= skins.length) idx = 0;
      const skin = skins[idx];
      if (!skin) return;

      const src = skin.image || skinFallbackSrc(data, idx);
      labPreview.style.backgroundImage = `linear-gradient(180deg, transparent 35%, rgba(0,0,0,0.82)), url(${JSON.stringify(src)})`;
      labPreview.className = `skin-lab-preview ${rarityCss(skin.rarity)}`;
      labPreview.querySelector(".skin-lab-preview-rarity").textContent = skin.rarity;
      labPreview.querySelector(".skin-lab-preview-name").textContent = skin.name;

      const state = paletteState();
      const regions = data.colorRegions || ["Head", "Body", "Pattern", "Accents"];
      const card = el("div", "skin-lab-card");
      const sub = el("p", "skin-lab-sub", skin.marks === 0 ? "Free" : `${skin.marks.toLocaleString()} marks`);
      card.appendChild(sub);
      const inner = el("div", "skin-lab-regions");
      regions.forEach((reg) => {
        const row = el("div", "region-row");
        row.appendChild(el("span", "region-name", reg));
        const sw = el("div", "region-swatches");
        const gk = gender === "male" ? "male" : "female";
        if (!state[skin.id]) state[skin.id] = { male: {}, female: {} };
        const pidx = state[skin.id][gk][reg] || 0;
        for (let k = 0; k < 6; k++) {
          const b = el("button", `swatch swatch-${k} ${k === pidx ? "swatch-on" : ""}`);
          b.type = "button";
          b.title = `Palette ${k}`;
          b.addEventListener("click", () => {
            const st = paletteState();
            if (!st[skin.id]) st[skin.id] = { male: {}, female: {} };
            st[skin.id][gk][reg] = k;
            writeJson(LS_PALETTE, st);
            renderSkinLab();
          });
          sw.appendChild(b);
        }
        row.appendChild(sw);
        inner.appendChild(row);
      });
      card.appendChild(inner);
      labHost.appendChild(card);
    }
    renderSkinLab();
    const labSec = el("section", "profile-section");
    labSec.id = "skin-lab";
    labSec.appendChild(wrapDetails("Pattern / color lab", labBody, false));
    root.appendChild(labSec);

    /* Curves */
    const curveBody = [];
    curveBody.push(
      el(
        "p",
        "muted",
        "Raw blocks copied from the NexLink KTO guide — convenient for server hosts pasting into INI (with the documented prefix)."
      )
    );
    const curvePanel = el("div", "panel curve-paste-panel");
    const curveFiles = [
      { label: "Attributes (Core.*)", file: `data/${slug}-curves-attributes.txt`, open: true },
      { label: "Multipliers", file: `data/${slug}-curves-multipliers.txt`, open: false },
      { label: "Combat", file: `data/${slug}-curves-combat.txt`, open: false },
    ];
    curveFiles.forEach((cf) => {
      const det = document.createElement("details");
      if (cf.open) det.open = true;
      const sm = document.createElement("summary");
      sm.textContent = cf.label;
      const pre = el("pre", "curve-dump", "Loading…");
      det.appendChild(sm);
      det.appendChild(pre);
      curvePanel.appendChild(det);
      fetchCurveText(cf.file).then((t) => {
        pre.textContent = t;
      });
    });
    curveBody.push(curvePanel);
    const curSec = el("section", "profile-section");
    curSec.id = "curves";
    curSec.appendChild(wrapDetails("Server curves (pasteable)", curveBody, false));
    root.appendChild(curSec);

    /* Sources */
    const srcSec = el("section", "profile-section");
    srcSec.id = "sources";
    srcSec.appendChild(el("h2", null, "Data sources"));
    const prov = data.dataProvenance;
    srcSec.appendChild(
      el(
        "div",
        "panel",
        `<p class="muted">Pass: <strong>${prov.lastContentPass}</strong>. ${prov.disclaimer}</p><p>${prov.curveNote}</p>`
      )
    );
    const su = document.createElement("ul");
    su.className = "sources-list";
    (data.wikiLinks || []).forEach((link) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = link.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = link.label;
      li.appendChild(a);
      su.appendChild(li);
    });
    srcSec.appendChild(su);
    root.appendChild(srcSec);

    root.classList.remove("loading");
  }

  init();
})();
