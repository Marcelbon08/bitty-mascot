"""Sprite del cursor propio de Bitty: un puntero neón de terminal.

Decisión de diseño
------------------
Se conserva la silueta canónica del puntero (punta arriba a la izquierda, cuerpo
diagonal y muesca inferior) para que siga reconociéndose como ratón de un
vistazo, incluso a 32x32 px (16x16 a SCALE=2). La personalidad Bitty/OpenCode
viene del tratamiento, no de la forma:

* ``h`` (bright) es el filo izquierdo: una línea luminosa continua que guía la
  mirada hacia la punta y destaca incluso sobre fondos oscuros de videojuegos.
* ``o`` (accent) dibuja el resto del contorno con el color del tema (azul
  OpenCode, rojo en Navidad, naranja en Halloween). Es el "neón" del cursor.
* ``d`` (panel) rellena el interior con el negro de la terminal, así que el
  puntero parece una ventanita recortada y no un cursor genérico de Windows.
* ``k`` (ink) traza un mini prompt ``>`` en la parte ancha: una pista de que
  quien mueve este ratón es Bitty, no el usuario.

Frente al diseño anterior (cuerpo sólido del color de acento), aquí el acento
va en el borde y el cuerpo es oscuro: cambia por completo el aspecto sin perder
legibilidad ni la identidad del tema.

Este módulo no importa Qt ni Pillow: ``colors_for()`` solo traduce caracteres a
tuplas RGB de la paleta del tema para que el view las convierta a QColor.
"""

from __future__ import annotations

from typing import Any

# Puntero de 16 x 16. h = filo, o = contorno, d = panel, k = prompt, . = vacío.
ARROW = (
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
    "hddddoodddo.....",
    "hdddo..odddoo...",
    "hddo....oddddo..",
    "hdo......oddddo.",
    "ho........oddddo",
    "..........oooooo",
)

# Punto = píxel transparente (no se pinta). Se declara aquí para que no quede
# ningún carácter del sprite sin entrada; colors_for() lo omite a propósito.
TRANSPARENT = "."

# Cada carácter del sprite apunta a una clave real de themes.ORIGINAL_PALETTE.
SPRITE_COLORS = {
    ".": "bg",
    "h": "bright",
    "o": "accent",
    "d": "panel",
    "k": "ink",
}


def colors_for(theme: Any) -> dict[str, tuple[int, int, int]]:
    """Devuelve ``{carácter: RGB}`` para el tema dado, sin tocar Qt.

    ``theme`` solo necesita exponer ``.palette`` con claves de themes.py.
    El carácter transparente no se incluye: quien pinte el sprite debe
    rellenar solo los caracteres presentes en el dict devuelto.
    """
    palette = theme.palette
    return {
        char: tuple(palette[key])
        for char, key in SPRITE_COLORS.items()
        if char != TRANSPARENT
    }


if __name__ == "__main__":
    for line in ARROW:
        print(line.replace(".", " "))
    print("caracteres:", " ".join(sorted({c for line in ARROW for c in line})))
    print("colores:  ", ", ".join(f"{c}={k}" for c, k in SPRITE_COLORS.items()))
