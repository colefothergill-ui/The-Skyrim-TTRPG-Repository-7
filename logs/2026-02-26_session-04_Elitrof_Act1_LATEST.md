# Session 4 (Act I): Elitrof Whitemane — Ysgramor's Tomb: Purity Path Ignites
**Date:** 2026-02-26  
**PC:** Elitrof Whitemane (Nord, Lord Stone)  
**Hold:** Winterhold — Ysgramor's Tomb  
**Party:** Elitrof + Kodlak + Farkas + Vilkas

---

## Current Scene *(session-start snapshot)*
- **Scene ID:** act1_scene_014_jorrvaskr_cure_rite_preparation
- **Type:** Travel → Ritual → Combat → Resolution
- **Location:** Jorrvaskr (departure) → Nightgate Pass → Ysgramor's Tomb (Winterhold)
- **Immediate Objective:** Reach Ysgramor's Tomb and perform the Harbinger Flame cure rites for Kodlak, Vilkas, and Farkas.

## Final Scene (End of Session)
- **Scene ID:** act1_scene_016_ysgramors_tomb_reliquary_after_rite
- **Next Scene (Queued):** Return to Jorrvaskr; secure the hall; manage Inner Circle fallout; Silver Hand escalation

---

## Active Clocks (End of Session)
- **Battle of Whiterun Countdown:** 1/8
- **Thalmor Retaliation: Whiterun:** 2/8
- **Elemental Fury Mastery:** 6/8
- **Fire Breath Mastery:** 4/8 *(advanced from 2/8 — Nightgate ambush, YOL used)*
- **Become Ethereal Mastery:** 1/4
- **Silver Hand Vendetta:** 4/6

## Fate & Condition (End of Session)
- **Elitrof Fate Points:** 3
- **Elitrof Refresh:** 2 *(increased this session)*
- **Elitrof Stress/Consequences:** Stress cleared; Mild consequence: Freshly Sealed Wound (carried forward)

---

## Key Events

1. **Departure from Jorrvaskr**: The cure party departed Whiterun at dawn — Elitrof, Kodlak, Farkas, and Vilkas. The witch heads were secured and Wuuthrad's reforged components were bundled for transport to Ysgramor's Tomb.

2. **Nightgate Pass Ambush (Silver Hand)**: En route through Nightgate Pass, a Silver Hand kill-team intercepted the party. The ambush was clearly planned — they knew the route. Elitrof used **Fire Breath (YOL)** to break the advance formation, buying space for Farkas and Vilkas to flank. The ambush was repelled; all Silver Hand dead. The use of YOL in a live combat pushed Fire Breath mastery to **4/8**.
   - *Mechanical note: Fire Breath (unmastered) — FP spent; SWS on the roll applied the Nightgate Ambush scene aspect 'Scattered Formation' for free invokes.*
   - Elitrof acquired the **Map Case: Nightgate Pass Notes** from a Silver Hand lieutenant — now carried as **Advantage: Know the Passes**.

3. **Arrival at Ysgramor's Tomb**: The party entered the tomb complex, navigating the Oath-Hall and the draugr guardians. Kodlak's authority — and the Oath of Ysgramor — smoothed passage through the innermost wards.

4. **The Cure Rites — Harbinger Flame**:
   - **Kodlak's Rite**: Kodlak knelt at the Harbinger Flame. The wolf spirit was called forth by the burning of the Glenmoril Witch Head and engaged in the spiritual plane. Elitrof and Kodlak together banished it. Kodlak rose cured — the beast blood burned clean.
   - **Vilkas's Rite**: Elitrof defended Vilkas's will as the wolf spirit surged. Vilkas landed the finishing strike himself — a moment of ownership and catharsis. Cured.
   - **Farkas's Rite**: Farkas's wolf-spirit manifested visibly, larger and more primal than the others. The spirit was destroyed. Farkas sat quietly for a long moment, then stood and said nothing further. Cured.
   - *Three Glenmoril Witch Heads spent. Zero remaining.*

5. **Wuuthrad Reforged**: At the Reliquary, the Wuuthrad fragments were presented to the ancient forge-rite. The reforging was completed — Wuuthrad, the legendary waraxe of Ysgramor, whole again for the first time in millennia. Elitrof carries it. [Weapon:4; +3 Fight while wielding; +3 vs Mer; Ancient Fury 1/session]

