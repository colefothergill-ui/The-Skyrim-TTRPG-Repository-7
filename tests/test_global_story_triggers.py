#!/usr/bin/env python3
"""
Tests for global story triggers and hold-module wiring.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from triggers.falkreath_triggers import falkreath_location_triggers
from triggers.global_story_triggers import global_story_triggers
from triggers.hjaalmarch_triggers import hjaalmarch_location_triggers
from triggers.markarth_triggers import markarth_location_triggers
from triggers.pale_triggers import pale_location_triggers
from triggers.rift_triggers import rift_location_triggers
from triggers.solitude_triggers import solitude_location_triggers
from triggers.whiterun_triggers import whiterun_location_triggers
from triggers.windhelm_triggers import windhelm_location_triggers
from triggers.winterhold_triggers import winterhold_location_triggers


def _state(progress=6):
    return {
        "campaign_clocks": {"battle_of_whiterun_countdown": {"current_progress": progress}},
        "companions_state": {"quest_progress": {"greymane_and_the_greater": "memory"}},
    }


def test_global_story_trigger_activates_greymane_from_memory():
    campaign_state = _state(6)
    events = global_story_triggers("whiterun_city", campaign_state)

    assert any("[TOWN CRIER]" in event for event in events)
    assert any("[QUEST ACTIVATED]" in event for event in events)
    assert campaign_state["scene_flags"]["battle_of_whiterun_march_announcement_done"] is True
    qp = campaign_state["companions_state"]["quest_progress"]
    assert qp["greymane_and_the_greater"] == "active"


def test_global_story_trigger_uses_courier_in_wilderness():
    campaign_state = {"campaign_clocks": {"battle_of_whiterun_countdown": {"current_progress": 6}}}
    events = global_story_triggers("frozen_tundra_road", campaign_state)

    assert any("[COURIER]" in event for event in events)


def test_global_story_trigger_fires_once():
    campaign_state = _state(6)
    first = global_story_triggers("whiterun", campaign_state)
    second = global_story_triggers("whiterun", campaign_state)

    assert first
    assert second == []


def test_global_story_trigger_wired_to_hold_modules():
    trigger_calls = [
        (whiterun_location_triggers, "whiterun"),
        (windhelm_location_triggers, "windhelm"),
        (winterhold_location_triggers, "winterhold"),
        (solitude_location_triggers, "solitude"),https://github.com/colefothergill-ui/The-Skyrim-TTRPG-Repository-7/pull/40/conflict?name=tests%252Ftest_whiterun_triggers.py&ancestor_oid=5449b36e2c1f477de08d09f357cefd96ffea63bb&base_oid=99fa0005ff45693bc2833059525a03f544091ac7&head_oid=9e5b885b6935697d2771bee62e378b94757424e5
        (markarth_location_triggers, "markarth"),
        (rift_location_triggers, "riften"),
        (pale_location_triggers, "dawnstar"),
        (hjaalmarch_location_triggers, "morthal"),
        (falkreath_location_triggers, "falkreath"),
    ]

    for trigger_func, loc in trigger_calls:
        events = trigger_func(loc, _state(6))
        assert any(
            marker in event for event in events for marker in ("[TOWN CRIER]", "[COURIER]")
        ), f"Expected global march announcement in {trigger_func.__name__}"


def test_global_story_trigger_uses_clocks_namespace():
    """Battle countdown stored under 'clocks' (not 'campaign_clocks') should still fire."""
    campaign_state = {"clocks": {"battle_of_whiterun_countdown": {"current_progress": 6}}}
    events = global_story_triggers("whiterun_city", campaign_state)
    assert any("[TOWN CRIER]" in e for e in events), "Expected town crier when clock in 'clocks' namespace"


def test_global_story_trigger_activates_greymane_from_companions_state():
    """Greymane quest stored in companions_state.quest_progress as 'memory' should activate."""
    campaign_state = {
        "campaign_clocks": {"battle_of_whiterun_countdown": {"current_progress": 6}},
        "companions_state": {
            "quest_progress": {"greymane_and_the_greater": "memory"},
        },
    }
    events = global_story_triggers("whiterun_city", campaign_state)
    assert any("[QUEST ACTIVATED]" in e for e in events), "Expected [QUEST ACTIVATED] for Greymane"
    assert campaign_state["companions_state"]["quest_progress"]["greymane_and_the_greater"] == "active", (
        "Expected greymane_and_the_greater to shift from memory to active"
    )
