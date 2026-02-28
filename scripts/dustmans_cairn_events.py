#!/usr/bin/env python3
"""
Dustman’s Cairn Events (Phase 3)

Provides:
- Room-by-room triggered descriptions keyed to location strings
- Companion-dependent barks (Aela / Vilkas / Farkas)
- Named Silver Hand antagonist intro scene (Hakon Moonbreaker)
- Seeds optional Silver Hand contact if PC is Purity-track

Integration:
- Called from scripts/triggers/whiterun_triggers.py when loc contains "dustman".
"""

from __future__ import annotations
from typing import Any, Dict, List


def _flags(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("scene_flags", {})


def _partner(state: Dict[str, Any]) -> str:
    return str(_flags(state).get("dustmans_partner", state.get("companions_state", {}).get("proving_honor_assigned_partner", "farkas"))).lower()


def _once(state: Dict[str, Any], key: str) -> bool:
    flags = _flags(state)
    if flags.get(key):
        return False
    flags[key] = True
    return True


def _seed_join_offer_if_purity(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    companions_state = state.get("companions_state", {}) or {}
    purity_track = companions_state.get("embraced_curse") is False
    if not purity_track:
        return []
    if flags.get("silver_hand_join_seeded"):
        return []
    flags["silver_hand_join_seeded"] = True
    flags["silver_hand_token_obtained"] = True
    # Also mark quest seed if quest system exists
    quests = state.setdefault("quests", {})
    quests.setdefault("active", [])
    if "silver_hand_contact" not in quests["active"]:
        quests["active"].append("silver_hand_contact")
    return [
        "[SEED] Among the Silver Hand supplies you find a silver token etched with a broken moon and a short phrase: “No moon, no master.”",
        "It feels less like loot and more like a door left ajar."
    ]


def _companion_bark(partner: str, context: str) -> str:
    # Very light flavor barks; expand in later phases.
    if partner == "aela":
        if context == "entrance":
            return 'Aela murmurs, “Smells like old death and new arrogance. Keep your eyes open.”'
        if context == "camp":
            return 'Aela’s voice is a knife: “Silver Hand. They always come where they shouldn’t.”'
    if partner == "vilkas":
        if context == "entrance":
            return 'Vilkas says quietly, “Discipline. The barrow wants panic. Don’t give it any.”'
        if context == "camp":
            return 'Vilkas: “They’re organized. Not raiders. Remember that.”'
    # default / farkas
    if context == "entrance":
        return 'Farkas grins a little too hard. “Alright. Let’s show the dead they picked the wrong day.”'
    if context == "camp":
        return 'Farkas spits. “Silver freaks. Stay tight on me.”'
    return ""


def dustmans_cairn_triggers(loc: str, state: Dict[str, Any]) -> List[str]:
    loc_lower = str(loc).lower()
    if "dustman" not in loc_lower:
        return []

    partner = _partner(state)
    events: List[str] = []

    # Entrance
    if any(k in loc_lower for k in ["entrance", "barrow", "dustmans_entrance"]) and _once(state, "dustmans_entrance_seen"):
        events.append("[DUSTMAN’S CAIRN] The grave-mound rises from the tundra like a clenched fist. Wind combs the stones. The door yawns black.")
        bark = _companion_bark(partner, "entrance")
        if bark:
            events.append(bark)

    # Trap rooms
    if any(k in loc_lower for k in ["anteroom", "runes", "hall of axes", "axes"]) and _once(state, "dustmans_trap_rooms_seen"):
        events.append("Runes scratch the stone. Old pressure plates wait like patience. This place was built to punish the careless.")

    # Ossuary
    if any(k in loc_lower for k in ["ossuary", "maze", "bones"]) and _once(state, "dustmans_ossuary_seen"):
        events.append("Bone-dust clings to your boots. The corridors bend like a throat swallowing sound. Something shifts deeper in the dark.")

    # Silver Hand camp + named antagonist intro
    if any(k in loc_lower for k in ["silver hand camp", "camp", "dustmans_silver_hand_camp"]) and _once(state, "dustmans_silver_hand_intro_done"):
        bark = _companion_bark(partner, "camp")
        if bark:
            events.append(bark)

        events += [
            "[INTRO ANTAGONIST] A man in wolf-hunter gear steps from behind a toppled pillar, silver charms clinking. He does not shout. He *measures* you.",
            "Hakon Moonbreaker: “Companions sending pups into barrows now? Or is this the Harbinger’s latest mistake?”",
            "He gestures at the silver tools. “We’re not bandits. We’re a cure you haven’t accepted yet.”",
            "GM NOTE: You can run this as (a) a tense parley then skirmish, or (b) a cutscene where Hakon withdraws deeper and leaves traps.",
            "[FORESHADOW] Hakon’s gaze lingers on anyone who reeks of refusal rather than worship. “If you ever decide the wolf isn’t a gift… find the broken moon.”"
        ]
        events.extend(_seed_join_offer_if_purity(state))

    # Deep crypt (fragment)
    if any(k in loc_lower for k in ["deep crypt", "fragment", "wuuthrad", "chamber", "dustmans_deep_crypt"]) and _once(state, "dustmans_fragment_chamber_seen"):
        events.append("[FRAGMENT CHAMBER] A heavy stone door gives way to a chamber that feels like a sealed breath. The Wuuthrad fragment waits where the dead wanted it guarded.")
        events.append("GM NOTE: Trigger the guardian fight here (draugr guardian / overlord). Let the partner contribute spotlight support.")

    # Word wall (optional)
    if any(k in loc_lower for k in ["word wall", "wall vault", "dustmans_word_wall"]) and _once(state, "dustmans_word_wall_seen"):
        events.append("[WORD WALL] A wall of carved power hums with language older than kings. If the PC can read it, it reads them back.")

    return events
