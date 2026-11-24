"""Busca el logo de una app permitida en una captura de pantalla.

Es la «visión» de Bitty para el lanzador: compara una plantilla pequeña con
las franjas de la captura donde suele estar el icono (abajo en Windows, también
izquierda/derecha/arriba en macOS y Linux). No usa clasificadores remotos ni
envía la imagen a ningún sitio; todo ocurre en el equipo.

La búsqueda se hizo más barata sin cambiar el resultado: se recorta con Pillow
antes de convertir a float32, se cachean las plantillas y solo se prueban tres
escalas. La FFT de cada plantilla se reutiliza para los tres canales.
"""

from __future__ import annotations

import sys
from functools import lru_cache
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
# Tres tamaños bastan para un icono de 32 px; antes se probaban cinco.
SCALES = (22, 30, 38)


@lru_cache(maxsize=24)
def _template(template: str, size: int) -> tuple[np.ndarray, np.ndarray]:
    """Array RGB y máscara alfa de la plantilla en un tamaño dado."""
    with Image.open(template) as source:
        rgba = np.asarray(
            source.convert("RGBA").resize((size, size), Image.Resampling.LANCZOS),
            dtype=np.float32,
        )
    alpha = rgba[:, :, 3:4] / 255.0
    weight = alpha[:, :, 0] ** 2
    return rgba[:, :, :3], weight


def _fft_shape(height: int, width: int, size: int) -> tuple[int, int]:
    return (
        1 << (height + size - 1).bit_length(),
        1 << (width + size - 1).bit_length(),
    )


def _best_in_region(
    strip_image: Image.Image,
    origin: tuple[int, int],
    template: str,
) -> tuple[float, int, int, int] | None:
    """Mejor coincidencia dentro de un recorte, en coordenadas de pantalla."""
    width, height = strip_image.size
    strip = np.asarray(strip_image, dtype=np.float32)
    best: tuple[float, int, int, int] | None = None
    for size in SCALES:
        if size > height or size > width:
            continue
        rgb, weight = _template(template, size)
        shape = _fft_shape(height, width, size)
        # La FFT de la máscara y de cada canal de la plantilla es constante
        # para este tamaño y resolución: se calcula una vez por escala.
        mask_fft = np.fft.rfft2(weight[::-1, ::-1], s=shape)
        channel_ffts = [
            np.fft.rfft2((rgb[:, :, c] * weight)[::-1, ::-1], s=shape)
            for c in range(3)
        ]
        score = np.zeros((height - size + 1, width - size + 1), dtype=np.float32)
        for channel in range(3):
            plane = strip[:, :, channel]
            plane_fft = np.fft.rfft2(plane, s=shape)
            squared_fft = np.fft.rfft2(plane * plane, s=shape)
            score += np.fft.irfft2(squared_fft * mask_fft, s=shape)[
                size - 1:height, size - 1:width
            ]
            score -= 2.0 * np.fft.irfft2(plane_fft * channel_ffts[channel], s=shape)[
                size - 1:height, size - 1:width
            ]
        score += float(np.sum(rgb * rgb * weight[:, :, None]))

        y, x = divmod(int(np.argmin(score)), score.shape[1])
        value = float(score[y, x])
        if best is None or value < best[0]:
            best = (
                value,
                origin[0] + x + size // 2,
                origin[1] + y + size // 2,
                size,
            )
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

    with Image.open(screenshot) as image:
        base = image.convert("RGB")
        width, height = base.size
        best: tuple[float, int, int, int] | None = None
        for x0, y0, x1, y1 in _regions(width, height, bottom_px, all_edges):
            crop = base.crop((x0, y0, x1, y1))
            candidate = _best_in_region(crop, (x0, y0), str(template_path))
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
