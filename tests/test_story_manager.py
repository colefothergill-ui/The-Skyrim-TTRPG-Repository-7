#!/usr/bin/env python3
"""
Tests for StoryManager – College of Winterhold questline integration.

Covers:
- load_college_quests() loads all six quests from the JSON file.
- start_college_questline() sets college_first_lessons as active.
- complete_college_quest() chains quests in COLLEGE_CHAIN order.
- dragonbreak_precheck_college() triggers at eye_instability >= 5.
- get_available_quests() surfaces the active College quest.
- session_zero update_campaign_state() queues college_first_lessons
  when starting faction is college_of_winterhold.
- Battle of Whiterun is not blocked when College intro is incomplete
  (the engine exposes the requirement as a hook, not a hard gate).
"""

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

# Resolve absolute path so tests run from any working directory
_REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from story_manager import StoryManager, COLLEGE_CHAIN, COMPANIONS_CHAIN, SILVER_HAND_CHAIN
from session_zero import SessionZeroManager


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_minimal_state(
    tmpdir: Path,
    college_state: dict | None = None,
    companions_state: dict | None = None,
) -> Path:
    """Write a minimal campaign_state.json into tmpdir and return its path."""
    state = {
        "campaign_id": "test_001",
        "current_act": 1,
        "civil_war_state": {
            "player_alliance": "neutral",
            "battle_of_whiterun_status": "approaching",
            "imperial_victories": 0,
            "stormcloak_victories": 0,
            "key_battles_completed": [],
            "faction_relationship": {"imperial_legion": 0, "stormcloaks": 0},
        },
        "main_quest_state": {},
        "thalmor_arc": {},
        "branching_decisions": {},
        "world_consequences": {"major_choices": []},
        "active_story_arcs": [],
        "companions": {
            "active_companions": [],
            "available_companions": [],
            "dismissed_companions": [],
        },
        "college_state": college_state or {
            "active_quest": None,
            "completed_quests": [],
            "quest_progress": {},
            "eye_instability": 0,
            "ancano_suspicion": 0,
            "internal_politics": 0,
        },
        "companions_state": companions_state or {
            "active_quest": None,
            "completed_quests": [],
            "quest_progress": {},
            "embraced_curse": False,
            "skjor_alive": True,
            "kodlak_cured": False,
        },
    }
    state_path = tmpdir / "campaign_state.json"
    state_path.write_text(json.dumps(state, indent=2))
    return state_path


