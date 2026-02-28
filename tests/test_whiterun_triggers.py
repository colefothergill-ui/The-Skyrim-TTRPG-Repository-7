#!/usr/bin/env python3
"""
Tests for Whiterun Location Triggers

This module tests the whiterun_location_triggers function to ensure
proper event generation based on location and campaign state.
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from triggers.whiterun_triggers import whiterun_location_triggers
import jorvaskr_events


def test_plains_district_trigger():
    """Test that Plains District triggers appropriate events"""
    print("\n=== Testing Plains District Trigger ===")
    
    campaign_state = {
        "companions": {
            "active_companions": []
        }
    }
    
    events = whiterun_location_triggers("whiterun_plains_district", campaign_state)
    
    assert len(events) > 0, "Expected at least one event for Plains District"
    assert any("Plains District" in event for event in events), "Expected Plains District description"
    print(f"✓ Plains District trigger works: {events}")


def test_wind_district_trigger():
    """Test that Wind District triggers appropriate events"""
    print("\n=== Testing Wind District Trigger ===")
    
    campaign_state = {
        "companions": {
            "active_companions": []
        }
    }
    
    events = whiterun_location_triggers("whiterun_wind_district", campaign_state)
    
    assert len(events) > 0, "Expected at least one event for Wind District"
    assert any("Wind District" in event for event in events), "Expected Wind District description"
    assert any("Gildergreen" in event or "Jorrvaskr" in event for event in events), "Expected district landmarks"
    print(f"✓ Wind District trigger works: {events}")


def test_cloud_district_trigger():
    """Test that Cloud District triggers appropriate events"""
    print("\n=== Testing Cloud District Trigger ===")
    
    campaign_state = {
        "companions": {
            "active_companions": []
        }
    }
    
    events = whiterun_location_triggers("whiterun_cloud_district", campaign_state)
    
    assert len(events) > 0, "Expected at least one event for Cloud District"
    assert any("Cloud District" in event for event in events), "Expected Cloud District description"
    assert any("Dragonsreach" in event for event in events), "Expected Dragonsreach mention"
    print(f"✓ Cloud District trigger works: {events}")


def test_general_whiterun_trigger():
    """Test general Whiterun entrance trigger"""
    print("\n=== Testing General Whiterun Trigger ===")
    
    campaign_state = {
        "companions": {
            "active_companions": []
        }
    }
    
    events = whiterun_location_triggers("whiterun", campaign_state)
    
    assert len(events) > 0, "Expected at least one event for Whiterun"
    assert any("gates" in event.lower() or "whiterun" in event.lower() for event in events), "Expected Whiterun entrance description"
    print(f"✓ General Whiterun trigger works: {events}")


def test_lydia_companion_commentary():
    """Test that Lydia provides commentary when in Whiterun"""
    print("\n=== Testing Lydia Companion Commentary ===")
    
    # Test with Lydia as active companion
    campaign_state = {
        "companions": {
            "active_companions": ["Lydia", "Hadvar"]
        }
    }
    
    events = whiterun_location_triggers("whiterun", campaign_state)
    
    assert len(events) > 0, "Expected events when Lydia is present"
    lydia_event = [e for e in events if "Lydia" in e and "Thane" in e]
    assert len(lydia_event) > 0, "Expected Lydia to comment about being in Whiterun"
    print(f"✓ Lydia commentary works: {lydia_event[0]}")


def test_lydia_commentary_case_insensitive():
    """Test that Lydia detection is case-insensitive"""
    print("\n=== Testing Lydia Commentary (Case Insensitive) ===")
    
    # Test with lowercase lydia
    campaign_state = {
        "companions": {
            "active_companions": ["lydia"]
        }
    }
    
    events = whiterun_location_triggers("Whiterun", campaign_state)
    
    lydia_event = [e for e in events if "Lydia" in e]
    assert len(lydia_event) > 0, "Expected Lydia commentary with lowercase companion name"
    print(f"✓ Case-insensitive Lydia detection works")


def test_lydia_commentary_in_district():
    """Test that Lydia comments in Whiterun districts"""
    print("\n=== Testing Lydia Commentary in Districts ===")
    
    campaign_state = {
        "companions": {
            "active_companions": ["Lydia"]
        }
    }
    
    # Test in Plains District
    events = whiterun_location_triggers("whiterun_plains_district", campaign_state)
    lydia_event = [e for e in events if "Lydia" in e]
    assert len(lydia_event) > 0, "Expected Lydia to comment in Plains District"
    
    # Test in Wind District
    events = whiterun_location_triggers("whiterun_wind_district", campaign_state)
    lydia_event = [e for e in events if "Lydia" in e]
    assert len(lydia_event) > 0, "Expected Lydia to comment in Wind District"
    
    print(f"✓ Lydia comments in all Whiterun districts")


def test_no_lydia_commentary_outside_whiterun():
    """Test that Lydia doesn't comment when outside Whiterun"""
    print("\n=== Testing No Lydia Commentary Outside Whiterun ===")
    
    campaign_state = {
        "companions": {
            "active_companions": ["Lydia"]
        }
    }
    
    # Test in a non-Whiterun location
    events = whiterun_location_triggers("riverwood", campaign_state)
    lydia_event = [e for e in events if "Lydia" in e and "Thane" in e]
    
    # Lydia should not comment in non-Whiterun locations
    assert len(lydia_event) == 0, "Lydia should not comment outside Whiterun"
    print(f"✓ Lydia correctly silent outside Whiterun")


