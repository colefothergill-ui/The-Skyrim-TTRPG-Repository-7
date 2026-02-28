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
    clocks = state.setdefault("clocks", {})
    if not isinstance(clocks, dict):
        state["clocks"] = {}
        clocks = state["clocks"]

    legacy = state.get("campaign_clocks")
    if isinstance(legacy, dict):
        if not clocks:
            state["clocks"] = legacy
            clocks = legacy
        else:
            for k, v in legacy.items():
                clocks.setdefault(k, v)
    else:
        state["campaign_clocks"] = clocks

    return clocks


def _companions_qprog(state: Dict[str, Any]) -> Dict[str, Any]:
    c = state.get("companions_state", {}) or {}
    qp = c.get("quest_progress", {}) or {}
    return qp if isinstance(qp, dict) else {}


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

        qp = _companions_qprog(campaign_state)
        if qp.get("greymane_and_the_greater") == "memory":
            qp["greymane_and_the_greater"] = "active"
            events.append(
                "[QUEST ACTIVATED] Greymane and the Greater: Vignar’s whispered plan now intersects the coming battle. "
                "You may warn Balgruuf… or conspire with Vignar."
            )

    return events
