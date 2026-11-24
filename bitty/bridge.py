"""Puente local de Bitty para OpenCode.

Expone un servidor HTTP **solo en 127.0.0.1** con un token aleatorio. El token y
el puerto se escriben en `BittyMascot/bridge.json` para que el plugin los lea.
Nada escucha en la red y las peticiones sin token se rechazan.
"""

from __future__ import annotations

import hmac
import json
import os
import secrets
import tempfile
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable

from . import state

MAX_BODY = 65536
MAX_COORD = 100000
KEEP_CAPTURES = 6


class AgreementRequired(Exception):
    """El usuario leyó el acuerdo pero no lo aceptó."""

# Únicas apps que el clic virtual de Bitty puede abrir. Nunca se acepta una
# orden arbitraria: si no está aquí, se rechaza.
ALLOWED_OPEN = frozenset({"brave"})


class Bridge:
    """Servidor loopback que manda coordenadas al cursor y capturas a OpenCode."""

    def __init__(
        self,
        on_cursor: Callable[[int, int], None],
        on_capture: Callable[[Callable[[], None]], None] | None = None,
        on_click: Callable[[int, int, str], None] | None = None,
        on_agreement: Callable[[Callable[[bool], None]], None] | None = None,
        on_gate: Callable[[], bool] | None = None,
    ) -> None:
        self.on_cursor = on_cursor
        self.on_capture = on_capture
        self.on_click = on_click
        self.on_agreement = on_agreement
        # Puerta central: la llaman /cursor, /click y /capture antes de tocar
        # nada. Así no basta con llamar al puente directamente saltándose el
        # plugin: sin acuerdo aceptado, la acción se corta aquí.
        self.on_gate = on_gate
        self.token = secrets.token_urlsafe(32)
        self.port = 0
        self.server: ThreadingHTTPServer | None = None
        self.thread: threading.Thread | None = None
        self.captures: list[Path] = []
        self.capture_lock = threading.Lock()
        self.capture_dir = Path(tempfile.gettempdir()) / "BittyMascot" / "captures"

    # ------------------------------------------------------------ lifecycle
    def start(self) -> None:
        if self.server is not None:
            return
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            server_version = "BittyBridge/1"

            def log_message(self, fmt: str, *args) -> None:  # noqa: A002
                return

            def _reply(self, code: int, payload: dict) -> None:
                body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
                self.send_response(code)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self) -> None:  # noqa: N802
                if self.path == "/ping":
                    self._reply(200, {"ok": True, "name": "bitty"})
                else:
                    self._reply(404, {"error": "no encontrado"})

            def do_POST(self) -> None:  # noqa: N802
                if not hmac.compare_digest(
                    self.headers.get("X-Bitty-Token", ""), bridge.token
                ):
                    self._reply(401, {"error": "token invalido"})
                    return
                length = int(self.headers.get("Content-Length", "0") or 0)
                if length <= 0 or length > MAX_BODY:
                    self._reply(413, {"error": "cuerpo invalido"})
                    return
                try:
                    body = json.loads(self.rfile.read(length).decode("utf-8"))
                except (ValueError, UnicodeDecodeError):
                    self._reply(400, {"error": "json invalido"})
                    return
                if not isinstance(body, dict):
                    self._reply(400, {"error": "json invalido"})
                    return

                if self.path == "/agreement":
                    try:
                        accepted = bridge.agreement()
                    except AgreementRequired as exc:
                        self._reply(403, {"error": str(exc), "code": "agreement_required"})
                    except Exception as exc:
                        self._reply(500, {"error": str(exc)[:200]})
                    else:
                        self._reply(200, {"ok": True, "agreement": accepted})
                    return

                # El plugin ya llama a /agreement antes de pedir permiso, pero
                # el puente no puede fiarse de eso: cualquier proceso local con
                # el token debe pasar también esta puerta.
                if bridge.on_gate and bridge.on_gate() is False:
                    self._reply(403, {
                        "error": "acuerdo pendiente: lee y acepta en Bitty",
                        "code": "agreement_required",
                    })
                    return

                if self.path == "/cursor":
                    x, y = body.get("x"), body.get("y")
                    if (
                        isinstance(x, bool) or isinstance(y, bool)
                        or not isinstance(x, int) or not isinstance(y, int)
                        or abs(x) > MAX_COORD or abs(y) > MAX_COORD
                    ):
                        self._reply(400, {"error": "coordenadas invalidas"})
                        return
                    if bridge.on_cursor(x, y) is False:
                        self._reply(403, {
                            "error": "acuerdo pendiente: lee y acepta en Bitty",
                            "code": "agreement_required",
                        })
                        return
                    self._reply(200, {"ok": True, "x": x, "y": y})
                    return

                if self.path == "/click":
                    x, y = body.get("x"), body.get("y")
                    if (
                        isinstance(x, bool) or isinstance(y, bool)
                        or not isinstance(x, int) or not isinstance(y, int)
                        or abs(x) > MAX_COORD or abs(y) > MAX_COORD
                    ):
                        self._reply(400, {"error": "coordenadas invalidas"})
                        return
                    open_app = body.get("open")
                    if open_app is not None and (
                        not isinstance(open_app, str) or open_app not in ALLOWED_OPEN
                    ):
                        self._reply(400, {"error": "aplicacion no permitida"})
                        return
                    if bridge.on_click and bridge.on_click(x, y, open_app or "") is False:
                        self._reply(403, {
                            "error": "acuerdo pendiente: lee y acepta en Bitty",
                            "code": "agreement_required",
                        })
                        return
                    self._reply(200, {"ok": True, "x": x, "y": y, "click": True})
                    return

                if self.path == "/capture":
                    try:
                        self._reply(200, bridge.capture())
                    except AgreementRequired:
                        self._reply(403, {
                            "error": "acuerdo pendiente: lee y acepta en Bitty",
                            "code": "agreement_required",
                        })
                    except Exception as exc:
                        self._reply(500, {"error": str(exc)[:200]})
                    return

                self._reply(404, {"error": "no encontrado"})

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.port = int(self.server.server_address[1])
        self.thread = threading.Thread(
            target=self.server.serve_forever, name="bitty-bridge", daemon=True
        )
        self.thread.start()
        self._write_connection()

    def stop(self) -> None:
        if self.server is not None:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
        self.thread = None
        try:
            self.connection_path().unlink(missing_ok=True)
        except OSError:
            pass
        with self.capture_lock:
            for path in self.captures:
                try:
                    path.unlink(missing_ok=True)
                except OSError:
                    pass
            self.captures.clear()

    @staticmethod
    def connection_path() -> Path:
        return state.config_dir() / "bridge.json"

    def _write_connection(self) -> None:
        path = self.connection_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps({"port": self.port, "token": self.token, "pid": os.getpid()}),
            encoding="utf-8",
        )
        try:
            path.chmod(0o600)
        except OSError:
            pass

    def agreement(self) -> bool:
        """Pide a Bitty que muestre el acuerdo y espera a la respuesta."""
        done = threading.Event()
        box: dict = {}

        def work(accepted: bool) -> None:
            box["accepted"] = bool(accepted)
            done.set()

        if self.on_agreement:
            self.on_agreement(work)
        else:
            work(True)
        if not done.wait(timeout=30):
            raise RuntimeError("Bitty no respondió al acuerdo.")
        if not box["accepted"]:
            raise AgreementRequired("Acuerdo rechazado en Bitty: no he mirado ni actuado.")
        return True

    def capture(self) -> dict:
        """Pide una captura al hilo de Qt y espera a que esté lista.

        QScreen.grabWindow solo es seguro en el hilo de la interfaz. El handler
        HTTP no puede llamarlo directamente: encola el trabajo y espera.
        """
        done = threading.Event()
        box: dict = {}

        def work() -> None:
            try:
                box["result"] = self._capture_sync()
            except BaseException as exc:  # se propaga al hilo HTTP
                box["error"] = exc
            finally:
                done.set()

        if self.on_capture:
            if self.on_capture(work) is False:
                box["error"] = AgreementRequired(
                    "Acuerdo rechazado en Bitty: no he mirado ni actuado."
                )
                done.set()
        else:
            work()
        if not done.wait(timeout=20):
            raise RuntimeError("Bitty no respondió a la captura de pantalla.")
        if "error" in box:
            raise box["error"]
        return box["result"]

    def _capture_sync(self) -> dict:
        from .screen import capture_to_png

        self.capture_dir.mkdir(parents=True, exist_ok=True)
        name = "bitty-%d.png" % int(time.time() * 1000)
        result = capture_to_png(self.capture_dir / name)
        with self.capture_lock:
            self.captures.append(Path(result["path"]))
            while len(self.captures) > KEEP_CAPTURES:
                old = self.captures.pop(0)
                try:
                    old.unlink(missing_ok=True)
                except OSError:
                    pass
        return result
