#!/usr/bin/env bash
set -euo pipefail

inside() {
    [[ -z ${WAYLAND_DISPLAY:-}${DISPLAY:-} && ! -S /run/user/$(id -u)/bus ]]
    [[ ! -e /dev/dri/card0 && ! -e /dev/dri/card1 && -S /run/carbon-parent ]]
    ulimit -c 0
    WAYLAND_DISPLAY=/run/carbon-parent Hyprland -c "$PWD/layout.lua" > compositor.log 2>&1 &
    local compositor=$!
    trap "kill $compositor 2>/dev/null || true" EXIT
    local socket ipc
    for _ in {1..65}; do
        socket=$(find "$XDG_RUNTIME_DIR" -maxdepth 1 -type s -name 'wayland-*' -print -quit)
        ipc=$(find "$XDG_RUNTIME_DIR/hypr" -name .socket.sock -print -quit 2>/dev/null || true)
        if [[ -S $socket && -S $ipc ]]; then break; fi
        sleep .1
    done
    [[ -S $socket && -S $ipc ]]
    export WAYLAND_DISPLAY="$socket"
    export HYPRLAND_INSTANCE_SIGNATURE=$(basename "$(dirname "$ipc")")
    hyprctl dismissnotify -1 >/dev/null
    # Private session daemon only. Never add --systemd.
    dbus-update-activation-environment WAYLAND_DISPLAY HYPRLAND_INSTANCE_SIGNATURE
    /usr/lib/xdg-desktop-portal-gtk > results/portal-backend.log 2>&1 &
    local backend=$!
    trap "kill $backend $compositor 2>/dev/null || true" EXIT
    for _ in {1..45}; do
        if [[ $(busctl --user call org.freedesktop.DBus /org/freedesktop/DBus             org.freedesktop.DBus NameHasOwner s org.freedesktop.impl.portal.desktop.gtk) == 'b true' ]]; then
            break
        fi
        sleep .1
    done
    /usr/lib/xdg-desktop-portal > results/portal-frontend.log 2>&1 &
    local frontend=$!
    trap "kill $frontend $backend $compositor 2>/dev/null || true" EXIT
    for _ in {1..45}; do
        if [[ $(busctl --user --auto-start=no call org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop             org.freedesktop.portal.Settings Read ss org.freedesktop.appearance color-scheme 2>/dev/null) == 'v v u 0' ]]; then
            break
        fi
        sleep .1
    done
    printf '%s\n' "$WAYLAND_DISPLAY" > results/wayland-socket.txt
    python -B wayland-run.py
}

if [[ ${CARBON_WAYLAND_TEST:-} == "$PWD" && ${1:-} == --inside ]]; then
    inside
    exit
