"""Temas de Bitty: paleta, teñido de sprites y accesorios de temporada.

Los sprites base son los 21 PNG originales (escala de grises de OpenCode con
un acento azul). Cada tema los recoloriza y les añade un accesorio dibujado
con Pillow, sin necesidad de mantener 21 PNG por tema.
"""

from __future__ import annotations

import datetime as _dt
from dataclasses import dataclass, field
from typing import Callable

from PIL import Image, ImageDraw

# Colores exactos con los que se generaron los sprites base.
BASE = {
    (12, 12, 12): "bg",
    (22, 22, 22): "panel",
    (26, 26, 26): "subtle",
    (75, 75, 75): "shade",
    (143, 143, 143): "muted2",
    (174, 174, 174): "muted",
    (219, 219, 219): "emphasis",
    (238, 238, 238): "ink",
    (250, 250, 250): "bright",
    (107, 143, 255): "accent",
}

# Paleta OpenCode original.
ORIGINAL_PALETTE = {
    "bg": (12, 12, 12),
    "panel": (22, 22, 22),
    "subtle": (26, 26, 26),
    "shade": (75, 75, 75),
    "muted2": (143, 143, 143),
    "muted": (174, 174, 174),
    "emphasis": (219, 219, 219),
    "ink": (238, 238, 238),
    "bright": (250, 250, 250),
    "accent": (107, 143, 255),
    "divider": (46, 46, 46),
    "border": (75, 75, 75),
}


def _santa_hat(img: Image.Image) -> None:
    """Gorro rojo sentado sobre el borde superior de la terminal (y=8..11)."""
    d = ImageDraw.Draw(img)
    d.polygon([(18, 5), (31, 0), (46, 5)], fill=(200, 48, 48))
    d.rectangle([15, 5, 48, 8], fill=(245, 245, 245))
    d.ellipse([28, -3, 36, 4], fill=(245, 245, 245))


def _pumpkin(img: Image.Image) -> None:
    """Calabaza pequeña con cara, sobre el borde superior de la terminal."""
    d = ImageDraw.Draw(img)
    d.ellipse([24, 0, 40, 9], fill=(232, 126, 32))
    d.rectangle([30, -2, 34, 2], fill=(86, 140, 60))
    d.polygon([(27, 3), (29, 5), (27, 6)], fill=(40, 20, 20))
    d.polygon([(35, 3), (37, 5), (35, 6)], fill=(40, 20, 20))
    d.line([(29, 8), (32, 7), (35, 8)], fill=(40, 20, 20), width=1)


@dataclass(frozen=True)
class Theme:
    key: str
    label: str
    palette: dict[str, tuple[int, int, int]]
    greeting: str
    accessory: Callable[[Image.Image], None] | None = None


THEMES: dict[str, Theme] = {
    "original": Theme(
        key="original",
        label="OPENCODE",
        palette=ORIGINAL_PALETTE,
        greeting="¿Qué necesitas?",
    ),
    "navidad": Theme(
        key="navidad",
        label="NAVIDAD",
        palette={
            **ORIGINAL_PALETTE,
            "accent": (239, 83, 80),
            "divider": (70, 30, 30),
            "border": (120, 55, 55),
        },
        greeting="¡Feliz Navidad! ¿Qué necesitas?",
        accessory=_santa_hat,
    ),
    "halloween": Theme(
        key="halloween",
        label="HALLOWEEN",
        palette={
            **ORIGINAL_PALETTE,
            "accent": (255, 147, 41),
            "divider": (55, 30, 65),
            "border": (105, 60, 125),
        },
        greeting="¡Truco o trato! ¿Qué necesitas?",
        accessory=_pumpkin,
    ),
}


def theme_for_date(today: _dt.date | None = None) -> str:
    """Tema automático según la época del año."""
    today = today or _dt.date.today()
    if today.month == 12:
        return "navidad"
    if today.month == 10:
        return "halloween"
    return "original"


def resolve_theme(choice: str) -> Theme:
    if choice == "auto":
        return THEMES[theme_for_date()]
    return THEMES.get(choice, THEMES["original"])


def tint_sprite(image: Image.Image, theme: Theme) -> Image.Image:
    """Recoloriza un sprite base y le pone el accesorio del tema.

    Se cachea desde sprites.py; aquí solo se hace el trabajo puro.
    """
    src = image.convert("RGBA")
    remap = {}
    for rgb, name in BASE.items():
        remap[rgb] = theme.palette.get(name, rgb)

    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    px_in = src.load()
    px_out = out.load()
    w, h = src.size
    bg = ORIGINAL_PALETTE["bg"]
    for y in range(h):
        for x in range(w):
            r, g, b, a = px_in[x, y]
            if a == 0:
                continue
            # El fondo del PNG era el TransparencyKey de la version WinForms.
            # En Qt se vuelve alfa 0 para que no aparezca un cuadro oscuro.
            if (r, g, b) == bg:
                px_out[x, y] = (0, 0, 0, 0)
                continue
            px_out[x, y] = (*remap.get((r, g, b), (r, g, b)), a)

    if theme.accessory:
        theme.accessory(out)
    return out
