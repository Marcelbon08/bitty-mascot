"""Ventana flotante de Bitty (PySide6), multiplataforma."""

from __future__ import annotations

import datetime as _dt
import json
import random
import shutil
import subprocess
import sys
import threading
from pathlib import Path
from typing import Callable

from PIL import Image
from PySide6.QtCore import Qt, QEvent, QPoint, QRect, QSize, QTimer, Signal
from PySide6.QtGui import (
    QAction, QColor, QCursor, QFont, QGuiApplication, QImage, QPainter,
    QPen, QPixmap,
)
from PySide6.QtWidgets import (
    QApplication, QComboBox, QLineEdit, QMenu, QPlainTextEdit,
    QPushButton, QToolTip, QWidget,
)

from . import opencode, state
from .bridge import Bridge
from .cursor_view import BittyCursorView
from .desktop_action import invoke_taskbar_button
from .gaming import GamingShortcut
from .icon_finder import find_icon
from .screen import capture_to_png
from .themes import THEMES, resolve_theme, theme_for_date, tint_sprite
from .virtual_cursor import parse_cursor_command

if getattr(sys, "frozen", False):
    # PyInstaller extrae los datos a _MEIPASS (en onedir, la carpeta del bundle).
    RESOURCES = Path(getattr(sys, "_MEIPASS")) / "bitty" / "resources"
else:
    RESOURCES = Path(__file__).resolve().parent / "resources"
SPRITES = RESOURCES / "sprites"

# Lista cerrada: el clic virtual solo puede abrir estas apps, nunca un comando
# que venga de fuera. Se busca en las rutas típicas y en el PATH.
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

EXPRESSIONS = {
    "idleA": "bitty-neutral.png", "idleB": "bitty-blink.png",
    "celebrate": "bitty-celebrate.png", "surprise": "bitty-surprise.png",
    "thinking": "bitty-thinking.png", "doubt": "bitty-doubt.png",
    "error": "bitty-error.png", "happy": "bitty-happy.png",
    "laugh": "bitty-laugh.png", "sad": "bitty-sad.png",
    "angry": "bitty-angry.png", "love": "bitty-love.png",
    "wink": "bitty-wink.png", "cool": "bitty-cool.png",
    "sleepy": "bitty-sleepy.png", "scared": "bitty-scared.png",
    "curious": "bitty-curious.png", "smug": "bitty-smug.png",
    "bored": "bitty-bored.png", "walk1": "bitty-walk1.png",
    "walk2": "bitty-walk2.png", "normal": "bitty-neutral.png",
}
IDLE_FACES = ["happy", "curious", "wink", "cool", "sleepy", "love", "smug", "bored"]
WAIT_FACES = ["thinking", "curious", "thinking", "doubt", "thinking", "sleepy"]

IDLE_SIZE = QSize(84, 84)
INPUT_SIZE = QSize(340, 300)
REPLY_SIZE = QSize(340, 322)


def _rgb(color: tuple[int, int, int]) -> QColor:
    return QColor(*color)


def limit_text(text: str, maximum: int) -> str:
    text = " ".join(str(text).split())
    return text if len(text) <= maximum else text[: maximum - 2] + ".."


