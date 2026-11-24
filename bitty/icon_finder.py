"""Busca el logo de una app permitida en una captura de pantalla.

Es la «visión» de Bitty para el lanzador: compara una plantilla pequeña con
las franjas de la captura donde suele estar el icono (abajo en Windows, también
izquierda/derecha/arriba en macOS y Linux). No usa clasificadores remotos ni
envía la imagen a ningún sitio; todo ocurre en el equipo.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

if getattr(sys, "frozen", False):
    _BASE = Path(getattr(sys, "_MEIPASS")) / "bitty"
else:
    _BASE = Path(__file__).resolve().parent

TEMPLATES = {
    "brave": _BASE / "resources" / "icons" / "brave-taskbar.png",
}

# La barra de tareas de Windows/Linux suele estar en los últimos 100 px.
BOTTOM_PX = 110
SCALES = (22, 26, 30, 34, 38)


def _valid_correlation(image: np.ndarray, kernel: np.ndarray) -> np.ndarray:
    """Correlación válida: corr[i,j] = sum(image[i+u,j+v] * kernel[u,v]).

    El tamaño de la FFT se calcula por eje: usar un cuadrado de 4096x4096 para
    una franja de 110x2560 hacía que la búsqueda tardara ~24 s. Por ejes tarda
    menos de un segundo y da el mismo resultado.
    """
    ih, iw = image.shape
    kh, kw = kernel.shape
    shape = (
        1 << (ih + kh - 1).bit_length(),
        1 << (iw + kw - 1).bit_length(),
    )
    left = np.fft.rfft2(image, s=shape)
    right = np.fft.rfft2(kernel[::-1, ::-1], s=shape)
    conv = np.fft.irfft2(left * right, s=shape)
    return conv[kh - 1:ih, kw - 1:iw]


def _best_in_region(
    shot: np.ndarray,
    base: Image.Image,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
) -> tuple[float, int, int, int] | None:
    """Mejor coincidencia dentro de un rectángulo, en coordenadas de pantalla."""
    strip = shot[y0:y1, x0:x1]
    best: tuple[float, int, int, int] | None = None
    for size in SCALES:
        rgba = np.asarray(base.resize((size, size), Image.Resampling.LANCZOS), dtype=np.float32)
        alpha = rgba[:, :, 3:4] / 255.0
        weight = (alpha * alpha)[:, :, 0]
        rgb = rgba[:, :, :3]
        if rgb.shape[0] > strip.shape[0] or rgb.shape[1] > strip.shape[1]:
            continue

        # SSD ponderada por la máscara alfa, descompuesta en tres correlaciones.
        score = np.zeros(
            (strip.shape[0] - size + 1, strip.shape[1] - size + 1), dtype=np.float32
        )
        for channel in range(3):
            plane = strip[:, :, channel]
            score += _valid_correlation(plane * plane, weight)
            score -= 2.0 * _valid_correlation(plane, rgb[:, :, channel] * weight)
        score += float(np.sum(rgb * rgb * weight[:, :, None]))

        flat = int(np.argmin(score))
        y, x = divmod(flat, score.shape[1])
        value = float(score[y, x])
        if best is None or value < best[0]:
            best = (value, x0 + x + size // 2, y0 + y + size // 2, size)
    return best


def _regions(
    width: int,
    height: int,
    bottom_px: int,
    all_edges: bool,
) -> list[tuple[int, int, int, int]]:
    """Franjas a explorar, en orden de probabilidad."""
    bottom = max(0, min(bottom_px, height))
    regions = [(0, height - bottom, width, height)]
    if all_edges:
        # Dock de macOS y panel de Linux pueden estar en cualquier borde.
        edge = max(0, min(bottom_px, width))
        regions += [
            (0, 0, width, bottom),
            (0, 0, edge, height),
            (width - edge, 0, width, height),
        ]
    return regions


def find_icon(
    screenshot: Path,
    app: str,
    *,
    bottom_px: int = BOTTOM_PX,
    all_edges: bool = False,
) -> tuple[int, int, int] | None:
    """Devuelve (centro_x, centro_y, tamaño) del logo, o None si no lo ve.

    Con ``all_edges=True`` mira también los otros tres bordes: es lo que usan
    macOS y Linux, donde el lanzador no está necesariamente abajo.
    """
    template_path = TEMPLATES.get(app)
    if not template_path or not template_path.is_file():
        return None

    shot = np.asarray(Image.open(screenshot).convert("RGB"), dtype=np.float32)
    height, width = shot.shape[:2]
    base = Image.open(template_path).convert("RGBA")

    best: tuple[float, int, int, int] | None = None
    for x0, y0, x1, y1 in _regions(width, height, bottom_px, all_edges):
        candidate = _best_in_region(shot, base, x0, y0, x1, y1)
        if candidate is not None and (best is None or candidate[0] < best[0]):
            best = candidate

    if best is None:
        return None
    value, cx, cy, size = best
    # Un logo parecido puede dar un mínimo débil: lo descartamos.
    if value / (size * size * 3) > 9000:
        return None
    return cx, cy, size


__all__ = ["find_icon", "TEMPLATES"]
