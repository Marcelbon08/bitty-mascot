"""Cálculo del cursor virtual de Bitty: interpolación paso a paso.

Este módulo no importa Qt: solo decide dónde debe estar el segundo cursor en
cada instante. Nunca mueve el ratón real, no hace clics y no escribe teclas.
"""

from __future__ import annotations

import math
import re

# 30 Hz sigue viéndose fluido y recorta un 40 % los despiertes del cursor.
TICK_MS = 32
# Paso mayor para conservar la velocidad del movimiento con menos ticks.
STEP_PX = 22.0
EASE = 0.22
# Distancia a partir de la cual se considera llegado.
ARRIVE_PX = 0.8

_CURSOR_RE = re.compile(r"^/cursor\s+(-?\d+)\s*[ ,;]+\s*(-?\d+)\s*$", re.IGNORECASE)
_CLICK_RE = re.compile(
    r"^/(?:click|clic)\s+(-?\d+)\s*[ ,;]+\s*(-?\d+)(?:\s+([a-z-]+))?\s*$",
    re.IGNORECASE,
)


class CursorNavigator:
    """Interpola la posición actual hacia un objetivo con desaceleración suave."""

    def __init__(
        self,
        x: float,
        y: float,
        step: float = STEP_PX,
        ease: float = EASE,
    ) -> None:
        self.x = float(x)
        self.y = float(y)
        self.target_x = self.x
        self.target_y = self.y
        self.step = max(1.0, float(step))
        self.ease = min(1.0, max(0.01, float(ease)))

    def go_to(self, x: float, y: float) -> None:
        """Cambia el objetivo sin teletransportar el cursor."""
        self.target_x = float(x)
        self.target_y = float(y)

    def snap_to(self, x: float, y: float) -> None:
        """Coloca el cursor y su objetivo en el mismo punto (inicio/reset)."""
        self.x = self.target_x = float(x)
        self.y = self.target_y = float(y)

    @property
    def moving(self) -> bool:
        return math.hypot(self.target_x - self.x, self.target_y - self.y) > ARRIVE_PX

    @property
    def distance(self) -> float:
        return math.hypot(self.target_x - self.x, self.target_y - self.y)

    def advance(self) -> tuple[int, int]:
        """Da un paso y devuelve la posición entera donde dibujar el cursor."""
        dx = self.target_x - self.x
        dy = self.target_y - self.y
        if math.hypot(dx, dy) <= ARRIVE_PX:
            self.x, self.y = self.target_x, self.target_y
            return round(self.x), round(self.y)

        vx, vy = dx * self.ease, dy * self.ease
        length = math.hypot(vx, vy)
        if length > self.step:
            factor = self.step / length
            vx, vy = vx * factor, vy * factor
        elif length < 1.0:
            # Último tramo: cerrar el objetivo de un solo salto corto.
            vx, vy = dx, dy
        self.x += vx
        self.y += vy
        return round(self.x), round(self.y)


def clamp_point(point: tuple[int, int], rects: list[tuple[int, int, int, int]]) -> tuple[int, int]:
    """Mantiene un punto dentro de la unión de rectángulos (multimonitor)."""
    x, y = point
    if not rects:
        return x, y
    left = min(r[0] for r in rects)
    top = min(r[1] for r in rects)
    right = max(r[2] for r in rects)
    bottom = max(r[3] for r in rects)
    return max(left, min(x, right)), max(top, min(y, bottom))


def parse_cursor_command(text: str) -> tuple[str, tuple | None]:
    """Interpreta los comandos locales del panel de Bitty.

    - `/cursor 500,300` o `/cursor 500 300` -> ('move', (500, 300))
    - `/click 500,300 [app]` -> ('click', (500, 300, app))
    - `/cursor demo` -> ('demo', None)
    - `/cursor para` -> ('stop', None)
    - cualquier otro texto -> ('', None) para enviarlo a OpenCode.
    """
    cleaned = " ".join(str(text).split())
    click = _CLICK_RE.match(cleaned)
    if click:
        return "click", (
            int(click.group(1)), int(click.group(2)), (click.group(3) or "").lower()
        )
    match = _CURSOR_RE.match(cleaned)
    if match:
        return "move", (int(match.group(1)), int(match.group(2)))
    lowered = cleaned.lower()
    if lowered in ("/cursor demo", "/cursor ruta"):
        return "demo", None
    if lowered in ("/cursor para", "/cursor stop"):
        return "stop", None
    return "", None
