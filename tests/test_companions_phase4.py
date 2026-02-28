#!/usr/bin/env python3
"""
Tests for Phase 4 Companions arc: Schism events and Jorrvaskr assault.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import companions_schism_events as schism
import jorvaskr_assault_events as assault


# ──────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────

def _base_state(active_quest: str = "companions_circle_revelation") -> dict:
    return {
        "companions_state": {"active_quest": active_quest},
        "scene_flags": {},
        "clocks": {
            "companions_schism_tradition_vs_newway": {"current_progress": 0, "total_segments": 6},
            "companions_whelps_polarization": {"current_progress": 0, "total_segments": 4},
            "silver_hand_assault_preparation": {"current_progress": 0, "total_segments": 6},
        },
        "npc_trust": {},
    }


# ──────────────────────────────────────────────────────────────────────────
# Circle Revelation
# ──────────────────────────────────────────────────────────────────────────

def test_circle_revelation_scene_fires_once():
    """Circle revelation scene fires once when active quest is set."""
    state = _base_state("companions_circle_revelation")
    first = schism.circle_revelation_scene_once(state)
    second = schism.circle_revelation_scene_once(state)

    assert len(first) > 0, "Expected scene to fire on first call"
    assert len(second) == 0, "Expected scene to fire only once"
    assert any("UNDERFORGE" in e for e in first), "Expected Underforge scene"
    assert any("CHOICE" in e for e in first), "Expected choice prompt"


def test_circle_revelation_scene_wrong_quest():
    """Circle revelation does not fire if active quest is wrong."""
    state = _base_state("companions_proving_honor")
    # Force active_quest to something else
    state["companions_state"]["active_quest"] = "companions_schism_pressure"
    events = schism.circle_revelation_scene_once(state)
    assert len(events) == 0


def test_resolve_circle_revelation_embrace():
    """Embracing sets beast_blood_embraced=True and advances to pack_run_night."""
    state = _base_state("companions_circle_revelation")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_circle_revelation(state, "embrace")

    assert state["companions_state"]["beast_blood_embraced"] is True
    assert state["companions_state"]["active_quest"] == "companions_pack_run_night"
    assert any("BEAST BLOOD EMBRACED" in e for e in events)
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 1, "Schism clock should tick +1 on embrace"


def test_resolve_circle_revelation_refuse():
    """Refusing sets beast_blood_embraced=False and advances to oath_of_purity."""
    state = _base_state("companions_circle_revelation")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_circle_revelation(state, "refuse")

    assert state["companions_state"]["beast_blood_embraced"] is False
    assert state["companions_state"]["active_quest"] == "companions_oath_of_purity"
    assert any("BEAST BLOOD REFUSED" in e for e in events)
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 1


def test_resolve_circle_revelation_idempotent():
    """Resolving twice is idempotent."""
    state = _base_state("companions_circle_revelation")
    schism._ensure_schism_clocks(state)
    schism.resolve_circle_revelation(state, "embrace")
    events2 = schism.resolve_circle_revelation(state, "refuse")
    assert len(events2) == 0, "Second call should return nothing"
    assert state["companions_state"]["beast_blood_embraced"] is True, "First choice preserved"


# ──────────────────────────────────────────────────────────────────────────
# Pack Run Night
# ──────────────────────────────────────────────────────────────────────────

def test_pack_run_night_fires_once():
    state = _base_state("companions_pack_run_night")
    first = schism.pack_run_night_scene_once(state)
    second = schism.pack_run_night_scene_once(state)
    assert len(first) > 0
    assert len(second) == 0


def test_resolve_pack_run_night_honest():
    state = _base_state("companions_pack_run_night")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_pack_run_night(state, honest=True)
    assert state["companions_state"]["active_quest"] == "companions_schism_pressure"
    assert state["scene_flags"].get("pack_run_told_kodlak_truth") is True
    assert any("HONEST" in e for e in events)
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 1


def test_resolve_pack_run_night_deceptive():
    state = _base_state("companions_pack_run_night")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_pack_run_night(state, honest=False)
    assert state["scene_flags"].get("circle_lied_to_kodlak") is True
    assert any("DECEPTION" in e for e in events)
    # No clock tick for deception
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 0


# ──────────────────────────────────────────────────────────────────────────
# Oath of Purity
# ──────────────────────────────────────────────────────────────────────────

def test_oath_of_purity_fires_once():
    state = _base_state("companions_oath_of_purity")
    first = schism.oath_of_purity_scene_once(state)
    second = schism.oath_of_purity_scene_once(state)
    assert len(first) > 0
    assert len(second) == 0


def test_resolve_oath_of_purity_take_oath():
    state = _base_state("companions_oath_of_purity")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_oath_of_purity(state, take_oath=True)
    assert state["scene_flags"].get("oath_of_purity_taken") is True
    assert state["companions_state"]["active_quest"] == "companions_schism_pressure"
    assert any("OATH TAKEN" in e for e in events)
    trust = state["npc_trust"].get("kodlak_whitemane", {}).get("trust", 50)
    assert trust >= 60, "Kodlak trust should increase"
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 1


def test_resolve_oath_of_purity_decline():
    state = _base_state("companions_oath_of_purity")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_oath_of_purity(state, take_oath=False)
    assert state["scene_flags"].get("oath_of_purity_declined") is True
    assert any("NEUTRAL" in e for e in events)
    # No clock tick for declining
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 0


# ──────────────────────────────────────────────────────────────────────────
# Schism pressure scenes
# ──────────────────────────────────────────────────────────────────────────

def test_schism_secrecy_argument_fires_once():
    state = _base_state("companions_schism_pressure")
    first = schism.schism_secrecy_argument_scene(state)
    second = schism.schism_secrecy_argument_scene(state)
    assert len(first) > 0
    assert len(second) == 0
    assert any("SECRECY ARGUMENT" in e for e in first)


def test_schism_whelp_recruitment():
    state = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state)
    events = schism.schism_whelp_recruitment_scene(state, whelp="athis")
    assert len(events) > 0
    assert any("WHELP RECRUITMENT" in e for e in events)


def test_resolve_schism_scene_mediate():
    state = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state)
    # Pre-set clock to 3
    state["clocks"]["companions_schism_tradition_vs_newway"]["current_progress"] = 3
    events = schism.resolve_schism_scene(state, "secrecy_argument", "mediate")
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 2, "Mediation should reduce clock by 1"
    assert any("MEDIATED" in e for e in events)


def test_resolve_schism_scene_ignore_triggers_breakpoint():
    state = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state)
    state["clocks"]["companions_schism_tradition_vs_newway"]["current_progress"] = 5
    events = schism.resolve_schism_scene(state, "secrecy_argument", "ignore")
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 6
    assert any("BREAKPOINT TRIGGERED" in e for e in events)
    assert state["companions_state"]["active_quest"] == "companions_schism_breakpoint"


def test_resolve_whelp_recruitment_polarization():
    state = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state)
    schism.resolve_whelp_recruitment(state, "ria", "new_way")
    schism.resolve_whelp_recruitment(state, "torvar", "tradition")
    schism.resolve_whelp_recruitment(state, "athis", "new_way")
    events = schism.resolve_whelp_recruitment(state, "njada", "tradition")
    clock_val = schism._get_clock_progress(state, "companions_whelps_polarization")
    assert clock_val == 4
    assert state["companions_state"].get("whelps_polarized") is True
    assert any("FULLY POLARIZED" in e for e in events)


# ──────────────────────────────────────────────────────────────────────────
# Schism breakpoint
# ──────────────────────────────────────────────────────────────────────────

def test_schism_breakpoint_reconcile():
    state = _base_state("companions_schism_breakpoint")
    schism._ensure_schism_clocks(state)
    state["clocks"]["companions_schism_tradition_vs_newway"]["current_progress"] = 6
    events = schism.resolve_schism_breakpoint(state, "reconcile")
    assert state["companions_state"]["schism_resolution"] == "reconcile"
    assert state["companions_state"]["active_quest"] == "companions_silver_hand_intel"
    clock_val = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert clock_val == 3, "Reconcile should reset clock to 3"
    assert any("RECONCILE" in e for e in events)


def test_schism_breakpoint_civil_war():
    state = _base_state("companions_schism_breakpoint")
    schism._ensure_schism_clocks(state)
    events = schism.resolve_schism_breakpoint(state, "civil_war")
    assert state["companions_state"].get("internal_civil_war") is True
    clock_val = schism._get_clock_progress(state, "silver_hand_assault_preparation")
    assert clock_val == 2, "Civil war should tick assault prep clock +2"
    assert any("CIVIL WAR" in e for e in events)


def test_schism_breakpoint_reform_trust_deltas():
    state = _base_state("companions_schism_breakpoint")
    schism._ensure_schism_clocks(state)
    state["npc_trust"]["skjor"] = {"trust": 60, "scale": "0-100"}
    state["npc_trust"]["aela_the_huntress"] = {"trust": 70, "scale": "0-100"}
    schism.resolve_schism_breakpoint(state, "reform")
    assert state["npc_trust"]["skjor"]["trust"] == 45
    assert state["npc_trust"]["aela_the_huntress"]["trust"] == 55


def test_schism_breakpoint_tradition_trust_deltas():
    state = _base_state("companions_schism_breakpoint")
    schism._ensure_schism_clocks(state)
    state["npc_trust"]["kodlak_whitemane"] = {"trust": 60, "scale": "0-100"}
    state["npc_trust"]["skjor"] = {"trust": 50, "scale": "0-100"}
    schism.resolve_schism_breakpoint(state, "tradition")
    assert state["npc_trust"]["kodlak_whitemane"]["trust"] == 50
    assert state["npc_trust"]["skjor"]["trust"] == 65


def test_schism_breakpoint_idempotent():
    state = _base_state("companions_schism_breakpoint")
    schism._ensure_schism_clocks(state)
    schism.resolve_schism_breakpoint(state, "reform")
    events2 = schism.resolve_schism_breakpoint(state, "tradition")
    assert len(events2) == 0, "Second call should be no-op"
    assert state["companions_state"]["schism_resolution"] == "reform"


# ──────────────────────────────────────────────────────────────────────────
# Schism triggers dispatcher
# ──────────────────────────────────────────────────────────────────────────

def test_schism_triggers_underforge():
    state = _base_state("companions_circle_revelation")
    events = schism.schism_triggers("underforge", state)
    assert any("UNDERFORGE" in e for e in events)


def test_schism_triggers_tundra_beast_blood():
    state = _base_state("companions_pack_run_night")
    events = schism.schism_triggers("whiterun_plains_tundra", state)
    assert len(events) > 0
    assert any("PACK RUN" in e for e in events)


def test_schism_triggers_jorrvaskr_schism_pressure():
    state = _base_state("companions_schism_pressure")
    events = schism.schism_triggers("jorrvaskr_downstairs", state)
    # Should emit at least the secrecy argument scene (first time)
    assert any("SECRECY ARGUMENT" in e for e in events)


def test_schism_triggers_no_events_wrong_location():
    state = _base_state("companions_circle_revelation")
    events = schism.schism_triggers("riverwood_inn", state)
    assert len(events) == 0


def test_schism_triggers_elder_ultimatum_gated_by_clock():
    """Elder ultimatum should NOT fire when clock < 4; should fire when clock >= 4."""
    state_low = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state_low)
    state_low["clocks"]["companions_schism_tradition_vs_newway"]["current_progress"] = 2
    events_low = schism.schism_triggers("jorrvaskr_downstairs", state_low)
    assert not any("ELDER ULTIMATUM" in e for e in events_low), \
        "Elder ultimatum should not fire at clock < 4"

    state_high = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state_high)
    state_high["clocks"]["companions_schism_tradition_vs_newway"]["current_progress"] = 4
    events_high = schism.schism_triggers("jorrvaskr_downstairs", state_high)
    assert any("ELDER ULTIMATUM" in e for e in events_high), \
        "Elder ultimatum should fire at clock >= 4"


def test_resolve_schism_scene_idempotent():
    """Calling resolve_schism_scene twice for the same scene should be a no-op on second call."""
    state = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state)
    state["clocks"]["companions_schism_tradition_vs_newway"]["current_progress"] = 3
    schism.resolve_schism_scene(state, "secrecy_argument", "ignore")
    clock_after_first = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    events2 = schism.resolve_schism_scene(state, "secrecy_argument", "mediate")
    clock_after_second = schism._get_clock_progress(state, "companions_schism_tradition_vs_newway")
    assert len(events2) == 0, "Second call should be no-op"
    assert clock_after_second == clock_after_first, "Clock should not change on second call"


def test_resolve_whelp_recruitment_idempotent():
    """Calling resolve_whelp_recruitment twice for the same whelp is a no-op on second call."""
    state = _base_state("companions_schism_pressure")
    schism._ensure_schism_clocks(state)
    schism.resolve_whelp_recruitment(state, "ria", "new_way")
    clock_after_first = schism._get_clock_progress(state, "companions_whelps_polarization")
    events2 = schism.resolve_whelp_recruitment(state, "ria", "tradition")
    clock_after_second = schism._get_clock_progress(state, "companions_whelps_polarization")
    assert len(events2) == 0, "Second call should be no-op"
    assert clock_after_second == clock_after_first, "Clock should not change on second call"
    assert state["scene_flags"]["whelp_ria_side"] == "new_way", "First choice preserved"


def test_resolve_pack_run_night_ensures_clocks():
    """resolve_pack_run_night should work even without pre-initialized clocks."""
    state = {
        "companions_state": {"active_quest": "companions_pack_run_night"},
        "scene_flags": {},
    }
    events = schism.resolve_pack_run_night(state, honest=True)
    assert len(events) > 0, "Should work without pre-initialized clocks"
    assert "companions_schism_tradition_vs_newway" in state.get("clocks", {})


def test_resolve_oath_of_purity_ensures_clocks():
    """resolve_oath_of_purity should work even without pre-initialized clocks."""
    state = {
        "companions_state": {"active_quest": "companions_oath_of_purity"},
        "scene_flags": {},
    }
    events = schism.resolve_oath_of_purity(state, take_oath=True)
    assert len(events) > 0, "Should work without pre-initialized clocks"
    assert "companions_schism_tradition_vs_newway" in state.get("clocks", {})


def test_elder_ultimatum_ensures_clocks():
    """schism_elder_ultimatum_scene should work without pre-initialized clocks."""
    state = {
        "companions_state": {"active_quest": "companions_schism_pressure"},
        "scene_flags": {},
    }
    events = schism.schism_elder_ultimatum_scene(state)
    assert len(events) > 0, "Should work without pre-initialized clocks"


# ──────────────────────────────────────────────────────────────────────────
# Assault events — defense pool
# ──────────────────────────────────────────────────────────────────────────

def _assault_state(resolution: str = "reconcile") -> dict:
    state = _base_state("companions_jorvaskr_assault")
    state["companions_state"]["schism_resolution"] = resolution
    state["clocks"]["silver_hand_assault_preparation"]["current_progress"] = 6
    return state


def test_defense_pool_base_capacity():
    state = _assault_state("reform")
    pool = assault._build_defense_pool(state)
    assert pool["capacity"] == 6, "Base pool has 6 defenders"
    assert "kodlak_whitemane" in pool["defenders"]
    assert "skjor" in pool["defenders"]


def test_defense_pool_civil_war_modifier():
    state = _assault_state("civil_war")
    state["companions_state"]["internal_civil_war"] = True
    pool = assault._build_defense_pool(state)
    assert pool["capacity"] == 4, "Civil war reduces pool by 2"
    assert any("civil_war" in m for m in pool["modifiers_applied"])


def test_defense_pool_reconcile_modifier():
    state = _assault_state("reconcile")
    pool = assault._build_defense_pool(state)
    assert pool["capacity"] == 7, "Reconcile adds +1 to pool"


def test_defense_pool_skjor_already_dead():
    state = _assault_state("reform")
    state["companions_state"]["skjor_dead"] = True
    pool = assault._build_defense_pool(state)
    assert "skjor" not in pool["defenders"]
    assert pool["capacity"] == 5


def test_apply_defender_consequence_first_hit():
    state = _assault_state()
    events = assault.apply_defender_consequence(state, "farkas", "Shoulder Wound")
    pool = assault._build_defense_pool(state)
    assert pool["defenders"]["farkas"]["consequence"] == "Shoulder Wound"
    assert pool["defenders"]["farkas"]["status"] == "active"
    assert any("POOL" in e for e in events)


def test_apply_defender_consequence_second_hit_kills():
    state = _assault_state()
    assault.apply_defender_consequence(state, "vilkas", "First Wound")
    events = assault.apply_defender_consequence(state, "vilkas", "Second Wound")
    pool = assault._build_defense_pool(state)
    assert pool["defenders"]["vilkas"]["status"] == "taken_out"
    assert any("taken out" in e.lower() for e in events)


def test_apply_lethal_risk_npc_triggers_save_gate():
    state = _assault_state()
    events = assault.apply_defender_consequence(state, "kodlak_whitemane", "Killing Blow")
    assert any("SAVE GATE" in e for e in events)


def test_save_gate_success_preserves_npc():
    state = _assault_state()
    assault.apply_defender_consequence(state, "kodlak_whitemane", "Near Fatal")
    events = assault.attempt_save_gate(state, "kodlak_whitemane", "success")
    pool = assault._build_defense_pool(state)
    # NPC survives but is withdrawn (status: wounded) -- no longer "active"
    assert pool["defenders"]["kodlak_whitemane"]["status"] == "wounded"
    assert any("SUCCESS" in e for e in events)


def test_save_gate_failure_kills_npc():
    state = _assault_state()
    assault.apply_defender_consequence(state, "kodlak_whitemane", "Near Fatal")
    events = assault.attempt_save_gate(state, "kodlak_whitemane", "failure")
    pool = assault._build_defense_pool(state)
    assert pool["defenders"]["kodlak_whitemane"]["status"] == "taken_out"
    assert state["companions_state"].get("kodlak_dead_assault") is True
    assert any("FAILURE" in e for e in events)


# ──────────────────────────────────────────────────────────────────────────
# Assault acts
# ──────────────────────────────────────────────────────────────────────────

def test_assault_act1_fires_once():
    state = _assault_state()
    first = assault.assault_act1_outer_yard(state)
    second = assault.assault_act1_outer_yard(state)
    assert len(first) > 0
    assert len(second) == 0
    assert any("ACT 1" in e for e in first)


def test_assault_act2_fires_once():
    state = _assault_state()
    first = assault.assault_act2_grand_hall(state)
    second = assault.assault_act2_grand_hall(state)
    assert len(first) > 0
    assert len(second) == 0


def test_assault_act3_fires_once():
    state = _assault_state()
    first = assault.assault_act3_commanders_gambit(state)
    second = assault.assault_act3_commanders_gambit(state)
    assert len(first) > 0
    assert len(second) == 0
    assert any("ACT 3" in e for e in first)


def test_resolve_assault_act_held():
    state = _assault_state()
    events = assault.resolve_assault_act(state, 1, held=True)
    assert any("HELD" in e for e in events)


def test_resolve_assault_act_breached_applies_consequence():
    state = _assault_state()
    events = assault.resolve_assault_act(state, 1, held=False)
    pool = assault._build_defense_pool(state)
    assert pool["defenders"]["farkas"]["consequence"] is not None
    assert any("BREACHED" in e for e in events)


# ──────────────────────────────────────────────────────────────────────────
# Assault finale
# ──────────────────────────────────────────────────────────────────────────

def test_resolve_assault_finale_both_survive():
    state = _assault_state()
    events = assault.resolve_assault_finale(state, kodlak_alive=True, skjor_alive=True)
    cstate = state["companions_state"]
    assert cstate.get("kodlak_survived_assault") is True
    assert cstate.get("skjor_survived_assault") is True
    assert cstate.get("hall_shattered_state") is None or cstate.get("hall_shattered_state") is False
    assert cstate["active_quest"] == "companions_funeral_rites"
    assert any("ASSAULT REPELLED" in e for e in events)


def test_resolve_assault_finale_both_fall():
    state = _assault_state()
    events = assault.resolve_assault_finale(state, kodlak_alive=False, skjor_alive=False)
    cstate = state["companions_state"]
    assert cstate.get("kodlak_dead_assault") is True
    assert cstate.get("skjor_dead_assault") is True
    assert cstate.get("hall_shattered_state") is True
    assert any("HALL SHATTERED" in e for e in events)


def test_resolve_assault_finale_idempotent():
    state = _assault_state()
    assault.resolve_assault_finale(state, kodlak_alive=True, skjor_alive=True)
    events2 = assault.resolve_assault_finale(state, kodlak_alive=False, skjor_alive=False)
    assert len(events2) == 0
    assert state["companions_state"].get("kodlak_survived_assault") is True


# ──────────────────────────────────────────────────────────────────────────
# Assault triggers dispatcher
# ──────────────────────────────────────────────────────────────────────────

def test_jorrvaskr_assault_triggers_wrong_quest():
    state = _base_state("companions_schism_pressure")
    events = assault.jorrvaskr_assault_triggers("jorrvaskr_yard", state)
    assert len(events) == 0


def test_jorrvaskr_assault_triggers_skipped_when_cleared():
    state = _assault_state()
    state["companions_state"]["silver_hand_endgame_cleared"] = True
    state["clocks"]["silver_hand_assault_preparation"]["current_progress"] = 0
    events = assault.jorrvaskr_assault_triggers("jorrvaskr_yard", state)
    assert any("SKIPPED" in e for e in events)


def test_jorrvaskr_assault_triggers_act1_yard():
    state = _assault_state()
    events = assault.jorrvaskr_assault_triggers("jorrvaskr_yard", state)
    assert any("ACT 1" in e for e in events)


def test_jorrvaskr_assault_triggers_act3_harbinger():
    state = _assault_state()
    events = assault.jorrvaskr_assault_triggers("jorrvaskr_harbinger", state)
    assert any("ACT 3" in e for e in events)


def test_save_gate_wounds_npc_blocks_further_consequences():
    """After save gate success, wounded NPC cannot absorb further consequences."""
    state = _assault_state()
    assault.apply_defender_consequence(state, "kodlak_whitemane", "Near Fatal")
    assault.attempt_save_gate(state, "kodlak_whitemane", "success")
    # Now wounded -- further consequences should be blocked
    events = assault.apply_defender_consequence(state, "kodlak_whitemane", "Second Hit")
    pool = assault._build_defense_pool(state)
    assert pool["defenders"]["kodlak_whitemane"]["status"] == "wounded", \
        "Wounded NPC should stay wounded, not become taken_out from another hit"
    assert any("cannot apply" in e.lower() or "already" in e.lower() for e in events)


def test_save_gate_removed_npc_returns_message():
    """attempt_save_gate on an NPC removed from pool returns a clear message."""
    state = _assault_state("reform")
    # Remove Skjor pre-assault
    state["companions_state"]["skjor_dead"] = True
    events = assault.attempt_save_gate(state, "skjor", "failure")
    assert any("not in the defense pool" in e for e in events)


def test_jorrvaskr_assault_skipped_advances_quest():
    """When assault is skipped, active_quest advances to companions_funeral_rites."""
    state = _assault_state()
    state["companions_state"]["silver_hand_endgame_cleared"] = True
    state["clocks"]["silver_hand_assault_preparation"]["current_progress"] = 0
    assault.jorrvaskr_assault_triggers("jorrvaskr_yard", state)
    assert state["companions_state"]["active_quest"] == "companions_funeral_rites"


def test_jorrvaskr_assault_skipped_is_stable():
    """After skip, repeated trigger calls don't re-fire (state already advanced)."""
    state = _assault_state()
    state["companions_state"]["silver_hand_endgame_cleared"] = True
    state["clocks"]["silver_hand_assault_preparation"]["current_progress"] = 0
    assault.jorrvaskr_assault_triggers("jorrvaskr_yard", state)
    # second call: quest is now funeral_rites, so triggers return nothing
    events2 = assault.jorrvaskr_assault_triggers("jorrvaskr_yard", state)
    assert len(events2) == 0, "After quest advances, triggers should be silent"
