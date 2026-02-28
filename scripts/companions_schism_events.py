#!/usr/bin/env python3
"""
Companions Schism Events (Phase 4)

Emits schism scenes based on state flags and clock positions.
Covers the Tradition vs New Way arc from companions_circle_revelation
through companions_schism_breakpoint.

Integration:
- Called from scripts/triggers/whiterun_triggers.py for jorrvaskr locations.
- Standalone: call schism_triggers(loc, state) like dustmans_cairn_triggers.
"""

from __future__ import annotations
from typing import Any, Dict, List, Literal, Optional

SchismResolution = Literal["reconcile", "reform", "tradition", "civil_war"]
BreakpointChoice = Literal["reconcile", "reform", "tradition", "civil_war"]


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


def _companions_state(state: Dict[str, Any]) -> Dict[str, Any]:
    return state.setdefault("companions_state", {})


def _get_clock_progress(state: Dict[str, Any], clock_id: str) -> int:
    c = _clocks(state).get(clock_id, {})
    return int(c.get("current_progress", c.get("current", 0)) or 0)


def _tick_clock(state: Dict[str, Any], clock_id: str, amount: int = 1) -> int:
    clocks = _clocks(state)
    if clock_id not in clocks:
        return 0
    entry = clocks[clock_id]
    current = int(entry.get("current_progress", 0))
    total = int(entry.get("total_segments", 6))
    new_val = min(max(0, current + amount), total)
    entry["current_progress"] = new_val
    return new_val


def _ensure_schism_clocks(state: Dict[str, Any]) -> None:
    clocks = _clocks(state)
    defaults = {
        "companions_schism_tradition_vs_newway": {
            "name": "Tradition vs New Way",
            "current_progress": 0,
            "total_segments": 6,
        },
        "companions_whelps_polarization": {
            "name": "Whelps Polarization",
            "current_progress": 0,
            "total_segments": 4,
        },
        "silver_hand_assault_preparation": {
            "name": "Silver Hand: Assault Preparation",
            "current_progress": 0,
            "total_segments": 6,
        },
    }
    for clock_id, template in defaults.items():
        clocks.setdefault(clock_id, dict(template))


def _once(state: Dict[str, Any], key: str) -> bool:
    flags = _flags(state)
    if flags.get(key):
        return False
    flags[key] = True
    return True


def _beast_blood_embraced(state: Dict[str, Any]) -> Optional[bool]:
    cstate = _companions_state(state)
    val = cstate.get("beast_blood_embraced")
    if val is None:
        val = cstate.get("embraced_curse")
    if val is None:
        return None
    return bool(val)


# ──────────────────────────────────────────────────────────────────────────
# Circle Revelation: Underforge truth scene + branch prompt
# ──────────────────────────────────────────────────────────────────────────

def circle_revelation_scene_once(state: Dict[str, Any]) -> List[str]:
    """
    Fires when PC enters the Underforge and companions_circle_revelation is active.
    Returns the truth-reveal scene and branch prompt.
    """
    cstate = _companions_state(state)
    active = cstate.get("active_quest")
    if active not in ("companions_circle_revelation", "companions_proving_honor"):
        return []
    if not _once(state, "circle_revelation_scene_done"):
        return []

    _ensure_schism_clocks(state)

    return [
        "[SCRIPTED SCENE -- UNDERFORGE] The chamber beneath Jorrvaskr is cold in a way no fire fixes."
        " Moonlight falls through the stone grate overhead.",
        "Skjor stands at the basin. His voice is flat and certain:"
        ' "This is what we are. This is what the Circle has always been."',
        'Aela: "The blood is a gift. Ysgramor himself would have taken it."',
        'From the doorway, Kodlak\'s voice cuts through: "He would have refused it. As I wish I had."',
        "The silence that follows is a wall between two worlds.",
        "",
        "[CHOICE -- BEAST BLOOD OR PURITY]",
        "Option A -- Embrace the Beast Blood: Call resolve_circle_revelation(state, choice='embrace').",
        "Option B -- Refuse the Beast Blood: Call resolve_circle_revelation(state, choice='refuse').",
        "GM NOTE: Neither choice is forced. The Underforge's symbolism"
        " (Skyforge above = sun; Underforge below = moon) is worth narrating.",
    ]


