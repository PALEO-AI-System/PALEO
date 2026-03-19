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

  function buildToc(sections) {
    const nav = el("nav", "profile-toc");
    nav.setAttribute("aria-label", "On this page");
    nav.appendChild(el("h2", "toc-title", "Contents"));
    const ul = document.createElement("ul");
    sections.forEach(({ id, label }) => {
      const li = document.createElement("li");
      const a = document.createElement("a");
      a.href = `#${id}`;
      a.textContent = label;
      li.appendChild(a);
      ul.appendChild(li);
    });
    nav.appendChild(ul);
    return nav;
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

    root.appendChild(buildToc(sections));

    /* —— Hero —— */
    const top = el("section", "profile-top");
    const split = el("div", "profile-hero-split");
    const vis = el("div", "profile-hero-visual");
    vis.style.backgroundImage = `linear-gradient(145deg, rgba(0,0,0,0.5), transparent), url(${JSON.stringify(data.heroImage)})`;
    const heroMain = el("div", "profile-hero-main");
    heroMain.appendChild(el("div", "eyebrow", `${data.modTeam} · ${data.game}`));
    heroMain.appendChild(el("h1", "profile-title", data.displayName));
    heroMain.appendChild(el("p", "profile-intro", data.intro || data.description.gameplay));
    const quick = el("div", "quick-facts");
    quick.innerHTML = `
      <div class="qf-item"><span class="qf-label">Nicknames</span><span class="qf-val">${data.nicknames.slice(0, 4).join(", ")}</span></div>
      <div class="qf-item"><span class="qf-label">Species flavors</span><span class="qf-val">${data.taxon.speciesEpithets.join(", ")}</span></div>
      <div class="qf-item"><span class="qf-label">Category</span><span class="qf-val">${data.classification.diet}</span></div>
      <div class="qf-item"><span class="qf-label">Class</span><span class="qf-val">${data.classification.class}</span></div>
    `;
    heroMain.appendChild(quick);

    const gs = data.classification.groupSlotSize;
    const groupBanner = el("div", "group-slot-hero");
    groupBanner.innerHTML = `<span class="gsl">Group slot size</span><span class="gsn">${gs}</span><span class="gsd">Players per group quota for this playable — critical for roster planning.</span>`;
    heroMain.appendChild(groupBanner);

    const modStrip = el("div", "mod-strip");
    const mid = data.modIdentifiers || {};
    modStrip.innerHTML = `<span class="mod-pill"><strong>Curve prefix</strong> ${mid.curvePrefix || "—"}</span>
      <span class="mod-pill"><strong>Internal key</strong> ${mid.internalKey || "—"}</span>
      <span class="mod-pill note">${(mid.workshopNote || "").replace(/</g, "&lt;")}</span>`;
    heroMain.appendChild(modStrip);

    heroMain.appendChild(el("p", "hero-caption muted", `<small>${data.heroImageCaption || ""}</small>`));
    heroMain.appendChild(renderStarsBlock(data));
    split.appendChild(vis);
    split.appendChild(heroMain);
    top.appendChild(split);
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
    paleoSec.appendChild(wrapDetails("Paleontology (real world)", paleoInner, true));
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
    table.innerHTML = `<thead><tr>
      <th></th><th>Ability</th><th>Slot</th><th>Description</th><th>Marks</th>
      <th>Dmg</th><th>CD (s)</th><th>Stam</th><th>Detail</th><th>Curves</th>
    </tr></thead>`;
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
        tr.appendChild(el("td", "abil-detail", st.detail || "—"));
      } else {
        tr.appendChild(el("td", "num", "—"));
        tr.appendChild(el("td", "num", "—"));
        tr.appendChild(el("td", "num", "—"));
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
      el("p", "muted", "Toggle sex, then click swatches per body region to cycle palette indices (0–5). Values save per skin. Add per-skin renders in media/ when you have them.")
    );
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
      const state = paletteState();
      const regions = data.colorRegions || ["Head", "Body", "Pattern", "Accents"];
      (data.skins || []).forEach((skin) => {
        const card = el("div", "skin-lab-card");
        card.appendChild(el("h4", null, skin.name));
        const inner = el("div", "skin-lab-regions");
        regions.forEach((reg) => {
          const row = el("div", "region-row");
          row.appendChild(el("span", "region-name", reg));
          const sw = el("div", "region-swatches");
          const gk = gender === "male" ? "male" : "female";
          if (!state[skin.id]) state[skin.id] = { male: {}, female: {} };
          const idx = state[skin.id][gk][reg] || 0;
          for (let k = 0; k < 6; k++) {
            const b = el("button", `swatch swatch-${k} ${k === idx ? "swatch-on" : ""}`);
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
      });
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