def test_no_companion_commentary_without_lydia():
    """Test that no Lydia commentary appears without her as companion"""
    print("\n=== Testing No Commentary Without Lydia ===")
    
    campaign_state = {
        "companions": {
            "active_companions": ["Hadvar", "Ralof"]
        }
    }
    
    events = whiterun_location_triggers("whiterun", campaign_state)
    lydia_event = [e for e in events if "Lydia" in e]
    
    assert len(lydia_event) == 0, "Expected no Lydia commentary without her in party"
    print(f"✓ No Lydia commentary when she's not a companion")


def test_empty_companions_list():
    """Test handling of empty companions list"""
    print("\n=== Testing Empty Companions List ===")
    
    campaign_state = {
        "companions": {
            "active_companions": []
        }
    }
    
    events = whiterun_location_triggers("whiterun", campaign_state)
    
    assert len(events) > 0, "Expected events even with no companions"
    lydia_event = [e for e in events if "Lydia" in e]
    assert len(lydia_event) == 0, "Expected no Lydia commentary with empty companions"
    print(f"✓ Handles empty companions list correctly")


def test_missing_companions_key():
    """Test handling of missing companions key in campaign state"""
    print("\n=== Testing Missing Companions Key ===")
    
    campaign_state = {}
    
    events = whiterun_location_triggers("whiterun", campaign_state)
    
    # Should not crash, just return location events without companion commentary
    assert len(events) > 0, "Expected events even without companions key"
    print(f"✓ Handles missing companions key gracefully")


def test_complex_companion_objects():
    """Test with companion as dictionary objects (more realistic)"""
    print("\n=== Testing Complex Companion Objects ===")
    
    # More realistic campaign state with companion objects
    campaign_state = {
        "companions": {
            "active_companions": [
                {
                    "name": "Lydia",
                    "npc_id": "lydia",
                    "loyalty": 70
                },
                {
                    "name": "Hadvar",
                    "npc_id": "hadvar",
                    "loyalty": 65
                }
            ]
        }
    }
    
    events = whiterun_location_triggers("whiterun", campaign_state)
    
    # The function should properly detect Lydia from dictionary companions
    assert len(events) > 0, "Expected events when Lydia dict is present"
    lydia_event = [e for e in events if "Lydia" in e and "Thane" in e]
    assert len(lydia_event) > 0, "Expected Lydia commentary with dictionary companion"
    print(f"✓ Function handles complex companion objects correctly")


def test_kodlak_cure_or_sacrifice_cured():
    """Test that kodlak_cure_or_sacrifice emits 'lives' text when kodlak is cured"""
    print("\n=== Testing Kodlak Cure - Cured Branch ===")

    campaign_state = {
        "companions": {"active_companions": []},
        "companions_state": {
            "active_quest": "companions_kodlak_cure_or_sacrifice",
            "kodlak_cured": True,
        },
    }

    events = whiterun_location_triggers("jorrvaskr", campaign_state)

    assert any("lives" in e for e in events), "Expected 'lives' text when kodlak is cured"
    assert not any("struck down" in e for e in events), "Expected no 'struck down' text when kodlak is cured"
    print(f"✓ Kodlak cured branch works: {events}")


def test_kodlak_cure_or_sacrifice_cure_preemptive():
    """Test that kodlak_cure_or_sacrifice emits 'lives' text when cure_preemptive is set"""
    print("\n=== Testing Kodlak Cure - Preemptive Branch ===")

    campaign_state = {
        "companions": {"active_companions": []},
        "companions_state": {
            "active_quest": "companions_kodlak_cure_or_sacrifice",
            "cure_preemptive": True,
        },
    }

    events = whiterun_location_triggers("jorrvaskr", campaign_state)

    assert any("lives" in e for e in events), "Expected 'lives' text when cure_preemptive is set"
    assert not any("struck down" in e for e in events), "Expected no 'struck down' text when cure_preemptive is set"
    print(f"✓ cure_preemptive branch works: {events}")


