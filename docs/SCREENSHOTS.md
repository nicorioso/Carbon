# Carbon · Capturas de región

Print sigue ejecutando `~/.local/bin/save-screenshot.sh`. La versión de CARBON-003-A guarda PNG en `~/imagenes/screenshots`, los copia como `image/png` y avisa mediante `notify-send` y el servidor de notificaciones de la sesión. El guardado y la copia determinan el éxito. Un fallo de notificación se informa por stderr y mantiene la captura. Un fallo al copiar se informa como error y también conserva el PNG.

Slurp 1.5.0 devuelve código 1 tanto para cancelación como para otros fallos. Se reconoce la salida de cancelación limpia por su diagnóstico en inglés y se informa cualquier otra salida de error. Si Wayland se desconecta y Slurp emite únicamente el mismo diagnóstico, su interfaz no permite distinguirlo. [Código fuente de Slurp 1.5.0](https://github.com/emersion/slurp/blob/v1.5.0/main.c#L1000-L1010)

Grim emite el PNG por stdout. La tubería detecta también errores de escritura del archivo temporal. El script publica la imagen mediante un enlace duro exclusivo en el mismo sistema de archivos. Conserva el nombre con timestamp de segundos y prueba sufijos `-1`, `-2` y sucesivos ante colisiones. Los archivos nuevos tienen modo 0600 bajo el umask privado.

## Pruebas aisladas

```bash
cd ~/carbon
bash -n dotfiles/.local/bin/save-screenshot.sh
python tests/screenshots/test_screenshots.py -v
if command -v shellcheck >/dev/null; then
    shellcheck dotfiles/.local/bin/save-screenshot.sh
fi
```

Resultado de CARBON-003-A: 15 pruebas pasaron, al igual que `bash -n`. ShellCheck no estaba disponible. Se probaron éxito con rutas con espacios y coordenadas negativas, Escape, fallo real de Slurp con el mismo código de salida, geometría inválida, error y salida vacía de Grim, directorio no disponible, fallos de escritura al reservar y al escribir datos parciales, fallo de copia, fallo y ausencia de notificador, colisión con archivo y enlace, dependencias críticas ausentes y capturas sucesivas en el mismo segundo.

Las pruebas usan HOME y PATH aislados, comandos gráficos simulados y una fecha fija. Los bytes simulados verifican la transferencia y el ciclo de vida del archivo. La codificación PNG real, los protocolos Wayland y la entrega D-Bus requieren la prueba gráfica.

## Instalación propuesta

Ejecutar solo tras autorización. El bloque exige que el script activo sea regular, pertenezca al usuario, sea ejecutable y conserve el contenido de la línea base auditada. El respaldo se crea en HOME con acceso privado. El candidato se obtiene de la rama local, se valida y se renombra dentro del directorio de destino.

```bash
(
    set -euo pipefail
    umask 077
    repo="$HOME/carbon"
    active="$HOME/.local/bin/save-screenshot.sh"
    tracked=dotfiles/.local/bin/save-screenshot.sh
    baseline=$(git -C "$repo" rev-parse "da996ea:$tracked")
    [[ -f $active && ! -L $active && -O $active && -x $active ]]
    test "$(git -C "$repo" hash-object -- "$active")" = "$baseline"

    backup=$(mktemp -d -- "$HOME/carbon-screenshot-backup.XXXXXXXX")
    cp -p -- "$active" "$backup/save-screenshot.sh"
    (cd "$backup" && sha256sum save-screenshot.sh > SHA256SUMS && sha256sum -c SHA256SUMS)
    cmp -- "$active" "$backup/save-screenshot.sh"
    printf 'Respaldo: %s\n' "$backup"

    candidate=$(mktemp -- "${active%/*}/.save-screenshot.XXXXXXXX")
    trap 'rm -f -- "$candidate"' EXIT
    git -C "$repo" show "feature/carbon-003-screenshots:$tracked" > "$candidate"
    bash -n "$candidate"
    chmod --reference="$active" -- "$candidate"
    git -C "$repo" hash-object -- "$candidate" > "$backup/installed.git-blob"
    test ! -L "$active"
    cmp -- "$active" "$backup/save-screenshot.sh"
    mv -T -- "$candidate" "$active"
)
```

En Hyprland, presionar Print, seleccionar una región y abrir el PNG guardado. Pegar en una aplicación compatible con imágenes y comprobar la notificación. Repetir Print y pulsar Escape. Confirmar que el directorio y el portapapeles no cambiaron y que no hubo aviso.

## Rollback

Sustituir `RUTA_DEL_RESPALDO` por la ruta impresa durante la instalación. Se verifica el respaldo y que el script activo siga siendo el instalado. Si hay cambios posteriores, conservarlos y revisar antes de restaurar.

```bash
(
    set -euo pipefail
    umask 077
    backup=RUTA_DEL_RESPALDO
    repo="$HOME/carbon"
    active="$HOME/.local/bin/save-screenshot.sh"
    (cd "$backup" && sha256sum -c SHA256SUMS)
    [[ -f $active && ! -L $active && -O $active ]]
    test "$(git -C "$repo" hash-object -- "$active")" = "$(cat "$backup/installed.git-blob")"
    candidate=$(mktemp -- "${active%/*}/.save-screenshot.XXXXXXXX")
    trap 'rm -f -- "$candidate"' EXIT
    cp -p -- "$backup/save-screenshot.sh" "$candidate"
    test ! -L "$active"
    test "$(git -C "$repo" hash-object -- "$active")" = "$(cat "$backup/installed.git-blob")"
    mv -T -- "$candidate" "$active"
    cmp -- "$backup/save-screenshot.sh" "$active"
)
```

Print ejecuta el archivo por su ruta. El reemplazo o la restauración del script no requieren recargar Hyprland.
