"""Settings management for oh-my-gitstats."""

import json
from pathlib import Path


GITSTATS_DIR = Path("~/.gitstats").expanduser()
SETTINGS_PATH = GITSTATS_DIR / "settings.json"

DEFAULT_SETTINGS = {
    "data_dir": "~/.gitstats/data",
    "output_html": "~/.gitstats/stats.html",
    "collect_paths": [],
}


def _resolve_path(p: str) -> str:
    return str(Path(p).expanduser())


def load_settings() -> dict:
    """Load settings from disk, merging with defaults.

    Returns a dict with resolved Path objects for data_dir/output_html,
    and a list of resolved strings for collect_paths.
    """
    settings = dict(DEFAULT_SETTINGS)
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                user_settings = json.load(f)
            settings.update(user_settings)
        except (json.JSONDecodeError, PermissionError) as e:
            print(f"Warning: could not read {SETTINGS_PATH}: {e}")

    return {
        "data_dir": Path(_resolve_path(settings["data_dir"])),
        "output_html": Path(_resolve_path(settings["output_html"])),
        "collect_paths": [_resolve_path(p) for p in settings.get("collect_paths", [])],
    }


def save_settings(settings: dict) -> None:
    GITSTATS_DIR.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def add_collect_path(path: str) -> None:
    """Add an absolute path to collect_paths in settings, with dedup."""
    abs_path = str(Path(path).resolve())
    raw = dict(DEFAULT_SETTINGS)
    if SETTINGS_PATH.exists():
        try:
            with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
                raw.update(json.load(f))
        except (json.JSONDecodeError, PermissionError):
            pass

    existing = [_resolve_path(p) for p in raw.get("collect_paths", [])]
    existing_resolved = [str(Path(p).resolve()) for p in existing]
    if abs_path not in existing_resolved:
        raw["collect_paths"].append(abs_path)
        save_settings(raw)


def init_default_settings() -> None:
    """Create default settings file if it does not exist."""
    if not SETTINGS_PATH.exists():
        save_settings(DEFAULT_SETTINGS)
        print(f"Created default settings at {SETTINGS_PATH}")
        print(f"Edit it to configure collect_paths for 'gitstats auto'.\n")