def test_kodlak_cure_or_sacrifice_not_cured():
    """Test that kodlak_cure_or_sacrifice emits 'struck down' text when kodlak is not cured"""
    print("\n=== Testing Kodlak Cure - Not Cured Branch ===")

    campaign_state = {
        "companions": {"active_companions": []},
        "companions_state": {
            "active_quest": "companions_kodlak_cure_or_sacrifice",
        },
    }

    events = whiterun_location_triggers("jorrvaskr", campaign_state)

    assert any("struck down" in e for e in events), "Expected 'struck down' text when kodlak is not cured"
    assert not any("lives" in e for e in events), "Expected no 'lives' text when kodlak is not cured"
    print(f"✓ Not cured branch works: {events}")


def test_jorrvaskr_downstairs_phase2_triggers():
    """Test downstairs first-entry and repeating Vignar notice prompt."""
    campaign_state = {
        "companions": {"active_companions": []},
        "scene_flags": {},
    }

    first_events = whiterun_location_triggers("jorrvaskr_downstairs", campaign_state)
    second_events = whiterun_location_triggers("jorrvaskr_downstairs", campaign_state)

    assert any("[TRIGGERED DESCRIPTION] You descend into Jorrvaskr’s downstairs living area." in e for e in first_events), "Expected downstairs first-entry description"
    assert any("MISSABLE OVERHEAR" in e for e in first_events), "Expected Vignar/Eorlund notice prompt"
    assert not any("[TRIGGERED DESCRIPTION] You descend into Jorrvaskr’s downstairs living area." in e for e in second_events), "Expected downstairs description only once"
    assert any("MISSABLE OVERHEAR" in e for e in second_events), "Expected notice prompt repeat until resolved"
    assert campaign_state.get("scene_flags", {}).get("last_location") == "jorrvaskr_downstairs"


def test_jorrvaskr_harbinger_phase2_scene_once():
    """Test Harbinger room description and foreshadow scene fire once."""
    campaign_state = {
        "companions": {"active_companions": []},
        "scene_flags": {},
    }

    first_events = whiterun_location_triggers("jorrvaskr_harbinger_room", campaign_state)
    second_events = whiterun_location_triggers("jorrvaskr_harbinger_room", campaign_state)

    assert any("Kodlak’s chamber is humble for a legend" in e for e in first_events), "Expected Harbinger room first-entry description"
    assert any("SCRIPTED SCENE" in e for e in first_events), "Expected Kodlak/Vilkas foreshadow scene"
    assert not any("Kodlak’s chamber is humble for a legend" in e for e in second_events), "Expected Harbinger description only once"
    assert not any("SCRIPTED SCENE" in e for e in second_events), "Expected foreshadow scene only once"


def test_jorrvaskr_dustmans_summon_when_contract_clock_full():
    """Test Dustman's Cairn summon triggers at 2/2 contracts during Proving Honor."""
    campaign_state = {
        "companions": {"active_companions": []},
        "scene_flags": {},
        "companions_state": {"active_quest": "companions_proving_honor"},
        "campaign_clocks": {
            "honor_proving_contracts_done": {
                "current_progress": 2,
                "total_segments": 2
            }
        }
    }

    first_events = whiterun_location_triggers("jorrvaskr", campaign_state)
    second_events = whiterun_location_triggers("jorrvaskr", campaign_state)

    assert any("[SUMMON]" in e for e in first_events), "Expected Dustman's Cairn summon at full contracts clock"
    assert not any("[SUMMON]" in e for e in second_events), "Expected summon to trigger only once"


def test_resolve_vilkas_trial_uses_active_pc_id():
    """Vilkas trial should target active_pc_id when queuing pending aspect updates."""
    state = {
        "active_pc_id": "pc_test_runner",
        "scene_flags": {},
        "companions_state": {"active_quest": "companions_proving_honor"},
    }

    jorvaskr_events.resolve_vilkas_trial(state, pc_won=False)

    pending = state.get("pending_pc_updates", [])
    assert any(p.get("target") == "pc_test_runner" for p in pending), "Expected pending update target to use active_pc_id"


def test_join_request_promotes_locked_sidequests_with_string_active_quests():
    """Locked side quests in quest_progress should promote cleanly without dict entries in active_quests."""
    state = {
        "scene_flags": {},
        "active_quests": [],
        "companions_state": {
            "quest_progress": {
                "companions_investigate_jorrvaskr": "completed",
                "companions_honorable_combat": "locked",
                "companions_prey_and_predator": "locked",
            }
        },
    }

    jorvaskr_events.resolve_kodlak_join_request(state, accepted=True)

    qprog = state["companions_state"]["quest_progress"]
    assert qprog["companions_honorable_combat"] == "active"
    assert qprog["companions_prey_and_predator"] == "active"
    assert "companions:companions_honorable_combat" in state["active_quests"]
    assert "companions:companions_prey_and_predator" in state["active_quests"]
    assert all(isinstance(q, str) for q in state["active_quests"])


