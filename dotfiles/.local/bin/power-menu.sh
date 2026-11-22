#!/bin/sh

theme="${XDG_CONFIG_HOME:-$HOME/.config}/rofi/power-menu.rasi"

selection=$(printf '<span font_family="Font Awesome 7 Free Solid" foreground="#ffffff">%s</span>   %s\n' \
    '' 'Apagar' \
    '' 'Reiniciar' \
    '' 'Suspender' \
    '' 'Cerrar sesión' |
    rofi -no-config -dmenu -theme "$theme" -markup-rows -no-custom -format i)
status=$?
[ "$status" -eq 1 ] && exit 0
[ "$status" -eq 0 ] || exit "$status"

case "$selection" in
    0) exec systemctl poweroff ;;
    1) exec systemctl reboot ;;
    2) exec systemctl suspend ;;
    3)
        if command -v hyprshutdown >/dev/null 2>&1; then
            exec hyprshutdown
        fi
        exec hyprctl dispatch 'hl.dsp.exit()'
        ;;
esac
