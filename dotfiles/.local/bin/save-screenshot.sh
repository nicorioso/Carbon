#!/usr/bin/env bash

set -euo pipefail

screenshots_dir="$HOME/imagenes/screenshots"
mkdir -p "$screenshots_dir"

filename="$(date +'%Y-%m-%d_%H-%M-%S').png"
filepath="$screenshots_dir/$filename"

grim -g "$(slurp)" "$filepath"
wl-copy < "$filepath"
makoctl notify -a "Captura de pantalla" -i "$filepath" "Guardada en $filepath"
