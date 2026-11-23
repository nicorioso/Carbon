#!/bin/sh

theme="${XDG_CONFIG_HOME:-$HOME/.config}/rofi/power-menu.rasi"

require_command() {
    if ! command -v "$1" >/dev/null; then
        printf 'Menú de energía: falta %s.\n' "$1" >&2
        exit 127
    fi
}

require_command rofi
if [ ! -f "$theme" ] || [ ! -r "$theme" ]; then
    printf 'Menú de energía: no se puede leer el tema Rofi.\n' >&2
    exit 1
fi

selection=$(printf '<span font_family="Font Awesome 7 Free Solid" foreground="#ffffff">%s</span>   %s\n' \
    '' 'Apagar' \
    '' 'Reiniciar' \
    '' 'Suspender' \
    '' 'Cerrar sesión' |
    rofi -no-config -dmenu -theme "$theme" -markup-rows -no-custom -format i)
status=$?
if [ "$status" -eq 1 ] && [ -z "$selection" ]; then
    exit 0
fi
if [ "$status" -ne 0 ]; then
    printf 'Menú de energía: Rofi terminó con código %s.\n' "$status" >&2
    exit "$status"
fi

case "$selection" in
    '') exit 0 ;;
    0) action=poweroff ;;
    1) action=reboot ;;
    2) action=suspend ;;
    3)
        if command -v hyprshutdown >/dev/null 2>&1; then
            exec hyprshutdown
        fi
        require_command hyprctl
        exec hyprctl dispatch 'hl.dsp.exit()'
        ;;
    *)
        printf 'Menú de energía: selección no válida.\n' >&2
        exit 2
        ;;
esac

require_command systemctl
exec systemctl "$action"
