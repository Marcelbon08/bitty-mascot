"""Sprites del cursor propio de Bitty: puntero clásico completo y variantes.

Las cuatro variantes comparten **exactamente la misma silueta**: la flecha
tradicional de ratón, rellena por completo, con su muesca inferior. Lo que
cambia es el tratamiento interior, siempre con la paleta de OpenCode:

* ``clasico`` (por defecto): contorno negro, cuerpo blanco, filete del color
  del tema por dentro y un mini prompt ``>`` oscuro. Es el más "ratón".
* ``neon``: filo izquierdo brillante, contorno neón, interior de terminal y
  prompt claro. El más llamativo sobre fondos oscuros.
* ``terminal``: cuerpo del color del tema con líneas de escaneo y prompt
  blanco, como una pantalla de consola.
* ``bitty``: contorno neón, cuerpo blanco, dos ojos y el prompt en negro.

El módulo no importa Qt ni Pillow: ``colors_for()`` traduce caracteres a RGB
de la paleta del tema para que ``cursor_view.py`` los pinte.
"""

from __future__ import annotations

from typing import Any

# Puntero de 16 x 16. . = transparente; el resto son colores de la paleta.
CLASICO = (
    "o...............",
    "ko..............",
    "kwo.............",
    "kwwo............",
    "kwwwo...........",
    "kwwwwo..........",
    "kwdwwwo.........",
    "kwwdwwwo........",
    "kwdwwwwwo.......",
    "kwwwwwwwwo......",
    "kwwwwwkkwwo.....",
    "kwwwko..kwwkko..",
    "kwwo....kwwwwo..",
    "kwo......kwwwwo.",
    "ko........kwwwwo",
    "..........kkkkko",
)

NEON = (
    "h...............",
    "ho..............",
    "hdo.............",
    "hddo............",
    "hdddo...........",
    "hddddo..........",
    "hdkdddo.........",
    "hddkdddo........",
    "hdkdddddo.......",
    "hddddddddo......",
    "hdddddooddo.....",
    "hdddoo..oddooo..",
    "hddo....oddddo..",
    "hdo......oddddo.",
    "ho........oddddo",
    "..........oooooo",
)

TERMINAL = (
    "k...............",
    "kk..............",
    "kok.............",
    "kssk............",
    "koook...........",
    "kooook..........",
    "kswsssk.........",
    "koowoook........",
    "kowoooook.......",
    "kssssssssk......",
    "koooookkook.....",
    "koookk..kookkk..",
    "kssk....kssssk..",
    "kok......kooook.",
    "kk........kooook",
    "..........kkkkkk",
)

BITTY = (
    "o...............",
    "oo..............",
    "owo.............",
    "owwo............",
    "owwwo...........",
    "owwwwo..........",
    "owkwwwo.........",
    "owwkwwwo........",
    "owkwkwkwo.......",
    "owwwwwwwwo......",
    "owwwwwoowwo.....",
    "owwwoo..owwooo..",
    "owwo....owwwwo..",
    "owo......owwwwo.",
    "oo........owwwwo",
    "..........oooooo",
)

# Cada carácter apunta a una clave real de themes.ORIGINAL_PALETTE.
SPRITE_COLORS = {
    "clasico": {"k": "bg", "w": "bright", "o": "accent", "d": "panel"},
    "neon": {"h": "bright", "o": "accent", "d": "panel", "k": "ink"},
    "terminal": {"k": "bg", "o": "accent", "s": "shade", "w": "bright"},
    "bitty": {"o": "accent", "w": "bright", "k": "bg"},
}

SPRITES = {
    "clasico": CLASICO,
    "neon": NEON,
    "terminal": TERMINAL,
    "bitty": BITTY,
}

STYLE_LABELS = {
    "clasico": "CLASICO",
    "neon": "NEON",
    "terminal": "TERMINAL",
    "bitty": "BITTY",
}

DEFAULT_STYLE = "clasico"
TRANSPARENT = "."

# Compatibilidad: quien importaba ARROW / SPRITE_COLORS sigue obteniendo el
# sprite por defecto sin tener que conocer el nombre de la variante.
ARROW = CLASICO


def sprite_for(style: str) -> tuple[str, ...]:
    """Devuelve las filas del sprite pedido (el clásico si no existe)."""
    return SPRITES.get(style, SPRITES[DEFAULT_STYLE])


def colors_for(theme: Any, style: str = DEFAULT_STYLE) -> dict[str, tuple[int, int, int]]:
    """Devuelve ``{carácter: RGB}`` para el tema y la variante dados.

    El carácter transparente se omite: quien pinte el sprite solo rellena los
    caracteres presentes en el dict devuelto.
    """
    palette = theme.palette
    mapping = SPRITE_COLORS.get(style, SPRITE_COLORS[DEFAULT_STYLE])
    return {
        char: tuple(palette[key])
        for char, key in mapping.items()
        if char != TRANSPARENT
    }


if __name__ == "__main__":
    for style, rows in SPRITES.items():
        print(f"--- {STYLE_LABELS[style]} ---")
        for line in rows:
            print(line.replace(".", " "))
