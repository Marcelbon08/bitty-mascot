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

# Bitty solo usa QtCore, QtGui y QtWidgets. El resto de PySide6 (WebEngine,
# Pdf, Qml, Multimedia...) añade cientos de MB que nunca se ejecutan.
UNUSED_MODULES = [
    "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets", "PySide6.QtWebEngine",
    "PySide6.QtWebChannel", "PySide6.QtPdf", "PySide6.QtPdfWidgets",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuick3D",
    "PySide6.QtMultimedia", "PySide6.QtMultimediaWidgets",
    "PySide6.QtBluetooth", "PySide6.QtNfc", "PySide6.QtPositioning",
    "PySide6.QtSensors", "PySide6.QtSerialPort", "PySide6.QtSql",
    "PySide6.QtTest", "PySide6.QtDesigner", "PySide6.QtHelp",
    "PySide6.QtNetworkAuth", "PySide6.QtScxml", "PySide6.QtSpatialAudio",
    "PySide6.QtStateMachine", "PySide6.QtTextToSpeech", "PySide6.QtUiTools",
    "PySide6.QtCharts", "PySide6.QtDataVisualization",
]


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
    for module in UNUSED_MODULES:
        cmd += ["--exclude-module", module]

    # PySide6 6.5+ necesita libxcb-cursor para cargar el plugin xcb en Linux.
    # Lo incluimos en el bundle para que el binario funcione sin instalar nada.
    if sys.platform == "linux":
        for candidate in (
            "/usr/lib/x86_64-linux-gnu/libxcb-cursor.so.0",
            "/usr/lib64/libxcb-cursor.so.0",
        ):
            if Path(candidate).exists():
                cmd += ["--add-binary", f"{candidate}:."]
                break

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