def test_dustmans_cairn_entrance_trigger_via_whiterun_hooks():
    """Dustman's Cairn entrance trigger should flow through whiterun trigger wiring."""
    campaign_state = {
        "companions": {"active_companions": []},
        "companions_state": {"proving_honor_assigned_partner": "aela"},
        "scene_flags": {},
    }

    events = whiterun_location_triggers("dustmans_entrance", campaign_state)

    assert any("[DUSTMAN’S CAIRN]" in e for e in events), "Expected Dustman's Cairn entrance description"
    assert any("Aela murmurs" in e for e in events), "Expected Aela entrance bark"


def test_dustmans_cairn_silver_hand_seed_for_purity_track_once():
    """Purity track should seed Silver Hand contact once at camp intro."""
    campaign_state = {
        "companions": {"active_companions": []},
        "companions_state": {
            "embraced_curse": False,
            "proving_honor_assigned_partner": "farkas",
        },
        "scene_flags": {},
    }

    first_events = whiterun_location_triggers("dustmans_silver_hand_camp", campaign_state)
    second_events = whiterun_location_triggers("dustmans_silver_hand_camp", campaign_state)

    assert any("[INTRO ANTAGONIST]" in e for e in first_events), "Expected Hakon intro on first camp trigger"
    assert any("[SEED]" in e for e in first_events), "Expected Silver Hand seed text for purity track"
    assert not any("[SEED]" in e for e in second_events), "Expected seed text only once"
    assert campaign_state.get("scene_flags", {}).get("silver_hand_token_obtained") is True
    assert "silver_hand_contact" in campaign_state.get("quests", {}).get("active", [])


def test_dustmans_cairn_additional_room_triggers_once():
    """Trap/ossuary/deep-crypt/word-wall branches should trigger once each."""
    campaign_state = {
        "companions": {"active_companions": []},
        "scene_flags": {},
    }

    checks = [
        ("dustmans_anteroom", "dustmans_trap_rooms_seen", "Runes scratch the stone."),
        ("dustmans_ossuary_maze", "dustmans_ossuary_seen", "Bone-dust clings to your boots."),
        ("dustmans_deep_crypt_chamber", "dustmans_fragment_chamber_seen", "[FRAGMENT CHAMBER]"),
        ("dustmans_word_wall", "dustmans_word_wall_seen", "[WORD WALL]"),
    ]

    for loc, flag, expected in checks:
        first_events = whiterun_location_triggers(loc, campaign_state)
        second_events = whiterun_location_triggers(loc, campaign_state)

        assert any(expected in e for e in first_events), f"Expected first trigger text for {loc}"
        assert not any(expected in e for e in second_events), f"Expected once-only behavior for {loc}"
        assert campaign_state.get("scene_flags", {}).get(flag) is True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("Running Whiterun Triggers Tests")
    print("=" * 60)
    
    tests = [
        test_plains_district_trigger,
        test_wind_district_trigger,
        test_cloud_district_trigger,
        test_general_whiterun_trigger,
        test_lydia_companion_commentary,
        test_lydia_commentary_case_insensitive,
        test_lydia_commentary_in_district,
        test_no_lydia_commentary_outside_whiterun,
        test_no_companion_commentary_without_lydia,
        test_empty_companions_list,
        test_missing_companions_key,
        test_complex_companion_objects,
        test_kodlak_cure_or_sacrifice_cured,
        test_kodlak_cure_or_sacrifice_cure_preemptive,
        test_kodlak_cure_or_sacrifice_not_cured,
        test_jorrvaskr_downstairs_phase2_triggers,
        test_jorrvaskr_harbinger_phase2_scene_once,
        test_jorrvaskr_dustmans_summon_when_contract_clock_full,
        test_resolve_vilkas_trial_uses_active_pc_id,
        test_join_request_promotes_locked_sidequests_with_string_active_quests,
        test_dustmans_cairn_entrance_trigger_via_whiterun_hooks,
        test_dustmans_cairn_silver_hand_seed_for_purity_track_once,
        test_dustmans_cairn_additional_room_triggers_once,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            failed += 1
            print(f"✗ {test.__name__} failed: {e}")
        except Exception as e:
            failed += 1
            print(f"✗ {test.__name__} error: {e}")
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
