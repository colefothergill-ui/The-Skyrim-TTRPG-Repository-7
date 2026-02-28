#!/usr/bin/env python3
"""
Global Story Triggers

Used by all hold triggers to emit world events that should fire regardless of hold.
Phase 2 includes:
- Battle of Whiterun Countdown 6/8 announcement (town crier in settlements; courier in wilderness)
- Activates greymane_and_the_greater if the PC has the memory flag quest entry
"""

from __future__ import annotations

from typing import Any, Dict, List

SETTLEMENT_KEYWORDS = [
    "whiterun", "windhelm", "riften", "solitude", "markarth", "winterhold", "morthal", "falkreath", "dawnstar",
    "city", "town", "village", "district", "gate", "market", "inn", "keep", "dragonsreach"
]


def _flags(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("scene_flags", {})


def _clocks(state: Dict[str, Any]) -> Dict[str, Any]:
    # Bridge: prefer 'clocks' namespace (jorvaskr_events convention), fall back to 'campaign_clocks'.
    clocks = state.get("clocks")
    if isinstance(clocks, dict):
        return clocks
    return state.setdefault("campaign_clocks", {})


def _companions_qprog(state: Dict[str, Any]) -> Dict[str, Any]:
    c = state.get("companions_state", {}) or {}
    qp = c.get("quest_progress", {}) or {}
    return qp if isinstance(qp, dict) else {}


def _active_quests(state: Dict[str, Any]) -> List[Any]:
    aq = state.get("active_quests")
    if isinstance(aq, list):
        return aq
    # Normalize: ensure campaign_state['active_quests'] is always a list.
    state["active_quests"] = []
    return state["active_quests"]


def _is_settlement(loc_lower: str) -> bool:
    return any(k in loc_lower for k in SETTLEMENT_KEYWORDS)


def global_story_triggers(loc: str, campaign_state: Dict[str, Any]) -> List[str]:
    events: List[str] = []
    loc_lower = str(loc).lower()
    flags = _flags(campaign_state)

    clocks = _clocks(campaign_state)
    bow = clocks.get("battle_of_whiterun_countdown", {}) or {}
    cur = int(bow.get("current_progress", bow.get("current", 0)) or 0)

    if cur >= 6 and not flags.get("battle_of_whiterun_march_announcement_done"):
        if _is_settlement(loc_lower):
            events.append(
                "[TOWN CRIER] Hear ye! Hear ye! Word from the roads: Stormcloak banners move in force. "
                "Whiterun Hold braces for war. Civilians begin evacuating; gates tighten; patrols double."
            )
        else:
            events.append(
                "[COURIER] A rider finds you with frozen lashes and a sealed note: Stormcloak forces are officially on the march for Whiterun Hold. "
                "The Battle of Whiterun is no longer rumor. It is scheduled."
            )
        flags["battle_of_whiterun_march_announcement_done"] = True

        # If Greymane quest exists as memory in active_quests (dict entries), activate it.
        greymane_activated = False
        for q in _active_quests(campaign_state):
            if isinstance(q, dict) and q.get("id") == "greymane_and_the_greater" and q.get("status") == "memory":
                q["status"] = "active"
                q["note"] = "Stormcloak mobilization has begun. Vignar’s words matter now."
                greymane_activated = True

        # Also check companions_state.quest_progress (set by jorvaskr_events._ensure_quest_entry).
        cstate = campaign_state.get("companions_state") or {}
        qprog = cstate.get("quest_progress") or {}
        if isinstance(qprog, dict) and qprog.get("greymane_and_the_greater") == "memory":
            qprog["greymane_and_the_greater"] = "active"
            cstate.setdefault("quest_notes", {})["greymane_and_the_greater"] = (
                "Stormcloak mobilization has begun. Vignar’s words matter now."
            )
            greymane_activated = True

        if greymane_activated:
            events.append(
                "[QUEST ACTIVATED] Greymane and the Greater: Vignar’s whispered plan now intersects the coming battle. "
                "You may warn Balgruuf… or conspire with Vignar."
            )

    return events
