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

_POWER_ARTIFACTS = {
    "power-menu.rasi": "power-menu.rasi.tmpl",
    "preview.html": "power-menu-preview.html.tmpl",
}

_MAKO_ARTIFACTS = {
    "config": "mako.conf.tmpl",
    "preview.html": "mako-preview.html.tmpl",
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
    "power-grid": _POWER_ARTIFACTS,
    "power-list": _POWER_ARTIFACTS,
    "mako-compact": _MAKO_ARTIFACTS,
    "mako-segmented": _MAKO_ARTIFACTS,
}


# The redesign variants differ only in the horizontal padding of status modules.
WAYBAR_STATUS_PADDING = {"waybar-compact": "unit", "waybar-balanced": "small"}

_WOFI_LAYOUTS = {
    "wofi-compact": ("Compact", 440, 324, "small", "unit", "surface", "background", False),
    "wofi-segmented": ("Segmented", 540, 396, "medium", "small", "background", "surfaceRaised", True),
}

_POWER_LAYOUTS = {
    "power-grid": ("Grid", 408, 2, "small", "medium", "0.5"),
    "power-list": ("List", 320, 1, "unit", "small", "0.0"),
}

_MAKO_LAYOUTS = {
    "mako-compact": ("Compact", 320, 112, "small", "borderThin", "surface", 10),
    "mako-segmented": ("Segmented", 376, 144, "medium", "borderStrong", "surfaceRaised", 11),
}

_GRID_KEYS = """configuration {
    kb-row-left: "Left,Control+Page_Up";
    kb-row-right: "Right,Control+Page_Down";
    kb-move-char-back: "Control+b";
    kb-move-char-forward: "Control+f";
}

"""


def _html_css_string(quoted):
    return quoted.replace("<", r"\3c ")


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
        "wofiHtmlFont": _html_css_string(values["fontFamily"]),
        "wofiHtmlIcons": _html_css_string(values["iconsSolid"]),
    }


def _power_values(theme, values, layout):
    title, width, columns, gap, padding, alignment = layout
    return {
        "powerTitle": title,
        "powerWidth": str(width),
        "powerColumns": str(columns),
        "powerRows": str(4 // columns),
        "powerGap": values[gap],
        "powerRowPadding": values[padding],
        "powerAlignment": alignment,
        "powerJustify": "center" if columns == 2 else "flex-start",
        "powerKeys": _GRID_KEYS if columns == 2 else "",
        "powerFont": _quote(f'{theme["typography"]["family"]} 11'),
        "powerHtmlFont": _html_css_string(values["fontFamily"]),
        "powerHtmlIcons": _html_css_string(values["iconsSolid"]),
    }


def _mako_values(theme, values, layout):
    title, width, height, spacing, border, background, points = layout
    segmented = title == "Segmented"
    return {
        "makoTitle": title,
        "makoWidth": str(width),
        "makoHeight": str(height),
        "makoSpacing": values[spacing].removesuffix("px"),
        "makoBorder": values[border].removesuffix("px"),
        "makoRadius": values["radius"].removesuffix("px"),
        "makoSurface": values[background],
        "makoFont": f'{theme["typography"]["family"]} {points}',
        "makoTitleMarkup": '<span size="large"><b>%s</b></span>' if segmented else "<b>%s</b>",
        "makoHtmlFont": _html_css_string(values["fontFamily"]),
        "makoHtmlIcons": _html_css_string(values["iconsSolid"]),
        "makoHtmlPoints": str(points),
        "makoHtmlTitleSize": "1.2em" if segmented else "1em",
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
    if target in _POWER_LAYOUTS:
        values.update(_power_values(theme, values, _POWER_LAYOUTS[target]))
    if target in _MAKO_LAYOUTS:
        values.update(_mako_values(theme, values, _MAKO_LAYOUTS[target]))
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
