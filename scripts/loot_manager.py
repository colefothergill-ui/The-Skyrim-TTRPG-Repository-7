#!/usr/bin/env python3
"""
Loot Manager for Skyrim TTRPG (Fate-friendly)
"""

import json
import random
from pathlib import Path
from datetime import datetime


class LootManager:
    def __init__(self, data_dir: str = "../data", state_dir: str = "../state"):
        self.data_dir = Path(data_dir)
        self.state_dir = Path(state_dir)
        self.tables_path = self.data_dir / "loot" / "loot_tables.json"
        self.history_path = self.state_dir / "loot_history.json"

    def _load_tables(self):
        if self.tables_path.exists():
            with open(self.tables_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"tables": {}}

    def _append_history(self, table_id: str, results: list):
        try:
            self.state_dir.mkdir(parents=True, exist_ok=True)
            payload = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "table": table_id,
                "results": results,
            }
            history = []
            if self.history_path.exists():
                with open(self.history_path, "r", encoding="utf-8") as f:
                    history = json.load(f) or []
            history.append(payload)
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2)
        except Exception:
            pass

    def roll_table(self, table_id: str, rolls: int = None, *, seed=None) -> list:
        tables = self._load_tables().get("tables", {})
        table = tables.get(table_id)
        if not table:
            return []

        if rolls is None:
            rolls = int(table.get("rolls", 1))

        rng = random.Random(seed)
        entries = table.get("entries", [])
        if not entries:
            return []

        population = []
        for e in entries:
            try:
                w = int(e.get("weight", 1))
            except (TypeError, ValueError):
                w = 1
            if w <= 0:
                continue
            population.extend([e] * w)

        if not population:
            return []

        results = []
        for _ in range(max(1, int(rolls))):
            pick = rng.choice(population)
            results.append(str(pick.get("text") or pick))

        self._append_history(table_id, results)
        return results