def resolve_circle_revelation(
    state: Dict[str, Any], choice: Literal["embrace", "refuse"]
) -> List[str]:
    """
    Records the PC's Underforge decision and sets up the Phase 4 branch.
    """
    flags = _flags(state)
    if flags.get("circle_revelation_resolved"):
        return []
    flags["circle_revelation_resolved"] = True

    cstate = _companions_state(state)

    if choice == "embrace":
        cstate["beast_blood_embraced"] = True
        cstate["active_quest"] = "companions_pack_run_night"
        _tick_clock(state, "companions_schism_tradition_vs_newway", 1)
        return [
            "[BEAST BLOOD EMBRACED] You step forward. The blood is cold and then everything else is warm.",
            "Skjor nods. Aela watches you with something that is not quite pride, but close.",
            "Kodlak turns away without a word.",
            "Sets beast_blood_embraced=true. Schism clock +1 (secrecy enforced).",
            "Next quest: companions_pack_run_night.",
        ]
    else:
        cstate["beast_blood_embraced"] = False
        cstate["active_quest"] = "companions_oath_of_purity"
        _tick_clock(state, "companions_schism_tradition_vs_newway", 1)
        return [
            "[BEAST BLOOD REFUSED] You take one step back. \"I won't take it.\"",
            "Skjor's jaw tightens. Aela goes very still.",
            "Kodlak exhales slowly. When he turns, there is something like relief in his face.",
            "Sets beast_blood_embraced=false. Schism clock +1 (public position declared).",
            "Next quest: companions_oath_of_purity.",
        ]


# ──────────────────────────────────────────────────────────────────────────
# Pack Run Night (Beast Blood path)
# ──────────────────────────────────────────────────────────────────────────

def pack_run_night_scene_once(state: Dict[str, Any]) -> List[str]:
    """
    Fires when Beast Blood was embraced and companions_pack_run_night is active.
    """
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_pack_run_night":
        return []
    if not _once(state, "pack_run_night_scene_done"):
        return []

    return [
        "[SCRIPTED SCENE -- PACK RUN] The tundra at night is a different country.",
        "You run. Skjor is ahead and Aela is a shadow at your flank."
        " The world is scent and speed and the cold air that tastes like prey.",
        "For one scene you are something else entirely."
        " The Circle's power is not a gift -- it is a weight that also lifts you.",
        "",
        "GM NOTE: Run one full beast-form scene. Let the PC use Werewolf Form stunt."
        " Then call resolve_pack_run_night(state, honest=True/False).",
        "CHOICE: Does the PC tell Kodlak the truth when they return?",
    ]


def resolve_pack_run_night(state: Dict[str, Any], honest: bool) -> List[str]:
    flags = _flags(state)
    if flags.get("pack_run_night_resolved"):
        return []
    flags["pack_run_night_resolved"] = True

    cstate = _companions_state(state)
    cstate["active_quest"] = "companions_schism_pressure"

    if honest:
        flags["pack_run_told_kodlak_truth"] = True
        _tick_clock(state, "companions_schism_tradition_vs_newway", 1)
        return [
            "[HONEST] You tell Kodlak. His face is stone, but he listens.",
            "Kodlak: \"I won't pretend I'm not grieved. But I won't pretend you didn't choose honestly either.\"",
            "Schism clock +1 (division openly acknowledged).",
            "Next: companions_schism_pressure.",
        ]
    else:
        flags["circle_lied_to_kodlak"] = True
        return [
            "[DECEPTION] You say nothing."
            " Or you say something that isn't quite a lie but isn't the truth either.",
            "Kodlak watches you for a long moment. He does not press.",
            "The deception holds -- for now. Flag circle_lied_to_kodlak=true."
            " If exposed, Kodlak trust -10.",
            "Next: companions_schism_pressure.",
        ]


# ──────────────────────────────────────────────────────────────────────────
# Oath of Purity (Purity path)
# ──────────────────────────────────────────────────────────────────────────

def oath_of_purity_scene_once(state: Dict[str, Any]) -> List[str]:
    """
    Fires when Purity path was chosen and companions_oath_of_purity is active.
    """
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_oath_of_purity":
        return []
    if not _once(state, "oath_of_purity_scene_done"):
        return []

    return [
        "[SCRIPTED SCENE -- KODLAK'S CHAMBER] Kodlak speaks quietly, the door shut behind you.",
        "Kodlak: \"I have wanted this for years. Someone who would stand in that room and say no.\"",
        "Kodlak: \"I'm not asking you to lead a crusade. I'm asking you to be proof that it's possible.\"",
        "",
        "[CHOICE]",
        "Option A -- Take the Oath: Call resolve_oath_of_purity(state, take_oath=True).",
        "Option B -- Decline, remain neutral: Call resolve_oath_of_purity(state, take_oath=False).",
    ]


