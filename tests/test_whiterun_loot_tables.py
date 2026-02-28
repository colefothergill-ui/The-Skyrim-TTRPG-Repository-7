#!/usr/bin/env python3
"""
Tests for Whiterun and civil war loot tables.
Verifies that all new tables load correctly and produce results when rolled.
"""

import json
import sys
import os
import pytest
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

from loot_manager import LootManager


WHITERUN_TABLES = [
    "whiterun_common",
    "whiterun_siege_intelligence",
    "whiterun_officer_trophy",
]

CIVIL_WAR_TABLES = [
    "civil_war_field",
    "civil_war_common",
]


@pytest.fixture
def loot_manager(tmp_path):
    data_dir = Path(__file__).parent.parent / "data"
    return LootManager(data_dir=str(data_dir), state_dir=str(tmp_path))


def test_loot_tables_json_is_valid():
    """The loot_tables.json file must be valid JSON."""
    tables_path = Path(__file__).parent.parent / "data" / "loot" / "loot_tables.json"
    assert tables_path.exists(), "loot_tables.json not found"
    with open(tables_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "tables" in data, "loot_tables.json missing top-level 'tables' key"


def test_whiterun_tables_present():
    """All Whiterun-specific tables must be present in loot_tables.json."""
    tables_path = Path(__file__).parent.parent / "data" / "loot" / "loot_tables.json"
    with open(tables_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tables = data.get("tables", {})
    for table_id in WHITERUN_TABLES:
        assert table_id in tables, f"Missing Whiterun loot table: {table_id}"
        assert "entries" in tables[table_id], f"Table '{table_id}' missing 'entries'"
        assert len(tables[table_id]["entries"]) > 0, f"Table '{table_id}' has no entries"


def test_civil_war_tables_present():
    """All civil war common tables must be present in loot_tables.json."""
    tables_path = Path(__file__).parent.parent / "data" / "loot" / "loot_tables.json"
    with open(tables_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tables = data.get("tables", {})
    for table_id in CIVIL_WAR_TABLES:
        assert table_id in tables, f"Missing civil war loot table: {table_id}"


def test_whiterun_common_roll_produces_results(loot_manager):
    """Rolling whiterun_common should return at least one result."""
    results = loot_manager.roll_table("whiterun_common", rolls=1, seed=42)
    assert len(results) >= 1, "whiterun_common roll returned no results"
    assert all(isinstance(r, str) and len(r) > 0 for r in results), \
        "whiterun_common roll returned non-string or empty entries"


def test_whiterun_siege_intelligence_roll(loot_manager):
    """Rolling whiterun_siege_intelligence should return a non-empty result."""
    results = loot_manager.roll_table("whiterun_siege_intelligence", rolls=1, seed=7)
    assert len(results) >= 1, "whiterun_siege_intelligence roll returned no results"


def test_whiterun_officer_trophy_roll(loot_manager):
    """Rolling whiterun_officer_trophy should return a result."""
    results = loot_manager.roll_table("whiterun_officer_trophy", rolls=1, seed=1)
    assert len(results) >= 1, "whiterun_officer_trophy roll returned no results"


def test_civil_war_common_roll(loot_manager):
    """Rolling civil_war_common should return results with default rolls count."""
    results = loot_manager.roll_table("civil_war_common", seed=99)
    assert len(results) >= 1, "civil_war_common roll returned no results"


def test_unknown_table_returns_empty(loot_manager):
    """Rolling an unknown table should return an empty list, not raise."""
    results = loot_manager.roll_table("nonexistent_table_xyz")
    assert results == [], "Unknown table should return empty list"
