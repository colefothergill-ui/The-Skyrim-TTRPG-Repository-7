#!/usr/bin/env python3
"""
Jorrvaskr Event Helpers (Phase 1)

Contains:
- Athis sparring offer text (with bet raising rules)
- Resolution helper that mutates campaign_state + PC gold + whelp loyalty
- Follow-up approach hooks for Farkas/Aela depending on fighting style

Designed to be called by whiterun_triggers.py.
"""

from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional


BET_BASE = 100
BET_CAP = 500
BET_PER_SHIFT = 50

Style = Literal["warrior", "tactical", "mixed"]
Result = Literal["win", "lose"]
Followup = Literal["farkas", "aela", "none"]


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


def compute_bet_amount(base: int = BET_BASE, raise_shifts: int = 0, cap: int = BET_CAP) -> int:
    """
    Bet raising rule:
    - Base is 100
    - Each shift of success on a social raise roll adds +50
    - Cap at 500
    """
    return clamp(base + max(0, raise_shifts) * BET_PER_SHIFT, base, cap)


def offer_athis_spar_event(campaign_state: Dict[str, Any]) -> List[str]:
    """
    One-time offer text. Stores a pending choice marker in scene_flags.
    GM resolves using resolve_athis_spar_event(...).
    """
    flags = campaign_state.setdefault("scene_flags", {})
    if flags.get("jorvaskr_athis_spar_resolved") or flags.get("jorvaskr_athis_spar_offered"):
        return []

    flags["jorvaskr_athis_spar_offered"] = True

    return [
        "[SCRIPTED EVENT] Athis the Dunmer duelist is goading the whelps into a 1v1 spar. He offers a wager.",
        "Rule: First combatant to impose a Mild Consequence wins (sparring rules; no killing).",
        "Whelps present: Ria, Njada, Torvar (and others file out if you accept).",
        "Senior eyes nearby: Farkas and Aela watch from a respectful distance.",
        "Bet: 100 septims base. You may raise it via a social roll:",
        " - Roll Rapport or Provoke vs Athis' Will. Each shift of success raises the bet by +50 (cap 500).",
        "CHOICE: Accept the spar? If YES, run resolve_athis_spar_event(accepted=True, ...). If NO, run resolve_athis_spar_event(accepted=False)."
    ]


def _bump_whelp_loyalty(campaign_state: Dict[str, Any], npc_ids: List[str], delta: int) -> None:
    """
    Whelps are tracked in campaign_state['companions']['available_companions'] with a 'loyalty' int (0-100).
    """
    comp = campaign_state.setdefault("companions", {})
    avail = comp.setdefault("available_companions", [])
    for entry in avail:
        nid = str(entry.get("npc_id", "")).lower()
        if nid in [x.lower() for x in npc_ids]:
            entry["loyalty"] = clamp(int(entry.get("loyalty", 50)) + delta, 0, 100)


def _ensure_side_quest_entry(campaign_state: Dict[str, Any], quest_id: str, status: str, reason: str) -> None:
    """
    Side quests are tracked in campaign_state['active_quests'] as dicts.
    """
    active = campaign_state.setdefault("active_quests", [])
    for q in active:
        if isinstance(q, dict) and q.get("id") == quest_id:
            return
    active.append({"id": quest_id, "status": status, "reason": reason})


def resolve_athis_spar_event(
    campaign_state: Dict[str, Any],
    pc_sheet: Dict[str, Any],
    accepted: bool,
    bet_amount: int = BET_BASE,
    result: Optional[Result] = None,
    style: Style = "mixed",
    raise_shifts: int = 0,
) -> Dict[str, Any]:
    """
    Mutates campaign_state + pc_sheet.

    Parameters:
    - accepted: did the PC accept the spar
    - bet_amount: final bet (use compute_bet_amount if raising)
    - result: "win"/"lose" if accepted; None if declined
    - style: "warrior" (aggressive melee), "tactical" (athletics/bow/finesse), "mixed"
    - raise_shifts: optional, if you want resolver to compute bet automatically
    """
    flags = campaign_state.setdefault("scene_flags", {})
    flags["jorvaskr_athis_spar_resolved"] = True

    # If raise_shifts provided, compute bet amount and override.
    if raise_shifts > 0:
        bet_amount = compute_bet_amount(BET_BASE, raise_shifts, BET_CAP)

    bet_amount = clamp(int(bet_amount), BET_BASE, BET_CAP)

    # Record
    flags["jorvaskr_athis_spar_record"] = {
        "accepted": accepted,
        "bet_amount": bet_amount,
        "result": result,
        "style": style
    }

    if not accepted:
        flags["jorvaskr_athis_spar_followup"] = "none"
        return {"campaign_state": campaign_state, "pc_sheet": pc_sheet}

    if result not in ("win", "lose"):
        raise ValueError("resolve_athis_spar_event: result must be 'win' or 'lose' when accepted=True")

    # Gold swing (per spec: win = +bet, lose = -bet)
    pc_sheet["gold"] = int(pc_sheet.get("gold", 0))
    if result == "win":
        pc_sheet["gold"] += bet_amount
    else:
        pc_sheet["gold"] -= bet_amount
        pc_sheet["gold"] = max(0, pc_sheet["gold"])

    # If win: loyalty bumps for the whelps who witness it (and Athis)
    if result == "win":
        _bump_whelp_loyalty(campaign_state, npc_ids=["ria", "njada_stonearm", "torvar", "athis"], delta=10)

        # Follow-up approach based on style
        followup: Followup = "none"
        if style == "warrior":
            followup = "farkas"
            _ensure_side_quest_entry(
                campaign_state,
                quest_id="companions_honorable_combat",
                status="locked",
                reason="Unlocked by winning Athis spar (warrior style). Activates once Proving Honor is active."
            )
        elif style == "tactical":
            followup = "aela"
            _ensure_side_quest_entry(
                campaign_state,
                quest_id="companions_prey_and_predator",
                status="locked",
                reason="Unlocked by winning Athis spar (tactical style). Activates once Proving Honor is active."
            )

        flags["jorvaskr_athis_spar_followup"] = followup
    else:
        flags["jorvaskr_athis_spar_followup"] = "none"

    return {"campaign_state": campaign_state, "pc_sheet": pc_sheet}
