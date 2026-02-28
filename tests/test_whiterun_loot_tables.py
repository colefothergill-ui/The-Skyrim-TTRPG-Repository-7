# tests/test_whiterun_loot_tables.py
import json
from pathlib import Path
from scripts.loot_manager import LootManager

def test_whiterun_loot_tables_load(tmp_path):
    data_dir = tmp_path / "data"
    state_dir = tmp_path / "state"
    (data_dir / "loot").mkdir(parents=True, exist_ok=True)

    loot_tables = {
        "tables": {
            "whiterun_battlefield_major": {
                "rolls": 1,
                "entries": [{"weight": 1, "text": "Test loot"}]
            }
        }
    }
    (data_dir / "loot" / "loot_tables.json").write_text(json.dumps(loot_tables), encoding="utf-8")

    lm = LootManager(data_dir=str(data_dir), state_dir=str(state_dir))
    out = lm.roll_table("whiterun_battlefield_major", seed=123)
    assert out == ["Test loot"]


def test_whiterun_hidden_treasure_major_table(tmp_path):
    state_dir = tmp_path / "state"
    repo_data_dir = Path(__file__).parent.parent / "data"

    lm = LootManager(data_dir=str(repo_data_dir), state_dir=str(state_dir))
    out = lm.roll_table("whiterun_hidden_treasure_major", seed=42)
    assert len(out) > 0
    assert all(isinstance(item, str) for item in out)
