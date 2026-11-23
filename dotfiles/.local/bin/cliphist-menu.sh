#!/usr/bin/env bash

set -u

fail() {
    printf 'Historial del portapapeles: %s\n' "$1" >&2
    exit 1
}

for dependency in cliphist wofi wl-copy mktemp unlink; do
    command -v "$dependency" >/dev/null || fail "Falta $dependency."
done

# Solo los textos de vista previa pasan por variables de Bash.
history=$(cliphist list) || fail 'No se pudo listar el historial.'
[[ -n $history ]] || exit 0
selection=$(printf '%s\n' "$history" | wofi --dmenu) || {
    status=$?
    # Wofi comparte el estado 1 entre Escape y algunos fallos.
    if [[ $status == 1 && -z $selection ]]; then
        exit 0
    fi
    fail "Wofi terminó con código $status."
}
[[ -n $selection ]] || exit 0

# Wofi admite entrada libre. Solo se acepta una fila del listado presentado.
if [[ $selection == *$'\n'* || ! $selection =~ ^[0-9]+$'\t' ||
    $'\n'$history$'\n' != *$'\n'"$selection"$'\n'* ]]; then
    fail 'La selección no corresponde a una entrada del historial.'
fi

# Validar la decodificación completa antes de ofrecer bytes al portapapeles.
umask 077
payload=$(mktemp -- "${XDG_RUNTIME_DIR:-${TMPDIR:-/tmp}}/carbon-cliphist.XXXXXXXX") ||
    fail 'No se pudo preparar un archivo temporal privado.'
trap 'unlink -- "$payload"' EXIT
trap 'exit 129' HUP
trap 'exit 130' INT
trap 'exit 143' TERM
cliphist decode <<< "$selection" > "$payload" || fail 'No se pudo recuperar la entrada seleccionada.'
[[ -s $payload ]] || fail 'La entrada recuperada está vacía.'
wl-copy < "$payload" || fail 'No se pudo copiar la entrada seleccionada.'
