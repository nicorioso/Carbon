"""Read and validate the Carbon v1 token document."""

from decimal import Decimal, DecimalException
import json
import re
import unicodedata


class ThemeError(ValueError):
    """An input or output could not be accepted."""


PALETTE = {
    "background": "#121212",
    "surface": "#1b1b1b",
    "surfaceRaised": "#252525",
    "border": "#333333",
    "selection": "#d6d6d6",
    "text": "#f5f5f5",
}


class _Object(list):
    """Preserve object pairs until their full paths are known."""


def _unpack(value, path):
    if isinstance(value, _Object):
        result = {}
        for key, item in value:
            child = f"{path}.{key}"
            if key in result:
                raise ThemeError(f"{child}: clave duplicada")
            result[key] = _unpack(item, child)
        return result
    if isinstance(value, list):
        return [_unpack(item, f"{path}[{index}]") for index, item in enumerate(value)]
    return value


def _fields(value, name, *required):
    if not isinstance(value, dict):
        raise ThemeError(f"{name}: se esperaba un objeto")
    for key in required:
        if key not in value:
            raise ThemeError(f"{name}.{key}: clave obligatoria ausente")
    for key in value:
        if key not in required:
            raise ThemeError(f"{name}.{key}: clave desconocida")
    return value


def _integer(value, name, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ThemeError(f"{name}: se esperaba un entero entre {low} y {high}")


def _color(value, name):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ThemeError(f"{name}: se esperaba un color hexadecimal #RRGGBB")
    return value.lower()


def _font(value, name):
    if (not isinstance(value, str) or not value.strip() or len(value) > 120
            or any(unicodedata.category(char).startswith("C") or
                   unicodedata.category(char) in {"Zl", "Zp"} for char in value)):
        raise ThemeError(f"{name}: se esperaba una familia de 1 a 120 caracteres visibles, sin controles")


def validate(theme):
    root = _fields(theme, "theme", "metadata", "colors", "semantic",
                   "typography", "geometry", "spacing", "opacity")
    meta = _fields(root["metadata"], "metadata", "name", "schemaVersion")
    if meta["name"] != "Carbon":
        raise ThemeError('metadata.name: se esperaba "Carbon"')
    if type(meta["schemaVersion"]) is not int or meta["schemaVersion"] != 1:
        raise ThemeError("metadata.schemaVersion: esta versión del motor admite el entero 1")

    colors = _fields(root["colors"], "colors", *PALETTE)
    for key, official in PALETTE.items():
        if _color(colors[key], f"colors.{key}") != official:
            raise ThemeError(f"colors.{key}: Carbon v1 requiere el valor oficial {official}")
    semantic = _fields(root["semantic"], "semantic", "textSecondary",
                       "textDisabled", "textOnSelection", "hover", "focus")
    for key in ("textSecondary", "textDisabled", "textOnSelection"):
        _color(semantic[key], f"semantic.{key}")
    for key in ("hover", "focus"):
        if not isinstance(semantic[key], str) or semantic[key] not in PALETTE:
            raise ThemeError(f"semantic.{key}: se esperaba una referencia a un token de colors")

    fonts = _fields(root["typography"], "typography", "family", "sizePx", "iconsSolid", "iconsBrands")
    for key in ("family", "iconsSolid", "iconsBrands"):
        _font(fonts[key], f"typography.{key}")
    _integer(fonts["sizePx"], "typography.sizePx", 1, 96)

    geometry = _fields(root["geometry"], "geometry", "radius", "borderThin", "borderStrong")
    _integer(geometry["radius"], "geometry.radius", 0, 32)
    for key in ("borderThin", "borderStrong"):
        _integer(geometry[key], f"geometry.{key}", 1, 2)
    if geometry["borderStrong"] < geometry["borderThin"]:
        raise ThemeError("geometry.borderStrong: debe ser al menos geometry.borderThin")

    spacing = _fields(root["spacing"], "spacing", "unit", "small", "medium")
    _integer(spacing["unit"], "spacing.unit", 1, 32)
    for key in ("small", "medium"):
        _integer(spacing[key], f"spacing.{key}", 0, 128)
        if spacing[key] % spacing["unit"]:
            raise ThemeError(f"spacing.{key}: debe ser múltiplo de spacing.unit")
    if spacing["medium"] < spacing["small"]:
        raise ThemeError("spacing.medium: debe ser al menos spacing.small")

    opacity = _fields(root["opacity"], "opacity", "surface")["surface"]
    if type(opacity) not in (int, Decimal) or not Decimal(opacity).is_finite() or not 0 <= opacity <= 1:
        raise ThemeError("opacity.surface: se esperaba un número finito entre 0 y 1")
    return root


def load_theme(path):
    try:
        with path.open(encoding="utf-8") as stream:
            data = json.load(stream, object_pairs_hook=_Object, parse_float=Decimal,
                             parse_constant=Decimal)
        return validate(_unpack(data, "theme"))
    except json.JSONDecodeError as error:
        raise ThemeError(f"theme: JSON inválido (línea {error.lineno}, columna {error.colno})") from error
    except ThemeError:
        raise
    except (DecimalException, RecursionError, ValueError) as error:
        raise ThemeError("theme: JSON inválido, ilegible o demasiado profundo") from error
