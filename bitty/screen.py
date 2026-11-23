"""Captura de pantalla para el puente local de Bitty.

Usa Qt (ya incluido en la mascota), sin dependencias nuevas. Devuelve un PNG
en disco para que OpenCode pueda adjuntarlo como imagen a una herramienta.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QGuiApplication, QPainter


def capture_to_png(destination: Path) -> dict:
    """Captura todas las pantallas y guarda un PNG. Devuelve sus dimensiones."""
    screens = QGuiApplication.screens()
    if not screens:
        raise RuntimeError("No hay pantallas disponibles para capturar.")

    if len(screens) == 1:
        image = screens[0].grabWindow(0).toImage()
    else:
        geometries = [s.geometry() for s in screens]
        left = min(g.left() for g in geometries)
        top = min(g.top() for g in geometries)
        right = max(g.right() for g in geometries)
        bottom = max(g.bottom() for g in geometries)
        from PySide6.QtGui import QImage, QColor

        image = QImage(right - left + 1, bottom - top + 1, QImage.Format.Format_ARGB32)
        image.fill(QColor(0, 0, 0, 255))
        painter = QPainter(image)
        for screen, geometry in zip(screens, geometries):
            pixmap = screen.grabWindow(0)
            if not pixmap.isNull():
                painter.drawPixmap(geometry.left() - left, geometry.top() - top, pixmap)
        painter.end()

    if image.isNull():
        raise RuntimeError("Qt no pudo capturar la pantalla (Wayland o sesión sin escritorio).")

    destination.parent.mkdir(parents=True, exist_ok=True)
    if not image.save(str(destination), "PNG"):
        raise RuntimeError("No se pudo guardar la captura PNG.")
    return {
        "path": str(destination),
        "uri": destination.resolve().as_uri(),
        "width": image.width(),
        "height": image.height(),
        "screens": len(screens),
    }


__all__ = ["capture_to_png"]
