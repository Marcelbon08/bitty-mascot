"""Persistencia portable de Bitty (posición, paseo, sesión y tema)."""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

from .cursor_sprite import SPRITES


_SESSION_ID_RE = re.compile(r"^[A-Za-z0-9_][A-Za-z0-9_-]{0,127}$")


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
    "cursor_style": "clasico",
    "bridge_enabled": True,
    "agreement_version": 0,
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
    if data.get("cursor_style") not in SPRITES:
        data["cursor_style"] = "clasico"
    version = data.get("agreement_version")
    data["agreement_version"] = (
        version if not isinstance(version, bool) and version in (0, 1) else 0
    )

    # Un state.json manipulado no debe poder introducir valores raros en la
    # interfaz ni en los argumentos del ejecutable de OpenCode.
    sid = data.get("session_id")
    if not isinstance(sid, str) or not _SESSION_ID_RE.fullmatch(sid):
        data["session_id"] = ""
    label = data.get("session_label")
    data["session_label"] = label[:80] if isinstance(label, str) else ""
    data["roam_paused"] = bool(data.get("roam_paused"))
    data["bridge_enabled"] = bool(data.get("bridge_enabled", True))
    for axis in ("x", "y"):
        value = data.get(axis)
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            data[axis] = None
    return data


def serialize(data: dict) -> str:
    """Representación estable del estado; permite no escribir si no cambió."""
    return json.dumps(
        {k: data.get(k, v) for k, v in DEFAULT.items()},
        ensure_ascii=False, sort_keys=True,
    )


def save(data: dict) -> None:
    try:
        STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATE_PATH.write_text(serialize(data), encoding="utf-8")
    except OSError:
        pass
