#!/usr/bin/env bash

set -uo pipefail

report_error() {
    printf 'Captura de pantalla: %s\n' "$1" >&2
}

fail() {
    report_error "$1"
    if command -v notify-send >/dev/null &&
        ! notify-send --app-name='Carbon' 'Error de captura' "$1"; then
        report_error 'No se pudo enviar la notificación de error.'
    fi
    exit 1
}

for dependency in slurp grim wl-copy date mkdir mktemp ln rm cat; do
    command -v "$dependency" >/dev/null || fail "Falta la dependencia $dependency."
done

# Slurp 1.5.0 usa el mismo código para cancelar y para otros errores.
if selection=$(LC_ALL=C slurp </dev/null 2>&1); then
    geometry=${selection##*$'\n'}
else
    status=$?
    if [[ $status == 1 && $selection == 'selection cancelled' ]]; then
        exit 0
    fi
    [[ -z $selection ]] || report_error "$selection"
    fail "Falló la selección de región (slurp: $status)."
fi

geometry_pattern='^-?[0-9]+,-?[0-9]+ [1-9][0-9]*x[1-9][0-9]*$'
[[ $geometry =~ $geometry_pattern ]] || fail 'Slurp devolvió una geometría inválida.'

screenshots_dir="$HOME/imagenes/screenshots"
umask 077
mkdir -p -- "$screenshots_dir" || fail 'No se pudo preparar el directorio de capturas.'
timestamp=$(date +'%Y-%m-%d_%H-%M-%S') || fail 'No se pudo obtener la fecha de la captura.'
temporary_dir=$(mktemp -d -- "$screenshots_dir/.capture.XXXXXXXX") ||
    fail 'No se pudo crear el directorio temporal de la captura.'
trap 'rm -rf -- "$temporary_dir"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM

temporary_png="$temporary_dir/screenshot.png"
# Comprueba tanto el estado de Grim como la escritura al disco.
if ! grim -g "$geometry" -t png - | cat > "$temporary_png" ||
    [[ ! -s $temporary_png ]]; then
    fail 'Grim no pudo escribir la captura PNG.'
fi

# Publica el PNG completo de forma exclusiva, incluso con capturas simultáneas.
filepath="$screenshots_dir/$timestamp.png"
suffix=0
while ! ln -T -- "$temporary_png" "$filepath" 2>/dev/null; do
    if [[ ! -e $filepath && ! -L $filepath ]]; then
        fail 'No se pudo guardar el PNG en el directorio de capturas.'
    fi
    suffix=$((suffix + 1))
    filepath="$screenshots_dir/$timestamp-$suffix.png"
done

if ! wl-copy --type image/png < "$filepath"; then
    report_error "PNG guardado en $filepath"
    fail 'Se guardó el PNG, pero no se pudo copiar al portapapeles.'
fi

if ! command -v notify-send >/dev/null; then
    report_error 'Falta notify-send. El PNG se guardó y se copió al portapapeles.'
elif ! notify-send --app-name='Carbon' --icon="$filepath" 'Captura de pantalla' \
    "Guardada y copiada al portapapeles: ${filepath##*/}"; then
    report_error 'Falló la notificación. El PNG se guardó y se copió al portapapeles.'
fi
