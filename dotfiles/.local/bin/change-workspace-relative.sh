#!/usr/bin/env bash

set -u

fail() {
    printf 'Escritorios: %s\n' "$1" >&2
    exit 1
}

case "$#:${1-}" in
    1:next) step=1 ;;
    1:previous) step=-1 ;;
    *)
        printf 'Uso: %s next|previous\n' "${0##*/}" >&2
        exit 2
        ;;
esac

for dependency in hyprctl python3; do
    command -v "$dependency" >/dev/null || fail "Falta $dependency."
done

response=$(hyprctl -j activeworkspace) || fail 'No se pudo consultar el escritorio activo.'
current=$(python3 -c '
import json
import sys

try:
    workspace = json.load(sys.stdin)
except (ValueError, RecursionError):
    sys.exit(1)

if not isinstance(workspace, dict) or workspace.get("type", "normal") != "normal":
    sys.exit(1)
workspace_id = workspace.get("id")
if type(workspace_id) is not int or not 1 <= workspace_id <= 10:
    sys.exit(1)
print(workspace_id)
' <<< "$response") || fail 'El escritorio activo no es un escritorio numerado válido (1–10).'

target=$(( (current - 1 + step + 10) % 10 + 1 ))
result=$(hyprctl dispatch "hl.dsp.focus({ workspace = $target })") ||
    fail "No se pudo solicitar el cambio al escritorio $target."
[[ $result == ok ]] || fail "Hyprland no confirmó el cambio al escritorio $target."