fi
if (($#)); then printf 'Uso: bash tests/gtk4-contrast/wayland.sh\n' >&2; exit 2; fi
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd -- "$source_dir/../.." && pwd)
parent=${WAYLAND_DISPLAY:?}
[[ $parent == /* ]] || parent="${XDG_RUNTIME_DIR:?}/$parent"
[[ -S $parent ]]
[[ -c /dev/dri/renderD128 ]]
stage=$(mktemp -d /tmp/cw.XXXXXX)
printf 'Staging: %s\n' "$stage"
mkdir -m 700 -p "$stage"/{r,home,conf/xdg-desktop-portal,data/{color-schemes,applications},cache,state,results,fixtures}
cp "$source_dir"/{wayland.sh,wayland-run.py,wayland-probe.py,verify.py} "$stage/"
for major in 3 4; do
    src="$repo/dotfiles/.config/gtk-$major.0"
    for file in settings.ini gtk.css; do cmp "$src/$file" "$HOME/.config/gtk-$major.0/$file"; done
    mkdir "$stage/conf/gtk-$major.0"
    cp "$src/"{settings.ini,gtk.css} "$stage/conf/gtk-$major.0/"
done
b="$repo/dotfiles"
cmp "$b/.local/bin/dolphin-carbon" "$HOME/.local/bin/dolphin-carbon"
cmp "$b/.local/share/color-schemes/Carbon.colors" "$HOME/.local/share/color-schemes/Carbon.colors"
cmp "$b/.config/kdeglobals" "$HOME/.config/kdeglobals"
cp "$b/.local/bin/dolphin-carbon" "$stage/"
cp "$b/.local/share/color-schemes/Carbon.colors" "$stage/data/color-schemes/"
cp "$b/.config/kdeglobals" "$stage/conf/"
printf '[UiSettings]\nColorScheme=Carbon\n' > "$stage/conf/dolphinrc"
mkdir "$stage/conf/wofi"
cp "$HOME/.config/wofi/"{config,style.css} "$stage/conf/wofi/"
printf '[preferred]\ndefault=gtk\n' > "$stage/conf/xdg-desktop-portal/portals.conf"
printf 'Documento ficticio de Carbon\n' > "$stage/fixtures/01-Muestra.txt"
mkdir "$stage/fixtures/02-Carpeta"
cat > "$stage/data/applications/carbon-fixture.desktop" <<'DESKTOP'
[Desktop Entry]
Type=Application
Name=Carbon aplicación ficticia
Icon=/usr/share/icons/Adwaita/symbolic/places/folder-symbolic.svg
Exec=/usr/bin/true
DESKTOP
cat > "$stage/layout.lua" <<'LUA'
hl.monitor({ output = "", mode = "preferred", position = "0x0", scale = 1 })
hl.config({
    general = { gaps_in = 5, gaps_out = 20, border_size = 2,
                ['col.active_border'] = "rgb(d6d6d6)", ['col.inactive_border'] = "rgb(333333)" },
    decoration = { rounding = 0, active_opacity = 0.97, inactive_opacity = 0.8 },
    animations = { enabled = false },
    misc = { disable_hyprland_logo = true, disable_splash_rendering = true, disable_autoreload = true },
    ecosystem = { no_update_news = true, no_donation_nag = true },
    xwayland = { enabled = false },
})
LUA
read -ra qt_flags <<< "$(pkg-config --cflags --libs Qt6Widgets)"
g++ -Wall -Wextra -fPIC -shared "$source_dir/wayland-qt.cpp" -o "$stage/qt-probe.so"     -I/usr/include/KF6/KIconThemes -lKF6IconThemes "${qt_flags[@]}"
protected=(
    .config/gtk-{3,4}.0/{settings.ini,gtk.css}
    .config/{kdeglobals,dolphinrc,kitty/kitty.conf,hypr/hyprland.lua}
    .config/{waybar/{config.jsonc,style.css},wofi/{config,style.css},rofi/power-menu.rasi,mako/config}
    .local/{bin/dolphin-carbon,share/applications/org.kde.dolphin.desktop,share/color-schemes/Carbon.colors}
)
session_state() {
    dconf read /org/gnome/desktop/interface/color-scheme
    busctl --user --auto-start=no call org.freedesktop.portal.Desktop \
        /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss \
        org.freedesktop.appearance color-scheme
    systemctl --user show -p Id,MainPID,ActiveState,InvocationID \
        waybar mako xdg-desktop-portal xdg-desktop-portal-gtk xdg-desktop-portal-hyprland
}
(cd "$HOME" && sha256sum -- "${protected[@]}") > "$stage/protected.sha256"
session_state > "$stage/session.before"
status=0
bwrap --unshare-all --die-with-parent --ro-bind / / --tmpfs /home --tmpfs /tmp     --dir "$stage" --bind "$stage" "$stage" --dev /dev --proc /proc --tmpfs /run     --ro-bind "$parent" /run/carbon-parent     --dev-bind /dev/dri/renderD128 /dev/dri/renderD128     --chdir "$stage" --clearenv --setenv PATH /usr/bin --setenv LC_ALL C.UTF-8     --setenv HOME "$stage/home" --setenv XDG_RUNTIME_DIR "$stage/r"     --setenv XDG_CONFIG_HOME "$stage/conf" --setenv XDG_DATA_HOME "$stage/data"     --setenv XDG_CACHE_HOME "$stage/cache" --setenv XDG_STATE_HOME "$stage/state"     --setenv GSETTINGS_BACKEND dconf --setenv XDG_CURRENT_DESKTOP CarbonAudit     --setenv XDG_SESSION_TYPE wayland --setenv GDK_BACKEND wayland     --setenv DBUS_SYSTEM_BUS_ADDRESS "unix:path=$stage/r/no-system-bus"     --setenv NO_AT_BRIDGE 1 --setenv GTK_A11Y none     --setenv CARBON_WAYLAND_TEST "$stage" -- /usr/bin/dbus-run-session -- /usr/bin/bash "$stage/wayland.sh" --inside || status=$?
(cd "$HOME" && sha256sum -c --quiet "$stage/protected.sha256")
session_state > "$stage/session.after"
cmp "$stage/session.before" "$stage/session.after"
printf 'Integridad de la sesión principal verificada.\n'
exit "$status"