def resolve_oath_of_purity(state: Dict[str, Any], take_oath: bool) -> List[str]:
    flags = _flags(state)
    if flags.get("oath_of_purity_resolved"):
        return []
    flags["oath_of_purity_resolved"] = True

    cstate = _companions_state(state)
    cstate["active_quest"] = "companions_schism_pressure"

    trust = state.setdefault("npc_trust", {})
    kodlak = trust.setdefault("kodlak_whitemane", {"trust": 50, "scale": "0-100"})
    kodlak["trust"] = min(100, int(kodlak.get("trust", 50)) + 15)

    if take_oath:
        flags["oath_of_purity_taken"] = True
        _tick_clock(state, "companions_schism_tradition_vs_newway", 1)
        return [
            "[OATH TAKEN] Kodlak speaks the old binding words. You answer them.",
            "Skjor hears about it by nightfall. He finds you in the yard.",
            "Skjor: \"You want to cure the blood out of this hall. Over my body.\"",
            "Schism clock +1 (public humiliation of Tradition faction).",
            "Kodlak trust +15. Next: companions_schism_pressure.",
        ]
    else:
        flags["oath_of_purity_declined"] = True
        return [
            "[NEUTRAL] \"I'm not ready for an oath. But I'm not going to pretend I don't agree with you.\"",
            "Kodlak nods. \"Your silence is its own answer. And that's enough for now.\"",
            "Both factions are wary. No clock tick. Kodlak trust +15.",
            "Next: companions_schism_pressure.",
        ]


# ──────────────────────────────────────────────────────────────────────────
# Schism Pressure arc scenes
# ──────────────────────────────────────────────────────────────────────────

def schism_secrecy_argument_scene(state: Dict[str, Any]) -> List[str]:
    """
    One of three schism scenes. Should only fire if companions_schism_pressure is active.
    """
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_schism_pressure":
        return []
    if not _once(state, "schism_secrecy_argument_done"):
        return []

    return [
        "[SCHISM SCENE -- SECRECY ARGUMENT] Vilkas confronts Skjor in the downstairs hall."
        " The whelps freeze.",
        "Vilkas: \"The whole city knows something is wrong in Jorrvaskr."
        " Keeping secrets is making it worse.\"",
        "Skjor: \"You open that door, you invite everyone with a silver knife to walk through it.\"",
        "The argument spills into the corridor. Njada and Athis are watching.",
        "",
        "[CHOICE] Intervene (mediate / side with Vilkas / side with Skjor) or let it burn.",
        "- Mediate (Rapport vs Good +3): Success = schism clock -1, both sides respect PC.",
        "- Side with Vilkas: schism clock +0, Skjor trust -5, Vilkas trust +5.",
        "- Side with Skjor: schism clock +0, Vilkas trust -5, Skjor trust +5.",
        "- Do nothing: schism clock +1.",
        "Call resolve_schism_scene(state, 'secrecy_argument', outcome='mediate'|'new_way'|'tradition'|'ignore').",
    ]


def schism_whelp_recruitment_scene(state: Dict[str, Any], whelp: str = "ria") -> List[str]:
    """
    Whelp recruitment event. whelp should be one of: ria, torvar, athis, njada.
    """
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_schism_pressure":
        return []
    key = "schism_whelp_{}_recruited".format(whelp)
    if not _once(state, key):
        return []

    whelp_name = whelp.capitalize()
    return [
        "[SCHISM SCENE -- WHELP RECRUITMENT] Someone has been talking to {}.".format(whelp_name),
        "{} corners you in the yard with a question they've clearly rehearsed:".format(whelp_name),
        "\"Is the blood a gift or a curse?"
        " Because everyone keeps telling me different things and I need to know whose side I'm on.\"",
        "",
        "[CHOICE] Guide the whelp or let them choose alone.",
        "- Guide toward New Way: {} joins New Way faction. Whelps polarization +1.".format(whelp_name),
        "- Guide toward Tradition: {} joins Tradition faction. Whelps polarization +1.".format(whelp_name),
        "- Encourage neutrality (Empathy vs Fair +2): Success = whelp stays neutral, no polarization tick.",
        "- Say nothing: whelp chooses based on who they last spoke to.",
        "Call resolve_whelp_recruitment(state, '{}', side='new_way'|'tradition'|'neutral').".format(whelp),
    ]


