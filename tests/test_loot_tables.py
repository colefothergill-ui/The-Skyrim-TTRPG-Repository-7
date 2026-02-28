#!/usr/bin/env python3
"""
Tests for Whiterun loot tables.
Validates that all new Whiterun-region tables are present in loot_tables.json
and that LootManager can roll them correctly.
"""

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../scripts")))

from loot_manager import LootManager

DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../data"))


@pytest.fixture(scope="module")
def loot_manager(tmp_path_factory):
    state_dir = tmp_path_factory.mktemp("state")
    return LootManager(DATA_DIR, str(state_dir))

WHITERUN_TABLES = [
    "whiterun_creature_scavenged",
    "whiterun_bandit_cache_minor",
    "whiterun_bandit_cache_major",
    "whiterun_barrow_reliquary",
    "whiterun_giant_camp_haul",
    "whiterun_hidden_treasure_minor",
    "whiterun_hidden_treasure_major",
    "whiterun_battlefield_minor",
    "whiterun_battlefield_major",
    "civil_war_field",
    "officer_trophy",
]


def _load_tables():
    path = os.path.join(DATA_DIR, "loot", "loot_tables.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_all_whiterun_tables_present():
    data = _load_tables()
    tables = data.get("tables", {})
    for table_id in WHITERUN_TABLES:
        assert table_id in tables, f"Missing loot table: {table_id}"


def test_whiterun_tables_have_required_fields():
    data = _load_tables()
    tables = data.get("tables", {})
    for table_id in WHITERUN_TABLES:
        table = tables.get(table_id)
        assert table is not None, f"Missing loot table: {table_id}"
        assert "rolls" in table, f"{table_id}: missing 'rolls'"
        assert "entries" in table, f"{table_id}: missing 'entries'"
        assert len(table["entries"]) > 0, f"{table_id}: entries must not be empty"
        for entry in table["entries"]:
            assert "text" in entry, f"{table_id}: entry missing 'text'"
            assert "weight" in entry, f"{table_id}: entry missing 'weight'"
            assert int(entry["weight"]) > 0, f"{table_id}: weight must be positive"


@pytest.mark.parametrize("table_id", WHITERUN_TABLES)
def test_loot_manager_rolls_whiterun_table(table_id, loot_manager):
    results = loot_manager.roll_table(table_id, seed=42)
    assert isinstance(results, list)
    assert len(results) > 0, f"Expected results from table '{table_id}'"
    for item in results:
        assert isinstance(item, str) and item, f"Each result must be a non-empty string"


def test_whiterun_bandit_cache_major_rolls_three(loot_manager):
    data = _load_tables()
    assert data["tables"]["whiterun_bandit_cache_major"]["rolls"] == 3
    results = loot_manager.roll_table("whiterun_bandit_cache_major", seed=1)
    assert len(results) == 3


def test_whiterun_hidden_treasure_minor_rolls_one(loot_manager):
    data = _load_tables()
    assert data["tables"]["whiterun_hidden_treasure_minor"]["rolls"] == 1
    results = loot_manager.roll_table("whiterun_hidden_treasure_minor", seed=1)
    assert len(results) == 1


def test_civil_war_field_updated_rolls():
    """civil_war_field should now use rolls=2 (updated from original rolls=1)."""
    data = _load_tables()
    assert data["tables"]["civil_war_field"]["rolls"] == 2


def test_officer_trophy_has_four_entries():
    """officer_trophy should now have 4 entries (updated from original 3)."""
    data = _load_tables()
    assert len(data["tables"]["officer_trophy"]["entries"]) == 4
