#!/usr/bin/env bash

set -euo pipefail

direction="${1:?Usage: change-workspace-relative.sh next|previous}"
current="$(hyprctl -j activeworkspace | sed -n 's/.*"id": *\([0-9]*\).*/\1/p')"

case "$direction" in
    next)
        target=$((current + 1))
        ((target <= 10)) || target=1
        ;;
    previous)
        target=$((current - 1))
        ((target >= 1)) || target=10
        ;;
    *)
        exit 2
        ;;
esac

hyprctl dispatch "hl.dsp.focus({ workspace = $target })"
