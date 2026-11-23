# CARBON-003-C · Scripts e interacciones

## Comportamiento de la línea base

Los tres scripts existentes y el Lua activo coincidían byte a byte con `fd260b0`. La lectura de IPC confirmó una respuesta JSON de Hyprland con `id` en la raíz y `type` normal para un escritorio numerado. No se ejercieron acciones reales.

| Flujo | Comportamiento que se conserva | Fallos, riesgos y límites observados |
|---|---|---|
| Escritorios | Ctrl+Alt+izquierda y derecha recorren 1–10 con vuelta en ambos extremos. El despacho Lua enfoca un número directamente, incluso si el escritorio está vacío. | Con mocks, la versión anterior despachó hacia 1 al recibir salida vacía o el ID especial negativo. También aceptó un fragmento con `id` dentro de texto que no era JSON válido. Una salida IPC con código distinto de cero ya abortaba mediante `pipefail`. |
| Historial | Super+Shift+V presenta el listado de cliphist en Wofi y copia el contenido seleccionado. | Un mock de Escape reprodujo que la tubería anterior ejecuta `decode` y `wl-copy` con entrada vacía y puede devolver éxito del último tramo. El efecto sobre el portapapeles real no se reprodujo. Wofi usa estado 1 al cancelar, que también puede indicar un fallo. [Código de salida de Wofi](https://raw.githubusercontent.com/SimplyCEO/wofi/master/src/wofi.c#L1240) |
| Energía | Super+Escape abre Rofi con las cuatro filas e índices 0–3. Escape sale en silencio. Apagado, reinicio y suspensión delegan a systemctl. Cerrar sesión usa hyprshutdown si existe y, en su ausencia, el despacho Lua de salida. | Los índices desconocidos ya quedaban sin acción. Faltaban diagnósticos explícitos para dependencias y selección inesperada. El equipo no tiene hyprshutdown en PATH. No se verificaron acciones reales. |
| Dolphin | Super+Shift+F ejecuta el wrapper, que exporta `QT_QPA_PLATFORMTHEME=gtk3` y `GTK_THEME=Adwaita:dark` y pasa los argumentos a Dolphin con `exec`. | El binario y el plugin Qt están presentes. `exec` conserva argumentos y código de salida. Si Dolphin ya está abierto, su reutilización podría conservar el entorno anterior. La apariencia de esa segunda apertura requiere verificación gráfica. |

## Cambio mínimo en Hyprland

El despliegue de `7af124e` sustituyó únicamente el comando asociado al historial. Se conserva Super+Shift+V y se delega el control de errores al auxiliar.

```diff
-hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd("cliphist list | wofi --dmenu | cliphist decode | wl-copy"))
+hl.bind(mainMod .. " + SHIFT + V", hl.dsp.exec_cmd('"$HOME/.local/bin/cliphist-menu.sh"'))
```

## Cambios implementados

- **Escritorios.** Python 3, ya instalado, analiza el JSON con su biblioteca estándar. Hace falta un parser para distinguir el entero de nivel raíz de cadenas, booleanos, valores anidados y respuestas malformadas. Se conservan los argumentos del script y el despacho `hyprctl dispatch 'hl.dsp.focus({ workspace = N })'`. El número de destino sigue siendo absoluto y no se filtra por ocupación. Se valida el estado IPC y la confirmación `ok`. [Interfaz Lua de hyprctl](https://wiki.hypr.land/configuring/core/advanced-configuration/using-hyprctl/#dispatch)
- **Historial.** Se comprueba el listado y se acepta solo una fila presentada por Wofi. Si Wofi sale con 1 y stdout vacío, se omiten decodificación y copia. Los diagnósticos stderr de Wofi permanecen visibles. Un fallo silencioso con ese mismo estado es indistinguible de Escape. La decodificación completa se escribe en un temporal privado y se valida antes de iniciar `wl-copy`. Se preservan bytes binarios y saltos de línea. El temporal se retira al salir y al recibir HUP, INT o TERM; SIGKILL no permite limpieza. El historial queda a cargo del servicio existente. [Formato de selección de cliphist](https://github.com/sentriz/cliphist/blob/v0.7.0/cliphist.go#L198-L243)
- **Energía.** Se comprueba Rofi y el tema, se validan los índices y se verifica el ejecutable de la acción elegida. Se conservan las filas, los argumentos de Rofi y las cuatro acciones. Una salida 1 sin selección se trata como cancelación, con stderr disponible si Rofi emitió un diagnóstico.
- **Dolphin.** Se conserva el wrapper. El ejecutable absoluto evita resolver otro por PATH, y la prueba de ausencia verifica el estado 127 de `exec`.

## Estado al cierre

En Hyprland 0.57.2, `hyprctl configerrors` salió sin errores y `misc:disable_autoreload=false` ya estaba vigente al comenzar el cierre. Se comprobó en memoria que Super+Shift+V apunta al auxiliar aprobado. La inspección leyó la referencia Lua del atajo sin invocarlo. El cierre conservó la configuración cargada y el valor efectivo de la opción. [Interfaz de consulta de Hyprland](https://wiki.hypr.land/configuring/core/advanced-configuration/using-hyprctl/)

Los archivos activos coinciden byte a byte con `7af124e`.

| Destino relativo a HOME | Modo | SHA-256 |
|---|---|---|
| `.config/hypr/hyprland.lua` | `0644` | `3601f10a7d829e69bae247ade79d25452a1a96a10eef719b99cbaf1fc027c26d` |
| `.local/bin/change-workspace-relative.sh` | `0755` | `ae942e45dc81b2693b43fd6aa9ada9f5a542a5ebb27e3b2128c0fbff5772e545` |
| `.local/bin/cliphist-menu.sh` | `0755` | `e3253abce6bb2eefca89516d848e4fd6e1efa06dea181300e1ad1c74958cc744` |
| `.local/bin/power-menu.sh` | `0755` | `9a4b62549e647cd1a8756a40418848312915c85ccd6f9461444802d615699e7a` |

Los cuatro respaldos se conservan fuera de Git en `~/carbon-003c-backup.13aC3jD1/`. Sus manifiestos SHA-256 pasaron la verificación. Consultar `RECUPERACION.md` dentro del respaldo para los comandos de TTY. Para revertir el despliegue, restaurar primero el Lua y confirmar que Hyprland cargó el atajo anterior. Después devolver los scripts existentes a su versión original y mover el auxiliar de historial a cuarentena, porque antes estaba ausente. [Rollback por archivo](#rollback-por-archivo)

## Pruebas de repositorio

```bash
cd ~/carbon
bash -n dotfiles/.local/bin/change-workspace-relative.sh
bash -n dotfiles/.local/bin/cliphist-menu.sh
sh -n dotfiles/.local/bin/power-menu.sh
sh -n dotfiles/.local/bin/dolphin-carbon
luac -p dotfiles/.config/hypr/hyprland.lua
python tests/scripts/test_interactions.py -v
python tests/screenshots/test_screenshots.py
```

Las 16 pruebas de interacciones y las 15 de capturas pasaron. Los mocks cubren navegación válida y límites, entradas inválidas y especiales, fallos de IPC y despacho, selección/cancelación y fallos en el historial, las cuatro acciones de energía y dependencias ausentes. El wrapper Dolphin se prueba en una copia temporal que redirige exclusivamente su ruta de ejecutable al mock, con argumentos con espacios, código de salida y ejecutable ausente. El PATH de pruebas contiene solo mocks y las utilidades explícitas. Las pruebas no cubren el comportamiento de ventanas, el renderizado Qt, el portapapeles Wayland o la carga real de Lua. `luac -p` valida sintaxis, y la lectura de IPC comprobó el formato de Hyprland 0.57.2. ShellCheck no estaba disponible.

## Procedimiento de instalación por archivo

Los archivos del despliegue fueron `.local/bin/change-workspace-relative.sh`, `.local/bin/power-menu.sh`, `.local/bin/cliphist-menu.sh` y `.config/hypr/hyprland.lua`, con origen en `dotfiles/`. Instalar el auxiliar antes de introducir la referencia en Lua. Los originales existentes deben coincidir con `fd260b0`; la ruta del auxiliar debe estar ausente. El entorno observado usa `~/.config` para Hyprland. Si otro perfil cambia el origen efectivo del Lua, revisar el destino antes de usar estos comandos. Dolphin, el Rasi y la unidad de cliphist quedan fuera de la instalación.

Tras autorización, definir esta función en Bash y llamarla una vez por archivo, pasando el hash del commit aprobado y la ruta relativa. Prepara un respaldo individual con SHA-256 y conserva los modos. Anotar cada directorio impreso para un posible rollback.

```bash
carbon_install_script() (
    set -euo pipefail
    umask 077
    local ref="$1" file="$2" repo="$HOME/carbon"
    local target="$HOME/$file" backup candidate
    case "$file" in
        .local/bin/change-workspace-relative.sh|.local/bin/power-menu.sh|.local/bin/cliphist-menu.sh|.config/hypr/hyprland.lua) ;;
        *) return 2 ;;
    esac
    ref=$(git -C "$repo" rev-parse --verify "${ref}^{commit}")
    if [[ $file == .local/bin/cliphist-menu.sh ]]; then
        [[ ! -e $target && ! -L $target ]]
    else
        [[ -f $target && ! -L $target && -O $target ]]
        cmp -- "$target" <(git -C "$repo" show "fd260b0:dotfiles/$file")
    fi

    backup=$(mktemp -d -- "$HOME/carbon-script-backup.XXXXXXXX")
    printf '%s\n' "$file" > "$backup/target"
    if [[ -e $target ]]; then
        cp -p -- "$target" "$backup/original"
        (cd "$backup" && sha256sum original > SHA256SUMS && sha256sum -c SHA256SUMS)
    else
        touch "$backup/absent"
    fi
    printf 'Respaldo de %s: %s\n' "$file" "$backup"
    candidate=$(mktemp -- "${target%/*}/.carbon-candidate.XXXXXXXX")
    trap 'if [[ -e $candidate ]]; then unlink -- "$candidate"; fi' EXIT
    git -C "$repo" show "$ref:dotfiles/$file" > "$candidate"
    case "$file" in
        *.lua) luac -p "$candidate" ;;
        */power-menu.sh) sh -n "$candidate" ;;
        *) bash -n "$candidate" ;;
    esac
    git -C "$repo" hash-object -- "$candidate" > "$backup/installed.git-blob"
    if [[ -f $backup/absent ]]; then
        chmod 755 "$candidate"
        ln -T -- "$candidate" "$target"
    else
        [[ -f $target && ! -L $target && -O $target ]]
        cmp -- "$target" "$backup/original"
        chmod --reference="$backup/original" -- "$candidate"
        mv -T -- "$candidate" "$target"
    fi
    [[ $(git -C "$repo" hash-object -- "$target") == "$(cat "$backup/installed.git-blob")" ]]
)
```

Orden de llamadas tras autorización, con `COMMIT_APROBADO` sustituido por el hash revisado.

```bash
(
    set -e
    carbon_install_script COMMIT_APROBADO .local/bin/change-workspace-relative.sh
    carbon_install_script COMMIT_APROBADO .local/bin/power-menu.sh
    carbon_install_script COMMIT_APROBADO .local/bin/cliphist-menu.sh
    carbon_install_script COMMIT_APROBADO .config/hypr/hyprland.lua
)
```

Los scripts se leen en cada invocación. Solo el cambio Lua requiere que Hyprland cargue de nuevo su configuración, lo que puede ocurrir por recarga automática. Comprobar `hyprctl configerrors` tras la carga. Si hace falta un `hyprctl reload` explícito, realizarlo únicamente con la autorización del despliegue. Si se interrumpe la tanda, usar los directorios impresos para revertir los archivos ya aplicados.

## Rollback por archivo

Usar el directorio individual como argumento. Revertir primero el Lua y confirmar que se cargó el atajo anterior antes de retirar el auxiliar. Si el archivo activo difiere de la versión instalada, el comando se detiene para que se revise esa edición.

```bash
carbon_restore_script() (
    set -euo pipefail
    umask 077
    local backup="$1" file target candidate
    file=$(cat "$backup/target")
    case "$file" in
        .local/bin/change-workspace-relative.sh|.local/bin/power-menu.sh|.local/bin/cliphist-menu.sh|.config/hypr/hyprland.lua) ;;
        *) return 2 ;;
    esac
    target="$HOME/$file"
    [[ -f $target && ! -L $target && -O $target ]]
    [[ $(git -C "$HOME/carbon" hash-object -- "$target") == "$(cat "$backup/installed.git-blob")" ]]
    if [[ $file == .local/bin/cliphist-menu.sh && -f $backup/absent ]]; then
        local quarantine
        quarantine=$(mktemp -d -- "${target%/*}/.carbon-quarantine.XXXXXXXX")
        mv -T -- "$target" "$quarantine/cliphist-menu.sh"
        [[ ! -e $target && ! -L $target ]]
        return
    fi
    (cd "$backup" && sha256sum -c SHA256SUMS)
    candidate=$(mktemp -- "${target%/*}/.carbon-restore.XXXXXXXX")
    trap 'if [[ -e $candidate ]]; then unlink -- "$candidate"; fi' EXIT
    cp -p -- "$backup/original" "$candidate"
    cmp -- "$candidate" "$backup/original"
    [[ -f $target && ! -L $target ]]
    [[ $(git -C "$HOME/carbon" hash-object -- "$target") == "$(cat "$backup/installed.git-blob")" ]]
    mv -T -- "$candidate" "$target"
    cmp -- "$target" "$backup/original"
    [[ $(stat -c %a -- "$target") == "$(stat -c %a -- "$backup/original")" ]]
)
carbon_restore_script RUTA_DEL_RESPALDO_INDIVIDUAL
```

Se ensayaron los comandos de instalación y rollback de los cuatro destinos en un HOME temporal. La prueba comprobó contenido, modos de los archivos restaurados y cuarentena del auxiliar que estaba ausente.

## Guía de regresión manual

- **Escritorios:** probar ambas direcciones, 10→1 y 1→10, y entrar en un escritorio vacío. Si el IPC devuelve un ID especial, confirmar que no se emite otro despacho.
- **Historial:** preparar dos textos de prueba, recuperar uno con Super+Shift+V y comprobar su pegado. Repetir y pulsar Escape con el otro texto en el portapapeles. Comprobar que su contenido permanece y que la selección sigue usando Wofi.
- **Energía:** abrir con Super+Escape, verificar las cuatro filas y cancelar. Las cuatro acciones ya se verificaron con mocks. Una prueba real de energía o cierre de sesión requiere una sesión de pruebas y autorización específica.
- **Dolphin:** abrir con Super+Shift+F con y sin una instancia existente, verificar la apariencia Carbon y abrir una ruta con espacios. Mantener cualquier prueba visual dentro de la sesión del usuario.