class BittyWindow(QWidget):
    hotkey_pressed = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.data = state.load()
        self.theme_key = self.data["theme"]
        self.theme = resolve_theme(self.theme_key)
        self.exe = opencode.find_exe()
        opencode.ensure_agent()

        self.mode = "idle"
        self.reaction = "normal"
        self.bubble_text = ""
        self.last_reply = ""
        self.last_prompt = ""
        self.last_session_id = ""
        self.reaction_until = _dt.datetime.min
        self.wait_proc: subprocess.Popen | None = None
        self.wait_out = Path()
        self.wait_err = Path()
        self.history: list[str] = []
        self.history_index = -1
        self.session_choices: list[dict] = []
        self.updating_combo = False

        self.random = random.Random()
        self.anchor = QPoint(
            int(self.data["x"]) if self.data["x"] is not None else 0,
            int(self.data["y"]) if self.data["y"] is not None else 0,
        )
        self.roam_center = QPoint(self.anchor)
        self.roam_target = QPoint(self.anchor)
        self.roam_paused = bool(self.data["roam_paused"])
        self.dragging = False
        self.drag_origin = QPoint()
        self.drag_offset = QPoint()
        self.moved = False
        self.frame = 0
        self.idle_face_index = 0
        self.wait_face_index = 0
        self.sprite_override: str | None = None
        self.override_until = _dt.datetime.min
        self.pixmap_cache: dict[tuple[str, str], QPixmap] = {}

        self._build_ui()
        self._build_menu()
        self._build_timers()

        self.hotkey_pressed.connect(self.open_bubble)
        self._start_hotkey()

        if self.data["x"] is None or self.data["y"] is None:
            center = QGuiApplication.primaryScreen().availableGeometry().center()
            self.anchor = QPoint(center.x(), center.y())
            self.roam_center = QPoint(self.anchor)
            self.roam_target = QPoint(self.anchor)

        # Sin padre: si fuera ventana hija de Bitty, Windows la mantendría
        # siempre por encima de su dueño y no podría esconderse detrás.
        self.cursor_view = BittyCursorView(self.theme)
        self.cursor_view.set_home(self.anchor)
        self.cursor_view.go_to(self.anchor.x() + 90, self.anchor.y() + 70)
        # El cursor solo aparece cuando Bitty tiene que actuar.
        self.cursor_view.park()

        # Modo gaming: Bitty se oculta por completo y deja un atajo mínimo.
        self.gaming = False
        self.gaming_shortcut = GamingShortcut(self.theme)
        self.gaming_shortcut.restore_requested.connect(self._gaming_restore)
        self.gaming_shortcut.restore_quiet_requested.connect(self._exit_gaming)

        # El puente HTTP vive en un hilo: las órdenes se encolan y se aplican
        # desde el timer de Qt, que sí está en el hilo de la interfaz.
        self.bridge_queue: list[tuple[str, tuple]] = []
        self.bridge = Bridge(self._queue_cursor, self._queue_capture, self._queue_click)
        self.bridge_action.setChecked(bool(self.data.get("bridge_enabled", True)))
        if self.bridge_action.isChecked():
            try:
                self.bridge.start()
            except OSError:
                self.bridge_action.setChecked(False)
                self.data["bridge_enabled"] = False
        self._sync_bridge_action()

        self.set_mode("idle", "happy", "")
        self.override_until = _dt.datetime.now() + _dt.timedelta(seconds=4)

    # ------------------------------------------------------------------ UI
    def _build_ui(self) -> None:
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAutoFillBackground(False)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setMouseTracking(True)
        self.setObjectName("bitty")
        self.setWindowTitle("Bitty")

        self.session_combo = QComboBox(self)
        self.session_combo.setGeometry(QRect(22, 27, 152, 24))
        self.session_combo.currentIndexChanged.connect(self._session_selected)
        self.session_combo.setVisible(False)

        self.new_btn = QPushButton("NUEVA", self)
        self.new_btn.setGeometry(QRect(180, 27, 60, 24))
        self.new_btn.clicked.connect(self._new_session)
        self.new_btn.setVisible(False)

        self.input_box = QLineEdit(self)
        self.input_box.setGeometry(QRect(22, 56, 180, 28))
        self.input_box.returnPressed.connect(self._on_send)
        self.input_box.installEventFilter(self)
        self.input_box.setVisible(False)

        self.reply_view = QPlainTextEdit(self)
        self.reply_view.setGeometry(QRect(16, 90, 304, 112))
        self.reply_view.setReadOnly(True)
        self.reply_view.setLineWrapMode(QPlainTextEdit.LineWrapMode.WidgetWidth)
        self.reply_view.setVisible(False)

        self.send_btn = QPushButton("ENVIAR", self)
        self.send_btn.setGeometry(QRect(210, 56, 62, 28))
        self.send_btn.clicked.connect(self._on_send)

        self.follow_btn = QPushButton("SEGUIR", self)
        self.follow_btn.setGeometry(QRect(22, 222, 62, 28))
        self.follow_btn.clicked.connect(self._follow)

        self.open_app_btn = QPushButton("ABRIR APP", self)
        self.open_app_btn.setGeometry(QRect(88, 222, 88, 28))
        self.open_app_btn.clicked.connect(self._open_app)

        self.copy_btn = QPushButton("COPIAR", self)
        self.copy_btn.setGeometry(QRect(210, 222, 62, 28))
        self.copy_btn.clicked.connect(self._copy_reply)

        self.cancel_btn = QPushButton("CANCELAR", self)
        self.cancel_btn.setGeometry(QRect(210, 222, 62, 28))
        self.cancel_btn.clicked.connect(self._cancel)

        self.exit_btn = QPushButton("SALIR", self)
        self.exit_btn.setGeometry(QRect(278, 222, 44, 28))
        self.exit_btn.clicked.connect(self.close_bubble)

        for b in (
            self.new_btn, self.send_btn, self.follow_btn, self.open_app_btn,
            self.copy_btn, self.exit_btn,
        ):
            b.setObjectName("primary" if b in (self.new_btn, self.send_btn, self.follow_btn) else "secondary")
        self.cancel_btn.setObjectName("accent")
        self.apply_stylesheet()

    def apply_stylesheet(self) -> None:
        p = self.theme.palette
        c = lambda key: "#%02x%02x%02x" % p[key]  # noqa: E731
        self.setStyleSheet(f"""
            #bitty {{ background: transparent; }}
            QPushButton {{
                border: 0px solid {c('border')}; border-radius: 0px;
                padding: 2px; font: 8pt Consolas, 'Courier New', monospace;
            }}
            QPushButton#primary {{ background: {c('bright')}; color: {c('bg')}; }}
            QPushButton#secondary {{ background: {c('subtle')}; color: {c('muted')};
                                     border: 1px solid {c('border')}; }}
            QPushButton#accent {{ background: {c('subtle')}; color: {c('accent')};
                                  border: 1px solid {c('accent')}; }}
            QPushButton:hover {{ background: {c('divider')}; color: {c('bright')}; }}
            QLineEdit, QComboBox, QPlainTextEdit {{
                background: {c('panel')}; color: {c('ink')};
                border: 1px solid {c('border')}; border-radius: 0px;
                font: 9pt Consolas, 'Courier New', monospace;
                selection-background-color: {c('accent')};
            }}
            QLineEdit:focus, QComboBox:focus {{ border: 1px solid {c('accent')}; }}
            QPlainTextEdit {{ border: 0px; padding: 4px; }}
            QComboBox::drop-down {{ border: 0px; width: 14px; }}
            QScrollBar:vertical {{ background: {c('panel')}; width: 8px; margin: 0; }}
            QScrollBar::handle:vertical {{ background: {c('border')}; min-height: 16px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
            QMenu {{ background: {c('panel')}; color: {c('ink')};
                     border: 1px solid {c('border')};
                     font: 9pt Consolas, 'Courier New', monospace; }}
            QMenu::item:selected {{ background: {c('divider')}; color: {c('bright')}; }}
            QToolTip {{ background: {c('panel')}; color: {c('ink')};
                        border: 1px solid {c('border')}; }}
        """)

    def _build_menu(self) -> None:
        self.menu = QMenu(self)
        self.menu.addAction("> HABLAR", self.open_bubble)
        self.pause_action = QAction(self._pause_label(), self)
        self.pause_action.triggered.connect(self._toggle_pause)
        self.menu.addAction(self.pause_action)
        self.menu.addSeparator()
        self.menu.addAction("> COPIAR RESPUESTA", self._copy_reply)
        self.menu.addAction("> REPETIR ULTIMO MENSAJE", self._repeat)
        self.menu.addAction("> VOLVER AL CENTRO", self._center)
        self.menu.addSeparator()
        self.cursor_visible_action = QAction("> CURSOR: MOSTRAR", self)
        self.cursor_visible_action.setCheckable(True)
        self.cursor_visible_action.setChecked(False)
        self.cursor_visible_action.triggered.connect(self._toggle_cursor_visible)
        self.menu.addAction(self.cursor_visible_action)
        self.cursor_demo_action = QAction("> CURSOR: RUTA ALEATORIA", self)
        self.cursor_demo_action.setCheckable(True)
        self.cursor_demo_action.triggered.connect(self._toggle_cursor_demo)
        self.menu.addAction(self.cursor_demo_action)
        self.menu.addAction("> CURSOR: IR AL CENTRO", self._cursor_center)
        self.menu.addSeparator()
        self.bridge_action = QAction("> PUENTE OPENCODE: DESACTIVAR", self)
        self.bridge_action.setCheckable(True)
        self.bridge_action.triggered.connect(self._toggle_bridge)
        self.menu.addAction(self.bridge_action)
        self.menu.addSeparator()
        self.gaming_action = QAction("> GAMING: ACTIVAR", self)
        self.gaming_action.setCheckable(True)
        self.gaming_action.triggered.connect(self._toggle_gaming)
        self.menu.addAction(self.gaming_action)
        self.menu.addSeparator()
        theme_menu = self.menu.addMenu("> TEMA")
        self.theme_actions = {}
        for key, item in [("auto", "AUTOMATICO"), *[(k, t.label) for k, t in THEMES.items()]]:
            act = QAction(item, self)
            act.setCheckable(True)
            act.triggered.connect(lambda checked=False, k=key: self._set_theme(k))
            theme_menu.addAction(act)
            self.theme_actions[key] = act
        self._sync_theme_actions()
        self.menu.addSeparator()
        self.menu.addAction("> SALIR DE BITTY", self._quit)

    def _build_timers(self) -> None:
        self.roam_timer = QTimer(self)
        self.roam_timer.setInterval(40)
        self.roam_timer.timeout.connect(self._roam)
        self.roam_timer.start()

        self.wait_timer = QTimer(self)
        self.wait_timer.setInterval(300)
        self.wait_timer.timeout.connect(self._poll_wait)

        self.face_timer = QTimer(self)
        self.face_timer.setInterval(2000)
        self.face_timer.timeout.connect(self._rotate_faces)

        self.auto_theme_timer = QTimer(self)
        self.auto_theme_timer.setInterval(60 * 60 * 1000)
        self.auto_theme_timer.timeout.connect(self._check_auto_theme)
        self.auto_theme_timer.start()

    def _start_hotkey(self) -> None:
        try:
            from pynput import keyboard

            combos = {"<ctrl>+<alt>+b": self._hotkey}
            if sys.platform == "darwin":
                combos["<cmd>+<alt>+b"] = self._hotkey
            self.hotkey_listener = keyboard.GlobalHotKeys(combos)
            self.hotkey_listener.start()
        except Exception:
            self.hotkey_listener = None

    def _hotkey(self) -> None:
        if self.gaming:
            # El atajo de teclado también sirve para salir del modo gaming:
            # no hace falta ir a la esquina con el ratón durante una partida.
            self._exit_gaming()
        self.hotkey_pressed.emit()

    # ------------------------------------------------------------ sprites
    def pixmap(self, name: str) -> QPixmap:
        key = (name, self.theme.key)
        if key in self.pixmap_cache:
            return self.pixmap_cache[key]
        path = SPRITES / EXPRESSIONS.get(name, EXPRESSIONS["normal"])
        if not path.exists():
            return QPixmap()
        source = Image.open(path).convert("RGBA")
        themed = tint_sprite(source, self.theme)
        data = themed.tobytes("raw", "RGBA")
        image = QImage(data, themed.width, themed.height, QImage.Format.Format_RGBA8888)
        pixmap = QPixmap.fromImage(image)
        self.pixmap_cache[key] = pixmap
        return pixmap

    def current_face(self) -> str:
        now = _dt.datetime.now()
        if now < self.override_until and self.sprite_override:
            return self.sprite_override
        if self.mode == "reaction" and self.wait_proc is not None:
            return WAIT_FACES[self.wait_face_index % len(WAIT_FACES)]
        if self.mode == "idle":
            return IDLE_FACES[self.idle_face_index % len(IDLE_FACES)]
        return self.reaction if self.reaction in EXPRESSIONS else "normal"

    def _rotate_faces(self) -> None:
        self.wait_face_index += 1
        if self.mode == "idle" and self.wait_proc is None:
            self.idle_face_index += 1
            self.override_until = _dt.datetime.now() + _dt.timedelta(seconds=2)
            self.sprite_override = None
        if self.mode == "idle" and self.frame % 20 == 0:
            self.sprite_override = "idleB"
            self.override_until = _dt.datetime.now() + _dt.timedelta(milliseconds=240)
        self.update()

    def _check_auto_theme(self) -> None:
        if self.theme_key == "auto":
            wanted = theme_for_date()
            if wanted != self.theme.key:
                self._set_theme("auto", notify=False)

    # -------------------------------------------------------------- paint
    def paintEvent(self, event) -> None:  # noqa: N802
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        pal = self.theme.palette
        col = lambda key: _rgb(pal[key])  # noqa: E731

        if self.mode == "idle":
            sprite = self.pixmap(self.current_face())
            p.drawPixmap((84 - sprite.width()) // 2, (84 - sprite.height()) // 2, sprite)
            font = QFont("Consolas", 6)
            p.setFont(font)
            p.setPen(col("muted"))
            text_w = p.fontMetrics().horizontalAdvance("BITTY")
            p.drawText((84 - text_w) // 2, 81, "BITTY")
        else:
            rect = QRect(12, 6, 316, 200)
            p.fillRect(rect, col("panel"))
            p.setPen(QPen(col("border"), 1))
            p.drawRect(rect)
            p.fillRect(QRect(12, 6, 316, 20), col("subtle"))
            p.drawLine(15, 26, 325, 26)
            p.setPen(col("bright"))
            p.setFont(QFont("Consolas", 9, QFont.Weight.Bold))
            p.drawText(18, 20, f"> {self.theme.label} / OPENCODE")
            p.setPen(col("accent"))
            p.drawRect(QRect(12, 200, 10, 8))

            sprite = self.pixmap(self.current_face())
            y = 284 if self.mode == "reaction" else 262
            p.drawPixmap(40 - sprite.width() // 2, y - sprite.height() // 2, sprite)
        p.end()

    # --------------------------------------------------------------- mode
    def set_mode(self, mode: str, reaction: str = "normal", text: str = "") -> None:
        self.stop_waiting()
        self.mode = mode
        self.reaction = reaction
        self.bubble_text = text
        if mode == "idle":
            self.resize(IDLE_SIZE)
        elif mode == "reaction":
            self.resize(REPLY_SIZE)
            self.reply_view.setPlainText(text)
            self.reply_view.setVisible(True)
        else:
            self.resize(INPUT_SIZE)
            self.reply_view.setVisible(False)
            self.input_box.clear()
            self._update_sessions()
            self.input_box.setFocus()

        is_input = mode == "input"
        self.input_box.setVisible(is_input)
        self.session_combo.setVisible(is_input)
        self.new_btn.setVisible(is_input)
        self.send_btn.setVisible(is_input)
        self.exit_btn.setVisible(mode != "idle")
        self.exit_btn.setGeometry(
            QRect(278, 56, 44, 28) if is_input else QRect(278, 222, 44, 28)
        )
        self._update_buttons()
        self._update_location()
        self.update()

    def _update_buttons(self) -> None:
        is_input = self.mode == "input"
        has_reply = self.mode == "reaction" and self.wait_proc is None
        waiting = self.mode == "reaction" and self.wait_proc is not None
        self.follow_btn.setVisible(has_reply and bool(self.last_session_id))
        self.open_app_btn.setVisible(has_reply and bool(self.last_session_id))
        self.copy_btn.setVisible(has_reply)
        self.cancel_btn.setVisible(waiting)

    def close_bubble(self) -> None:
        self.set_mode("idle", "normal", "")
        self.sprite_override = "normal"
        self.override_until = _dt.datetime.now() + _dt.timedelta(seconds=2)

    def open_bubble(self) -> None:
        if self.mode == "idle":
            self.set_mode("input", "normal", "")
        elif self.mode == "reaction":
            self.set_mode("input", "normal", "")
        else:
            self.close_bubble()
        self.raise_()
        self.activateWindow()

    # ------------------------------------------------------------ sessions
    def _new_session(self) -> None:
        self.data["session_mode"] = "new"
        self.data["session_id"] = ""
        self._sync_session_ui()
        state.save(self.data)

    def _update_sessions(self) -> None:
        sessions = opencode.list_sessions(self.exe) if self.exe else []
        self.session_choices = [{"id": "", "label": "(ultima sesion)"}]
        for s in sessions:
            title = s.get("title") or s.get("id", "")
            label = limit_text(title, 18)
            sid = str(s.get("id", ""))
            if len(label) >= 18:
                label = label[:16] + ".."
            self.session_choices.append({"id": sid, "label": f"{label} #{sid[-4:]}"})
        self.updating_combo = True
        self.session_combo.clear()
        self.session_combo.addItems([c["label"] for c in self.session_choices])
        idx = 0
        for i, c in enumerate(self.session_choices):
            if c["id"] and c["id"] == self.data.get("session_id"):
                idx = i
                break
        self.session_combo.setCurrentIndex(idx)
        self.updating_combo = False
        self._sync_session_ui()

    def _session_selected(self, index: int) -> None:
        if self.updating_combo or index < 0 or index >= len(self.session_choices):
            return
        choice = self.session_choices[index]
        if choice["id"]:
            self.data["session_mode"] = "continue"
            self.data["session_id"] = choice["id"]
        else:
            self.data["session_mode"] = "new"
            self.data["session_id"] = ""
        self._sync_session_ui()
        state.save(self.data)

    def _sync_session_ui(self) -> None:
        is_new = self.data["session_mode"] == "new"
        self.new_btn.setObjectName("primary" if is_new else "secondary")
        self.new_btn.setStyleSheet("")
        self.apply_stylesheet()

    # -------------------------------------------------------------- send
    def eventFilter(self, obj, event) -> bool:  # noqa: N802
        if obj is self.input_box and event.type() == QEvent.Type.KeyPress:
            key = event.key()
            if key == Qt.Key.Key_Escape:
                self.close_bubble()
                return True
            if key == Qt.Key.Key_Up:
                if self.history and self.history_index < len(self.history) - 1:
                    self.history_index += 1
                    self.input_box.setText(self.history[-1 - self.history_index])
                return True
            if key == Qt.Key.Key_Down:
                if self.history_index > 0:
                    self.history_index -= 1
                    self.input_box.setText(self.history[-1 - self.history_index])
                elif self.history_index == 0:
                    self.history_index = -1
                    self.input_box.clear()
                return True
        return super().eventFilter(obj, event)

    def _on_send(self) -> None:
        text = self.input_box.text().strip()
        if not text:
            return

        kind, coords = parse_cursor_command(text)
        if kind == "move" and coords:
            self.cursor_view.go_to(*coords)
            self._cursor_notice(f"CURSOR -> {coords[0]},{coords[1]}")
            self.input_box.clear()
            return
        if kind == "click" and coords:
            self._bitty_click(*coords)
            self.input_box.clear()
            return
        if kind == "demo":
            self._toggle_cursor_demo()
            self._cursor_notice("CURSOR: RUTA " + ("ON" if self.cursor_view.demo else "OFF"))
            self.input_box.clear()
            return
        if kind == "stop":
            self.cursor_view.stop_demo()
            self.cursor_demo_action.setChecked(False)
            self._cursor_notice("CURSOR: DETENIDO")
            self.input_box.clear()
            return

        if not self.exe:
            self.set_mode("reaction", "error", "No encuentro el ejecutable de OpenCode.")
            self.reaction_until = _dt.datetime.now() + _dt.timedelta(seconds=9)
            return
        self.last_prompt = text
        self.last_reply = ""
        self.last_session_id = ""
        self.history.append(text)
        self.history_index = -1
        self.set_mode("reaction", "thinking", "Pensando...")
        self.reaction_until = _dt.datetime.now() + _dt.timedelta(minutes=5)
        try:
            self.wait_proc, self.wait_out, self.wait_err = opencode.send_message(
                self.exe, text, self.data.get("session_id", "")
            )
        except OSError as exc:
            self.wait_proc = None
            self.set_mode("reaction", "error", f"No pude lanzar OpenCode: {exc}")
            self.reaction_until = _dt.datetime.now() + _dt.timedelta(seconds=9)
            return
        self.wait_timer.start()
        self._update_buttons()

    def _poll_wait(self) -> None:
        if not self.wait_proc or self.wait_proc.poll() is None:
            return
        self.wait_timer.stop()
        reply, sid = opencode.parse_reply(self.wait_out, self.wait_err)
        self.last_reply = reply
        self.last_session_id = sid
        self.wait_proc = None
        reaction = self._reaction_for(reply)
        self.set_mode("reaction", reaction, reply)
        self.reaction_until = _dt.datetime.now() + _dt.timedelta(seconds=60)
        self.reply_view.setPlainText(reply)
        self._update_buttons()

    def stop_waiting(self) -> None:
        self.wait_timer.stop()
        proc = self.wait_proc
        self.wait_proc = None
        if proc and proc.poll() is None:
            try:
                proc.terminate()
            except OSError:
                pass

    def _cancel(self) -> None:
        self.stop_waiting()
        self.set_mode(
            "reaction", "doubt",
            f"> {limit_text(self.last_prompt, 100)}\n< Cancelado.",
        )
        self.reaction_until = _dt.datetime.now() + _dt.timedelta(seconds=9)

    def _reaction_for(self, reply: str) -> str:
        t = f"{reply} {self.last_prompt}".lower()
        if "sin errores" in t or "no hay errores" in t:
            return "celebrate"
        if "error" in t or "fallo" in t:
            return "error"
        if "gracias" in t:
            return "love"
        if "?" in reply or "qué" in t or "cual" in t:
            return "curious"
        if "jaja" in t or "jeje" in t:
            return "laugh"
        return "happy"

    # ------------------------------------------------------------ actions
    def _follow(self) -> None:
        if not self.last_session_id:
            QToolTip.showText(QCursor.pos(), "No hay sesion aun", self, msecShowTime=1600)
            return
        self.data["session_mode"] = "continue"
        self.data["session_id"] = self.last_session_id
        self.data["session_label"] = "esta conversacion"
        self.set_mode("input", "normal", "")
        state.save(self.data)

    def _open_app(self) -> None:
        if not self.last_session_id:
            QToolTip.showText(QCursor.pos(), "No hay sesion aun", self, msecShowTime=1600)
            return
        if self.exe and opencode.open_app(self.exe, self.last_session_id):
            QToolTip.showText(QCursor.pos(), "Abriendo OpenCode...", self, msecShowTime=1600)
        else:
            QToolTip.showText(QCursor.pos(), "No se pudo abrir OpenCode", self, msecShowTime=1800)

    def _copy_reply(self) -> None:
        if self.last_reply:
            QApplication.clipboard().setText(self.last_reply)
            QToolTip.showText(QCursor.pos(), "Copiado al portapapeles", self, msecShowTime=1600)

    def _repeat(self) -> None:
        if self.last_prompt:
            self.input_box.setText(self.last_prompt)
            self.set_mode("input", "normal", "")
            self.input_box.setText(self.last_prompt)

    def _center(self) -> None:
        screen = QGuiApplication.screenAt(self.pos()) or QGuiApplication.primaryScreen()
        geo = screen.availableGeometry()
        self.anchor = QPoint(geo.center().x(), geo.center().y())
        self.roam_center = QPoint(self.anchor)
        self.roam_target = QPoint(self.anchor)
        self._update_location()
        self._save()

    # -------------------------------------------------------- cursor virtual
    def _cursor_notice(self, message: str) -> None:
        QToolTip.showText(self.mapToGlobal(QPoint(42, 42)), message, self, msecShowTime=1400)

    def _toggle_cursor_visible(self, checked: bool) -> None:
        self.cursor_view.set_visible_cursor(checked)
        self.cursor_visible_action.setText("> CURSOR: MOSTRAR" if not checked else "> CURSOR: OCULTAR")

    def _toggle_cursor_demo(self, checked: bool | None = None) -> None:
        active = self.cursor_view.toggle_demo()
        self.cursor_demo_action.setChecked(active)

    def _cursor_center(self) -> None:
        self.cursor_view.center()

    # ------------------------------------------------------- puente local
    def _queue_cursor(self, x: int, y: int) -> None:
        self.bridge_queue.append(("cursor", (x, y)))

    def _queue_capture(self, work: Callable[[], None]) -> None:
        self.bridge_queue.append(("capture", (work,)))

    def _queue_click(self, x: int, y: int, open_app: str) -> None:
        self.bridge_queue.append(("click", (x, y, open_app)))

    @staticmethod
    def _open_app(name: str) -> bool:
        """Abre solo una app de la whitelist, sin ejecutar comandos arbitrarios."""
        candidates = OPEN_APPS.get(name)
        if not candidates:
            return False
        for candidate in (*candidates, name):
            path = candidate if Path(candidate).is_file() else shutil.which(candidate)
            if path:
                subprocess.Popen([path], shell=False)
                return True
        return False

    def _bitty_click(self, x: int, y: int, open_app: str = "") -> None:
        """Bitty ve el logo, saca su cursor, hace clic y activa la app.

        El cursor propio de Bitty es el que hace el gesto visible. Tu ratón
        real nunca se mueve ni pulsa nada: la activación del botón de la barra
        de tareas se hace en el mismo instante por UI Automation, y solo para
        apps de la whitelist.
        """
        target = (x, y)
        seen = "CLIC VISUAL"
        if open_app:
            self._cursor_notice("BITTY ESTA BUSCANDO EL LOGO...")
            shot = self.bridge.capture_dir / (
                "vision-%d.png" % int(_dt.datetime.now().timestamp() * 1000)
            )
            try:
                info = capture_to_png(shot)
                located = find_icon(Path(info["path"]), open_app)
                if located:
                    target = (located[0], located[1])
                    seen = "LOGO VISTO"
            except Exception:
                seen = "SIN VISION"
            finally:
                shot.unlink(missing_ok=True)
            if seen == "SIN VISION":
                seen = "COORDENADA DADA"

            def on_clicked() -> None:
                # La activación va en otro hilo: el clic visual y el ocultado
                # del cursor no deben esperar a PowerShell/UI Automation.
                def work() -> None:
                    if not invoke_taskbar_button(open_app):
                        self._open_app(open_app)

                threading.Thread(target=work, name="bitty-open", daemon=True).start()

            self.cursor_view.click(target[0], target[1], on_clicked)
        else:
            self.cursor_view.click(target[0], target[1])
        self._cursor_notice(
            f"CLIC DE BITTY -> {target[0]},{target[1]} "
            f"({seen}; RATÓN INTACTO)"
        )
        self.sprite_override = "curious"

    def _apply_bridge_queue(self) -> None:
        while self.bridge_queue:
            kind, payload = self.bridge_queue.pop(0)
            # En gaming no se mueve nada en pantalla: ni el cursor ni el clic
            # visual podrían interrumpir una partida. La visión sigue disponible.
            if self.gaming and kind in ("cursor", "click"):
                continue
            if kind == "cursor":
                x, y = payload
                self.cursor_view.go_to(x, y)
                self._cursor_notice(f"CURSOR -> {x},{y} (OPENCODE)")
                self.sprite_override = "curious"
            elif kind == "click":
                self._bitty_click(*payload)
            elif kind == "capture":
                self.sprite_override = "surprise"
                self._cursor_notice("BITTY ESTA MIRANDO LA PANTALLA")
                # La captura se ejecuta aquí, en el hilo de Qt, y despierta al
                # hilo HTTP cuando ya tiene el PNG en disco.
                work = payload[0]
                work()
            self.override_until = _dt.datetime.now() + _dt.timedelta(seconds=2)

    def _sync_bridge_action(self) -> None:
        active = self.bridge_action.isChecked()
        self.bridge_action.setText(
            "> PUENTE OPENCODE: DESACTIVAR" if active else "> PUENTE OPENCODE: ACTIVAR"
        )

    def _toggle_bridge(self, checked: bool) -> None:
        if checked:
            try:
                self.bridge.start()
            except OSError:
                checked = False
        else:
            self.bridge.stop()
        self.bridge_action.setChecked(checked)
        self._sync_bridge_action()
        self.data["bridge_enabled"] = checked
        self._save()

    # ---------------------------------------------------------------- gaming
    def _sync_gaming_action(self) -> None:
        self.gaming_action.setText(
            "> GAMING: DESACTIVAR" if self.gaming else "> GAMING: ACTIVAR"
        )
        self.gaming_action.setChecked(self.gaming)

    def _toggle_gaming(self, checked: bool = False) -> None:
        if self.gaming:
            self._exit_gaming()
        else:
            self._enter_gaming()

    def _enter_gaming(self) -> None:
        """Oculta a Bitty y deja solo el atajo: nada estorba en la partida."""
        if self.gaming:
            return
        self.close_bubble()
        self.gaming = True
        self.cursor_view.stop()
        self.hide()
        self.gaming_shortcut.set_theme(self.theme)
        self.gaming_shortcut.show()
        self.gaming_shortcut.raise_()
        self._sync_gaming_action()

    def _exit_gaming(self) -> None:
        self.gaming_shortcut.hide()
        self.gaming = False
        self.show()
        self.raise_()
        self.cursor_view.park()
        self._sync_gaming_action()

    def _gaming_restore(self) -> None:
        """Clic izquierdo en el atajo: volver y abrir el bocadillo."""
        self._exit_gaming()
        self.open_bubble()

    def _toggle_pause(self) -> None:
        self.roam_paused = not self.roam_paused
        self.pause_action.setText(self._pause_label())
        self._save()

    def _pause_label(self) -> str:
        return "> REANUDAR PASEO" if self.roam_paused else "> PAUSAR PASEO"

    def _quit(self) -> None:
        self.stop_waiting()
        self.cursor_view.stop()
        self.gaming_shortcut.hide()
        self.bridge.stop()
        self._save()
        if self.hotkey_listener:
            try:
                self.hotkey_listener.stop()
            except Exception:
                pass
        QApplication.quit()

    # --------------------------------------------------------------- theme
    def _set_theme(self, key: str, notify: bool = True) -> None:
        self.theme_key = key
        self.theme = resolve_theme(key)
        self.data["theme"] = key
        self.pixmap_cache.clear()
        self.cursor_view.set_theme(self.theme)
        self.gaming_shortcut.set_theme(self.theme)
        self.apply_stylesheet()
        self._sync_theme_actions()
        self._save()
        if notify:
            QToolTip.showText(QCursor.pos(), f"Tema: {self.theme.label}", self, msecShowTime=1600)
        self.update()

    def _sync_theme_actions(self) -> None:
        for key, action in getattr(self, "theme_actions", {}).items():
            action.setChecked(key == self.theme_key)

    # ------------------------------------------------------------ movement
    def _update_location(self) -> None:
        off_x, off_y = (42, 42) if self.mode == "idle" else (40, self._sprite_y())
        screens = QGuiApplication.screens()
        if screens:
            rect = screens[0].geometry()
            for s in screens[1:]:
                rect = rect.united(s.geometry())
        else:
            rect = QGuiApplication.primaryScreen().geometry()
        x = self.anchor.x() - off_x
        y = self.anchor.y() - off_y
        x = max(rect.left(), min(x, rect.right() - self.width()))
        y = max(rect.top(), min(y, rect.bottom() - self.height()))
        self.anchor = QPoint(x + off_x, y + off_y)
        self.cursor_view.set_home(self.anchor)
        # Si está aparcado, sigue a Bitty aunque la mascota se pasee.
        if not (
            self.cursor_view.nav.moving
            or self.cursor_view.pending_click
            or self.cursor_view.returning
        ):
            self.cursor_view.park()
        self.move(x, y)

    def _sprite_y(self) -> int:
        return 284 if self.mode == "reaction" else 262

    def _roam(self) -> None:
        self.frame += 1
        self._apply_bridge_queue()
        if self.gaming:
            # Bitty está oculto: ni paseo ni guardado periódico de posición.
            return
        if self.mode == "reaction" and _dt.datetime.now() > self.reaction_until:
            self.close_bubble()
        if self.mode != "input" and not self.dragging and not self.roam_paused:
            dx = self.roam_target.x() - self.anchor.x()
            dy = self.roam_target.y() - self.anchor.y()
            if abs(dx) <= 2 and abs(dy) <= 2:
                self.roam_target = QPoint(
                    self.roam_center.x() + self.random.randint(-16, 16),
                    self.roam_center.y() + self.random.randint(-12, 12),
                )
            else:
                step_x = max(-1, min(1, int(dx / 3)))
                step_y = max(-1, min(1, int(dy / 3)))
                self.anchor = QPoint(self.anchor.x() + step_x, self.anchor.y() + step_y)
                self._update_location()
        if self.frame % 50 == 0:
            self._save()

    def _save(self) -> None:
        self.data.update({
            "x": self.anchor.x(), "y": self.anchor.y(),
            "roam_paused": self.roam_paused,
            "session_mode": self.data.get("session_mode", "new"),
            "session_id": self.data.get("session_id", ""),
            "theme": self.theme_key,
        })
        state.save(self.data)

    # --------------------------------------------------------------- mouse
    def keyPressEvent(self, event) -> None:  # noqa: N802
        if event.key() == Qt.Key.Key_Escape:
            self.close_bubble()
            return
        super().keyPressEvent(event)

    def mousePressEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.RightButton:
            self.menu.exec(QCursor.pos())
            return
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragging = True
            self.moved = False
            self.drag_origin = event.globalPosition().toPoint()
            self.drag_offset = self.pos() - self.drag_origin
            event.accept()

    def mouseMoveEvent(self, event) -> None:  # noqa: N802
        if self.dragging:
            pos = event.globalPosition().toPoint() + self.drag_offset
            if (pos - self.drag_origin).manhattanLength() > 4:
                self.moved = True
            self.move(pos)
            off_x, off_y = (42, 42) if self.mode == "idle" else (40, self._sprite_y())
            self.anchor = QPoint(pos.x() + off_x, pos.y() + off_y)
            self.roam_center = QPoint(self.anchor)
            self.roam_target = QPoint(self.anchor)
            event.accept()

    def mouseReleaseEvent(self, event) -> None:  # noqa: N802
        if event.button() == Qt.MouseButton.LeftButton and self.dragging:
            self.dragging = False
            if not self.moved:
                self.open_bubble()
            else:
                self._save()
            event.accept()

    def closeEvent(self, event) -> None:  # noqa: N802
        self._quit()
        event.accept()


def run() -> None:
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    window = BittyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    run()