6. **Harbinger Succession Signal (Private)**: Kodlak drew Elitrof aside after the rites and spoke plainly. He would not formally name a successor yet — the Circle had too much to process. But the message was clear: Elitrof was being considered. The official naming was deferred.

7. **Shield of Ysgramor — Confirmed**: The Shield remained with Elitrof from its recovery earlier in the session. No further events regarding it this session.

---

## NPC Trust Clock Updates (Session 4)

| NPC | Clock Before | Clock After | Notes |
|-----|-------------|-------------|-------|
| Kodlak Whitemane | 0/6 | 6/6 | Cured; privately signaled harbingership |
| Vilkas | 0/6 | 6/6 | Cured; Elitrof defended his will; Vilkas landed finishing blow |
| Farkas | 0/6 | 6/6 | Cured; wolf-spirit manifested and destroyed |
| Skjor | 0/6 | 4/6 | Alive; wary respect for battle record despite ideological friction |
| Aela (loyalty) | 50 | 45 | Witnessed cures; respects strength, distrusts purity push |

---

## Mechanical Fixes Applied (Session 4 Closeout)

- **Fire Breath Mastery Clock**: Corrected from 2/8 to **4/8** (Nightgate ambush use).
- **Refresh**: Corrected from 1 to **2** (milestone spend applied).
- **Equipment**: Wuuthrad Fragment and Glenmoril Witch Heads x3 removed; Wuuthrad (Reforged) and Map Case added.
- **Companions quest state**: Updated from `companions_kodlak_cure_or_sacrifice` → `companions_purity_path_ignites`.
- **Shouts learned**: Confirmed Fire Breath (Yol), Elemental Fury (Su Grah Dun), Become Ethereal (Feim).
- **NPC trust clocks**: Kodlak, Vilkas, Farkas all advanced to 6/6. Skjor set to 4/6.
- **Aela loyalty**: Dropped from 50 to 45 (cure witnessed, purity push distrusted).
- **Aela relationship with Skjor**: Updated to reflect Skjor alive.
- **Kodlak and Vilkas aspects.trouble**: Updated to reflect post-cure state.
- **Farkas other_aspects**: "Comfortable in Beast Skin" → "Freedom Earned, Still Loyal".
- **cured_beast_blood** flag set to true for Kodlak, Vilkas, Farkas in NPC files.

---

## End-of-Session State

- **Location:** Ysgramor's Tomb (Winterhold) — Reliquary
- **Objective:** Leave Ysgramor's Tomb and return to Jorrvaskr to secure the Hall, manage Inner Circle fallout, and respond to Silver Hand escalation.
- **Active Quest:** companions_purity_path_ignites
- **Companions Trust:** 10/10 (Legend)
- **Circle Cleansed:** Kodlak, Vilkas, Farkas
- **Circle Remaining Werewolves:** Aela, Skjor
- **Glenmoril Heads Remaining:** 0
- **Wuuthrad:** Reforged, carried by Elitrof

---

## Next Session Prep

- Return to Jorrvaskr: Aela and Skjor have had time to discuss the cure rites in the party's absence.
- Silver Hand Vendetta clock at 4/6 — one tick from moving on Jorrvaskr.
- Decide how the Inner Circle manages the public narrative (Companions do not advertise lycanthropy or cures).
- Harbinger succession: Kodlak deferred but signaled; when and how does the formal naming occur?
- Thalmor Retaliation clock: 2/8 — a witness pressure beat may arrive.

---

## Significant Milestone Award (Session 4 — Cure Rites)

**Session 4 is treated as a Significant Milestone** (cure rites completed; Inner Circle purity path formally ignited).

### Spend Applied
- **Skill Advance:** Lore raised from Fair (+2) to **Good (+3)**
- **Stunt Rewrite:** Rake and Rend → **Parry and Cleave**
  - *When Elitrof Defends with Fight while dual-wielding and succeeds with style, he may forgo the boost to instead make a zone-sweep attack — all enemies in the zone take 1 physical stress. He may also spend 1 Fate Point to create the scene aspect 'Bleeding Out' with 2 free invokes.*
