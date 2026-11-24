"""Recetas reutilizables de Bitty: guardan pasos, nunca credenciales.

Una receta es un plan corto y verificable: abrir Brave, ir a una URL permitida
y una lista de pasos visuales que Bitty repetirá mirando la pantalla. No hay
campos para usuario, contraseña, tokens ni comandos arbitrarios; OpenCode
sigue pidiendo permiso nativo para cada captura y cada clic.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from .state import config_dir

RECIPES_PATH = config_dir() / "recipes.json"

ALLOWED_HOSTS = frozenset({"mail.google.com", "accounts.google.com"})
ALLOWED_KINDS = frozenset({"open", "navigate", "look", "click", "verify"})
FORBIDDEN_WORDS = (
    "password", "passwd", "contraseña", "contrasena",
    "token", "clave", "secret", "credencial", "pin",
)

_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class InvalidRecipe(ValueError):
    """La receta contiene algo que Bitty no debe guardar o ejecutar."""


def validate_url(raw: Any) -> str | None:
    """Acepta solo HTTPS de los dominios de Gmail; sin credenciales en la URL."""
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw or len(raw) > 300:
        raise InvalidRecipe("URL no válida")
    try:
        parsed = urlsplit(raw)
    except ValueError as exc:
        raise InvalidRecipe("URL no válida") from exc
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise InvalidRecipe("solo HTTPS sin credenciales")
    if (parsed.hostname or "").lower() not in ALLOWED_HOSTS:
        raise InvalidRecipe("dominio no permitido")
    if parsed.port not in (None, 443):
        raise InvalidRecipe("puerto no permitido")
    return raw


def _safe_hint(raw: Any) -> str | None:
    if raw is None:
        return None
    if not isinstance(raw, str) or not raw or len(raw) > 60:
        raise InvalidRecipe("pista no válida")
    lowered = raw.lower()
    if "@" in raw or any(word in lowered for word in FORBIDDEN_WORDS):
        raise InvalidRecipe("la pista no puede contener credenciales")
    return raw


def validate_recipe(raw: Any) -> dict:
    """Normaliza y valida una receta. Cualquier clave extra se rechaza."""
    if not isinstance(raw, dict):
        raise InvalidRecipe("la receta debe ser un objeto")
    allowed = {"id", "label", "account", "url", "steps"}
    extra = set(raw) - allowed
    if extra:
        raise InvalidRecipe("clave no permitida: %s" % ",".join(sorted(extra)))

    recipe_id = raw.get("id")
    if not isinstance(recipe_id, str) or not _ID_RE.fullmatch(recipe_id):
        raise InvalidRecipe("id no válido")

    label = raw.get("label")
    if not isinstance(label, str) or not label or len(label) > 60 or "@" in label:
        raise InvalidRecipe("etiqueta no válida")

    account = raw.get("account")
    if account is not None:
        if (
            not isinstance(account, str) or len(account) > 120
            or not _EMAIL_RE.fullmatch(account)
        ):
            raise InvalidRecipe("cuenta no válida")

    url = raw.get("url")
    if url is not None:
        url = validate_url(url)

    steps = raw.get("steps")
    if not isinstance(steps, (list, tuple)) or not 1 <= len(steps) <= 12:
        raise InvalidRecipe("la receta necesita entre 1 y 12 pasos")
    clean_steps = []
    for step in steps:
        if not isinstance(step, dict):
            raise InvalidRecipe("paso no válido")
        if set(step) - {"kind", "hint"}:
            raise InvalidRecipe("clave no permitida en el paso")
        kind = step.get("kind")
        if kind not in ALLOWED_KINDS:
            raise InvalidRecipe("tipo de paso no permitido")
        clean_steps.append({"kind": kind, "hint": _safe_hint(step.get("hint"))})

    return {
        "id": recipe_id,
        "label": label,
        "account": account,
        "url": url,
        "steps": clean_steps,
    }


def load() -> dict[str, dict]:
    """Lee las recetas guardadas, descartando cualquier entrada manipulada."""
    try:
        raw = json.loads(RECIPES_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError, TypeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    clean: dict[str, dict] = {}
    for key, value in raw.items():
        try:
            recipe = validate_recipe(value)
        except InvalidRecipe:
            continue
        if recipe["id"] == key:
            clean[key] = recipe
    return clean


def save(recipes: dict[str, dict]) -> None:
    RECIPES_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECIPES_PATH.write_text(
        json.dumps(recipes, ensure_ascii=False, sort_keys=True, indent=2),
        encoding="utf-8",
    )


def upsert(raw: dict) -> dict:
    recipe = validate_recipe(raw)
    recipes = load()
    recipes[recipe["id"]] = recipe
    save(recipes)
    return recipe


def forget(recipe_id: str) -> bool:
    recipes = load()
    if recipe_id not in recipes:
        return False
    del recipes[recipe_id]
    save(recipes)
    return True


def get(recipe_id: str) -> dict | None:
    return load().get(recipe_id)


__all__ = [
    "ALLOWED_HOSTS", "ALLOWED_KINDS", "InvalidRecipe", "validate_url",
    "validate_recipe", "load", "save", "upsert", "forget", "get", "RECIPES_PATH",
]
