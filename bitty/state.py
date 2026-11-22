"""Persistencia portable de Bitty (posición, paseo, sesión y tema)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def config_dir() -> Path:
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or str(Path.home() / ".config")
    return Path(base) / "BittyMascot"


STATE_PATH = config_dir() / "state.json"

DEFAULT = {
    "x": None,
    "y": None,
    "roam_paused": False,
    "session_mode": "new",
    "session_id": "",
    "session_label": "",
    "theme": "auto",
}


def load() -> dict:
    data = dict(DEFAULT)
    try:
        if STATE_PATH.exists():
            raw = json.loads(STATE_PATH.read_text(encoding="utf-8"))
            for key in DEFAULT:
                if key in raw:
                    data[key] = raw[key]
    except (OSError, ValueError, TypeError):
        pass
    if data.get("theme") not in ("auto", "original", "navidad", "halloween"):
        data["theme"] = "auto"
    if data.get("session_mode") not in ("new", "continue"):
        data["session_mode"] = "new"
    return data


def save(data: dict) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(
            json.dumps({k: data.get(k, v) for k, v in DEFAULT.items()}, ensure_ascii=False),
            encoding="utf-8",
        )
    except OSError:
        pass
