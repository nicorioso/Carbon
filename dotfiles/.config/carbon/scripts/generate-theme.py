#!/usr/bin/env python3
"""Generate the Carbon preview without contacting the graphical session."""

import argparse
from pathlib import Path
import sys

# A preview invocation writes only to its staging area and destination.
sys.dont_write_bytecode = True

from carbon_theme.output import write_preview
from carbon_theme.render import render_theme
from carbon_theme.schema import ThemeError, load_theme


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True, help="documento JSON de tokens")
    parser.add_argument("--output", type=Path, required=True, help="destino explícito de pruebas")
    default_templates = (Path(__file__).resolve().parent / "../../../../templates/theme").resolve()
    parser.add_argument("--templates", type=Path, default=default_templates,
                        help="directorio de plantillas confiables (por defecto, las del checkout)")
    args = parser.parse_args()
    try:
        theme = load_theme(args.input)
        artifacts = render_theme(theme, args.templates)
        created = write_preview(args.output, artifacts)
    except (ThemeError, OSError) as error:
        parser.exit(1, f"Carbon: {error}\n")
    print("Vista previa generada." if created else "Vista previa idéntica, sin cambios.")
    for filename in artifacts:
        print(filename)


if __name__ == "__main__":
    main()
