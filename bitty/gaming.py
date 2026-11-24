"""Atajo flotante del modo gaming de Bitty.

Cuando Bitty se oculta para no molestar durante una partida, deja esta ventanita
del tamaño de una moneda en una esquina. No sustituye a la mascota: es solo un
acceso rápido para recuperarla. Se puede arrastrar; clic izquierdo devuelve a
Bitty y abre su bocadillo, clic derecho solo lo devuelve.

Nunca mueve el ratón del usuario ni envía clics al escritorio: es una ventana
propia de Qt que reacciona a los clics que el usuario hace sobre ella.
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QPainter, QPen
from PySide6.QtWidgets import QWidget, QToolTip

from .themes import Theme

SIZE = 48


class GamingShortcut(QWidget):
    """Mini terminal en la esquina: puerta de vuelta del modo gaming."""

    restore_requested = Signal()
    restore_quiet_requested = Signal()

    def __init__(self, theme: Theme, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.theme = theme
        self.setWindowTitle("Bitty (gaming)")
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setToolTip("BITTY EN GAMING — clic para volver")
        self.resize(SIZE, SIZE)
        self.setWindowOpacity(0.72)

        self.dragging = False
        self.moved = False
        self.drag_origin = QPoint()
        self.drag_offset = QPoint()
        self.button = Qt.MouseButton.NoButton

        screen = QGuiApplication.screenAt(QPoint(0, 0)) or QGuiApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(geo.left() + 12, geo.top() + 12)

    def set_theme(self, theme: Theme) -> None:
        self.theme = theme
        self.update()

    # --------------------------------------------------------------- paint
    def paintEvent(self, event) -> None:  # noqa: N802
        p = self.theme.palette
        col = lambda key: QColor(*p[key])  # noqa: E731
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)

        # Marco delgado del color de acento y pantalla interior oscura.
        painter.fillRect(1, 1, SIZE - 2, SIZE - 2, col("bg"))
        pen = QPen(col("accent"), 2)
        painter.setPen(pen)
        painter.drawRect(2, 2, SIZE - 4, SIZE - 4)
        painter.fillRect(6, 6, SIZE - 12, SIZE - 12, col("panel"))
        painter.fillRect(6, 6, SIZE - 12, 7, col("shade"))
        for x in (10, 15, 20):
            painter.fillRect(x, 8, 3, 3, col("accent"))

        # Ojos de Bitty y un prompt de terminal: se reconoce al instante.
        painter.fillRect(14, 19, 5, 5, col("ink"))
        painter.fillRect(29, 19, 5, 5, col("ink"))
        painter.setPen(col("bright"))
        painter.setFont(QFont("Consolas", 13, QFont.Weight.Bold))
        painter.drawText(9, 42, ">")

        painter.end()

    # --------------------------------------------------------------- mouse
    def enterEvent(self, event) -> None:  # noqa: N802
        self.setWindowOpacity(1.0)
        super().enterEvent(event)

    def leaveEvent(self, event) -> None:  # noqa: N802
        if not self.dragging:
            self.setWindowOpacity(0.72)
        super().leaveEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        self.button = event.button()
        self.dragging = True
        self.moved = False
        self.drag_origin = event.globalPosition().toPoint()
        self.drag_offset = self.pos() - self.drag_origin
        event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if not self.dragging:
            return
        pos = event.globalPosition().toPoint() + self.drag_offset
        if (pos - self.drag_origin).manhattanLength() > 4:
            self.moved = True
            self.move(pos)
        event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if not self.dragging:
            return
        self.dragging = False
        if not self.moved:
            QToolTip.showText(
                self.mapToGlobal(QPoint(SIZE // 2, SIZE // 2)),
                "VOLVIENDO CON BITTY", self, msecShowTime=900,
            )
            if self.button == Qt.MouseButton.RightButton:
                self.restore_quiet_requested.emit()
            else:
                self.restore_requested.emit()
        self.button = Qt.MouseButton.NoButton
        event.accept()