def resolve_schism_scene(
    state: Dict[str, Any],
    scene_id: str,
    outcome: Literal["mediate", "new_way", "tradition", "ignore"],
) -> List[str]:
    flags = _flags(state)
    result_key = "schism_scene_{}_outcome".format(scene_id)
    flags[result_key] = outcome

    events: List[str] = []
    if outcome == "mediate":
        new_val = _tick_clock(state, "companions_schism_tradition_vs_newway", -1)
        events.append("[MEDIATED] Schism clock reduced. Current: {}/6.".format(new_val))
    elif outcome == "ignore":
        new_val = _tick_clock(state, "companions_schism_tradition_vs_newway", 1)
        events.append("[IGNORED] Schism clock advanced. Current: {}/6.".format(new_val))
        if new_val >= 6:
            events.append("[BREAKPOINT TRIGGERED] Schism clock full. companions_schism_breakpoint fires.")
            _companions_state(state)["active_quest"] = "companions_schism_breakpoint"
    else:
        events.append("[SIDED WITH {}] No clock change. Faction trust adjusted.".format(outcome.upper()))

    return events


def resolve_whelp_recruitment(
    state: Dict[str, Any],
    whelp: str,
    side: Literal["new_way", "tradition", "neutral"],
) -> List[str]:
    flags = _flags(state)
    flags["whelp_{}_side".format(whelp)] = side

    events: List[str] = []
    if side in ("new_way", "tradition"):
        new_val = _tick_clock(state, "companions_whelps_polarization", 1)
        events.append(
            "[{} COMMITS TO {}] Whelps polarization: {}/4.".format(
                whelp.upper(), side.upper(), new_val
            )
        )
        if new_val >= 4:
            _companions_state(state)["whelps_polarized"] = True
            events.append(
                "[WHELPS FULLY POLARIZED] All whelps have chosen sides. Defense pool -1 at assault."
            )
    else:
        events.append("[{} STAYS NEUTRAL] No polarization tick.".format(whelp.upper()))

    return events


def schism_elder_ultimatum_scene(state: Dict[str, Any]) -> List[str]:
    """
    Elder ultimatum scene -- fires late in schism pressure arc.
    """
    cstate = _companions_state(state)
    if cstate.get("active_quest") != "companions_schism_pressure":
        return []
    if not _once(state, "schism_elder_ultimatum_done"):
        return []

    _tick_clock(state, "companions_schism_tradition_vs_newway", 1)

    beast_blood = _beast_blood_embraced(state)

    if beast_blood:
        speaker = "Kodlak"
        ultimatum = (
            '"This hall cannot exist in two truths. Choose one, or I will."'
        )
    else:
        speaker = "Skjor"
        ultimatum = (
            '"Walk this path and you walk it alone.'
            ' The Circle does not beg for its own blood."'
        )

    return [
        "[SCHISM SCENE -- ELDER ULTIMATUM] {} calls you aside."
        " The hall is quiet in a way that means everyone is listening.".format(speaker),
        "{}: {}".format(speaker, ultimatum),
        "The schism clock ticks. This is the last warning before the breakpoint.",
        "Schism clock +1 (elder ultimatum). Call maybe_trigger_schism_breakpoint(state) to check.",
    ]


# ──────────────────────────────────────────────────────────────────────────
# Breakpoint check and resolution
# ──────────────────────────────────────────────────────────────────────────

def maybe_trigger_schism_breakpoint(state: Dict[str, Any]) -> List[str]:
    """
    Checks if the schism clock has reached 6/6 or if the PC is in breakpoint quest.
    Returns breakpoint prompt if triggered.
    """
    cstate = _companions_state(state)
    clock_val = _get_clock_progress(state, "companions_schism_tradition_vs_newway")

    if clock_val < 6 and cstate.get("active_quest") != "companions_schism_breakpoint":
        return []

    if not _once(state, "schism_breakpoint_moot_fired"):
        return []

    cstate["active_quest"] = "companions_schism_breakpoint"
    return [
        "[BREAKPOINT TRIGGERED] Kodlak calls the hall-moot. Every Companion in Jorrvaskr is present.",
        "Kodlak: \"This ends tonight. We choose together, or we don't choose at all.\"",
        "Skjor stands across the hall. Vilkas is at the wall. The whelps are scattered between them.",
        "",
        "[CHOICE -- SCHISM RESOLUTION]",
        "Option A -- Reconcile: Broker a shared code and partial transparency."
        " Call resolve_schism_breakpoint(state, 'reconcile').",
        "Option B -- Spearhead Reform: Lead public accountability and new oaths."
        " Call resolve_schism_breakpoint(state, 'reform').",
        "Option C -- Enforce Tradition: Back Tradition's secrecy and strength."
        " Call resolve_schism_breakpoint(state, 'tradition').",
        "Option D -- Let it Burn (Faction Civil War): Refuse to choose, or if whelps_polarized=true."
        " Call resolve_schism_breakpoint(state, 'civil_war').",
    ]


