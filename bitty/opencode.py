"""Puente con la CLI de OpenCode: detección, agente, sesiones y mensajes."""

from __future__ import annotations

import datetime as _dt
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


AGENT_TEXT = """---
description: Bitty, la mascota flotante de OpenCode
mode: primary
---
Eres Bitty, la mascota flotante de OpenCode creada por Marcelbon. Vives en el escritorio del usuario: eres una terminal diminuta, pixelada, en blanco y negro con un pequeno acento azul.

El usuario se llama Marcelbon. Tratalo siempre por su nombre y usalo cuando hables de el.

Hablas siempre en espanol, de forma breve y cercana, como un companero de escritorio. Si te preguntan quien eres o como te llamas, contesta exactamente: "Soy Bitty, tu mascota de OpenCode". No uses otros nombres de asistentes ni de modelos.
"""


def agent_path() -> Path:
    return Path.home() / ".config" / "opencode" / "agents" / "bitty.md"


def ensure_agent() -> Path:
    path = agent_path()
    if not path.exists():
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(AGENT_TEXT, encoding="utf-8")
        except OSError:
            pass
    return path


def find_exe() -> str | None:
    candidates = []
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA", "")
        local = os.environ.get("LOCALAPPDATA", "")
        if appdata:
            candidates.append(str(Path(appdata) / "npm" / "node_modules" / "@opencode" / "cli" / "bin" / "opencode.exe"))
        if local:
            candidates.append(str(Path(local) / "npm" / "node_modules" / "@opencode" / "cli" / "bin" / "opencode.exe"))
    else:
        candidates += [
            "/opt/homebrew/bin/opencode",
            "/usr/local/bin/opencode",
            "/usr/bin/opencode",
            str(Path.home() / ".npm-global" / "bin" / "opencode"),
            str(Path.home() / ".local" / "bin" / "opencode"),
            str(Path.home() / ".opencode" / "bin" / "opencode"),
        ]
    which = shutil.which("opencode")
    if which:
        candidates.append(which)
    for candidate in candidates:
        if candidate and (Path(candidate).is_file() or shutil.which(candidate)):
            return candidate
    return None


def working_dir() -> str:
    custom = os.environ.get("BITTY_WORKDIR")
    if custom and Path(custom).is_dir():
        return custom
    return str(Path.home())


def list_sessions(exe: str, limit: int = 8) -> list[dict]:
    try:
        proc = subprocess.run(
            [exe, "session", "list", "--format", "json", "--max-count", str(limit)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            creationflags=_no_window_flags(),
        )
        data = json.loads(proc.stdout)
        if isinstance(data, list):
            return data
    except (OSError, ValueError, subprocess.SubprocessError):
        pass
    return []


def send_message(exe: str, text: str, session_id: str = "") -> tuple[subprocess.Popen, Path, Path]:
    """Lanza `opencode run` y devuelve (proceso, salida, errores).

    Nunca usa --continue: o crea sesión nueva o va a un ID concreto.
    """
    out = Path(tempfile.gettempdir()) / "bitty-opencode-out.txt"
    err = Path(tempfile.gettempdir()) / "bitty-opencode-err.txt"
    for path in (out, err):
        try:
            path.write_text("", encoding="utf-8")
        except OSError:
            pass

    title = "BITTY " + _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    args = [exe, "run", "--agent", "bitty", "--title", title, "--format", "json"]
    if session_id:
        args += ["--session", session_id]
    args.append(text)

    handle_out = out.open("wb")
    handle_err = err.open("wb")
    try:
        proc = subprocess.Popen(
            args,
            stdout=handle_out,
            stderr=handle_err,
            cwd=working_dir(),
            creationflags=_no_window_flags(),
        )
    finally:
        # El hijo ya tiene sus propios descriptors: soltamos los del padre
        # para que otros procesos puedan leer la salida mientras se espera.
        handle_out.close()
        handle_err.close()
    return proc, out, err


def open_app(exe: str, session_id: str) -> bool:
    try:
        subprocess.Popen(
            [exe, "--session", session_id],
            cwd=working_dir(),
            creationflags=_no_window_flags(),
        )
        return True
    except OSError:
        return False


def parse_reply(path: Path, err_path: Path) -> tuple[str, str]:
    """Devuelve (texto, session_id) de la salida JSON de OpenCode."""
    raw = ""
    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        pass
    parts: list[str] = []
    sid = ""
    for line in raw.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except ValueError:
            continue
        if obj.get("sessionID"):
            sid = str(obj["sessionID"])
        if obj.get("type") == "text" and obj.get("part", {}).get("text"):
            parts.append(str(obj["part"]["text"]))
    if parts:
        return "\n".join(parts), sid
    if not raw:
        try:
            raw = err_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            pass
    return raw, sid


def _no_window_flags() -> int:
    if sys.platform == "win32":
        import subprocess as sp

        return getattr(sp, "CREATE_NO_WINDOW", 0)
    return 0
