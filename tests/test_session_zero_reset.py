import json
import os
import sys
import pytest

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_campaign_state_session_one_checkpoint():
    path = os.path.join(REPO_ROOT, "state", "campaign_state.json")
    with open(path) as f:
        state = json.load(f)
    # Campaign has advanced past Session Zero into Session 01
    assert state.get("session_zero_completed") is True
    assert state.get("active_pc_id") == "pc_wayn"
    assert state.get("current_scene_id") == "A1-S2_Jorrvaskr_HarbingerDoor"
    assert state.get("pcs") == {}
    # scene_flags and npc_trust are now populated for session 01
    assert "jorvaskr_athis_spar_resolved" in state.get("scene_flags", {})
    assert "athis" in state.get("npc_trust", {})


def test_no_old_pc_names_in_repo():
    forbidden = [
        "Elitrof",
        "Insaerndel",
        "Isaerndel",
        "Orinthelo",
        "pc_elitrof_whitemane",
        "pc_insaerndel",
    ]
    skip_dirs = {".git", "__pycache__", "source_material"}
    skip_files = {"test_session_zero_reset.py"}
    
    violations = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if fname in skip_files:
                continue
            fpath = os.path.join(root, fname)
            # Only text files
            if not fname.endswith(('.json', '.md', '.py', '.txt', '.yaml', '.yml')):
                continue
            try:
                with open(fpath, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                for term in forbidden:
                    if term in content:
                        violations.append(f"{fpath}: contains '{term}'")
            except Exception:
                pass
    assert violations == [], "Found forbidden old-PC references:\n" + "\n".join(violations)


def test_no_rivalry_with_elitrof_clock():
    skip_dirs = {".git", "__pycache__"}
    violations = []
    for root, dirs, files in os.walk(REPO_ROOT):
        dirs[:] = [d for d in dirs if d not in skip_dirs]
        for fname in files:
            if not fname.endswith('.json'):
                continue
            fpath = os.path.join(root, fname)
            try:
                with open(fpath, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                if "rivalry_with_elitrof" in content:
                    violations.append(fpath)
            except Exception:
                pass
    assert violations == [], "Found rivalry_with_elitrof clock key in:\n" + "\n".join(violations)


def test_kodlak_whitemane_preserved():
    path = os.path.join(REPO_ROOT, "data", "npc_stat_sheets", "kodlak_whitemane.json")
    assert os.path.exists(path), "kodlak_whitemane.json must exist"
    with open(path) as f:
        data = json.load(f)
    assert "Kodlak" in json.dumps(data), "Kodlak must still be present in his stat sheet"


def test_companions_questline_preserved():
    path = os.path.join(REPO_ROOT, "data", "quests", "companions_questline.json")
    assert os.path.exists(path), "companions_questline.json must exist"


sys.path.insert(0, os.path.join(REPO_ROOT, "scripts"))

def test_resolve_active_pc_id_returns_none_when_empty():
    import importlib
    fi = importlib.import_module("first_impression")
    assert fi.resolve_active_pc_id({}) is None
    assert fi.resolve_active_pc_id({"pcs": {}}) is None
    assert fi.resolve_active_pc_id({"player_characters": []}) is None


def test_resolve_active_pc_id_returns_explicit():
    import importlib
    fi = importlib.import_module("first_impression")
    assert fi.resolve_active_pc_id({"active_pc_id": "pc_test"}) == "pc_test"
    assert fi.resolve_active_pc_id({"active_pc": "pc_test2"}) == "pc_test2"