def _make_story_manager(
    tmpdir: Path,
    college_state: dict | None = None,
    companions_state: dict | None = None,
) -> StoryManager:
    """Create a StoryManager pointing at real data but a temp state dir."""
    state_dir = tmpdir / "state"
    state_dir.mkdir(exist_ok=True)
    _make_minimal_state(state_dir, college_state, companions_state)
    data_dir = str(_REPO_ROOT / "data")
    return StoryManager(data_dir=data_dir, state_dir=str(state_dir))


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestCollegeQuests:
    """Tests for the College of Winterhold questline integration."""

    def test_load_college_quests_returns_all_six(self):
        """load_college_quests() should return a dict with all six quests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            quests = sm.college_quests
            assert isinstance(quests, dict), "college_quests should be a dict"
            expected_ids = {
                "college_first_lessons",
                "college_under_saarthal",
                "college_hitting_the_books",
                "college_revealing_the_unseen",
                "college_staff_of_magnus",
                "college_eye_of_magnus",
            }
            assert expected_ids.issubset(quests.keys()), (
                f"Missing quests: {expected_ids - quests.keys()}"
            )
            print(f"  ✓ {len(quests)} quests loaded")

    def test_start_college_questline_sets_active_quest(self):
        """start_college_questline() should set college_first_lessons as active."""
        state = {
            "college_state": {
                "active_quest": None,
                "completed_quests": [],
                "quest_progress": {},
                "eye_instability": 0,
                "ancano_suspicion": 0,
                "internal_politics": 0,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            sm.start_college_questline(state)
        cs = state["college_state"]
        assert cs["active_quest"] == "college_first_lessons"
        assert cs["quest_progress"]["college_first_lessons"] == "active"
        print("  ✓ start_college_questline sets college_first_lessons as active")

    def test_complete_college_quest_chains_in_order(self):
        """complete_college_quest() should advance quests in COLLEGE_CHAIN order."""
        ordered = [
            "college_first_lessons",
            "college_under_saarthal",
            "college_hitting_the_books",
            "college_revealing_the_unseen",
            "college_staff_of_magnus",
            "college_eye_of_magnus",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            state = {
                "college_state": {
                    "active_quest": "college_first_lessons",
                    "completed_quests": [],
                    "quest_progress": {"college_first_lessons": "active"},
                    "eye_instability": 0,
                    "ancano_suspicion": 0,
                    "internal_politics": 0,
                }
            }
            for i, current_id in enumerate(ordered):
                assert state["college_state"]["active_quest"] == current_id, (
                    f"Expected active quest '{current_id}', got '{state['college_state']['active_quest']}'"
                )
                next_q = sm.complete_college_quest(state)
                expected_next = COLLEGE_CHAIN[current_id]
                assert next_q == expected_next, (
                    f"After completing '{current_id}', expected next '{expected_next}', got '{next_q}'"
                )
                assert current_id in state["college_state"]["completed_quests"]
                assert state["college_state"]["quest_progress"][current_id] == "completed"

        print("  ✓ complete_college_quest chains through all six quests correctly")

    def test_complete_college_quest_arc_ends_cleanly(self):
        """After completing eye_of_magnus, active_quest should be None."""
        state = {
            "college_state": {
                "active_quest": "college_eye_of_magnus",
                "completed_quests": [],
                "quest_progress": {"college_eye_of_magnus": "active"},
                "eye_instability": 0,
                "ancano_suspicion": 0,
                "internal_politics": 0,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            result = sm.complete_college_quest(state)
        assert result is None
        assert state["college_state"]["active_quest"] is None
        assert "college_eye_of_magnus" in state["college_state"]["completed_quests"]
        print("  ✓ complete_college_quest ends arc cleanly at eye_of_magnus")

    def test_dragonbreak_precheck_triggers_at_threshold(self):
        """dragonbreak_precheck_college() returns True when instability >= 5."""
        state_high = {
            "college_state": {
                "active_quest": "college_eye_of_magnus",
                "eye_instability": 5,
            }
        }
        state_low = {
            "college_state": {
                "active_quest": "college_eye_of_magnus",
                "eye_instability": 3,
            }
        }
        state_wrong_quest = {
            "college_state": {
                "active_quest": "college_first_lessons",
                "eye_instability": 10,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            assert sm.dragonbreak_precheck_college(state_high) is True
            assert sm.dragonbreak_precheck_college(state_low) is False
            assert sm.dragonbreak_precheck_college(state_wrong_quest) is False
        print("  ✓ dragonbreak_precheck_college logic is correct")

    def test_get_available_quests_includes_active_college_quest(self):
        """get_available_quests() should list the active College quest."""
        college_state = {
            "active_quest": "college_first_lessons",
            "completed_quests": [],
            "quest_progress": {"college_first_lessons": "active"},
            "eye_instability": 0,
            "ancano_suspicion": 0,
            "internal_politics": 0,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir), college_state=college_state)
            available = sm.get_available_quests()

        college_entries = [q for q in available if q.get("type") == "college"]
        assert len(college_entries) >= 1, (
            "Expected at least one college quest in available quests"
        )
        quest_data = college_entries[0]["quest"]
        assert quest_data.get("quest_id") == "college_first_lessons", (
            f"Expected quest_id 'college_first_lessons', got: {quest_data.get('quest_id')!r}"
        )
        print("  ✓ get_available_quests surfaces active College quest")

    def test_get_available_quests_no_college_when_inactive(self):
        """get_available_quests() should not include College quest when none is active."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            available = sm.get_available_quests()

        college_entries = [q for q in available if q.get("type") == "college"]
        assert len(college_entries) == 0, (
            "Expected no college quests when active_quest is null"
        )
        print("  ✓ get_available_quests hides College quest when inactive")


