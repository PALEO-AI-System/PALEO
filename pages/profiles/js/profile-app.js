/**
 * PALEO Profiles — single-creature page renderer + loadout / skin note persistence.
 */
(function () {
  "use strict";

  const slug = document.body.dataset.slug;
  if (!slug) return;

  const root = document.getElementById("profile-root");
  const LS_LOADOUT = `paleo-profiles:v1:loadout:${slug}`;
  const LS_SKINS = `paleo-profiles:v1:skin-notes:${slug}`;
  const LS_PRESETS = `paleo-profiles:v1:loadout-presets:${slug}`;

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

  function renderTable(title, rows, stageLabels) {
    const wrap = el("div", "table-wrap");
    const t = document.createElement("table");
    t.className = "profile-table";
    const thead = document.createElement("thead");
    const hr = document.createElement("tr");
    hr.appendChild(el("th", null, "Curve / key"));
    stageLabels.forEach((lbl) => hr.appendChild(el("th", null, lbl)));
    thead.appendChild(hr);
    t.appendChild(thead);
    const tb = document.createElement("tbody");
    rows.forEach((row) => {
      const tr = document.createElement("tr");
      tr.appendChild(el("td", null, row.key));
      row.values.forEach((v) => tr.appendChild(el("td", "num", String(v))));
      tb.appendChild(tr);
    });
    t.appendChild(tb);
    wrap.appendChild(t);
    return wrap;
  }

  function combatRowsForAbility(ability, combatHighlight) {
    if (!ability.curveKeys || !ability.curveKeys.length) return null;
    const byKey = Object.fromEntries(combatHighlight.map((r) => [r.key, r.values]));
    const rows = [];
    ability.curveKeys.forEach((key) => {
      if (byKey[key]) rows.push({ key, values: byKey[key] });
    });
    return rows.length ? rows : null;
  }

  async function init() {
    root.classList.add("loading");
    let data;
    try {
      const res = await fetch(`data/${slug}.json`, { cache: "no-cache" });
      data = await res.json();
    } catch (e) {
      root.innerHTML = `<div class="error-banner" role="alert">Could not load profile data for <code>${slug}</code>.</div>`;
      root.classList.remove("loading");
      return;
    }

    document.title = `${data.displayName} | PALEO Profiles`;

    /* Hero */
    const hero = el("section", "profile-hero");
    const vis = el("div", "profile-hero-visual");
    vis.style.backgroundImage = `linear-gradient(145deg, rgba(0,0,0,0.45), transparent), url(${JSON.stringify(data.heroImage)})`;
    const heroText = el("div", "profile-hero-text");
    heroText.appendChild(el("div", "eyebrow", `${data.modTeam} · ${data.game}`));
    heroText.appendChild(el("h1", null, data.displayName));
    heroText.appendChild(el("p", "lead", data.subtitle));
    const chips = el("div", "stat-chips");
    chips.appendChild(el("span", "stat-chip", data.classification.diet));
    chips.appendChild(el("span", "stat-chip", data.classification.class));
    chips.appendChild(el("span", "stat-chip", `Group slot ${data.classification.groupSlotSize}`));
    chips.appendChild(el("span", "stat-chip", `Curve: ${data.curveNamePrefix}`));
    heroText.appendChild(chips);
    heroText.appendChild(renderStarsBlock(data));
    const cap = el("p", "muted", `<small>${data.heroImageCaption || ""}</small>`);
    heroText.appendChild(cap);
    hero.appendChild(vis);
    hero.appendChild(heroText);
    root.appendChild(hero);

    /* Overview */
    root.appendChild(el("h2", null, "Overview"));
    root.appendChild(el("p", "lead", data.description.gameplay));
    const nick = el("p", null, `<strong>Nicknames:</strong> ${data.nicknames.join(", ")}`);
    root.appendChild(nick);
    const tax = el("div", "panel");
    tax.innerHTML = `<h3>Taxon & subspecies flavors</h3><p>${data.taxon.note}</p><ul>${data.taxon.speciesEpithets.map((s) => `<li>${s}</li>`).join("")}</ul>`;
    root.appendChild(tax);

    /* Marks economy */
    if (data.marksEconomy) {
      const m = data.marksEconomy;
      const p = el("div", "panel");
      p.innerHTML = `<h3>Marks economy (wiki-sourced estimate)</h3>
        <p>Skins total ~<strong>${m.skinsTotalMarks.toLocaleString()}</strong> · Abilities ~<strong>${m.abilitiesTotalMarks.toLocaleString()}</strong> · Combined ~<strong>${m.combinedMarks.toLocaleString()}</strong>.</p>
        <p class="muted"><small>${m.source}</small></p>`;
      root.appendChild(p);
    }

    /* Trivia */
    root.appendChild(el("h2", null, "Trivia"));
    const ul = document.createElement("ul");
    data.trivia.forEach((t) => {
      const li = document.createElement("li");
      li.textContent = t;
      ul.appendChild(li);
    });
    root.appendChild(ul);

    /* Abilities */
    root.appendChild(el("h2", null, "Abilities"));
    const abWrap = el("div", "table-wrap");
    const abTbl = document.createElement("table");
    abTbl.className = "profile-table";
    abTbl.innerHTML = `<thead><tr><th>Slot</th><th></th><th>Ability</th><th>Description</th><th>Marks</th></tr></thead>`;
    const abBody = document.createElement("tbody");
    data.abilities.forEach((a) => {
      const tr = document.createElement("tr");
      tr.appendChild(el("td", null, a.slot));
      const ic = document.createElement("td");
      if (a.icon) {
        const img = document.createElement("img");
        img.className = "icon-inline";
        img.src = a.icon;
        img.alt = "";
        img.width = 28;
        img.height = 28;
        img.loading = "lazy";
        ic.appendChild(img);
      } else ic.textContent = "—";
      tr.appendChild(ic);
      const nameTd = document.createElement("td");
      nameTd.innerHTML = `<strong>${a.name}</strong>${a.curveKeys && a.curveKeys.length ? `<br/><small class="muted">Curves: ${a.curveKeys.join(", ")}</small>` : ""}`;
      tr.appendChild(nameTd);
      tr.appendChild(el("td", null, a.description));
      tr.appendChild(el("td", "num", a.costMarks === 0 ? "Free" : String(a.costMarks)));
      abBody.appendChild(tr);
    });
    abTbl.appendChild(abBody);
    abWrap.appendChild(abTbl);
    root.appendChild(abWrap);

    if (data.abilitySlotsEmpty && data.abilitySlotsEmpty.length) {
      root.appendChild(el("p", "muted", `Empty slot groups in wiki layout: ${data.abilitySlotsEmpty.join(", ")}.`));
    }

    root.appendChild(el("h3", null, "Combat curve samples (highlights)"));
    root.appendChild(el("p", "muted", data.growthStageCaption));
    root.appendChild(
      renderTable("Combat", data.combatCurveHighlight, data.growthStageLabels)
    );
    root.appendChild(el("h3", null, "Ability ↔ numbers (per growth index)"));
    data.abilities.forEach((a) => {
      const rows = combatRowsForAbility(a, data.combatCurveHighlight);
      if (!rows) return;
      root.appendChild(el("h4", null, a.name));
      root.appendChild(renderTable(a.name, rows, data.growthStageLabels));
    });

    /* Core highlights */
    root.appendChild(el("h2", null, "Core stats (curve highlights)"));
    root.appendChild(renderTable("Core", data.coreCurveHighlight, data.growthStageLabels));

    /* Loadout builder */
    root.appendChild(el("h2", null, "Loadout lab"));
    root.appendChild(
      el(
        "p",
        "muted",
        "Pick abilities per slot group. Saved in your browser only (localStorage). Export/import JSON to move between machines."
      )
    );
    const loadoutPanel = el("div", "panel");
    const slotConfig = [
      { id: "head1", label: "Head — primary", slotFilter: "Head" },
      { id: "head2", label: "Head — secondary", slotFilter: "Head" },
      { id: "metabolism", label: "Metabolism", slotFilter: "Metabolism" },
      { id: "hide", label: "Hide", slotFilter: "Hide" },
      { id: "back1", label: "Back limb — primary", slotFilter: "Back Limb" },
      { id: "back2", label: "Back limb — secondary", slotFilter: "Back Limb" },
      { id: "tail", label: "Tail", slotFilter: "Tail" },
    ];
    const bySlot = (s) => data.abilities.filter((a) => a.slot === s);
    const loadoutGrid = el("div", "loadout-grid");
    const selects = {};
    const saved = readJson(LS_LOADOUT, {});
    slotConfig.forEach((sc) => {
      const field = el("div", "loadout-field");
      field.appendChild(el("label", null, sc.label));
      const sel = document.createElement("select");
      sel.id = `loadout-${sc.id}`;
      const none = document.createElement("option");
      none.value = "";
      none.textContent = "— None —";
      sel.appendChild(none);
      bySlot(sc.slotFilter).forEach((a) => {
        const o = document.createElement("option");
        o.value = slugify(a.name);
        o.textContent = `${a.name} (${a.costMarks === 0 ? "Free" : a.costMarks + " marks"})`;
        sel.appendChild(o);
      });
      if (saved[sc.id]) sel.value = saved[sc.id];
      selects[sc.id] = sel;
      field.appendChild(sel);
      loadoutGrid.appendChild(field);
    });
    loadoutPanel.appendChild(loadoutGrid);

    const loadoutActions = el("div", "loadout-actions");
    const saveBtn = document.createElement("button");
    saveBtn.className = "primary";
    saveBtn.textContent = "Save loadout";
    const resetBtn = document.createElement("button");
    resetBtn.textContent = "Clear";
    const exportBtn = document.createElement("button");
    exportBtn.textContent = "Export JSON";
    const importBtn = document.createElement("button");
    importBtn.textContent = "Import JSON…";
    const importFile = document.createElement("input");
    importFile.type = "file";
    importFile.accept = "application/json";
    importFile.style.display = "none";

    const presetName = document.createElement("input");
    presetName.type = "text";
    presetName.placeholder = "Preset name (e.g. water ambush)";
    presetName.setAttribute("aria-label", "Preset name");
    presetName.style.marginTop = "10px";
    presetName.style.width = "100%";
    presetName.style.maxWidth = "280px";
    presetName.style.padding = "8px 10px";
    presetName.style.borderRadius = "8px";
    presetName.style.border = "1px solid var(--line)";
    presetName.style.background = "var(--bg-deep)";
    presetName.style.color = "var(--ink)";

    const savePresetBtn = document.createElement("button");
    savePresetBtn.className = "primary";
    savePresetBtn.type = "button";
    savePresetBtn.textContent = "Save as named preset";
    savePresetBtn.style.marginTop = "8px";

    const presetSelect = document.createElement("select");
    presetSelect.setAttribute("aria-label", "Load named preset");
    presetSelect.style.marginTop = "8px";
    presetSelect.style.display = "block";
    presetSelect.style.minWidth = "220px";
    presetSelect.style.padding = "8px 10px";

    const status = el("p", "loadout-status", "");

    function currentLoadoutObj() {
      const o = {};
      slotConfig.forEach((sc) => {
        o[sc.id] = selects[sc.id].value;
      });
      return o;
    }

    function applyLoadoutObj(o) {
      slotConfig.forEach((sc) => {
        if (Object.prototype.hasOwnProperty.call(o, sc.id)) selects[sc.id].value = o[sc.id] || "";
      });
    }

    function refreshPresetsDropdown() {
      const presets = readJson(LS_PRESETS, {});
      presetSelect.innerHTML = "";
      presetSelect.appendChild(new Option("— Load preset —", ""));
      Object.keys(presets).forEach((name) => {
        presetSelect.appendChild(new Option(name, name));
      });
    }

    saveBtn.addEventListener("click", () => {
      writeJson(LS_LOADOUT, currentLoadoutObj());
      status.textContent = "Loadout saved to this browser.";
    });
    resetBtn.addEventListener("click", () => {
      slotConfig.forEach((sc) => {
        selects[sc.id].value = "";
      });
      writeJson(LS_LOADOUT, currentLoadoutObj());
      status.textContent = "Loadout cleared.";
    });
    exportBtn.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(currentLoadoutObj(), null, 2)], { type: "application/json" });
      const a = document.createElement("a");
      a.href = URL.createObjectURL(blob);
      a.download = `paleo-loadout-${slug}.json`;
      a.click();
      URL.revokeObjectURL(a.href);
    });
    importBtn.addEventListener("click", () => importFile.click());
    importFile.addEventListener("change", () => {
      const f = importFile.files && importFile.files[0];
      if (!f) return;
      const reader = new FileReader();
      reader.onload = () => {
        try {
          applyLoadoutObj(JSON.parse(String(reader.result)));
          writeJson(LS_LOADOUT, currentLoadoutObj());
          status.textContent = "Imported loadout applied.";
        } catch {
          status.textContent = "Import failed (invalid JSON).";
        }
      };
      reader.readAsText(f);
      importFile.value = "";
    });
    savePresetBtn.addEventListener("click", () => {
      const name = (presetName.value || "").trim();
      if (!name) {
        status.textContent = "Enter a preset name first.";
        return;
      }
      const presets = readJson(LS_PRESETS, {});
      presets[name] = currentLoadoutObj();
      writeJson(LS_PRESETS, presets);
      refreshPresetsDropdown();
      status.textContent = `Preset “${name}” saved.`;
    });
    presetSelect.addEventListener("change", () => {
      const name = presetSelect.value;
      if (!name) return;
      const presets = readJson(LS_PRESETS, {});
      if (presets[name]) applyLoadoutObj(presets[name]);
      presetSelect.value = "";
      status.textContent = `Loaded preset “${name}”.`;
    });

    loadoutActions.appendChild(saveBtn);
    loadoutActions.appendChild(resetBtn);
    loadoutActions.appendChild(exportBtn);
    loadoutActions.appendChild(importBtn);
    loadoutActions.appendChild(importFile);
    loadoutPanel.appendChild(loadoutActions);
    loadoutPanel.appendChild(el("p", "muted", "Named presets (stay in this browser unless you export)."));
    loadoutPanel.appendChild(presetName);
    loadoutPanel.appendChild(document.createElement("br"));
    loadoutPanel.appendChild(savePresetBtn);
    loadoutPanel.appendChild(presetSelect);
    refreshPresetsDropdown();
    loadoutPanel.appendChild(status);
    root.appendChild(loadoutPanel);

    /* Skins */
    root.appendChild(el("h2", null, "Skins & pattern notes"));
    root.appendChild(
      el(
        "p",
        "muted",
        "Note your favorite color regions / sliders per skin. Stored locally only."
      )
    );
    const skinGrid = el("div", "skin-grid");
    const skinNotesState = readJson(LS_SKINS, {});
    data.skins.forEach((skin) => {
      const card = el("article", "skin-card");
      card.appendChild(el("h4", null, skin.name));
      card.appendChild(
        el(
          "p",
          "muted",
          `<small>${skin.rarity} · ${skin.marks === 0 ? "Free" : skin.marks.toLocaleString() + " marks"}</small>`
        )
      );
      const notes = el("div", "skin-notes");
      notes.appendChild(el("label", null, "My color notes"));
      const ta = document.createElement("textarea");
      ta.dataset.skinId = skin.id;
      ta.value = skinNotesState[skin.id] || "";
      const btn = document.createElement("button");
      btn.type = "button";
      btn.textContent = "Save notes";
      btn.addEventListener("click", () => {
        const st = readJson(LS_SKINS, {});
        st[skin.id] = ta.value;
        writeJson(LS_SKINS, st);
        const prev = btn.textContent;
        btn.textContent = "Saved";
        setTimeout(() => {
          btn.textContent = prev;
        }, 1200);
      });
      notes.appendChild(ta);
      notes.appendChild(btn);
      card.appendChild(notes);
      skinGrid.appendChild(card);
    });
    root.appendChild(skinGrid);

    /* Curve dumps */
    root.appendChild(el("h2", null, "Server curves (full NexLink seed)"));
    root.appendChild(
      el(
        "p",
        "muted",
        `Paste into <code>Game.ini</code> only with the host prefix documented on NexLink. Curve prefix: <code>${data.curveNamePrefix}.</code>`
      )
    );
    const curvePanel = el("div", "panel");
    curvePanel.style.padding = "12px 16px 16px";

    async function fillPre(pre, url) {
      try {
        const r = await fetch(url, { cache: "no-cache" });
        pre.textContent = r.ok ? await r.text() : `HTTP ${r.status} for ${url}`;
      } catch {
        pre.textContent = `Could not load ${url}`;
      }
    }

    const curveFiles = [
      { label: "Attributes (Core.*)", file: `data/${slug}-curves-attributes.txt`, open: true },
      { label: "Multipliers", file: `data/${slug}-curves-multipliers.txt`, open: false },
      { label: "Combat", file: `data/${slug}-curves-combat.txt`, open: false },
    ];
    curveFiles.forEach((cf) => {
      const det = document.createElement("details");
      if (cf.open) det.open = true;
      const summ = document.createElement("summary");
      summ.textContent = cf.label;
      summ.style.cursor = "pointer";
      summ.style.fontWeight = "600";
      const pre = el("pre", "curve-dump", "Loading…");
      det.appendChild(summ);
      det.appendChild(pre);
      curvePanel.appendChild(det);
      fillPre(pre, cf.file);
    });
    root.appendChild(curvePanel);

    /* Paleontology */
    root.appendChild(el("h2", null, "Paleontology (real world)"));
    const paleo = data.paleontology;
    root.appendChild(el("p", "lead", paleo.summary));
    root.appendChild(el("p", null, paleo.size));
    root.appendChild(el("h3", null, "Fossil record"));
    root.appendChild(el("p", null, paleo.fossilRecord));
    root.appendChild(el("h3", null, "Further reading"));
    const refUl = document.createElement("ul");
    paleo.papers.forEach((p) => {
      const li = document.createElement("li");
      li.innerHTML = `<em>${p.cite}</em><br/><span class="muted">${p.note}</span>`;
      refUl.appendChild(li);
    });
    root.appendChild(refUl);
    if (paleo.collections && paleo.collections.length) {
      root.appendChild(el("h3", null, "Museums & exhibits"));
      const cUl = document.createElement("ul");
      paleo.collections.forEach((c) => cUl.appendChild(el("li", null, c)));
      root.appendChild(cUl);
    }

    /* Gallery */
    if (data.gallery && data.gallery.length) {
      root.appendChild(el("h2", null, "Gallery"));
      const ggrid = el("div", "gallery-grid");
      data.gallery.forEach((g) => {
        const fig = document.createElement("figure");
        fig.className = "gallery-item";
        const img = document.createElement("img");
        img.src = g.src;
        img.alt = g.alt || "";
        img.loading = "lazy";
        const cap = document.createElement("figcaption");
        cap.textContent = g.caption || "";
        fig.appendChild(img);
        fig.appendChild(cap);
        ggrid.appendChild(fig);
      });
      root.appendChild(ggrid);
    }

    /* Sources & provenance */
    root.appendChild(el("h2", null, "Data sources"));
    const prov = data.dataProvenance;
    const provPanel = el("div", "panel");
    provPanel.innerHTML = `<p class="muted">Last content pass: <strong>${prov.lastContentPass}</strong>. ${prov.disclaimer}</p>
      <p>Seeded from:</p>
      <ul class="sources-list">${prov.seededFrom.map((s) => `<li>${s}</li>`).join("")}</ul>
      <p class="muted">${prov.curveNote}</p>`;
    root.appendChild(provPanel);
    const srcUl = document.createElement("ul");
    srcUl.className = "sources-list";
    data.wikiLinks.forEach((link) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = link.url;
      a.target = "_blank";
      a.rel = "noopener noreferrer";
      a.textContent = link.label;
      li.appendChild(a);
      srcUl.appendChild(li);
    });
    root.appendChild(srcUl);

    root.classList.remove("loading");
  }

  init();
})();
