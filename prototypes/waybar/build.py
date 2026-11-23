#!/usr/bin/env python3
"""Build the Waybar design review artifacts without touching the running desktop."""

import argparse
from copy import deepcopy
from html import escape
import json
from pathlib import Path
from string import Template
import sys
from tempfile import TemporaryDirectory

REPO = Path(__file__).resolve().parents[2]
CARBON = REPO / "dotfiles/.config/carbon"
HERE = Path(__file__).resolve().parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(CARBON / "scripts"))

from carbon_theme.output import write_preview
from carbon_theme.render import render_theme
from carbon_theme.schema import ThemeError, load_theme

GROUPS = {
    "connectivity": ["network", "bluetooth"],
    "media": ["pulseaudio", "backlight"],
    "energy": ["battery"],
    "productivity": ["custom/ai-usage"],
    "system": ["tray"],
}
CONCEPTS = {
    "segmented": ("Carbon Segmented", 36),
    "refined": ("Carbon Omarchy Refined", 32),
}
# Everything below is a local fixture. No live desktop sources are read.
SAMPLES = {
    "network": ("", "72%", "Sin Wi-Fi"),
    "bluetooth": ("", "", "12"),
    "pulseaudio": ("", "45%", "150%"),
    "backlight": ("", "70%", "100%"),
    "battery": ("", "82%", "100%"),
    "custom/ai-usage": ("", "C 24% · O 18k", "C 100% · O 1234.5k"),
}
WORKSPACE_END = "\n#network, #bluetooth, #pulseaudio, #backlight, #battery, #tray, #custom-ai-usage {"
STATES_START = "#network.disconnected,"
AI_SURFACE = "\n#custom-ai-usage {"
AI_STATE = "#custom-ai-usage.busy,"


def candidate_inputs():
    config_path = REPO / "dotfiles/.config/waybar/config.jsonc"
    original = config_path.read_bytes()
    config = json.loads(original)
    if config["modules-right"] != [module for modules in GROUPS.values() for module in modules]:
        raise ThemeError("Los módulos del piloto ya no coinciden con los grupos del prototipo.")
    segmented = deepcopy(config)
    segmented["height"] = CONCEPTS["segmented"][1]
    segmented["modules-right"] = [f"group/{group}" for group in GROUPS]
    for group, modules in GROUPS.items():
        segmented[f"group/{group}"] = {"orientation": "horizontal", "modules": modules}
    return {
        "segmented": (json.dumps(segmented, ensure_ascii=False, indent=4) + "\n").encode(),
        "refined": original,
    }


def candidate_css(theme, workspace):
    base = (REPO / "templates/theme/waybar-redesign.css.tmpl").read_text(encoding="utf-8")
    # Reuse the entire approved workspace block and the common status rules.
    prefix = base[:base.index(WORKSPACE_END)]
    states = base[base.index(STATES_START):base.index(AI_SURFACE)]
    ai_state = base[base.index(AI_STATE):]
    focus = """#network:focus, #bluetooth:focus, #pulseaudio:focus, #custom-ai-usage:focus {
    outline: ${borderThin} solid ${focus};
    outline-offset: -${borderThin};
}
"""
    outputs = {}
    for variant in CONCEPTS:
        design = (HERE / f"{variant}.css.tmpl").read_text(encoding="utf-8")
        (workspace / "waybar.css.tmpl").write_text(
            "\n\n".join((prefix, design, focus, states, ai_state)), encoding="utf-8"
        )
        outputs[variant] = render_theme(theme, workspace, target="waybar")["style.css"]
    return outputs


def icon(glyph):
    return f'<span class="icon" aria-hidden="true">{glyph}</span>' if glyph else ""


def demo(variant, css, *, long):
    _, height = CONCEPTS[variant]
    occupied = {1, 2, 4}
    if long:
        occupied.update(range(6, 11))
    selected = 7 if long else 2
    workspaces = "".join(
        f'<button class="{"active " if number == selected else ""}{"empty" if number not in occupied else ""}">{number}</button>'
        for number in (range(1, 11) if long else range(1, 6))
    )
    clock = icon("") + (" mié 30 sept  23:58" if long else " vie 20 nov  20:42")
    status = {}
    for module, (glyph, normal, longer) in SAMPLES.items():
        module_id = module.replace("/", "-")
        label = longer if long else normal
        classes = {"network": "disconnected" if long else "", "bluetooth": "connected" if long else "off",
                   "custom/ai-usage": "busy" if long else ""}
        status[module] = f'<div id="{module_id}" class="{classes.get(module, "")}">{icon(glyph)}{escape((" " if glyph and label else "") + label)}</div>'
    status["tray"] = '<div id="tray">' + "".join(map(icon, "" if long else "")) + "</div>"
    right = "".join(
        f'<div id="{group}" class="group">{"".join(status[item] for item in modules)}</div>'
        if variant == "segmented" else "".join(status[item] for item in modules)
        for group, modules in GROUPS.items()
    )
    # This layout simulates a center widget with a growing side. Native GTK does its own allocation.
    frame = f"""<!doctype html><html lang="es"><meta charset="utf-8"><style>
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; }}
window#waybar {{ display: grid; height: {height}px; grid-template-columns:
 minmax(max-content, 1fr) max-content minmax(max-content, 1fr);
 align-items: stretch; gap: 2px; white-space: pre; }}
#workspaces, .status, .group {{ display: flex; align-items: stretch; }}
.status {{ gap: 2px; justify-content: flex-end; }}
.status > div, .group > div, #clock {{ display: flex; align-items: center; white-space: pre; }}
#tray {{ gap: 6px; }}
#tray .icon {{ font-size: 16px; }}
{css.decode()}
</style>
<window id="waybar"><div id="workspaces">{workspaces}</div><div id="clock">{clock}</div><div class="status">{right}</div></window></html>"""
    return (f'<iframe sandbox title="{"Contenido largo" if long else "Uso habitual"}" '
            f'width="{1024 if long else 1280}" height="{height + 2}" srcdoc="{escape(frame, quote=True)}"></iframe>')


def build_artifacts():
    theme = load_theme(CARBON / "theme.json")
    configs = candidate_inputs()
    with TemporaryDirectory(prefix="carbon-waybar-concepts-", dir="/tmp") as directory:
        styles = candidate_css(theme, Path(directory))
    html = Template((HERE / "preview.html.tmpl").read_text(encoding="utf-8"))
    artifacts = {}
    for variant, (title, _) in CONCEPTS.items():
        artifacts[f"{variant}.css"] = styles[variant]
        artifacts[f"{variant}.jsonc"] = configs[variant]
        artifacts[f"{variant}.html"] = html.substitute(
            title=title, background=theme["colors"]["background"], text=theme["colors"]["text"],
            secondary=theme["semantic"]["textSecondary"], border=theme["colors"]["border"],
            normal=demo(variant, styles[variant], long=False),
            long=demo(variant, styles[variant], long=True),
        ).encode()
    return artifacts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        artifacts = build_artifacts()
        write_preview(args.output, artifacts)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Carbon: {error}\n")
    print("\n".join(artifacts))


if __name__ == "__main__":
    main()
