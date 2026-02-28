#!/usr/bin/env python3
"""
Test suite for Whiterun loot tables.
Validates that Whiterun-specific and civil war common tables load correctly and produce results.
"""

import sys
import os
import json
import tempfile
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'scripts'))

from loot_manager import LootManager


WHITERUN_TABLES = [
    "whiterun_market",
    "whiterun_siege",
    "whiterun_dragonsreach",
]

CIVIL_WAR_TABLES = [
    "civil_war_field",
    "civil_war_common",
    "officer_trophy",
]


def _manager(tmp_path):
    data_dir = Path(__file__).parent.parent / "data"
    return LootManager(data_dir=str(data_dir), state_dir=str(tmp_path))


def test_whiterun_loot_tables_exist():
    """All Whiterun tables are present in loot_tables.json."""
    tables_path = Path(__file__).parent.parent / "data" / "loot" / "loot_tables.json"
    assert tables_path.exists(), "loot_tables.json not found"
    data = json.loads(tables_path.read_text(encoding="utf-8"))
    tables = data.get("tables", {})
    for table_id in WHITERUN_TABLES + CIVIL_WAR_TABLES:
        assert table_id in tables, f"Expected table '{table_id}' not found in loot_tables.json"


def test_whiterun_loot_tables_have_entries():
    """All Whiterun and civil war tables have at least one weighted entry."""
    tables_path = Path(__file__).parent.parent / "data" / "loot" / "loot_tables.json"
    data = json.loads(tables_path.read_text(encoding="utf-8"))
    tables = data.get("tables", {})
    for table_id in WHITERUN_TABLES + CIVIL_WAR_TABLES:
        table = tables[table_id]
        entries = table.get("entries", [])
        assert len(entries) >= 1, f"Table '{table_id}' has no entries"
        for e in entries:
            assert "text" in e, f"Entry in '{table_id}' missing 'text'"
            assert "weight" in e, f"Entry in '{table_id}' missing 'weight'"
            try:
                w = int(e["weight"])
            except (ValueError, TypeError):
                raise AssertionError(f"Entry in '{table_id}' has non-numeric weight: {e['weight']!r}")
            assert w >= 1, f"Entry in '{table_id}' has non-positive weight: {w}"


def test_whiterun_loot_roll():
    """LootManager.roll_table produces results for each Whiterun table."""
    with tempfile.TemporaryDirectory() as tmp:
        mgr = _manager(tmp)
        for table_id in WHITERUN_TABLES:
            results = mgr.roll_table(table_id, seed=42)
            assert len(results) >= 1, f"roll_table('{table_id}') returned no results"
            for item in results:
                assert isinstance(item, str) and len(item) > 0, \
                    f"roll_table('{table_id}') returned non-string or empty result: {item!r}"


def test_civil_war_common_roll():
    """LootManager.roll_table produces results for civil war common tables."""
    with tempfile.TemporaryDirectory() as tmp:
        mgr = _manager(tmp)
        for table_id in CIVIL_WAR_TABLES:
            results = mgr.roll_table(table_id, seed=7)
            assert len(results) >= 1, f"roll_table('{table_id}') returned no results"


def test_whiterun_siege_contains_legate_hook():
    """The whiterun_siege table contains at least one Thalmor/cipher story hook entry."""
    tables_path = Path(__file__).parent.parent / "data" / "loot" / "loot_tables.json"
    data = json.loads(tables_path.read_text(encoding="utf-8"))
    entries = data["tables"]["whiterun_siege"]["entries"]
    hook_texts = [e["text"] for e in entries if "Thalmor" in e["text"] or "cipher" in e["text"]]
    assert len(hook_texts) >= 1, "whiterun_siege table should contain at least one Thalmor/cipher story hook"


def main():
    """Run all Whiterun loot tests."""
    print("=" * 60)
    print("WHITERUN LOOT TABLE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Tables exist in JSON", test_whiterun_loot_tables_exist),
        ("Tables have valid entries", test_whiterun_loot_tables_have_entries),
        ("Whiterun roll produces results", test_whiterun_loot_roll),
        ("Civil war common roll", test_civil_war_common_roll),
        ("Siege table contains Thalmor hook", test_whiterun_siege_contains_legate_hook),
    ]

    passed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"✓ PASS: {name}")
            passed += 1
        except Exception as exc:
            print(f"✗ FAIL: {name} — {exc}")

    print(f"\nTotal: {passed}/{len(tests)} passed")
    return 0 if passed == len(tests) else 1


if __name__ == "__main__":
    sys.exit(main())
