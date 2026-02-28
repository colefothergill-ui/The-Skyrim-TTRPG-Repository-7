from typing import Any, Dict, List, Literal, Optional

NoticeOutcome = Literal["fail", "success", "sws"]
WarStance = Literal["pro_stormcloak", "pro_empire", "neutral"]
AthisResult = Literal["win", "lose", "none"]
Partner = Literal["aela", "vilkas", "farkas"]
QuestResult = Literal["success", "failure", "unknown"]

# ---------------------------------------------------------------------------
# PHASE 1 HOTFIX: Athis spar event (offer + resolver)
# Required because whiterun_triggers.py calls offer_athis_spar_event(...)
# ---------------------------------------------------------------------------

BET_BASE = 100
BET_CAP = 500
BET_PER_SHIFT = 50

Style = Literal["warrior", "tactical", "mixed"]
Result = Literal["win", "lose"]
Followup = Literal["farkas", "aela", "none"]


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
            return legacy
        for key, value in legacy.items():
            clocks.setdefault(key, value)
    else:
        state.setdefault("campaign_clocks", clocks)
    return clocks


def _active_quests(state: Dict[str, Any]) -> List[Any]:
    aq = state.setdefault("active_quests", [])
    if not isinstance(aq, list):
        state["active_quests"] = []
    return state["active_quests"]


def _quests(state: Dict[str, Any]) -> Dict[str, Any]:
    q = state.setdefault("quests", {})
    q.setdefault("active", [])
    q.setdefault("completed", [])
    q.setdefault("failed", [])
    return q


def _get_clock_progress(state: Dict[str, Any], clock_id: str) -> int:
    c = _clocks(state).get(clock_id, {})
    return int(c.get("current_progress", c.get("current", 0)) or 0)


def _ensure_clock(
    state: Dict[str, Any],
    clock_id: str,
    name: str,
    max_segments: int,
    segments: Optional[List[str]] = None
) -> None:
    clocks = _clocks(state)
    if clock_id not in clocks:
        clocks[clock_id] = {
            "name": name,
            "current_progress": 0,
            "total_segments": max_segments,
            "segments": segments or []
        }


def _ensure_quest_entry(state: Dict[str, Any], quest_id: str, status: str, note: str) -> None:
    cstate = _companions_state(state)
    qprog = cstate.setdefault("quest_progress", {})
    qnotes = cstate.setdefault("quest_notes", {})
    qprog.setdefault(quest_id, status)
    qnotes.setdefault(quest_id, note)


def _set_quest_status(state: Dict[str, Any], quest_id: str, status: str) -> None:
    cstate = _companions_state(state)
    qprog = cstate.setdefault("quest_progress", {})
    qprog[quest_id] = status
    key = f"companions:{quest_id}"
    aq = _active_quests(state)
    if status == "active":
        if key not in aq:
            aq.append(key)
    elif key in aq:
        aq.remove(key)


def _quest_status(state: Dict[str, Any], quest_id: str) -> Optional[str]:
    cstate = _companions_state(state)
    qprog = cstate.get("quest_progress", {})
    if isinstance(qprog, dict) and quest_id in qprog:
        return str(qprog.get(quest_id))
    q = _quests(state)
    if quest_id in q.get("completed", []):
        return "completed"
    if quest_id in q.get("failed", []):
        return "failed"
    if quest_id in q.get("active", []):
        return "active"
    if quest_id in state.get("completed_quests", []):
        return "completed"
    if quest_id in state.get("active_quests", []):
        return "active"
    key = f"companions:{quest_id}"
    for q in _active_quests(state):
        if isinstance(q, str) and q == key:
            return "active"
        if isinstance(q, dict) and q.get("id") == quest_id:
            return str(q.get("status", "active"))
    return None


def _quest_result(state: Dict[str, Any], quest_id: str) -> QuestResult:
    s = _quest_status(state, quest_id)
    if s == "completed":
        return "success"
    if s == "failed":
        return "failure"
    return "unknown"


def _companions_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("companions_state", {})


