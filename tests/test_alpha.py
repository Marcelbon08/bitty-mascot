"""Alpha tests de Bitty: ejecución segura de OpenCode y estado persistido."""

from __future__ import annotations

import json
import os
import stat
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import build  # noqa: E402
from bitty import opencode, state  # noqa: E402


class OpenCodeSecurityTests(unittest.TestCase):
    def test_send_message_never_uses_shell_or_continue(self) -> None:
        with mock.patch.object(opencode.subprocess, "Popen") as popen:
            out, err = None, None
            proc, out, err = opencode.send_message("opencode", "hola Bitty", "ses_123")
            self.assertIs(proc, popen.return_value)
            args, kwargs = popen.call_args
            self.assertEqual(args[0][1], "run")
            self.assertNotIn("--continue", args[0])
            self.assertNotIn("-c", args[0])
            self.assertIn("--session", args[0])
            self.assertEqual(args[0][args[0].index("--session") + 1], "ses_123")
            self.assertEqual(args[0][-1], "hola Bitty")
            self.assertFalse(kwargs.get("shell", False))
            self.assertIn("cwd", kwargs)

            # La salida vive en un directorio privado y distinto por llamada.
            self.assertEqual(out.parent, err.parent)
            self.assertTrue(out.parent.name.startswith(opencode._TEMP_PREFIX))
            self.assertTrue(out.parent.is_dir())
            self.assertNotEqual(out, opencode._new_temp_paths()[1])

    def test_prompt_starting_with_dash_is_protected(self) -> None:
        with mock.patch.object(opencode.subprocess, "Popen") as popen:
            opencode.send_message("opencode", "-hola")
            args = popen.call_args.args[0]
            self.assertEqual(args[-2:], ["--", "-hola"])
            self.assertNotIn("--session", args)

    def test_unsafe_session_id_is_never_forwarded(self) -> None:
        for bad in ("--auto", "-h", "--session=x", "a b", "x" * 200, "ses;id"):
            with self.subTest(bad=bad), mock.patch.object(opencode.subprocess, "Popen") as popen:
                opencode.send_message("opencode", "hola", bad)
                args = popen.call_args.args[0]
                self.assertNotIn(bad, args)
                self.assertNotIn("--session", args)

    def test_open_app_rejects_unsafe_session_id(self) -> None:
        with mock.patch.object(opencode.subprocess, "Popen") as popen:
            self.assertFalse(opencode.open_app("opencode", "--auto"))
            popen.assert_not_called()
            self.assertTrue(opencode.open_app("opencode", "ses_123"))
            self.assertEqual(popen.call_args.args[0][-2:], ["--session", "ses_123"])

    def test_temp_dirs_are_unique_and_private(self) -> None:
        first, out1, err1 = opencode._new_temp_paths()
        second, out2, err2 = opencode._new_temp_paths()
        self.assertNotEqual(first, second)
        self.assertNotEqual(out1, out2)
        self.assertNotEqual(err1, err2)
        if os.name == "posix":
            self.assertEqual(stat.S_IMODE(first.stat().st_mode), 0o700)

    def test_stale_temp_dirs_are_cleaned_but_recent_are_kept(self) -> None:
        base = Path(tempfile.gettempdir())
        stale = base / (opencode._TEMP_PREFIX + "alpha-stale")
        recent = base / (opencode._TEMP_PREFIX + "alpha-recent")
        stale.mkdir(exist_ok=True)
        recent.mkdir(exist_ok=True)
        old = time.time() - 2 * 86400
        os.utime(stale, (old, old))
        try:
            opencode._cleanup_stale_temp_dirs()
            self.assertFalse(stale.exists())
            self.assertTrue(recent.exists())
        finally:
            if stale.exists():
                stale.rmdir()
            recent.rmdir()

    def test_parse_reply_reads_json_and_falls_back_to_stderr(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.txt"
            err = Path(tmp) / "err.txt"
            out.write_text(
                '{"sessionID":"ses_abc","type":"text","part":{"text":"parte 1"}}\n'
                '{"type":"text","part":{"text":"parte 2"}}\n',
                encoding="utf-8",
            )
            err.write_text("error de ejemplo", encoding="utf-8")
            text, sid = opencode.parse_reply(out, err)
            self.assertEqual(text, "parte 1\nparte 2")
            self.assertEqual(sid, "ses_abc")
            out.write_text("", encoding="utf-8")
            text, sid = opencode.parse_reply(out, err)
            self.assertEqual(text, "error de ejemplo")

    def test_agent_keeps_bitty_identity(self) -> None:
        self.assertIn("Marcelbon", opencode.AGENT_TEXT)
        self.assertIn("Soy Bitty, tu mascota de OpenCode", opencode.AGENT_TEXT)
        self.assertIn("espanol", opencode.AGENT_TEXT)


class StateValidationTests(unittest.TestCase):
    def test_load_sanitizes_persisted_values(self) -> None:
        raw = {
            "x": "no-numero",
            "y": True,
            "roam_paused": "sí",
            "session_mode": "continue",
            "session_id": "--auto",
            "session_label": "x" * 200,
            "theme": "inesperado",
        }
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            path.write_text(json.dumps(raw), encoding="utf-8")
            with mock.patch.object(state, "STATE_PATH", path):
                data = state.load()
        self.assertIsNone(data["x"])
        self.assertIsNone(data["y"])
        self.assertIs(data["roam_paused"], True)
        self.assertEqual(data["session_id"], "")
        self.assertEqual(len(data["session_label"]), 80)
        self.assertEqual(data["theme"], "auto")
        self.assertEqual(data["session_mode"], "continue")


class BundleTests(unittest.TestCase):
    def test_prune_unused_qt_keeps_required_libraries(self) -> None:
        if sys.platform == "darwin":
            self.skipTest("Los frameworks de macOS no se recortan en esta versión")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            folder = root / "_internal" / "PySide6"
            folder.mkdir(parents=True)
            suffix = ".dll" if sys.platform == "win32" else ".so.6"
            prefix = "" if sys.platform == "win32" else "lib"
            for lib in ("Qt6Quick", "Qt6Qml", "Qt6Pdf", "Qt6Widgets"):
                (folder / f"{prefix}{lib}{suffix}").write_bytes(b"x")

            removed = build.prune_unused_qt(root)

            self.assertIn(f"{prefix}Qt6Quick{suffix}", removed)
            self.assertIn(f"{prefix}Qt6Qml{suffix}", removed)
            self.assertIn(f"{prefix}Qt6Pdf{suffix}", removed)
            self.assertFalse((folder / f"{prefix}Qt6Quick{suffix}").exists())
            # QtWidgets es imprescindible: no se toca.
            self.assertTrue((folder / f"{prefix}Qt6Widgets{suffix}").exists())


class BridgeTests(unittest.TestCase):
    def test_loopback_token_and_cursor_commands(self) -> None:
        import http.client

        from bitty import bridge

        with tempfile.TemporaryDirectory() as tmp:
            calls: list[tuple[int, int]] = []
            with mock.patch.object(bridge.state, "config_dir", return_value=Path(tmp)):
                server = bridge.Bridge(
                    lambda x, y: calls.append((x, y)),
                    on_capture=lambda work: work(),
                )
                server.start()
                try:
                    config = json.loads((Path(tmp) / "bridge.json").read_text(encoding="utf-8"))
                    self.assertEqual(config["port"], server.port)
                    self.assertGreaterEqual(len(config["token"]), 20)

                    client = http.client.HTTPConnection("127.0.0.1", server.port, timeout=5)
                    client.request("GET", "/ping")
                    response = client.getresponse()
                    self.assertEqual(json.loads(response.read())["ok"], True)

                    headers = {"Content-Type": "application/json"}
                    client.request("POST", "/cursor", "{}", {**headers, "X-Bitty-Token": "incorrecto"})
                    self.assertEqual(client.getresponse().status, 401)

                    auth = {**headers, "X-Bitty-Token": config["token"]}
                    client.request("POST", "/cursor", '{"x": 12, "y": -4}', auth)
                    response = client.getresponse()
                    self.assertEqual(json.loads(response.read())["x"], 12)
                    self.assertEqual(calls, [(12, -4)])

                    client.request("POST", "/cursor", '{"x": 1.5, "y": 2}', auth)
                    self.assertEqual(client.getresponse().status, 400)

                    fake = {"path": str(Path(tmp) / "captura.png"), "uri": "file:///captura.png",
                            "width": 800, "height": 600, "screens": 1}
                    with mock.patch("bitty.screen.capture_to_png", return_value=fake):
                        client.request("POST", "/capture", "{}", auth)
                        response = client.getresponse()
                        self.assertEqual(json.loads(response.read())["uri"], "file:///captura.png")
                    client.close()
                finally:
                    server.stop()
            self.assertFalse((Path(tmp) / "bridge.json").exists())


class VirtualCursorTests(unittest.TestCase):
    def test_navigator_moves_smoothly_and_arrives(self) -> None:
        from bitty.virtual_cursor import CursorNavigator

        nav = CursorNavigator(0, 0)
        nav.go_to(100, 0)
        self.assertTrue(nav.moving)
        previous = 0
        steps = 0
        while nav.moving and steps < 200:
            x, y = nav.advance()
            self.assertGreaterEqual(x, previous)
            self.assertLessEqual(x - previous, 17)  # tope de 16 px + redondeo
            self.assertEqual(y, 0)
            previous = x
            steps += 1
        self.assertEqual((nav.x, nav.y), (100.0, 0.0))
        self.assertFalse(nav.moving)
        self.assertGreater(steps, 5)  # no es un salto instantáneo

    def test_navigator_does_not_overshoot_and_retargets(self) -> None:
        from bitty.virtual_cursor import CursorNavigator

        nav = CursorNavigator(10, 10)
        nav.go_to(50, 50)
        for _ in range(6):
            x, y = nav.advance()
            self.assertLessEqual(x, 50)
            self.assertLessEqual(y, 50)
        nav.go_to(0, 0)  # cambia de objetivo a mitad del camino
        for _ in range(100):
            x, y = nav.advance()
            self.assertGreaterEqual(x, 0)
            self.assertGreaterEqual(y, 0)
            if not nav.moving:
                break
        self.assertEqual((nav.x, nav.y), (0.0, 0.0))

    def test_clamp_multimonitor_and_commands(self) -> None:
        from bitty.virtual_cursor import clamp_point, parse_cursor_command

        rects = [(-1920, 0, 0, 1080), (0, 0, 1920, 1080)]
        self.assertEqual(clamp_point((-3000, 500), rects), (-1920, 500))
        self.assertEqual(clamp_point((3000, -20), rects), (1920, 0))

        self.assertEqual(parse_cursor_command("/cursor 500,300"), ("move", (500, 300)))
        self.assertEqual(parse_cursor_command("/cursor -12 40"), ("move", (-12, 40)))
        self.assertEqual(parse_cursor_command("/cursor demo"), ("demo", None))
        self.assertEqual(parse_cursor_command("/cursor para"), ("stop", None))
        self.assertEqual(parse_cursor_command("hola Bitty"), ("", None))


if __name__ == "__main__":
    unittest.main()
