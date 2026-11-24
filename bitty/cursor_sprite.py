"""Sprite del cursor propio de Bitty: un puntero con alma de terminal.

Decisión de diseño
------------------
Se mantiene la silueta canónica del puntero de ratón (punta arriba a la
izquierda, cuerpo diagonal y muesca inferior) para que se lea como cursor de
inmediato, incluso a 32x32 px (16x16 a SCALE=2). Lo que lo hace «Bitty» es el
tratamiento, no la forma:

* ``X`` (bg) recorta el puntero con el mismo negro que la terminal de la
  mascota, así que no parece un cursor de Windows sobre fondo claro.
* ``f`` (accent) tiñe el cuerpo con el acento del tema (azul OpenCode, rojo en
  Navidad, naranja en Halloween).
* ``h`` (bright) y ``s`` (shade) forman un bisel de 1 px: luz arriba a la
  izquierda, sombra abajo a la derecha. Es el mismo lenguaje de píxeles que
  los sprites de la mascota.
* En el centro, un mini prompt ``>`` (``k``) sobre una ventanita oscura
  (``p``, panel) convierte el puntero en una línea de comandos en miniatura:
  se reconoce como ratón, pero se siente como OpenCode.

Este módulo no importa Qt ni Pillow: ``colors_for()`` solo traduce caracteres
a tuplas RGB de la paleta del tema para que el view las convierta a QColor.
"""

from __future__ import annotations

from typing import Any

# Puntero de 16 x 16. X = marco, f = cuerpo, h = brillo, s = sombra,
# p = panel del mini prompt, k = glifo del prompt.
ARROW = (
    "h...............",
    "Xh..............",
    "XhX.............",
    "XhsX............",
    "XhfsX...........",
    "XhffsX..........",
    "XhfffsX.........",
    "XhfkppsX........",
    "XhfpkpfsX.......",
    "XhfkppffsX......",
    "XhfffXfffsX.....",
    "XhffX..XfffsX...",
    "XhfX....XfffsX..",
    "XhX......XfffsX.",
    "XX........XfffsX",
    "..........XXXXXX",
)

# Punto = píxel transparente (no se pinta). Se declara aquí para que no quede
# ningún carácter del sprite sin entrada, pero colors_for() lo omite a propósito
# y así la ventana del cursor no dibuja un rectángulo oscuro alrededor.
TRANSPARENT = "."

# Cada carácter del sprite apunta a una clave real de themes.ORIGINAL_PALETTE.
SPRITE_COLORS = {
    ".": "bg",
    "X": "bg",
    "f": "accent",
    "h": "bright",
    "s": "shade",
    "p": "panel",
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
