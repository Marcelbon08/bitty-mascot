"""Segundo cursor de Bitty: puntero pixelado estilo terminal, sin clics.

El ratón del usuario no se toca. Bitty saca este cursor cuando va a actuar,
hace su gesto y vuelve caminando hasta detrás de la mascota, donde queda
aparcado (no desaparece; se esconde en la espalda de Bitty).
"""

from __future__ import annotations

import ctypes
import math
import random
import sys
import time
from typing import Callable

from PySide6.QtCore import Qt, QPoint, QSize, QTimer
from PySide6.QtGui import QColor, QGuiApplication, QPainter
from PySide6.QtWidgets import QWidget

from .cursor_sprite import ARROW, colors_for
from .themes import Theme
from .virtual_cursor import TICK_MS, CursorNavigator, clamp_point

# El sprite vive en cursor_sprite.py: silueta de puntero con marco de terminal,
# acento del tema, bisel y un mini prompt «>». Aquí solo se escala y se pinta.
SCALE = 2
# Margen suficiente para dibujar el anillo del clic sin recortarlo.
PAD = 12
DEMO_MS = 1400
CLICK_MS = 450
# La vuelta no es un corte seco: una pausa breve, un arco suave y un último
# tramo en el que el cursor se «mete» bajo el sprite de Bitty.
RETURN_DELAY_MS = 180
RETURN_ARC_PX = 18
RETURN_STEP_PX = 10.0
RETURN_EASE = 0.16
RETURN_FADE_FROM = 0.72
RETURN_MIN_FADE = 0.35


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
        self._saved_step = self.nav.step
        self._saved_ease = self.nav.ease
        self.return_timer = QTimer(self)
        self.return_timer.setSingleShot(True)
        self.return_timer.timeout.connect(self._start_return)
        self.return_start = QPoint()
        self.return_total = 0.0
        self.move_timer = QTimer(self)
        self.move_timer.setInterval(TICK_MS)
        self.move_timer.timeout.connect(self._tick)

        self.demo_timer = QTimer(self)
        self.demo_timer.setInterval(DEMO_MS)
        self.demo_timer.timeout.connect(self._new_demo_point)
        self.demo = False
        # Oculto por defecto: solo aparece cuando Bitty va a actuar.
        self.visible = False
        self.pinned = False

        # El clic es solo un efecto visual del cursor propio de Bitty.
        self.click_timer = QTimer(self)
        self.click_timer.setInterval(40)
        self.click_timer.timeout.connect(self._click_tick)
        self.click_started = 0.0
        self.pending_click = False
        self.click_callback: Callable[[], None] | None = None
        # Tras el clic, el cursor vuelve hacia la mascota en lugar de ocultarse.
        self.returning = False
        # Atenuación al meter el cursor bajo Bitty. Se aplica al pintar (las
        # ventanas Tool de Qt no siempre respetan setWindowOpacity en Windows).
        self.fade = 1.0

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
        """Manda el cursor hacia una coordenada de pantalla con movimiento fluido."""
        cx, cy = clamp_point((int(x), int(y)), self.screen_rects())
        # Siempre se desplaza desde donde está (tras la mascota). Así se ve
        # cómo Bitty «saca» su ratón para hacer la acción.
        self.nav.go_to(cx, cy)
        if self.visible:
            # No cambiamos el Z aquí: durante la vuelta debe seguir visible
            # hasta llegar a la espalda de Bitty; el orden se ajusta al terminar.
            self.show()
        self.move_timer.start()

    def center(self) -> None:
        screen = QGuiApplication.screenAt(self.pos()) or QGuiApplication.primaryScreen()
        if screen:
            point = screen.availableGeometry().center()
            self.go_to(point.x(), point.y())

    def _tick(self) -> None:
        x, y = self.nav.advance()
        if self.returning and self.return_total > 0:
            # Arco suave hacia la espalda de Bitty: el cursor «salta» un poco
            # en lugar de seguir una línea recta, y al llegar se desvanece
            # cuando ya está a punto de quedar tapado por el sprite.
            progress = 1.0 - min(1.0, self.nav.distance / self.return_total)
            dx = self.home.x() - self.return_start.x()
            dy = self.home.y() - self.return_start.y()
            length = math.hypot(dx, dy) or 1.0
            bow = math.sin(progress * math.pi) * RETURN_ARC_PX
            x += int(round(-dy / length * bow))
            y += int(round(dx / length * bow))
            if progress > RETURN_FADE_FROM:
                fade = (progress - RETURN_FADE_FROM) / (1.0 - RETURN_FADE_FROM)
                self.fade = max(RETURN_MIN_FADE, 1.0 - (1.0 - RETURN_MIN_FADE) * fade)
            self.update()
        self.move(x, y)
        if not self.nav.moving:
            self.move_timer.stop()
            if self.pending_click:
                self._begin_click()
            elif self.returning:
                self._finish_return()

    # ---------------------------------------------------------------- clic
    def click(self, x: int, y: int, on_clicked: Callable[[], None] | None = None) -> None:
        """Sale de detrás de Bitty, hace clic en (x, y) y vuelve con él."""
        self.visible = True
        self.returning = False
        self.return_timer.stop()
        self._restore_nav()
        self.fade = 1.0
        self.click_callback = on_clicked
        self._set_z(True)
        self.go_to(x, y)
        self.pending_click = True
        if not self.nav.moving:
            self._begin_click()

    def park(self) -> None:
        """Se coloca detrás de la mascota: sigue ahí, pero lo tapa Bitty."""
        self.click_timer.stop()
        self.return_timer.stop()
        self.click_started = 0.0
        self.pending_click = False
        self.returning = False
        self.return_total = 0.0
        self._restore_nav()
        self.click_callback = None
        self.move_timer.stop()
        self.fade = 1.0
        self.nav.snap_to(self.home.x(), self.home.y())
        self.move(self.home.x(), self.home.y())
        self.visible = True
        self.show()
        self._tuck_behind()

    def _restore_nav(self) -> None:
        """Devuelve la velocidad normal tras la vuelta más lenta."""
        self.nav.step = self._saved_step
        self.nav.ease = self._saved_ease

    def _set_z(self, on_top: bool) -> None:
        """Coloca el cursor sobre Bitty (acción) o bajo él (aparcado)."""
        if sys.platform != "win32":
            if on_top:
                self.raise_()
            else:
                self.lower()
            return
        # Qt no pone WS_EX_TOPMOST en esta ventana Tool aunque lo pidamos.
        # HWND_TOPMOST (-1) lo eleva sobre Bitty durante la acción;
        # HWND_NOTOPMOST (-2) lo deja debajo del sprite al aparcarlo.
        flags = 0x0001 | 0x0002 | 0x0010  # NOSIZE | NOMOVE | NOACTIVATE
        user32 = ctypes.windll.user32
        user32.SetWindowPos.argtypes = [
            ctypes.c_void_p, ctypes.c_void_p,
            ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
            ctypes.c_uint,
        ]
        user32.SetWindowPos.restype = ctypes.c_bool
        user32.SetWindowPos(
            ctypes.c_void_p(int(self.winId())),
            ctypes.c_void_p(-1 if on_top else -2),
            0, 0, 0, 0, flags,
        )

    def _tuck_behind(self) -> None:
        """Deja el cursor vivo pero por debajo de la ventana de Bitty."""
        parent = self.parentWidget()
        if parent is not None:
            parent.raise_()
        self._set_z(False)

    def _start_return(self) -> None:
        """Inicia el camino de vuelta hacia la espalda de Bitty."""
        self.return_timer.stop()
        self.return_start = QPoint(round(self.nav.x), round(self.nav.y))
        self.return_total = max(
            1.0, math.hypot(self.home.x() - self.return_start.x(),
                            self.home.y() - self.return_start.y())
        )
        self._saved_step, self._saved_ease = self.nav.step, self.nav.ease
        self.nav.step = RETURN_STEP_PX
        self.nav.ease = RETURN_EASE
        self.returning = True
        self.go_to(self.home.x(), self.home.y())

    def _finish_return(self) -> None:
        self.returning = False
        self.fade = 1.0
        self.park()

    def _begin_click(self) -> None:
        self.pending_click = False
        self.click_started = time.monotonic()
        self.click_timer.start()
        self.update()
        callback, self.click_callback = self.click_callback, None
        if callback:
            try:
                callback()
            except Exception:
                pass

    def _click_tick(self) -> None:
        if time.monotonic() - self.click_started >= CLICK_MS / 1000:
            self.click_timer.stop()
            self.click_started = 0.0
            self.update()
            # Pequeña pausa: se ve el anillo del clic antes de darse la vuelta.
            self.return_timer.start(RETURN_DELAY_MS)
        else:
            self.update()

    # --------------------------------------------------------------- modes
    def toggle_demo(self) -> bool:
        """Activa/desactiva una ruta de puntos alrededor de la mascota."""
        self.demo = not self.demo
        if self.demo:
            self.return_timer.stop()
            self.returning = False
            self.return_total = 0.0
            self._restore_nav()
            self.fade = 1.0
            self.visible = True
            self.show()
            self._set_z(True)
            self._new_demo_point()
            self.demo_timer.start()
        else:
            self.demo_timer.stop()
            if not self.pinned:
                self.park()
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
        self.pinned = shown
        self.visible = shown
        if shown:
            self.show()
            self._set_z(True)
            self.move_timer.start()
        else:
            self.stop_demo()
            self.move_timer.stop()
            self.return_timer.stop()
            self._restore_nav()
            self.visible = False
            self.fade = 1.0
            self.hide()

    def stop(self) -> None:
        self.demo_timer.stop()
        self.move_timer.stop()
        self.click_timer.stop()
        self.return_timer.stop()
        self.click_started = 0.0
        self.pending_click = False
        self.returning = False
        self.return_total = 0.0
        self._restore_nav()
        self.click_callback = None
        self.visible = False
        self.fade = 1.0
        self.hide()

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    # -------------------------------------------------------------- paint
    def paintEvent(self, event) -> None:  # noqa: N802
        palette = self.theme.palette
        # El sprite define su propia paleta; el punto se omite (transparente).
        # La atenuación se aplica aquí para que se vea también en ventanas Tool.
        colors: dict[str, QColor] = {}
        for char, rgb in colors_for(self.theme).items():
            color = QColor(*rgb)
            color.setAlphaF(self.fade)
            colors[char] = color
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
        if self.click_started:
            # Anillo que se expande: es el clic del cursor de Bitty, nunca del
            # ratón del usuario. La ventana sigue siendo transparente a eventos.
            progress = min(1.0, (time.monotonic() - self.click_started) / (CLICK_MS / 1000))
            color = QColor(*palette["bright"])
            color.setAlphaF((1.0 - progress) * self.fade)
            center = QPoint(PAD + 4, PAD + 4)
            radius = int(3 + 9 * progress)
            painter.setPen(color)
            painter.drawEllipse(center, radius, radius)
            if progress < 0.4:
                painter.setBrush(color)
                painter.drawEllipse(center, 2, 2)
        painter.end()
