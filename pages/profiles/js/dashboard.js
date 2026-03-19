/**
 * PALEO Profiles dashboard — loads manifest and renders creature cards.
 */
(function () {
  "use strict";

  const grid = document.getElementById("creature-grid");
  const sub = document.getElementById("dashboard-subtitle");
  if (!grid) return;

  async function init() {
    let manifest;
    try {
      const res = await fetch("data/manifest.json", { cache: "no-cache" });
      manifest = await res.json();
    } catch {
      grid.innerHTML = `<p class="muted">Could not load creature list.</p>`;
      return;
    }
    if (sub && manifest.subtitle) sub.textContent = manifest.subtitle;
    grid.innerHTML = "";

    manifest.creatures.forEach((c) => {
      const a = document.createElement("a");
      a.className = `creature-card theme-${c.theme || "kto"}`;
      a.href = c.href;

      const img = document.createElement("div");
      img.className = "creature-card-image";
      img.style.backgroundImage = `linear-gradient(180deg, transparent 30%, rgba(7,9,14,0.9)), url(${JSON.stringify(c.thumbnail)})`;

      const body = document.createElement("div");
      body.className = "creature-card-body";
      const tag = document.createElement("span");
      tag.className = "creature-card-tag";
      tag.textContent = c.lineage || "Creature";

      const h = document.createElement("div");
      h.className = "creature-card-name";
      h.textContent = c.name;

      const p = document.createElement("p");
      p.className = "creature-card-sub";
      p.textContent = c.tagline || "";

      body.appendChild(tag);
      body.appendChild(h);
      body.appendChild(p);
      a.appendChild(img);
      a.appendChild(body);
      grid.appendChild(a);
    });
  }

  init();
})();
