"""Diálogo corto de Bitty: hay que leer antes de poder aceptar."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout,
)

from .agreement import AGREEMENT_LINES, AGREEMENT_TITLE


class AgreementDialog(QDialog):
    """Muestra el acuerdo y retrasa el botón ACEPTO unos segundos."""

    def __init__(self, parent=None, wait_seconds: int = 6) -> None:
        super().__init__(parent)
        self.setWindowTitle("Bitty — acuerdo rápido")
        self.setWindowFlag(Qt.WindowType.WindowStaysOnTopHint, True)
        self.setModal(True)
        self.setMinimumWidth(460)

        layout = QVBoxLayout(self)
        title = QLabel(AGREEMENT_TITLE)
        title.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(title)

        for line in AGREEMENT_LINES:
            label = QLabel(line)
            label.setWordWrap(True)
            label.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            layout.addWidget(label)

        hint = QLabel("Lee las cuatro líneas: el botón se activa solo.")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        buttons = QHBoxLayout()
        self.reject_button = QPushButton("RECHAZAR")
        self.accept_button = QPushButton(f"ACEPTO ({wait_seconds} s)")
        self.accept_button.setEnabled(False)
        buttons.addWidget(self.reject_button)
        buttons.addStretch(1)
        buttons.addWidget(self.accept_button)
        layout.addLayout(buttons)

        self.reject_button.clicked.connect(self.reject)
        self.accept_button.clicked.connect(self.accept)

        self._remaining = max(0, int(wait_seconds))
        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        if self._remaining:
            self._timer.start()
        else:
            self._unlock()

    def _tick(self) -> None:
        self._remaining -= 1
        if self._remaining <= 0:
            self._timer.stop()
            self._unlock()
        else:
            self.accept_button.setText(f"ACEPTO ({self._remaining} s)")

    def _unlock(self) -> None:
        self.accept_button.setEnabled(True)
        self.accept_button.setText("ACEPTO")


__all__ = ["AgreementDialog"]
