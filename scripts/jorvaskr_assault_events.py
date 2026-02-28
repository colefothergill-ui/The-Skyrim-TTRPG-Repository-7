#!/usr/bin/env python3
"""
Jorrvaskr Assault Events (Phase 4)

Runs the Silver Hand assault on Jorrvaskr in three acts and manages
the defender group consequence track (defense pool).

Integration:
- Wired into scripts/triggers/whiterun_triggers.py via jorrvaskr_assault_triggers(loc, state).
- Standalone: call jorrvaskr_assault_triggers(loc, state) directly.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional

ActNumber = Literal[1, 2, 3]
AssaultOutcome = Literal[
    "hall_holds_kodlak_lives",
    "hall_holds_kodlak_falls",
    "hall_holds_skjor_falls",
    "both_veterans_fall",
]


def _flags(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("scene_flags", {})


def _companions_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("companions_state", {})


def _clocks(state: Dict[str, Any]) -> Dict[str, Any]:
    clocks = state.setdefault("clocks", {})
    if not isinstance(clocks, dict):
        state["clocks"] = {}
        clocks = state["clocks"]
    legacy = state.get("campaign_clocks")
    if isinstance(legacy, dict):
        if not clocks:
            state["clocks"] = legacy
            return legacy
        for key, value in legacy.items():
            clocks.setdefault(key, value)
    else:
        state.setdefault("campaign_clocks", clocks)
    return clocks


def _get_clock_progress(state: Dict[str, Any], clock_id: str) -> int:
    c = _clocks(state).get(clock_id, {})
    return int(c.get("current_progress", c.get("current", 0)) or 0)


def _once(state: Dict[str, Any], key: str) -> bool:
    flags = _flags(state)
    if flags.get(key):
        return False
    flags[key] = True
    return True


# ──────────────────────────────────────────────────────────────────────────
# Defense pool initialization
# ──────────────────────────────────────────────────────────────────────────

_BASE_DEFENDERS = [
    "kodlak_whitemane",
    "skjor",
    "aela_the_huntress",
    "vilkas",
    "farkas",
    "vignar_gray_mane",
]

_LETHAL_RISK_NPCS = {"kodlak_whitemane", "skjor"}


def _build_defense_pool(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build or retrieve the Jorrvaskr Defense Pool from state.
    Applies modifiers from internal_civil_war, whelps_polarized, skjor_dead, and schism_resolution.
    """
    cstate = _companions_state(state)
    if "defense_pool" in cstate:
        return cstate["defense_pool"]

    defenders = list(_BASE_DEFENDERS)

    # Remove dead NPCs before the assault
    flags = _flags(state)
    if flags.get("skjor_dead") or cstate.get("skjor_dead"):
        defenders = [d for d in defenders if d != "skjor"]

    pool: Dict[str, Any] = {
        "defenders": {d: {"status": "active", "consequence": None} for d in defenders},
        "capacity": len(defenders),
        "modifiers_applied": [],
    }

    # Internal civil war: -2 capacity
    if cstate.get("internal_civil_war"):
        pool["capacity"] = max(0, pool["capacity"] - 2)
        pool["modifiers_applied"].append("internal_civil_war: capacity -2")

    # Whelps fully polarized: -1 capacity
    if cstate.get("whelps_polarized"):
        pool["capacity"] = max(0, pool["capacity"] - 1)
        pool["modifiers_applied"].append("whelps_polarized: capacity -1")

    # Reconcile path: +1 capacity
    if cstate.get("schism_resolution") == "reconcile":
        pool["capacity"] = pool["capacity"] + 1
        pool["modifiers_applied"].append("reconcile_resolution: capacity +1")

    cstate["defense_pool"] = pool
    return pool


def get_defense_pool_summary(state: Dict[str, Any]) -> List[str]:
    """Returns a GM-readable summary of the current defense pool."""
    pool = _build_defense_pool(state)
    lines = [
        f"[DEFENSE POOL] Jorrvaskr has {pool['capacity']} effective defender slots.",
        f"Active defenders: {', '.join(d for d, v in pool['defenders'].items() if v['status'] == 'active')}",
    ]
    if pool["modifiers_applied"]:
        lines.append(f"Modifiers: {'; '.join(pool['modifiers_applied'])}")
    return lines


def apply_defender_consequence(
    state: Dict[str, Any], npc_id: str, consequence: str
) -> List[str]:
    """
    Apply a consequence to a named defender.
    If the defender already has a consequence, they are taken out (killed/expelled).
    """
    pool = _build_defense_pool(state)
    if npc_id not in pool["defenders"]:
        return [f"[POOL] {npc_id} is not in the defense pool."]

    defender = pool["defenders"][npc_id]
    events: List[str] = []

    if defender["status"] != "active":
        return [f"[POOL] {npc_id} is already taken out — cannot apply further consequences."]

    if defender["consequence"] is None:
        defender["consequence"] = consequence
        events.append(f"[POOL] {npc_id} takes consequence: '{consequence}'.")
        if npc_id in _LETHAL_RISK_NPCS:
            events.append(f"[SAVE GATE] {npc_id} is at lethal risk. A save gate roll is available.")
    else:
        # Second hit — taken out
        defender["status"] = "taken_out"
        events.append(f"[POOL] {npc_id} is taken out — KILLED or expelled from the hall.")
        _record_npc_death(state, npc_id)

    return events


