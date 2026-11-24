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
AGREEMENT = ROOT / "ACUERDO.md"
ICON = ROOT / "bitty" / "resources" / "bitty.ico"
SPRITES = ROOT / "bitty" / "resources" / "sprites"
ICONS = ROOT / "bitty" / "resources" / "icons"
SEP = ";" if sys.platform == "win32" else ":"
NAME = "Bitty"

# Bitty solo usa QtCore, QtGui y QtWidgets. El resto de PySide6 (WebEngine,
# Pdf, Qml, Multimedia...) añade cientos de MB que nunca se ejecutan.
# PyInstaller copia las DLLs/SOs de PySide6 aunque el módulo Python esté
# excluido, así que hay que retirarlas del bundle ya generado.
UNUSED_QT_LIBS = [
    "Qt6Pdf", "Qt6Qml", "Qt6QmlMeta", "Qt6QmlModels", "Qt6QmlWorkerScript",
    "Qt6Quick", "Qt6VirtualKeyboard",
]


def prune_unused_qt(out: Path) -> list[str]:
    """Quita bibliotecas Qt que Bitty nunca carga. Devuelve lo eliminado."""
    removed: list[str] = []
    if sys.platform == "darwin":
        return removed  # Los frameworks de macOS se tratan en otra versión.

    folders = [out / "_internal", out / "_internal" / "PySide6"]
    if sys.platform == "linux":
        folders += [out / "PySide6", out]
    for folder in folders:
        if not folder.is_dir():
            continue
        for lib in UNUSED_QT_LIBS:
            patterns = (
                [f"{lib}.dll"] if sys.platform == "win32"
                else [f"lib{lib}.so*"]
            )
            for pattern in patterns:
                for path in folder.glob(pattern):
                    path.unlink()
                    removed.append(path.name)
    return sorted(set(removed))


def copy_agreement(out: Path) -> bool:
    """Copia el acuerdo dentro del paquete para que se pueda leer al instalar."""
    if not AGREEMENT.is_file():
        return False
    if sys.platform == "darwin":
        destination = out / "Contents" / "Resources" / "ACUERDO.md"
    else:
        destination = out / "ACUERDO.md"
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(AGREEMENT, destination)
    return True


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
    if ICONS.is_dir():
        cmd += ["--add-data", f"{ICONS}{SEP}bitty/resources/icons"]
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
    removed = prune_unused_qt(out)
    if removed:
        print("Bibliotecas Qt retiradas del bundle: " + ", ".join(removed))
    if copy_agreement(out):
        print("Acuerdo incluido en el paquete.")
    print(f"\nListo: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
