"""Convert validated tokens into GTK CSS and Rasi template values."""

from decimal import Decimal
from string import Template

from .schema import ThemeError


def _quote(value):
    # The schema rejects controls. Both grammars escape backslash and double quote.
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'


def _values(theme):
    colors = {key: value.lower() for key, value in theme["colors"].items()}
    semantic = theme["semantic"]
    values = colors | {key: semantic[key].lower()
                       for key in ("textSecondary", "textDisabled", "textOnSelection")}
    values.update({key: colors[semantic[key]] for key in ("hover", "focus")})

    # Avoid expanding inputs with a very large decimal exponent.
    opacity = max(Decimal(0), Decimal(theme["opacity"]["surface"]))
    alpha = format(opacity, ".6f").rstrip("0").rstrip(".")
    rgb = [int(colors["surface"][index:index + 2], 16) for index in (1, 3, 5)]
    values["surfaceAlpha"] = f"rgba({rgb[0]}, {rgb[1]}, {rgb[2]}, {alpha})"
    values.update({key: f"{value}px" for section in ("geometry", "spacing")
                   for key, value in theme[section].items()})
    fonts = theme["typography"]
    values["fontFamily"] = _quote(fonts["family"])
    values["iconsSolid"] = _quote(fonts["iconsSolid"])
    values["iconsBrands"] = _quote(fonts["iconsBrands"])
    values["fontSize"] = f'{fonts["sizePx"]}px'
    values["rasiFont"] = _quote(f'{fonts["family"]} {values["fontSize"]}')
    return values


_WOFI_ARTIFACTS = {
    "style.css": "wofi.css.tmpl",
    "config": "wofi.conf.tmpl",
    "preview.html": "wofi-preview.html.tmpl",
}

TARGETS = {
    "preview": {
        "carbon-preview.css": "gtk.css.tmpl",
        "carbon-tokens.rasi": "rofi.rasi.tmpl",
    },
    "waybar": {"style.css": "waybar.css.tmpl"},
    "waybar-compact": {"style.css": "waybar-redesign.css.tmpl"},
    "waybar-balanced": {"style.css": "waybar-redesign.css.tmpl"},
    "wofi-compact": _WOFI_ARTIFACTS,
    "wofi-segmented": _WOFI_ARTIFACTS,
}


# The redesign variants differ only in the horizontal padding of status modules.
WAYBAR_STATUS_PADDING = {"waybar-compact": "unit", "waybar-balanced": "small"}

_WOFI_LAYOUTS = {
    "wofi-compact": ("Compact", 440, 324, "small", "unit", "surface", "background", False),
    "wofi-segmented": ("Segmented", 540, 396, "medium", "small", "background", "surfaceRaised", True),
}


def _wofi_values(values, layout):
    title, width, height, padding, gap, panel, search, framed_list = layout
    return {
        "wofiTitle": title,
        "wofiWidth": str(width),
        "wofiHeight": str(height),
        "wofiPadding": values[padding],
        "wofiGap": values[gap],
        "wofiPanel": values[panel],
        "wofiSearch": values[search],
        "wofiListBorder": values["borderThin"] if framed_list else "0px",
        "wofiHtmlFont": values["fontFamily"].replace("<", r"\3c "),
        "wofiHtmlIcons": values["iconsSolid"].replace("<", r"\3c "),
    }


def render_theme(theme, template_dir, *, target="preview"):
    try:
        templates = TARGETS[target]
    except KeyError as error:
        raise ThemeError(f"destino de generación desconocido: {target}") from error
    values = _values(theme)
    if target in WAYBAR_STATUS_PADDING:
        values["statusPadding"] = values[WAYBAR_STATUS_PADDING[target]]
    if target in _WOFI_LAYOUTS:
        values.update(_wofi_values(values, _WOFI_LAYOUTS[target]))
    outputs = {}
    for filename, template_name in templates.items():
        try:
            source = (template_dir / template_name).read_text(encoding="utf-8")
            outputs[filename] = Template(source).substitute(values).encode("utf-8")
        except KeyError as error:
            raise ThemeError(f"{template_name}: variable desconocida {error.args[0]}") from error
        except ValueError as error:
            raise ThemeError(f"{template_name}: plantilla UTF-8 o marcador inválido") from error
    return outputs
