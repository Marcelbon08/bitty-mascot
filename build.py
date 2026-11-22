"""Empaqueta Bitty con PyInstaller para el sistema operativo actual.

Uso:
    python build.py

El resultado queda en dist/Bitty (Windows/Linux) o dist/Bitty.app (macOS).
Para distribuir, comprime esa carpeta/aplicación. GitHub Actions hace esto
automáticamente para los tres sistemas; ver .github/workflows/build.yml.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ICON = ROOT / "bitty" / "resources" / "bitty.ico"
SPRITES = ROOT / "bitty" / "resources" / "sprites"
SEP = ";" if sys.platform == "win32" else ":"
NAME = "Bitty"


def main() -> int:
    if shutil.which("pyinstaller") is None:
        try:
            import PyInstaller  # noqa: F401
        except ImportError:
            print("Falta PyInstaller: python -m pip install pyinstaller")
            return 1

    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm", "--clean", "--onedir", "--windowed",
        "--name", NAME,
        "--add-data", f"{SPRITES}{SEP}bitty/resources/sprites",
    ]
    if ICON.exists() and sys.platform == "win32":
        cmd += ["--icon", str(ICON)]
    cmd += ["--hidden-import", "pynput", str(ROOT / "run_bitty.py")]

    print(" ".join(cmd))
    env = dict(os.environ)
    result = subprocess.run(cmd, cwd=str(ROOT), env=env)
    if result.returncode != 0:
        return result.returncode

    out = ROOT / "dist" / (NAME + ".app" if sys.platform == "darwin" else NAME)
    print(f"\nListo: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