class TestSessionZeroCollegeFaction:
    """Tests for session_zero College-faction initialization."""

    def _make_session_zero_env(self, tmpdir: Path):
        """Set up a SessionZeroManager with a valid state/data layout."""
        data_dir = tmpdir / "data"
        state_dir = tmpdir / "state"
        (data_dir / "pcs").mkdir(parents=True)
        state_dir.mkdir(parents=True)

        # Minimal campaign state
        (state_dir / "campaign_state.json").write_text(json.dumps({
            "campaign_id": "test_001",
            "current_act": 1,
            "civil_war_state": {
                "player_alliance": "neutral",
                "battle_of_whiterun_status": "approaching",
                "imperial_victories": 0,
                "stormcloak_victories": 0,
                "key_battles_completed": [],
                "faction_relationship": {"imperial_legion": 0, "stormcloaks": 0},
            },
            "main_quest_state": {},
            "thalmor_arc": {},
            "branching_decisions": {},
            "world_consequences": {"major_choices": []},
            "active_story_arcs": [],
            "companions": {
                "active_companions": [],
                "available_companions": [],
                "dismissed_companions": [],
                "companion_relationships": {},
            },
        }, indent=2))

        return SessionZeroManager(data_dir=str(data_dir), state_dir=str(state_dir))

    def test_college_faction_queues_first_lessons(self):
        """Session-zero with College faction should activate college_first_lessons."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test",
                "name": "Test Mage",
                "player": "Player One",
                "race": "Breton",
                "standing_stone": "The Mage Stone",
                "faction_alignment": "neutral",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="neutral",
                characters=characters,
                neutral_subfaction="college",
            )

        assert "college_state" in state, "college_state should be present in campaign state"
        cs = state["college_state"]
        assert cs["active_quest"] == "college_first_lessons", (
            f"Expected college_first_lessons as active quest, got: {cs['active_quest']}"
        )
        assert cs["quest_progress"].get("college_first_lessons") == "active"
        assert state.get("starting_faction") == "college_of_winterhold"
        print("  ✓ session-zero with College queues college_first_lessons")

    def test_non_college_faction_does_not_activate_college_quests(self):
        """Session-zero with non-College faction should leave college_state inactive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test2",
                "name": "Test Warrior",
                "player": "Player Two",
                "race": "Nord",
                "standing_stone": "The Warrior Stone",
                "faction_alignment": "imperial",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="imperial",
                characters=characters,
            )

        cs = state.get("college_state", {})
        assert cs.get("active_quest") is None, (
            f"Expected no active college quest for Imperial faction, got: {cs.get('active_quest')}"
        )
        print("  ✓ non-College faction does not activate College quests")

    def test_college_state_initialised_for_all_factions(self):
        """college_state should always be present after session-zero (append-only)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test3",
                "name": "Test Thief",
                "player": "Player Three",
                "race": "Khajiit",
                "standing_stone": "The Thief Stone",
                "faction_alignment": "neutral",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="neutral",
                characters=characters,
                neutral_subfaction="thieves_guild",
            )

        assert "college_state" in state, "college_state should be present even for Thieves Guild start"
        print("  ✓ college_state always initialised by session-zero")


class TestCompanionsQuests:
    """Tests for the Companions questline integration."""

    def test_load_companions_quests_returns_all_five(self):
        """load_companions_quests() should return a dict with all five quests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            quests = sm.companions_quests
            assert isinstance(quests, dict), "companions_quests should be a dict"
            expected_ids = {
                "companions_proving_honor",
                "companions_inner_circle_rites",
                "companions_kodlak_cure_or_sacrifice",
                "companions_skjor_dragonbreak",
                "companions_final_journey",
            }
            assert expected_ids.issubset(quests.keys()), (
                f"Missing quests: {expected_ids - quests.keys()}"
            )
            print(f"  ✓ {len(quests)} Companions quests loaded")

    def test_start_companions_questline_sets_active_quest(self):
        """start_companions_questline() should set companions_proving_honor as active."""
        state = {
            "companions_state": {
                "active_quest": None,
                "completed_quests": [],
                "quest_progress": {},
                "embraced_curse": False,
                "skjor_alive": True,
                "kodlak_cured": False,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            sm.start_companions_questline(state)
        cs = state["companions_state"]
        assert cs["active_quest"] == "companions_investigate_jorrvaskr"
        assert cs["quest_progress"]["companions_investigate_jorrvaskr"] == "active"
        print("  ✓ start_companions_questline sets companions_investigate_jorrvaskr as active")

    def test_complete_companions_quest_default_chain(self):
        """complete_companions_quest() advances through the default chain."""
        # Default path: no dragonbreak (skjor_alive=False or embraced_curse=False)
        ordered = [
            "companions_proving_honor",
            "companions_inner_circle_rites",
            "companions_kodlak_cure_or_sacrifice",
            "companions_purity_path_ignites",
            "companions_final_journey",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            state = {
                "companions_state": {
                    "active_quest": "companions_proving_honor",
                    "completed_quests": [],
                    "quest_progress": {"companions_proving_honor": "active"},
                    "embraced_curse": False,
                    "skjor_alive": True,
                    "kodlak_cured": False,
                }
            }
            for i, current_id in enumerate(ordered):
                assert state["companions_state"]["active_quest"] == current_id, (
                    f"Expected active quest '{current_id}', got "
                    f"'{state['companions_state']['active_quest']}'"
                )
                next_q = sm.complete_companions_quest(state)
                expected_next = COMPANIONS_CHAIN[current_id]
                assert next_q == expected_next, (
                    f"After completing '{current_id}', expected next '{expected_next}', "
                    f"got '{next_q}'"
                )
                assert current_id in state["companions_state"]["completed_quests"]
                assert state["companions_state"]["quest_progress"][current_id] == "completed"

        print("  ✓ complete_companions_quest chains through default path correctly")

    def test_complete_companions_quest_arc_ends_cleanly(self):
        """After completing companions_final_journey, active_quest should be None."""
        state = {
            "companions_state": {
                "active_quest": "companions_final_journey",
                "completed_quests": [],
                "quest_progress": {"companions_final_journey": "active"},
                "embraced_curse": False,
                "skjor_alive": True,
                "kodlak_cured": False,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            result = sm.complete_companions_quest(state)
        assert result is None
        assert state["companions_state"]["active_quest"] is None
        assert "companions_final_journey" in state["companions_state"]["completed_quests"]
        print("  ✓ complete_companions_quest ends arc cleanly at final_journey")

    def test_dragonbreak_branch_fires_when_conditions_met(self):
        """complete_companions_quest() injects skjor_dragonbreak when skjor_alive and embraced_curse."""
        state = {
            "companions_state": {
                "active_quest": "companions_kodlak_cure_or_sacrifice",
                "completed_quests": [],
                "quest_progress": {"companions_kodlak_cure_or_sacrifice": "active"},
                "embraced_curse": True,
                "skjor_alive": True,
                "kodlak_cured": False,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            next_q = sm.complete_companions_quest(state)
        assert next_q == "companions_skjor_dragonbreak", (
            f"Expected dragonbreak quest, got '{next_q}'"
        )
        print("  ✓ Dragonbreak branch fires when skjor_alive=True and embraced_curse=True")

    def test_dragonbreak_branch_skipped_without_curse(self):
        """No dragonbreak when embraced_curse is False even if skjor_alive."""
        state = {
            "companions_state": {
                "active_quest": "companions_kodlak_cure_or_sacrifice",
                "completed_quests": [],
                "quest_progress": {"companions_kodlak_cure_or_sacrifice": "active"},
                "embraced_curse": False,
                "skjor_alive": True,
                "kodlak_cured": False,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            next_q = sm.complete_companions_quest(state)
        assert next_q == "companions_purity_path_ignites", (
            f"Expected final_journey, got '{next_q}'"
        )
        print("  ✓ Dragonbreak branch skipped when embraced_curse=False")

    def test_dragonbreak_branch_skipped_without_skjor(self):
        """No dragonbreak when skjor_alive is False even if embraced_curse."""
        state = {
            "companions_state": {
                "active_quest": "companions_kodlak_cure_or_sacrifice",
                "completed_quests": [],
                "quest_progress": {"companions_kodlak_cure_or_sacrifice": "active"},
                "embraced_curse": True,
                "skjor_alive": False,
                "kodlak_cured": False,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            next_q = sm.complete_companions_quest(state)
        assert next_q == "companions_purity_path_ignites", (
            f"Expected final_journey, got '{next_q}'"
        )
        print("  ✓ Dragonbreak branch skipped when skjor_alive=False")

    def test_dragonbreak_check_companions_logic(self):
        """dragonbreak_check_companions() returns True only when both flags set on correct quest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))

            state_both = {
                "companions_state": {
                    "active_quest": "companions_kodlak_cure_or_sacrifice",
                    "skjor_alive": True,
                    "embraced_curse": True,
                }
            }
            state_no_curse = {
                "companions_state": {
                    "active_quest": "companions_kodlak_cure_or_sacrifice",
                    "skjor_alive": True,
                    "embraced_curse": False,
                }
            }
            state_no_skjor = {
                "companions_state": {
                    "active_quest": "companions_kodlak_cure_or_sacrifice",
                    "skjor_alive": False,
                    "embraced_curse": True,
                }
            }
            state_wrong_quest = {
                "companions_state": {
                    "active_quest": "companions_proving_honor",
                    "skjor_alive": True,
                    "embraced_curse": True,
                }
            }
            assert sm.dragonbreak_check_companions(state_both) is True
            assert sm.dragonbreak_check_companions(state_no_curse) is False
            assert sm.dragonbreak_check_companions(state_no_skjor) is False
            assert sm.dragonbreak_check_companions(state_wrong_quest) is False
        print("  ✓ dragonbreak_check_companions logic is correct")

    def test_get_available_quests_includes_active_companions_quest(self):
        """get_available_quests() should list the active Companions quest."""
        companions_state = {
            "active_quest": "companions_proving_honor",
            "completed_quests": [],
            "quest_progress": {"companions_proving_honor": "active"},
            "embraced_curse": False,
            "skjor_alive": True,
            "kodlak_cured": False,
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir), companions_state=companions_state)
            available = sm.get_available_quests()

        companions_entries = [q for q in available if q.get("type") == "companions"]
        assert len(companions_entries) >= 1, (
            "Expected at least one companions quest in available quests"
        )
        quest_data = companions_entries[0]["quest"]
        assert quest_data.get("quest_id") == "companions_proving_honor", (
            f"Expected quest_id 'companions_proving_honor', got: {quest_data.get('quest_id')!r}"
        )
        print("  ✓ get_available_quests surfaces active Companions quest")

    def test_get_available_quests_no_companions_when_inactive(self):
        """get_available_quests() should not include Companions quest when none is active."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            available = sm.get_available_quests()

        companions_entries = [q for q in available if q.get("type") == "companions"]
        assert len(companions_entries) == 0, (
            "Expected no companions quests when active_quest is null"
        )
        print("  ✓ get_available_quests hides Companions quest when inactive")


class TestSessionZeroCompanionsFaction:
    """Tests for session_zero Companions-faction initialization."""

    def _make_session_zero_env(self, tmpdir: Path):
        """Set up a SessionZeroManager with a valid state/data layout."""
        data_dir = tmpdir / "data"
        state_dir = tmpdir / "state"
        (data_dir / "pcs").mkdir(parents=True)
        state_dir.mkdir(parents=True)

        (state_dir / "campaign_state.json").write_text(json.dumps({
            "campaign_id": "test_001",
            "current_act": 1,
            "civil_war_state": {
                "player_alliance": "neutral",
                "battle_of_whiterun_status": "approaching",
                "imperial_victories": 0,
                "stormcloak_victories": 0,
                "key_battles_completed": [],
                "faction_relationship": {"imperial_legion": 0, "stormcloaks": 0},
            },
            "main_quest_state": {},
            "thalmor_arc": {},
            "branching_decisions": {},
            "world_consequences": {"major_choices": []},
            "active_story_arcs": [],
            "companions": {
                "active_companions": [],
                "available_companions": [],
                "dismissed_companions": [],
                "companion_relationships": {},
            },
        }, indent=2))

        return SessionZeroManager(data_dir=str(data_dir), state_dir=str(state_dir))

    def test_companions_faction_queues_proving_honor(self):
        """Session-zero with Companions subfaction should activate companions_proving_honor."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test",
                "name": "Test Warrior",
                "player": "Player One",
                "race": "Nord",
                "standing_stone": "The Warrior Stone",
                "faction_alignment": "neutral",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="neutral",
                characters=characters,
                neutral_subfaction="companions",
            )

        assert "companions_state" in state, "companions_state should be present in campaign state"
        cs = state["companions_state"]
        assert cs["active_quest"] == "companions_investigate_jorrvaskr", (
            f"Expected companions_investigate_jorrvaskr as active quest, got: {cs['active_quest']}"
        )
        assert cs["quest_progress"].get("companions_investigate_jorrvaskr") == "active"
        assert state.get("starting_faction") == "companions"
        print("  ✓ session-zero with Companions queues companions_investigate_jorrvaskr")

    def test_non_companions_faction_does_not_activate_companions_quests(self):
        """Session-zero with non-Companions subfaction should leave companions_state inactive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test2",
                "name": "Test Mage",
                "player": "Player Two",
                "race": "Breton",
                "standing_stone": "The Mage Stone",
                "faction_alignment": "neutral",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="neutral",
                characters=characters,
                neutral_subfaction="college",
            )

        cs = state.get("companions_state", {})
        assert cs.get("active_quest") is None, (
            f"Expected no active companions quest for College faction, got: {cs.get('active_quest')}"
        )
        print("  ✓ non-Companions faction does not activate Companions quests")

    def test_companions_state_initialised_for_all_factions(self):
        """companions_state should always be present after session-zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test3",
                "name": "Test Imperial",
                "player": "Player Three",
                "race": "Imperial",
                "standing_stone": "The Lord Stone",
                "faction_alignment": "imperial",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="imperial",
                characters=characters,
            )

        assert "companions_state" in state, "companions_state should be present even for Imperial start"
        print("  ✓ companions_state always initialised by session-zero")


class TestSilverHandQuests:
    """Tests for the Silver Hand questline integration."""

    def test_load_silver_hand_quests_returns_all_five(self):
        """load_silver_hand_quests() should return a dict with all five quests."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            quests = sm.silver_hand_quests
            assert isinstance(quests, dict), "silver_hand_quests should be a dict"
            expected_ids = {
                "silver_hand_frostroot_contact",
                "silver_hand_prove_the_oath",
                "silver_hand_oath_records",
                "silver_hand_split_restorer_or_purger",
                "silver_hand_final_judgment",
            }
            assert expected_ids.issubset(quests.keys()), (
                f"Missing quests: {expected_ids - quests.keys()}"
            )
            print(f"  ✓ {len(quests)} Silver Hand quests loaded")

    def test_start_silver_hand_questline_sets_active_quest(self):
        """start_silver_hand_questline() should set silver_hand_frostroot_contact as active."""
        state = {
            "silver_hand_state": {
                "active_quest": None,
                "completed_quests": [],
                "quest_progress": {},
                "silver_hand_joined": False,
                "silver_hand_path": None,
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            sm.start_silver_hand_questline(state)
        sh = state["silver_hand_state"]
        assert sh["active_quest"] == "silver_hand_frostroot_contact"
        assert sh["quest_progress"]["silver_hand_frostroot_contact"] == "active"
        print("  ✓ start_silver_hand_questline sets silver_hand_frostroot_contact as active")

    def test_complete_silver_hand_quest_chains_in_order(self):
        """complete_silver_hand_quest() advances through the chain in order."""
        ordered = [
            "silver_hand_frostroot_contact",
            "silver_hand_prove_the_oath",
            "silver_hand_oath_records",
            "silver_hand_split_restorer_or_purger",
            "silver_hand_final_judgment",
        ]
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            state = {
                "silver_hand_state": {
                    "active_quest": "silver_hand_frostroot_contact",
                    "completed_quests": [],
                    "quest_progress": {"silver_hand_frostroot_contact": "active"},
                    "silver_hand_joined": False,
                    "silver_hand_path": None,
                }
            }
            for current_id in ordered:
                assert state["silver_hand_state"]["active_quest"] == current_id, (
                    f"Expected active quest '{current_id}', got "
                    f"'{state['silver_hand_state']['active_quest']}'"
                )
                next_q = sm.complete_silver_hand_quest(state)
                expected_next = SILVER_HAND_CHAIN[current_id]
                assert next_q == expected_next, (
                    f"After completing '{current_id}', expected next '{expected_next}', "
                    f"got '{next_q}'"
                )
                assert current_id in state["silver_hand_state"]["completed_quests"]
                assert state["silver_hand_state"]["quest_progress"][current_id] == "completed"

        print("  ✓ complete_silver_hand_quest chains through all five quests correctly")

    def test_complete_silver_hand_quest_arc_ends_cleanly(self):
        """After completing silver_hand_final_judgment, active_quest should be None."""
        state = {
            "silver_hand_state": {
                "active_quest": "silver_hand_final_judgment",
                "completed_quests": [],
                "quest_progress": {"silver_hand_final_judgment": "active"},
                "silver_hand_joined": True,
                "silver_hand_path": "restorer",
            }
        }
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            result = sm.complete_silver_hand_quest(state)
        assert result is None
        assert state["silver_hand_state"]["active_quest"] is None
        assert "silver_hand_final_judgment" in state["silver_hand_state"]["completed_quests"]
        print("  ✓ complete_silver_hand_quest ends arc cleanly at final_judgment")

    def test_get_available_quests_includes_active_silver_hand_quest(self):
        """get_available_quests() should list the active Silver Hand quest."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            state = sm.load_campaign_state() or {}
            state["silver_hand_state"] = {
                "active_quest": "silver_hand_frostroot_contact",
                "completed_quests": [],
                "quest_progress": {"silver_hand_frostroot_contact": "active"},
                "silver_hand_joined": False,
                "silver_hand_path": None,
            }
            sm.save_campaign_state(state)
            available = sm.get_available_quests()

        sh_entries = [q for q in available if q.get("type") == "silver_hand"]
        assert len(sh_entries) >= 1, (
            "Expected at least one silver_hand quest in available quests"
        )
        quest_data = sh_entries[0]["quest"]
        assert quest_data.get("quest_id") == "silver_hand_frostroot_contact", (
            f"Expected quest_id 'silver_hand_frostroot_contact', got: {quest_data.get('quest_id')!r}"
        )
        print("  ✓ get_available_quests surfaces active Silver Hand quest")

    def test_get_available_quests_no_silver_hand_when_inactive(self):
        """get_available_quests() should not include Silver Hand quest when none is active."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sm = _make_story_manager(Path(tmpdir))
            available = sm.get_available_quests()

        sh_entries = [q for q in available if q.get("type") == "silver_hand"]
        assert len(sh_entries) == 0, (
            "Expected no silver_hand quests when active_quest is null"
        )
        print("  ✓ get_available_quests hides Silver Hand quest when inactive")


class TestSessionZeroSilverHandFaction:
    """Tests for session_zero Silver Hand faction initialization."""

    def _make_session_zero_env(self, tmpdir: Path):
        data_dir = tmpdir / "data"
        state_dir = tmpdir / "state"
        (data_dir / "pcs").mkdir(parents=True)
        state_dir.mkdir(parents=True)

        (state_dir / "campaign_state.json").write_text(json.dumps({
            "campaign_id": "test_001",
            "current_act": 1,
            "civil_war_state": {
                "player_alliance": "neutral",
                "battle_of_whiterun_status": "approaching",
                "imperial_victories": 0,
                "stormcloak_victories": 0,
                "key_battles_completed": [],
                "faction_relationship": {"imperial_legion": 0, "stormcloaks": 0},
            },
            "main_quest_state": {},
            "thalmor_arc": {},
            "branching_decisions": {},
            "world_consequences": {"major_choices": []},
            "active_story_arcs": [],
            "companions": {
                "active_companions": [],
                "available_companions": [],
                "dismissed_companions": [],
                "companion_relationships": {},
            },
        }, indent=2))

        return SessionZeroManager(data_dir=str(data_dir), state_dir=str(state_dir))

    def test_silver_hand_faction_queues_frostroot_contact(self):
        """Session-zero with Silver Hand subfaction should activate silver_hand_frostroot_contact."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test",
                "name": "Test Oath-Warrior",
                "player": "Player One",
                "race": "Nord",
                "standing_stone": "The Warrior Stone",
                "faction_alignment": "neutral",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="neutral",
                characters=characters,
                neutral_subfaction="silver_hand",
            )

        assert "silver_hand_state" in state, "silver_hand_state should be present in campaign state"
        sh = state["silver_hand_state"]
        assert sh["active_quest"] == "silver_hand_frostroot_contact", (
            f"Expected silver_hand_frostroot_contact as active quest, got: {sh['active_quest']}"
        )
        assert sh["quest_progress"].get("silver_hand_frostroot_contact") == "active"
        assert state.get("starting_faction") == "silver_hand"
        print("  ✓ session-zero with Silver Hand queues silver_hand_frostroot_contact")

    def test_non_silver_hand_faction_does_not_activate_silver_hand_quests(self):
        """Session-zero with non-Silver Hand subfaction should leave silver_hand_state inactive."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test2",
                "name": "Test Companion",
                "player": "Player Two",
                "race": "Nord",
                "standing_stone": "The Warrior Stone",
                "faction_alignment": "neutral",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="neutral",
                characters=characters,
                neutral_subfaction="companions",
            )

        sh = state.get("silver_hand_state", {})
        assert sh.get("active_quest") is None, (
            f"Expected no active silver_hand quest for Companions faction, got: {sh.get('active_quest')}"
        )
        print("  ✓ non-Silver Hand faction does not activate Silver Hand quests")

    def test_silver_hand_state_initialised_for_all_factions(self):
        """silver_hand_state should always be present after session-zero."""
        with tempfile.TemporaryDirectory() as tmpdir:
            mgr = self._make_session_zero_env(Path(tmpdir))
            characters = [{
                "id": "pc_test3",
                "name": "Test Imperial",
                "player": "Player Three",
                "race": "Imperial",
                "standing_stone": "The Lord Stone",
                "faction_alignment": "imperial",
            }]
            state = mgr.update_campaign_state(
                faction_alignment="imperial",
                characters=characters,
            )

        assert "silver_hand_state" in state, "silver_hand_state should be present even for Imperial start"
        print("  ✓ silver_hand_state always initialised by session-zero")


def run_all_tests():
    """Run all test classes for College, Companions, and Silver Hand questlines."""
    test_classes = [
        TestCollegeQuests,
        TestSessionZeroCollegeFaction,
        TestCompanionsQuests,
        TestSessionZeroCompanionsFaction,
        TestSilverHandQuests,
        TestSessionZeroSilverHandFaction,
    ]
    passed = 0
    failed = 0

    for cls in test_classes:
        instance = cls()
        methods = [m for m in dir(instance) if m.startswith("test_")]
        print(f"\n[{cls.__name__}]")
        for method_name in methods:
            try:
                getattr(instance, method_name)()
                passed += 1
            except AssertionError as e:
                print(f"  ✗ {method_name} FAILED: {e}")
                failed += 1
            except Exception as e:
                import traceback
                print(f"  ✗ {method_name} ERROR: {e}")
                traceback.print_exc()
                failed += 1

    print("\n" + "=" * 60)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