def attempt_save_gate(
    state: Dict[str, Any],
    npc_id: str,
    roll_result: Literal["success", "failure"],
) -> List[str]:
    """
    Attempt a save gate for a lethal-risk NPC.
    On success: NPC survives but is withdrawn (status -> 'wounded'); cannot absorb further consequences.
    On failure: NPC is taken out (killed).
    """
    pool = _build_defense_pool(state)
    if npc_id not in _LETHAL_RISK_NPCS:
        return [f"[SAVE GATE] {npc_id} is not a lethal-risk NPC."]

    if npc_id not in pool["defenders"]:
        return [f"[SAVE GATE] {npc_id} is not in the defense pool (already removed before assault)."]

    if roll_result == "success":
        pool["defenders"][npc_id]["status"] = "wounded"
        return [
            f"[SAVE GATE -- SUCCESS] {npc_id} pulls through. Battered, but alive.",
            f"{npc_id} is withdrawn from the fight (status: wounded). They cannot absorb further consequences.",
        ]
    else:
        events = [f"[SAVE GATE -- FAILURE] {npc_id} falls. The hall loses a veteran."]
        pool["defenders"][npc_id]["status"] = "taken_out"
        _record_npc_death(state, npc_id)
        return events


def _record_npc_death(state: Dict[str, Any], npc_id: str) -> None:
    cstate = _companions_state(state)
    flags = _flags(state)
    if npc_id == "kodlak_whitemane":
        cstate["kodlak_dead_assault"] = True
        flags["kodlak_dead_assault"] = True
    elif npc_id == "skjor":
        cstate["skjor_dead_assault"] = True
        flags["skjor_dead_assault"] = True

    # Check if both veterans fell
    if cstate.get("kodlak_dead_assault") and cstate.get("skjor_dead_assault"):
        cstate["hall_shattered_state"] = True


# ──────────────────────────────────────────────────────────────────────────
# Act 1: Hold the Outer Yard
# ──────────────────────────────────────────────────────────────────────────

def assault_act1_outer_yard(state: Dict[str, Any]) -> List[str]:
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_jorvaskr_assault":
        return []
    if not _once(state, "assault_act1_started"):
        return []

    pool = _build_defense_pool(state)

    events = [
        "[ACT 1 — OUTER YARD] The torches are moving. Silver-armored shapes cross the Wind District in force.",
        "Farkas kicks the door open: \"They're here. *All* of them.\"",
        "The yard is open ground. No cover. The Skyforge watches from above.",
        "",
        "[ENCOUNTER] Silver Hand Footsoldiers — zone conflict.",
        "Mechanics: PC and available defenders vs first wave. Physique or Fight to create zone advantages.",
        f"Defense pool capacity: {pool['capacity']}.",
        "",
        "[SAVE GATE — ACT 1] PC Will vs Good (+3) to prevent whelp panic.",
        "Failure: one whelp flees or freezes; defense pool loses 1 effective slot this act.",
        "",
        "After Act 1 resolves, call resolve_assault_act(state, act=1, held=True/False).",
    ]

    events.extend(get_defense_pool_summary(state))
    return events


# ──────────────────────────────────────────────────────────────────────────
# Act 2: Protect the Grand Hall
# ──────────────────────────────────────────────────────────────────────────

def assault_act2_grand_hall(state: Dict[str, Any]) -> List[str]:
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_jorvaskr_assault":
        return []
    if not _once(state, "assault_act2_started"):
        return []

    events = [
        "[ACT 2 — GRAND HALL] The second wave breaches through the windows. A Silver Hand Siege Engineer throws a fire flask.",
        "The hall's banner catches. Smoke begins to fill the upper reaches.",
        "[SCENE ASPECT CREATED] 'Smoke Fills the Hall' (can be invoked to create disadvantage on ranged/Notice)",
        "",
        "[ENCOUNTER] Silver Hand Veterans (elite) + Siege Engineer (support).",
        "Mechanics: Chase + combat hybrid. Fight vs Superb (+5) to hold the breach.",
        "Failure: breach held at cost — apply a consequence to one defender of PC's choice.",
        "",
        "[SAVE GATE — ACT 2] PC Athletics vs Fair (+2) to drag a wounded NPC clear of fire.",
        "Failure: wounded NPC takes an additional consequence.",
        "",
        "Kodlak is in his chamber. Skjor is holding the breach. Both are at risk.",
        "After Act 2 resolves, call resolve_assault_act(state, act=2, held=True/False).",
    ]
    return events


# ──────────────────────────────────────────────────────────────────────────
# Act 3: The Commander's Gambit
# ──────────────────────────────────────────────────────────────────────────