def resolve_schism_breakpoint(
    state: Dict[str, Any], choice: BreakpointChoice
) -> List[str]:
    """
    Records the schism breakpoint resolution and sets downstream flags.
    """
    flags = _flags(state)
    if flags.get("schism_breakpoint_resolved"):
        return []
    flags["schism_breakpoint_resolved"] = True

    cstate = _companions_state(state)
    cstate["schism_resolution"] = choice
    cstate["active_quest"] = "companions_silver_hand_intel"

    trust = state.setdefault("npc_trust", {})

    events: List[str] = []

    if choice == "reconcile":
        _clocks(state)["companions_schism_tradition_vs_newway"]["current_progress"] = 3
        events += [
            "[RECONCILE] You find words that both sides can stand under, if not agree with.",
            "The schism clock resets to 3/6. The truce is cold but functional.",
            "The Silver Hand will find a less fractured hall when they come."
            " Assault prep clock ticks slower.",
            "Next: companions_silver_hand_intel.",
        ]

    elif choice == "reform":
        skjor = trust.setdefault("skjor", {"trust": 50, "scale": "0-100"})
        skjor["trust"] = max(0, int(skjor.get("trust", 50)) - 15)
        aela = trust.setdefault("aela_the_huntress", {"trust": 50, "scale": "0-100"})
        aela["trust"] = max(0, int(aela.get("trust", 50)) - 15)
        events += [
            "[REFORM] You stand with Kodlak and call for public accountability and new oaths.",
            "New Way wins. Skjor trust -15. Aela trust -15.",
            "The hall shifts. Not everyone is happy. But a new doctrine is possible.",
            "Next: companions_silver_hand_intel.",
        ]

    elif choice == "tradition":
        kodlak = trust.setdefault("kodlak_whitemane", {"trust": 50, "scale": "0-100"})
        kodlak["trust"] = max(0, int(kodlak.get("trust", 50)) - 10)
        vilkas = trust.setdefault("vilkas", {"trust": 50, "scale": "0-100"})
        vilkas["trust"] = max(0, int(vilkas.get("trust", 50)) - 10)
        skjor = trust.setdefault("skjor", {"trust": 50, "scale": "0-100"})
        skjor["trust"] = min(100, int(skjor.get("trust", 50)) + 15)
        aela = trust.setdefault("aela_the_huntress", {"trust": 50, "scale": "0-100"})
        aela["trust"] = min(100, int(aela.get("trust", 50)) + 15)
        events += [
            "[TRADITION] You side with Skjor. Secrecy and strength. The old way endures.",
            "Kodlak trust -10. Vilkas trust -10. Skjor trust +15. Aela trust +15.",
            "Next: companions_silver_hand_intel.",
        ]

    else:  # civil_war
        cstate["internal_civil_war"] = True
        _tick_clock(state, "silver_hand_assault_preparation", 2)
        events += [
            "[FACTION CIVIL WAR] The moot breaks apart before it resolves."
            " Whelps pick sides. Duels in the yard.",
            "Sets internal_civil_war=true."
            " Silver Hand assault prep clock +2 (they exploit the chaos).",
            "Defense pool will be reduced by 2 at the assault.",
            "Next: companions_silver_hand_intel.",
        ]

    return events


# ──────────────────────────────────────────────────────────────────────────
# Top-level trigger dispatcher
# ──────────────────────────────────────────────────────────────────────────

def schism_triggers(loc: str, state: Dict[str, Any]) -> List[str]:
    """
    Main entry point. Call with current location string and campaign state.
    Returns a list of event strings to emit.
    """
    loc_lower = str(loc).lower()
    events: List[str] = []

    cstate = _companions_state(state)
    active_quest = cstate.get("active_quest", "")

    if "underforge" in loc_lower:
        events.extend(circle_revelation_scene_once(state))

    if any(k in loc_lower for k in ["tundra", "plains", "outside_whiterun", "whiterun_plains"]):
        events.extend(pack_run_night_scene_once(state))

    if any(k in loc_lower for k in ["harbinger", "kodlak", "harbinger_room"]):
        events.extend(oath_of_purity_scene_once(state))

    if any(k in loc_lower for k in ["jorrvaskr", "grand_hall", "downstairs", "jorrvaskr_downstairs"]):
        if active_quest == "companions_schism_pressure":
            events.extend(schism_secrecy_argument_scene(state))
            events.extend(schism_elder_ultimatum_scene(state))

        if active_quest in ("companions_schism_pressure", "companions_schism_breakpoint"):
            events.extend(maybe_trigger_schism_breakpoint(state))

    return events
