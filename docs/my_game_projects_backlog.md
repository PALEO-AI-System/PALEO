# Personal game / mod / web project backlog

Single place to track ideas you mentioned wanting to work on. Update this file as scope changes.

## Active or named projects (yours)

| Project | Engine / stack | Notes |
|--------|------------------|--------|
| **PALEO** | Python + ML + companion site in this repo | Instinct Agent / Primal Mind per `docs/lexicon.md`; separate from POT modding acceptance. |
| **Path of Titans — horse mod** | POT official dev kit (UE) after approval | Goal: playable modern horse (e.g. thoroughbred-style) + prehistoric horse species; community-sensitive framing vs. pushing into PALEO branding. |
| **Path of Titans — UI mods** | POT dev kit: UMG widgets + Blueprints (subclass/extend, do not edit base game assets in place) | Ideas: extra HUD button, overlays in game’s visual language. Requires Alderon modding access + NDA workflow. |
| **Escape the Soup** | Unity 2D | Shrimp game concept. |
| **Breeze** | Unreal Engine 3D | Horse racing sim. |
| **Breeze Mobile** | 2D (separate mini-game) | Intended to share/feature-align with main Breeze where it makes sense. |
| **Wildtype+** | Unreal Engine 3D open world | Wild mustang open-world idea; no real development yet. |

### POT companion site (separate from in-game mod)

- **Intent:** Features like community build guides and skin presets (similar spirit to third-party POT info sites), hosted for **Path of Titans** players — not shipped as part of PALEO if that would hurt community trust.
- **AI use:** If you use AI for copy, codegen, or data scraping, consider disclosing on the site and keeping human review for accuracy and tone.

---

## External links — by developer / source

### kwiamwis — Aalenia

- **Site:** https://aalenia.com  
- **Repo (VitePress-style docs site):** https://github.com/kwiamwis/aalenia  
- **Scope (from public pages):** “Mods and Applications”, “Community Servers”, guidelines, bug reports; paths like `/potapps/`, `/potservers/` suggest POT-focused mod/app listings and server info.

*Whether this person used AI for the site or mod work cannot be determined from public repos alone; the GitHub tree is normal TypeScript/VitePress-style tooling, which is equally consistent with hand-written or AI-assisted authoring.*

### Reddit — short links you saved (Aalenia / POT discussion)

These are opaque `reddit.com/r/pathoftitans/s/...` short URLs in your notes; resolve them in-browser and paste canonical URLs here when you want a permanent archive.

- https://www.reddit.com/r/pathoftitans/s/egowlN5u8b  
- https://www.reddit.com/r/pathoftitans/s/LpAHUg5bn1  

### Reddit posts you grouped (modded-server stats / build-guide sites)

You suspected overlapping or AI-heavy presentation across some of these; treat attribution as **unverified** until you confirm authors.

1. https://www.reddit.com/r/pathoftitans/comments/1qn4htz/made_a_website_that_tracks_info_for_modded_pot/  
2. https://www.reddit.com/r/pathoftitans/comments/1r0lamf/pot_modded_server_statistics_and_server_finder/  
3. https://www.reddit.com/r/pathoftitans/comments/1rztn3i/we_built_a_free_build_guide_site_for_path_of/  
4. **DinoMeta** (builds & strategies — fetch was slow/unavailable from tooling): https://dinometa.gg  

---

## Quick technical pointers (POT UI + UE + AI)

- **Official modding entry:** https://pathoftitans.com/mods — dev kit is Unreal-based; apply via Alderon’s UGC process (GitHub + Epic linkage, NDA). Support article (apply): https://support.alderongames.com/hc/en-us/articles/46821274395545-How-To-Apply-For-Modding  
- **UI in POT mods:** Typically **UMG (widgets) + Blueprints** (and C++ if the kit allows for your mod), by **subclassing/extending** game UI classes rather than editing core assets. Exact hooks depend on what Alderon exposes in the kit version you have.  
- **“Unity’s new built-in UI AI” but for UE:** There is **no single Epic-shipped equivalent** to “AI writes my game UI inside the editor” as a product feature. Practical approaches are the same as most UE studios: **Cursor / Copilot / ChatGPT for code**, marketplace plugins, and experimental Epic tooling aimed at other products (e.g. Fortnite Verse ecosystem) — not a drop-in “POT UI generator.”  
- **Community norms:** Many players are skeptical of undisclosed AI for **player-facing guides** and **in-game art/copy**. Mitigations: clear credits, human verification of gameplay numbers, and conservative claims.

---

## Related in-repo reference

- POT wiki / stats references for PALEO work: `docs/pot_web_resources.md`  