def assault_act3_commanders_gambit(state: Dict[str, Any]) -> List[str]:
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_jorvaskr_assault":
        return []
    if not _once(state, "assault_act3_started"):
        return []

    events = [
        "[ACT 3 — HARBINGER'S CHAMBER] The commander cuts through the chaos with purpose. They know where Kodlak sleeps.",
        "The doorway narrows to one body wide. The smell of old leather and juniper — and now blood.",
        "",
        "[BOSS FIGHT] Silver Hand Commander. Target priority: Kodlak Whitemane.",
        "Mechanics: PC must split actions between attacking the commander and physically protecting Kodlak.",
        "",
        "[SAVE GATE — ACT 3] PC Physique vs Great (+4) to physically interpose between Commander and Kodlak.",
        "Success: Kodlak is shielded; commander redirects to PC.",
        "Failure: Commander reaches Kodlak — apply consequence to Kodlak (lethal risk trigger).",
        "",
        "After the commander is defeated, call resolve_assault_finale(state, kodlak_alive=True/False, skjor_alive=True/False).",
    ]
    return events


# ──────────────────────────────────────────────────────────────────────────
# Act resolution helpers
# ──────────────────────────────────────────────────────────────────────────

def resolve_assault_act(
    state: Dict[str, Any], act: ActNumber, held: bool
) -> List[str]:
    """
    Called after each act resolves.
    If the act was not held, applies pressure to the defense pool.
    """
    flags = _flags(state)
    flags[f"assault_act{act}_held"] = held

    events: List[str] = []
    if held:
        events.append(f"[ACT {act} HELD] The Companions hold. Advance to Act {act + 1}.")
    else:
        events.append(f"[ACT {act} BREACHED] The line didn't hold. Consequences ripple through the defense pool.")
        if act == 1:
            events.extend(apply_defender_consequence(state, "farkas", "Overwhelmed at the Gate"))
        elif act == 2:
            events.extend(apply_defender_consequence(state, "skjor", "Breach Wound"))

    return events


def resolve_assault_finale(
    state: Dict[str, Any],
    kodlak_alive: bool,
    skjor_alive: bool,
) -> List[str]:
    """
    Records the assault's final outcome flags and transitions to companions_funeral_rites.
    """
    flags = _flags(state)
    if flags.get("assault_finale_resolved"):
        return []
    flags["assault_finale_resolved"] = True

    cstate = _companions_state(state)
    cstate["hall_assault_repelled"] = True
    cstate["active_quest"] = "companions_funeral_rites"

    events: List[str] = ["[ASSAULT REPELLED] The Silver Hand withdraws. Jorrvaskr stands."]

    if kodlak_alive:
        cstate["kodlak_survived_assault"] = True
        events.append("Kodlak is alive — wounded, but present. He looks at the damage and says nothing for a long time.")
    else:
        cstate["kodlak_dead_assault"] = True
        events.append("Kodlak did not survive. The Harbinger is dead. The hall goes quiet in a way it has never been before.")

    if skjor_alive:
        cstate["skjor_survived_assault"] = True
        events.append("Skjor is alive. He's bleeding from the shoulder but he's still standing at the breach.")
    else:
        cstate["skjor_dead_assault"] = True
        events.append("Skjor is dead. Aela finds him near the breach. She does not weep where others can see.")

    if not kodlak_alive and not skjor_alive:
        cstate["hall_shattered_state"] = True
        events.append(
            "[HALL SHATTERED] Both veterans are gone. The Companions are not destroyed, but they are fractured in a way "
            "that will define what comes next."
        )

    events.append("Next: companions_funeral_rites — journey to Ysgramor's Tomb.")
    return events


# ──────────────────────────────────────────────────────────────────────────
# Top-level trigger dispatcher
# ──────────────────────────────────────────────────────────────────────────

def jorrvaskr_assault_triggers(loc: str, state: Dict[str, Any]) -> List[str]:
    """
    Main entry point. Call with current location string and campaign state.
    Only fires during companions_jorvaskr_assault quest.
    """
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_jorvaskr_assault":
        return []

    # Verify assault should fire (clock-based)
    clock_val = _get_clock_progress(state, "silver_hand_assault_preparation")
    assault_skipped = (
        cstate.get("silver_hand_endgame_cleared") is True and clock_val == 0
    )
    if assault_skipped:
        if _once(state, "assault_skip_state_advanced"):
            cstate["active_quest"] = "companions_funeral_rites"
        return [
            "[ASSAULT SKIPPED] The Silver Hand's cells were wiped out. Jorrvaskr is never directly assaulted. "
            "Proceeding to companions_funeral_rites."
        ]

    loc_lower = str(loc).lower()
    events: List[str] = []

    if any(k in loc_lower for k in ["jorrvaskr_yard", "outer_yard", "training_yard"]):
        events.extend(assault_act1_outer_yard(state))

    if any(k in loc_lower for k in ["jorrvaskr_grand_hall", "grand_hall", "jorrvaskr_downstairs"]):
        events.extend(assault_act2_grand_hall(state))

    if any(k in loc_lower for k in ["harbinger", "kodlak", "harbinger_room", "jorrvaskr_harbinger"]):
        events.extend(assault_act3_commanders_gambit(state))

    return events