def _companions_roster(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("companions", {})


def _bump_whelp_loyalty(state: Dict[str, Any], npc_ids: List[str], delta: int) -> None:
    roster = _companions_roster(state)
    avail = roster.setdefault("available_companions", [])
    for entry in avail:
        if not isinstance(entry, dict):
            continue
        if str(entry.get("npc_id", "")).lower() in [x.lower() for x in npc_ids]:
            entry["loyalty"] = int(entry.get("loyalty", 50)) + delta


def _athis_duel_result(state: Dict[str, Any]) -> AthisResult:
    rec = _flags(state).get("jorvaskr_athis_spar_record", {})
    if not isinstance(rec, dict):
        return "none"
    if rec.get("accepted") is not True:
        return "none"
    r = rec.get("result")
    return r if r in ("win", "lose") else "none"


# ──────────────────────────────────────────────────────────────────────────
# Athis spar — Phase 1 (during companions_investigate_jorrvaskr)
# ──────────────────────────────────────────────────────────────────────────
def offer_athis_spar_event(state: Dict[str, Any]) -> List[str]:
    """Offer the Athis spar once during the Investigate Jorrvaskr quest."""
    flags = _flags(state)
    if flags.get("jorvaskr_athis_spar_offered"):
        return []
    flags["jorvaskr_athis_spar_offered"] = True
    return [
        "[SCRIPTED ENCOUNTER] Athis eyes you from across the hall — a Dunmer with the stillness of someone who fights for real.",
        "His gaze tracks your weapons before your face. There's an unspoken question in the way he stands.",
        "[CHOICE] You may challenge Athis to a friendly spar (or wait for him to challenge you).",
        " - Accept: Call resolve_athis_spar_event(state, accepted=True, result='win'|'lose').",
        " - Decline: Call resolve_athis_spar_event(state, accepted=False).",
        "This is missable. If you leave Jorrvaskr without resolving, Athis will not offer again.",
    ]


def resolve_athis_spar_event(
    state: Dict[str, Any], accepted: bool, result: AthisResult = "none"
) -> None:
    """Resolve the Athis spar outcome and set follow-up flags."""
    flags = _flags(state)
    flags["jorvaskr_athis_spar_resolved"] = True
    actual_result = result if accepted and result in ("win", "lose") else "none"
    flags["jorvaskr_athis_spar_record"] = {"accepted": accepted, "result": actual_result}
    if not accepted:
        return
    # Set follow-up NPC based on spar result
    flags["jorvaskr_athis_spar_followup"] = "aela" if actual_result == "win" else "farkas"


# ──────────────────────────────────────────────────────────────────────────
# Downstairs first-entry description
# ──────────────────────────────────────────────────────────────────────────
def downstairs_living_area_description_once(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    if flags.get("jorvaskr_downstairs_description_done"):
        return []
    flags["jorvaskr_downstairs_description_done"] = True
    return [
        "[TRIGGERED DESCRIPTION] You descend into Jorrvaskr’s downstairs living area.",
        "The Grand Hall feels older than Whiterun’s stone: timber beams dark with smoke, weapons hung like family portraits, "
        "and the hush of a place where legends sleep with one eye open. The air is meat-fat and iron, warmed by hearths that "
        "have heard a thousand oaths. Here, the Companions aren’t ‘famous.’ They’re *present*."
    ]


# ──────────────────────────────────────────────────────────────────────────
# Vignar + Eorlund missable overhear scene (Notice vs Good +3)
# “Alarm” behavior: prompt repeats until resolved, but still missable on fail.
# ──────────────────────────────────────────────────────────────────────────
def vignar_eorlund_notice_prompt(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)

    # Only ever runs the FIRST time you enter downstairs, but repeats prompts until resolved.
    if flags.get("jorvaskr_vignar_notice_resolved"):
        return []

    flags["jorvaskr_vignar_notice_pending"] = True

    return [
        "[MISSABLE OVERHEAR — DO NOT SKIP] As you enter the downstairs living area, you catch voices nearby: Vignar Gray-Mane and Eorlund at the edge of the hall.",
        "GM NOTE: This is a MISS-AND-YOU-MISS-IT roll, but the system will keep prompting until you resolve it. Resolve ONCE, then lock it.",
        "Roll Notice vs Good (+3).",
        " - FAIL: You hear nothing useful.",
        " - SUCCESS: You overhear Vignar has confirmation the Stormcloaks will attack Whiterun and he will not stand against them.",
        " - SUCCESS WITH STYLE: You also overhear Ulfric has asked Vignar to become Jarl if the Stormcloaks win; Vignar has agreed.",
        "After rolling, call resolve_vignar_eorlund_notice(state, outcome='fail|success|sws').",
        "OPTION: After the overhear (or even if you fail), you may approach Vignar to talk politics as Eorlund steps away."
    ]


def resolve_vignar_eorlund_notice(state: Dict[str, Any], outcome: NoticeOutcome) -> None:
    flags = _flags(state)
    if flags.get("jorvaskr_vignar_notice_resolved"):
        return

    flags["jorvaskr_vignar_notice_pending"] = False
    flags["jorvaskr_vignar_notice_resolved"] = True
    flags["jorvaskr_vignar_notice_outcome"] = outcome

    if outcome == "success":
        flags["vignar_overhear_stormcloak_attack_whiterun"] = True
        flags["vignar_overhear_ulfric_jarl_offer"] = False

    if outcome == "sws":
        flags["vignar_overhear_stormcloak_attack_whiterun"] = True
        flags["vignar_overhear_ulfric_jarl_offer"] = True

        # Unlock memory quest stub that activates at Battle of Whiterun Countdown 6/8.
        _ensure_quest_entry(
            state,
            quest_id="greymane_and_the_greater",
            status="memory",
            note="I remember what Vignar said when I first entered Jorrvaskr’s living hall... but there’s no reason to act yet."
        )


# ──────────────────────────────────────────────────────────────────────────
# Vignar politics approach (trust deltas + Athis duel influence)
# Stores a simple local trust meter in state['npc_trust'].
# ──────────────────────────────────────────────────────────────────────────
def resolve_vignar_politics_talk(
    state: Dict[str, Any],
    pc_stance: WarStance,
    inferred_vignar_side: Optional[WarStance] = None
) -> Dict[str, Any]:
    flags = _flags(state)
    flags["jorvaskr_vignar_politics_talk_done"] = True

    npc_trust = state.setdefault("npc_trust", {})
    vignar = npc_trust.setdefault("vignar_gray_mane", {"trust": 50, "scale": "0-100"})
    trust = int(vignar.get("trust", 50))

    # Base for engaging sincerely
    delta = 20

    # Athis duel influence
    athis = _athis_duel_result(state)
    if athis == "win":
        delta += 10
    elif athis == "lose":
        delta += 5

    # War stance effect
    if pc_stance == "pro_stormcloak":
        delta += 10  # “respects greatly”
    elif pc_stance == "pro_empire":
        # distrust penalty; halved if Athis duel occurred (per spec)
        penalty = -20
        if athis in ("win", "lose"):
            penalty = penalty // 2  # halved
        delta += penalty

    # Optional: If player explicitly INFERS Vignar correctly, small bonus;
    # if they incorrectly insist he’s Imperial, soften the penalty slightly.
    if inferred_vignar_side == "pro_stormcloak":
        delta += 5
    elif inferred_vignar_side == "pro_empire":
        # “trust lost halved” already handled above; add no extra penalty
        pass

    vignar["trust"] = max(0, min(100, trust + delta))

    return {"vignar_trust": vignar["trust"], "delta": delta, "athis_duel": athis}


# ──────────────────────────────────────────────────────────────────────────
# Harbinger Room first-entry description + Kodlak/Vilkas foreshadow scene
# ──────────────────────────────────────────────────────────────────────────
def harbinger_room_description_once(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    if flags.get("jorvaskr_harbinger_room_description_done"):
        return []
    flags["jorvaskr_harbinger_room_description_done"] = True
    return [
        "[TRIGGERED DESCRIPTION] Kodlak’s chamber is humble for a legend.",
        "A simple bed, a small writing table, weapons kept clean not for vanity but ritual. "
        "The room smells of old leather and juniper. Here, the Harbinger is not a myth. He’s a man carrying a hall on his shoulders."
    ]


def kodlak_vilkas_foreshadow_scene_once(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    if flags.get("jorvaskr_kodlak_vilkas_scene_done"):
        return []
    flags["jorvaskr_kodlak_vilkas_scene_done"] = True

    # Set a join prompt marker so the GM can “resolve” it cleanly.
    flags["companions_join_request_pending"] = True

    return [
        "[SCRIPTED SCENE] As you reach the Harbinger’s door, you catch conversation inside.",
        "Vilkas (tight, controlled): “—I found it. The Glenmoril Coven. Not rumor. *Confirmed.*”",
        "Kodlak (quiet, tired): “Then it can be ended. Not today… but someday. And that matters.”",
        "Vilkas: “You really believe a man can walk back from it.”",
        "Kodlak: “I believe a man can choose what he becomes. That is the only kind of honor that lasts.”",
        "",
        "[CHOICE] You may knock and ask to join the Companions now.",
        "If the PC asks to join, call resolve_kodlak_join_request(state, accepted=True).",
        "If the PC walks away, call resolve_kodlak_join_request(state, accepted=False)."
    ]


def resolve_kodlak_join_request(state: Dict[str, Any], accepted: bool) -> None:
    flags = _flags(state)
    flags["companions_join_request_pending"] = False
    flags["companions_join_request_resolved"] = True
    flags["companions_join_request_accepted"] = accepted

    if not accepted:
        return

    # Guard: companions_investigate_jorrvaskr must be active or completed
    # before Proving Honor can be activated (Phase 1 spec gate).
    investigate_status = _quest_status(state, "companions_investigate_jorrvaskr")
    if investigate_status not in ("active", "completed"):
        return

    # Activate Proving Honor in companions_state if present.
    cstate = _companions_state(state)
    qprog = cstate.setdefault("quest_progress", {})
    cstate["active_quest"] = "companions_proving_honor"
    qprog["companions_proving_honor"] = "active"

    # Promote previously unlocked side quests from locked -> active.
    for quest_id in ("companions_honorable_combat", "companions_prey_and_predator"):
        if _quest_status(state, quest_id) == "locked":
            _set_quest_status(state, quest_id, "active")

    # Ensure Swiftclaw clocks exist if Prey and Predator is active
    if _quest_status(state, "companions_prey_and_predator") == "active":
        _ensure_clock(state, "race_is_on_with_aela", "Race is on with Aela", 5, ["0", "1", "2", "3", "4", "5"])
        _ensure_clock(state, "tracking_swiftclaw", "Tracking Swiftclaw", 3, ["0", "1", "2", "3"])

    # Ensure Honor Proving contracts clock exists (gates Dustman’s Cairn summon)
    _ensure_clock(state, "honor_proving_contracts_done", "Honor Proving — Contracts Done", 2, ["0", "1", "2"])


# ──────────────────────────────────────────────────────────────────────────
# Vilkas Trial by Combat (first mild consequence wins) + escort selection
# ──────────────────────────────────────────────────────────────────────────
def offer_vilkas_trial_once(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_proving_honor":
        return []
    if flags.get("vilkas_trial_resolved") or flags.get("vilkas_trial_offered"):
        return []
    flags["vilkas_trial_offered"] = True
    flags["vilkas_trial_pending"] = True

    return [
        "[SCRIPTED TRIAL] Kodlak sees fire in you and asks Vilkas to test your combat prowess in the yard.",
        "Rule: Sparring brawl (no killing). First to impose a Mild consequence wins.",
        "Outcome does NOT decide whether you may join. You will be invited in either way.",
        "If the PC wins, Vilkas is genuinely shocked and will think twice before talking down to you.",
        "After the duel, call resolve_vilkas_trial(state, pc_won=True/False)."
    ]


def resolve_vilkas_trial(state: Dict[str, Any], pc_won: bool) -> None:
    flags = _flags(state)
    flags["vilkas_trial_pending"] = False
    flags["vilkas_trial_resolved"] = True
    flags["vilkas_trial_pc_won"] = pc_won

    # Record aspect reward as a pending PC update (actual file patch is handled post-session)
    pending = state.setdefault("pending_pc_updates", [])
    target_pc_id = state.get("active_pc_id", "pc_elitrof_whitemane")
    pending.append({"type": "add_aspect", "target": target_pc_id, "aspect": "Whelp of the Companions"})

    # Vilkas trust note stored in companions_state (lightweight)
    cstate = _companions_state(state)
    trust = cstate.setdefault("inner_circle_trust", {})
    trust["vilkas"] = int(trust.get("vilkas", 0)) + (10 if pc_won else 0)

    # Escort selection after duel:
    # Priority: If Prey and Predator active -> Aela escorts.
    # Else if Honorable Combat active -> Farkas escorts.
    # Else -> Vilkas escorts.
    escort = "vilkas"
    if _quest_status(state, "companions_prey_and_predator") == "active":
        escort = "aela"
    elif _quest_status(state, "companions_honorable_combat") == "active":
        escort = "farkas"

    flags["whelps_quarters_escort"] = escort


def escort_to_whelps_quarters_scene(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    if not flags.get("vilkas_trial_resolved"):
        return []
    if flags.get("whelps_quarters_escort_scene_done"):
        return []
    flags["whelps_quarters_escort_scene_done"] = True

    escort = flags.get("whelps_quarters_escort", "vilkas")

    if escort == "aela":
        return [
            "[ESCORT] Aela appears after the yard trial and gestures you along.",
            "On the walk, she tells you *her* version of the Companions’ history: the hunt, the great Harbingers who understood teeth and winter. "
            "She praises Kodlak… and talks up Skjor with a reverence she refuses to explain."
        ]
    if escort == "farkas":
        return [
            "[ESCORT] Farkas claps your shoulder and guides you through Jorrvaskr like you belong.",
            "He gives you the real story: Ysgramor, Atmora, Saarthal, why the Companions carry legend like a burden and a blessing."
        ]
    return [
        "[ESCORT] Vilkas leads you with clipped words, but the history he gives is precise and true.",
        "He speaks of standards: why Jorrvaskr must outlast pride, and why discipline is the only thing that keeps power from becoming rot."
    ]


def whelps_quarters_first_entry_banter(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    if not flags.get("vilkas_trial_resolved"):
        return []
    if flags.get("whelps_quarters_intro_done"):
        return []
    flags["whelps_quarters_intro_done"] = True

    athis = _athis_duel_result(state)
    lines = ["[WHELPS QUARTERS] The whelps are here when you arrive: Ria, Torvar, Athis, Njada. The room smells like leather, steel oil, and loud opinions."]
    if athis == "win":
        lines += [
            "Ria grins: “So that was you. The outsider who made Athis shut up for a minute.”",
            "Torvar laughs: “You keep that up, you’ll be Circle before you’ve learned where they hide the good mead.”",
            "Njada eyes you hard: “One win doesn’t make you family. But… it’s a start.”",
            "Athis gives a short nod. Respect, not friendship. Yet."
        ]
    elif athis == "lose":
        lines += [
            "Torvar smirks: “Heh. You took the challenge at least. Most don’t.”",
            "Ria softens it: “You didn’t fold. That matters here.”",
            "Njada: “Train harder. Jorrvaskr doesn’t hand out pity.”",
            "Athis: “Again sometime. You learn faster when it costs you.”"
        ]
    else:
        lines += [
            "Ria: “New face. You looking to join?”",
            "Torvar: “If you’re here, you’re either brave or stupid. Sometimes both.”",
            "Njada: “Prove you can stand. Then we talk.”",
            "Athis watches you quietly, weighing your posture like it’s a sentence."
        ]
    lines.append("[BONDING HOOK] Offer the PC a chance to bond with any of: Ria, Torvar, Athis, Njada (short roleplay beats + small loyalty ticks at GM discretion).")
    return lines


# ──────────────────────────────────────────────────────────────────────────
# Honor Proving contracts clock -> Dustman’s Cairn summon trigger helper
# ──────────────────────────────────────────────────────────────────────────
def maybe_dustmans_cairn_summon(state: Dict[str, Any]) -> List[str]:
    flags = _flags(state)
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_proving_honor":
        return []
    if flags.get("dustmans_briefing_done"):
        return []
    if flags.get("dustmans_cairn_summon_done"):
        return []
    cur = _get_clock_progress(state, "honor_proving_contracts_done")
    mx = int(_clocks(state).get("honor_proving_contracts_done", {}).get("total_segments", 2))
    if cur < mx:
        return []

    flags["dustmans_cairn_summon_done"] = True
    return [
        "[SUMMON] A whelp finds you: “Harbinger wants you. Skjor is there too.”",
        "In Kodlak’s chamber, Kodlak and Skjor wait. The Hall’s tone is different now: you’ve done the contracts. Now you get the real trial.",
        "MISSION: Retrieve the next fragment of Wuuthrad from Dustman’s Cairn. (This advances Proving Honor into its dungeon phase.)"
    ]


def _set_partner(state: Dict[str, Any], partner: Partner) -> None:
    flags = _flags(state)
    flags["dustmans_partner"] = partner

    # Track in companions_state for visibility
    cstate = state.setdefault("companions_state", {})
    cstate["proving_honor_assigned_partner"] = partner

    # Also add them to active_companions list if the system uses it
    comps = state.setdefault("companions", {})
    active = comps.setdefault("active_companions", [])
    # Avoid duplicates by npc_id/name prefix match
    key = partner
    exists = False
    for c in active:
        if isinstance(c, dict):
            if str(c.get("npc_id", c.get("id", ""))).lower().startswith(key):
                exists = True
        else:
            if str(c).lower().startswith(key):
                exists = True
    if not exists:
        # Keep it lightweight: npc_id is enough for trigger_utils.is_companion_present
        active.append({"npc_id": partner, "name": partner.capitalize(), "loyalty": 50})


def _trust_delta_pending(state: Dict[str, Any], npc_id: str, delta: int) -> None:
    """
    We do NOT mutate data/npcs/*.json at runtime.
    We store pending trust deltas in state so the GM can patch or a post-step can apply.
    """
    pending = state.setdefault("pending_npc_updates", [])
    pending.append({"npc_id": npc_id, "type": "trust_clock_delta", "delta": delta})


def seed_silver_hand_join_offer(state: Dict[str, Any]) -> None:
    """
    Foreshadow joining the Silver Hand later IF beast blood is rejected (Purity track).
    We seed a dormant quest memory and a token flag.
    """
    flags = _flags(state)
    if flags.get("silver_hand_join_seeded"):
        return

    companions_state = state.get("companions_state", {}) or {}
    purity_track = companions_state.get("embraced_curse") is False  # rejected/never embraced

    if not purity_track:
        return

    flags["silver_hand_join_seeded"] = True
    flags["silver_hand_token_obtained"] = True

    q = _quests(state)
    if "silver_hand_contact" not in q["active"] and "silver_hand_contact" not in q["completed"]:
        q["active"].append("silver_hand_contact")


def dustmans_cairn_briefing_scene_once(state: Dict[str, Any]) -> List[str]:
    """
    Fires when Honor Proving — Contracts Done hits max and PC is in Harbinger’s Room.
    Branches based on completion of:
      - companions_prey_and_predator
      - companions_honorable_combat
    """
    flags = _flags(state)
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_proving_honor":
        return []
    if flags.get("dustmans_briefing_done"):
        return []

    contracts_clock = _clocks(state).get("honor_proving_contracts_done", {})
    contracts_max = int(contracts_clock.get("total_segments", 2) or 2)
    if _get_clock_progress(state, "honor_proving_contracts_done") < contracts_max:
        return []

    summon_already_done = bool(flags.get("dustmans_cairn_summon_done"))
    flags["dustmans_briefing_done"] = True
    flags["dustmans_cairn_summon_done"] = True

    prey_res = _quest_result(state, "companions_prey_and_predator")
    honor_res = _quest_result(state, "companions_honorable_combat")

    lines: List[str] = []
    summon_prefix = "[SUMMON] " if not summon_already_done else ""
    lines.append(f"{summon_prefix}You are called to Kodlak’s chamber. Skjor is already there, arms crossed. Kodlak’s gaze is calm, but heavy with intent.")
    lines.append("On the table: a map mark and a fragment case. The air tastes like the moment before a storm breaks.")

    # Branch 1: Prey & Predator completed (success OR fail)
    if prey_res in ("success", "failure"):
        # Trust delta to Skjor: +20 success, +10 failure
        _trust_delta_pending(state, "skjor", 20 if prey_res == "success" else 10)

        lines.append("[BRANCH] Skjor leads the briefing this time. His tone is grudging, but not hostile. He has seen what you can do in the wild.")
        lines.append("Skjor: “Dustman’s Cairn. Draugr. And worse… men in silver who don’t belong down there.”")

        # Pair with Aela
        _set_partner(state, "aela")

        # Aela enters (sass vs fond if bond deepened)
        bond = bool(_flags(state).get("aela_bond_deepened")) or (prey_res == "success")
        if bond:
            lines.append("[NPC ENTERS] Aela steps in, glances at you, and the corner of her mouth almost becomes a smile.")
            lines.append('Aela: “Try to keep up. I don’t want to drag you out when the dead start clawing.” (fond, but pretending it’s not)')
        else:
            lines.append("[NPC ENTERS] Aela strides in like she owns the room, eyes sharp as arrowheads.")
            lines.append('Aela: “Hope you’re faster than you look, outsider.” (sassy, testing)')

    # Branch 2: Honorable Combat completed (success OR fail) and Prey branch did NOT trigger
    elif honor_res in ("success", "failure"):
        # Trust delta to Kodlak: +2 segments (clock-style) regardless; add +1 more if success
        # (Kept small because Kodlak trust clock is 0-6, not 0-100.)
        _trust_delta_pending(state, "kodlak_whitemane", 2 if honor_res == "failure" else 3)

        lines.append("[BRANCH] Kodlak leads the briefing personally. His voice is gentle, but it pins the room in place.")
        lines.append('Kodlak: “This is a trial of who you are when steel is easy and honor is hard.”')

        # Pair with Vilkas
        _set_partner(state, "vilkas")

        # Vilkas enters with tone keyed to the yard trial outcome (from Phase 2)
        pc_won = bool(_flags(state).get("vilkas_trial_pc_won"))
        if pc_won:
            lines.append("[NPC ENTERS] Vilkas enters, nods once to you. Respect, controlled and real.")
            lines.append('Vilkas: “You’ve got hands. Now show you’ve got judgment.”')
        else:
            lines.append("[NPC ENTERS] Vilkas enters like a commander entering a war room.")
            lines.append('Vilkas: “Do not improvise. Do not posture. Do what you’re told and come back alive.”')

    # Default branch
    else:
        lines.append("[DEFAULT] Kodlak leads. Skjor watches, silent. This is the traditional path: prove reliability, then earn the real work.")
        _set_partner(state, "farkas")
        lines.append("[NPC ASSIGNED] Farkas is chosen to go with you to Dustman’s Cairn. He rolls his shoulders like he’s been waiting for this all day.")
        lines.append('Farkas: “Let’s go crack a barrow, then. Easy.” (it is not easy)')

    # Mission briefing (shared)
    lines.append("")
    lines.append("[MISSION] Retrieve the Wuuthrad fragment from Dustman’s Cairn. Expect draugr, traps, and Silver Hand defilers.")
    seed_silver_hand_join_offer(state)
    lines.append("GM NOTE: After this briefing, set location to 'Dustman’s Cairn — Entrance' to begin the dungeon triggers.")

    return lines
