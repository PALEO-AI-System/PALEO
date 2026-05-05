# Path of Titans HUD reference (PALEO)

Confirmed in-game HUD mapping from user screenshots:

- Left green icon: **hunger**
- Right blue icon: **thirst**
- Middle red bar: **health**
- White bar under health (left side): **stamina**
  - Stamina bar is hidden when completely full.
- Ability hotbar/icons are above health.
- Buffs/debuffs are above the abilities bar.

## Notes for PALEO perception

- Do not assume stamina bar always visible; missing white bar can mean full stamina.
- HUD parsing should treat bar "not visible" as a special case, not always "zero."
- If a future parser uses fixed ROI, begin with bottom-center HUD region and expose tunable offsets.
- Keep this file updated when UI scale/resolution changes are tested.
