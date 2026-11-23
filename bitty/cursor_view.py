"""Segundo cursor de Bitty: ventana transparente, siempre visible y sin clics.

El ratón del usuario no se toca. Esta ventana solo dibuja un puntero pixelado
que se desplaza hacia las coordenadas que se le dan, interpolando cada 20 ms.
"""

from __future__ import annotations

import random

from PySide6.QtCore import Qt, QPoint, QSize, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from .themes import Theme
from .virtual_cursor import TICK_MS, CursorNavigator, clamp_point

# Puntero pixelado de 12 x 15. X = borde, f = relleno, h = brillo.
ARROW = (
    "h...........",
    "Xh..........",
    "Xfh.........",
    "Xffh........",
    "Xfffh.......",
    "Xffffh......",
    "Xfffffh.....",
    "Xffffffh....",
    "Xffffffffh..",
    "XffffffffXX.",
    "XffXffffX...",
    "XfX.XfffX...",
    "XX...XffX...",
    "X.....XfX...",
    ".......XX...",
)
SCALE = 2
PAD = 2
DEMO_MS = 1400


class BittyCursorView(QWidget):
    """Puntero propio de Bitty, dibujado sobre el escritorio sin capturar entrada."""

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.random = random.Random()
        self.home = QPoint()

        flags = (
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        if hasattr(Qt.WindowType, "WindowTransparentForInput"):
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setWindowTitle("Bitty (cursor)")
        self.resize(QSize(len(ARROW[0]) * SCALE + PAD * 2, len(ARROW) * SCALE + PAD * 2))

        self.nav = CursorNavigator(0, 0)
        self.move_timer = QTimer(self)
        self.move_timer.setInterval(TICK_MS)
        self.move_timer.timeout.connect(self._tick)

        self.demo_timer = QTimer(self)
        self.demo_timer.setInterval(DEMO_MS)
        self.demo_timer.timeout.connect(self._new_demo_point)
        self.demo = False
        self.visible = True

    # ------------------------------------------------------------ posición
    @staticmethod
    def screen_rects() -> list[tuple[int, int, int, int]]:
        screens = QGuiApplication.screens()
        return [
            (s.geometry().left(), s.geometry().top(), s.geometry().right(), s.geometry().bottom())
            for s in screens
        ]

    def set_home(self, point: QPoint) -> None:
        """Punto de referencia para la ruta aleatoria (normalmente la mascota)."""
        self.home = QPoint(point)

    def go_to(self, x: int, y: int) -> None:
        """Manda el cursor hacia una coordenada de pantalla, con Movimiento fluido."""
        cx, cy = clamp_point((int(x), int(y)), self.screen_rects())
        if not self.nav.moving:
            # Solo al inicio: arranca desde donde se le pidió, sin venir de (0, 0).
            if self.nav.distance == 0 and not self.isVisible():
                self.nav.snap_to(cx, cy)
        self.nav.go_to(cx, cy)
        if self.visible:
            self.show()
            self.raise_()
        self.move_timer.start()

    def center(self) -> None:
        screen = QGuiApplication.screenAt(self.pos()) or QGuiApplication.primaryScreen()
        if screen:
            point = screen.availableGeometry().center()
            self.go_to(point.x(), point.y())

    def _tick(self) -> None:
        x, y = self.nav.advance()
        self.move(x, y)
        if not self.nav.moving:
            self.move_timer.stop()

    # --------------------------------------------------------------- modes
    def toggle_demo(self) -> bool:
        """Activa/desactiva una ruta de puntos alrededor de la mascota."""
        self.demo = not self.demo
        if self.demo:
            self.visible = True
            self.show()
            self.raise_()
            self._new_demo_point()
            self.demo_timer.start()
        else:
            self.demo_timer.stop()
        return self.demo

    def _new_demo_point(self) -> None:
        home = self.home
        x = home.x() + self.random.randint(-170, 170)
        y = home.y() + self.random.randint(-120, 120)
        self.go_to(x, y)

    def stop_demo(self) -> None:
        if self.demo:
            self.toggle_demo()

    def set_visible_cursor(self, shown: bool) -> None:
        self.visible = shown
        if shown:
            self.show()
            self.raise_()
            self.move_timer.start()
        else:
            self.stop_demo()
            self.move_timer.stop()
            self.hide()

    def stop(self) -> None:
        self.demo_timer.stop()
        self.move_timer.stop()
        self.hide()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    # -------------------------------------------------------------- paint
    def paintEvent(self, event) -> None:  # noqa: N802
        palette = self.theme.palette
        colors = {
            "X": QColor(0, 0, 0),
            "f": QColor(*palette["accent"]),
            "h": QColor(*palette["bright"]),
        }
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for row, line in enumerate(ARROW):
            for column, char in enumerate(line):
                if char in colors:
                    painter.fillRect(
                        column * SCALE + PAD,
                        row * SCALE + PAD,
                        SCALE,
                        SCALE,
                        colors[char],
                    )
        painter.end()
