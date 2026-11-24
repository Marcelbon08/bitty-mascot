"""Acuerdo breve de Bitty antes de mirar la pantalla o actuar.

No sustituye al permiso nativo de OpenCode: ese se pide cada vez. Este acuerdo
es el paso previo, en la propia mascota, para que nadie acepte sin haber leído
cuatro líneas cortas. Se guarda la versión aceptada en ``state.json``.
"""

from __future__ import annotations

AGREEMENT_VERSION = 1

AGREEMENT_TITLE = "ACUERDO BITTY — 4 líneas"

AGREEMENT_LINES = (
    "1. Solo miro la pantalla cuando tú lo pides desde OpenCode.",
    "2. Nada se graba: la imagen se usa en esa respuesta y ya.",
    "3. Nada sale de tu equipo; OpenCode pregunta cada vez y rechazar no conecta nada.",
    "4. Mi cursor es propio: tu ratón no se mueve y no pulso teclas.",
)

AGREEMENT_TEXT = "\n".join(AGREEMENT_LINES)


def is_accepted(data: dict) -> bool:
    """True solo cuando la versión vigente del acuerdo fue aceptada."""
    return data.get("agreement_version") == AGREEMENT_VERSION


__all__ = [
    "AGREEMENT_VERSION", "AGREEMENT_TITLE", "AGREEMENT_LINES",
    "AGREEMENT_TEXT", "is_accepted",
]
