"""Lista cerrada de aplicaciones que Bitty puede abrir.

Solo Brave. El nombre nunca se interpreta como comando: se busca en rutas
conocidas y en el PATH, y se lanza con `shell=False`. Si se pasa una URL,
debe superar la validación de `bitty.recipes` (HTTPS de Gmail/Google).
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any

OPEN_APPS = {
    "brave": (
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe",
        str(Path.home() / "AppData" / "Local" / "BraveSoftware" / "Brave-Browser" / "Application" / "brave.exe"),
        "/usr/bin/brave-browser",
        "/usr/bin/brave",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
    ),
}


def open_app(name: Any, url: Any = None) -> bool:
    """Abre una app permitida, opcionalmente en una URL permitida."""
    if not isinstance(name, str) or name not in OPEN_APPS:
        return False
    if url is not None:
        from .recipes import InvalidRecipe, validate_url
        try:
            url = validate_url(url)
        except InvalidRecipe:
            return False
    for candidate in (*OPEN_APPS[name], name):
        path = candidate if Path(candidate).is_file() else shutil.which(candidate)
        if path:
            args = [path] + ([url] if url else [])
            subprocess.Popen(args, shell=False)
            return True
    return False


__all__ = ["OPEN_APPS", "open_app"]
