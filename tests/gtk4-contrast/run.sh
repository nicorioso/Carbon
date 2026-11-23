#!/usr/bin/env bash
set -euo pipefail

portal_code() {
    busctl --user call org.freedesktop.portal.Desktop         /org/freedesktop/portal/desktop org.freedesktop.portal.Settings         Read ss org.freedesktop.appearance color-scheme 2>/dev/null
}

run_scenario() {
    local name=$1 preference=$2 expected=$3
    gsettings set org.gnome.desktop.interface color-scheme "$preference"
    BROADWAY_DISPLAY=:3 /usr/lib/xdg-desktop-portal-gtk \
        >"results/$name-gtk-portal.log" 2>&1 &
    local gtk_portal=$!
    trap "kill $gtk_portal 2>/dev/null || true" EXIT
    for _ in {1..40}; do
        if [[ $(busctl --user call org.freedesktop.DBus /org/freedesktop/DBus \
            org.freedesktop.DBus NameHasOwner s org.freedesktop.impl.portal.desktop.gtk) == 'b true' ]]; then
            break
        fi
        sleep .1
    done
    /usr/lib/xdg-desktop-portal >"results/$name-front.log" 2>&1 &
    local frontend=$!
    trap "kill $gtk_portal $frontend 2>/dev/null || true" EXIT
    for _ in {1..40}; do
        if [[ $(portal_code) == "v v u $expected" ]]; then break; fi
        sleep .1
    done
    [[ $(portal_code) == "v v u $expected" ]]
    for toolkit in gtk adw; do
        ./probe "$toolkit" "results/$name-$toolkit" >"results/$name-$toolkit.log" 2>&1
    done
    if [[ $name == original || $name == B ]]; then
        BROADWAY_DISPLAY=:3 python -B gtk3.py "results/$name-gtk3.png" >"results/$name-gtk3.log" 2>&1
    fi
}

run_matrix() {
    if [[ -S /run/user/$(id -u)/bus || -n ${WAYLAND_DISPLAY:-}${DISPLAY:-}${DBUS_SESSION_BUS_ADDRESS:-} ]]; then
        printf 'El entorno de prueba tiene acceso a una sesión existente.\n' >&2
        return 1
    fi
    export GDK_BACKEND=broadway BROADWAY_DISPLAY=:4 GTK_A11Y=none NO_AT_BRIDGE=1
    export GSETTINGS_BACKEND=keyfile XDG_CURRENT_DESKTOP=CarbonAudit
    export DBUS_SYSTEM_BUS_ADDRESS="unix:path=$PWD/runtime/no-system-bus"
    ulimit -c 0
    gtk4-broadwayd -a 127.0.0.1 :4 >broadway4.log 2>&1 &
    local gtk4_display=$!
    broadwayd -a 127.0.0.1 :3 >broadway3.log 2>&1 &
    local gtk3_display=$!
    trap "kill $gtk4_display $gtk3_display 2>/dev/null || true" EXIT
    for _ in {1..40}; do
        if [[ -S "$XDG_RUNTIME_DIR/broadway5.socket" && -S "$XDG_RUNTIME_DIR/broadway4.socket" ]]; then break; fi
        sleep .1
    done
    mkdir results
    for scenario in 'original default css 0' 'A prefer-light css 2' 'B prefer-dark css 1'                     'C prefer-light none 2' 'D prefer-dark none 1' 'ablation prefer-light css 2'; do
        read -r name preference css expected <<< "$scenario"
        export HOME="$PWD/$name/home"
        export XDG_CONFIG_HOME="$PWD/$name/conf" XDG_DATA_HOME="$PWD/$name/data"
        export XDG_STATE_HOME="$PWD/$name/state" XDG_CACHE_HOME="$PWD/$name/cache"
        mkdir -p "$XDG_CONFIG_HOME"/{gtk-3.0,gtk-4.0,xdg-desktop-portal}             "$HOME" "$XDG_DATA_HOME" "$XDG_STATE_HOME" "$XDG_CACHE_HOME"
        cp input/gtk3/{settings.ini,gtk.css} "$XDG_CONFIG_HOME/gtk-3.0/"
        cp input/gtk4/settings.ini "$XDG_CONFIG_HOME/gtk-4.0/"
        if [[ $css == css ]]; then cp input/gtk4/gtk.css "$XDG_CONFIG_HOME/gtk-4.0/"; fi
        if [[ $name == ablation ]]; then
            printf '\nheaderbar { background-image: none; }\n' >>"$XDG_CONFIG_HOME/gtk-4.0/gtk.css"
        fi
        printf '[preferred]\ndefault=gtk\n' >"$XDG_CONFIG_HOME/xdg-desktop-portal/portals.conf"
        dbus-run-session -- bash "$PWD/run.sh" --scenario "$name" "$preference" "$expected"             >"results/$name-bus.log" 2>&1
    done
}

if [[ ${CARBON_GTK4_SANDBOX:-} == "$PWD" ]]; then
    case ${1:-} in
        --matrix) run_matrix ;;
        --scenario) shift; run_scenario "$@" ;;
        *) exit 2 ;;
    esac
    exit
fi

if (($#)); then printf 'Uso: bash tests/gtk4-contrast/run.sh\n' >&2; exit 2; fi
source_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
repo=$(cd -- "$source_dir/../.." && pwd)
stage=$(mktemp -d /tmp/carbon-gtk4.XXXXXXXX)
printf 'Staging: %s\n' "$stage"
mkdir -m 700 -p "$stage"/{home,runtime,input/{gtk3,gtk4}}
cp "$source_dir"/{run.sh,gtk3.py} "$stage/"
for major in 3 4; do
    cp "$repo/dotfiles/.config/gtk-$major.0/"{settings.ini,gtk.css} "$stage/input/gtk$major/"
done
cp "$repo/dotfiles/.config/carbon/theme.json" "$stage/input/theme.json"
read -ra flags <<< "$(pkg-config --cflags --libs libadwaita-1)"
gcc -Wall -Wextra -Wno-unused-parameter -Wno-deprecated-declarations     "$source_dir/probe.c" -o "$stage/probe" "${flags[@]}"
bwrap --unshare-all --die-with-parent --ro-bind / / --tmpfs /home --tmpfs /tmp     --dir "$stage" --bind "$stage" "$stage" --dev /dev --proc /proc --tmpfs /run     --chdir "$stage" --clearenv --setenv PATH /usr/bin --setenv LC_ALL C.UTF-8     --setenv HOME "$stage/home" --setenv XDG_RUNTIME_DIR "$stage/runtime"     --setenv CARBON_GTK4_SANDBOX "$stage" -- /usr/bin/bash "$stage/run.sh" --matrix
python -B "$source_dir/verify.py" "$stage"
