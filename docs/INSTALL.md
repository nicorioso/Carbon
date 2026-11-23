# Instalación futura

La línea base es un árbol de referencia para Arch Linux con una sesión Wayland e Hyprland con API Lua. Para preparar un despliegue, comprobar versiones, herramientas y dispositivos contra el inventario. Mantener un acceso alternativo y un respaldo de la tanda antes de probar componentes de la sesión. [Dependencias](DEPENDENCIES.md) · [Respaldo](BACKUP-PLAN.md)

## Correspondencia de dotfiles

Cada ruta siguiente tiene origen `~/RUTA`, copia en `dotfiles/RUTA` y el mismo destino nativo `~/RUTA` en una futura instalación con XDG por defecto.

```text
.config/hypr/hyprland.lua
.config/hypr/hyprlock.conf
.config/hypr/hypridle.conf
.config/hypr/hyprpaper.conf
.config/waybar/config.jsonc
.config/waybar/style.css
.config/wofi/config
.config/wofi/style.css
.config/rofi/power-menu.rasi
.config/kitty/kitty.conf
.config/gtk-3.0/settings.ini
.config/gtk-3.0/gtk.css
.config/gtk-4.0/settings.ini
.config/gtk-4.0/gtk.css
.config/kdeglobals
.config/mimeapps.list
.config/systemd/user/cliphist.service
.local/bin/change-workspace-relative.sh
.local/bin/cliphist-menu.sh
.local/bin/dolphin-carbon
.local/bin/power-menu.sh
.local/bin/save-screenshot.sh
.local/share/color-schemes/Carbon.colors
```

Las referencias absolutas a imágenes personales se conservan literalmente en Hyprlock y Hyprpaper, con dos referencias en el primero y una en el segundo. Resolver su disponibilidad antes de desplegar en otra cuenta. Revisar también `eDP-1`, `wlp3s0` y `amdgpu_bl1`. La disponibilidad de `ai-usage` es un requisito local para su atajo y módulo originales. Los archivos del repositorio conservan esas invocaciones. Gestionar aparte la configuración de Dolphin y los enlaces de habilitación de usuario conservados en el respaldo.

## Procedimiento por componente

1. Confirmar XDG, cerrar la lista de destinos y verificar dependencias, archivos importados y recursos locales. Validar las copias con parsers y comprobar el diff en staging.
2. Crear un respaldo privado y verificar restauración, permisos y enlaces. Si cambia un destino entre el respaldo y la aplicación, revisar la edición antes de seguir.
3. Con autorización de despliegue, instalar por tandas desde staging en las rutas nativas, conservando modos y tipos. Empezar por un consumidor de bajo impacto. Los enlaces systemd y la configuración de SDDM tienen tratamientos separados.
4. Validar el arranque y la interacción de cada componente con la sesión de pruebas. Para Hyprland, revisar `hyprctl configerrors`. Para Waybar, validar JSONC y módulos. Para scripts, comprobar sintaxis y ejercitar los flujos en un entorno aislado. Confirmar recursos, fuentes y resolución de rutas.
5. Ante un fallo, restaurar los destinos afectados desde el staging del respaldo y comparar contenidos y permisos. Pasar a cuarentena los destinos que antes estaban ausentes. Aprobar por separado cualquier recarga o prueba de un inicio de sesión real.

Para el script de capturas, consultar el [procedimiento específico de instalación, prueba gráfica y rollback](SCREENSHOTS.md).

Para los scripts e interacciones de CARBON-003-C, consultar [el orden de instalación, respaldos individuales, rollback y pruebas manuales](SCRIPTS.md).

## Waybar Carbon Segmented

Carbon Segmented es la variante oficial aprobada. Desde la raíz del repositorio, generar sus archivos en staging:

```bash
stage=$(mktemp -d /tmp/carbon-waybar-segmented.XXXXXXXX)
python -B prototypes/waybar/build.py --output "$stage/candidates"
```

Los candidatos para los destinos nativos `~/.config/waybar/style.css` y `~/.config/waybar/config.jsonc` son `segmented.css` y `segmented.jsonc`, respectivamente. Los archivos Waybar de `dotfiles/` sirven como referencias del motor. Para un despliegue autorizado, verificar las rutas activas, respaldar ambos destinos y consultar los hashes, la espera de arranque y la recuperación de Balanced Refinada. [Procedimiento de Waybar](WAYBAR-REDESIGN.md#carbon-005-a3--activación-controlada-de-carbon-segmented)

## Wofi Carbon Segmented

Carbon Launcher Segmented es la variante aprobada para `drun` y `dmenu`, con un tamaño declarado de 540 × 396 px. Desde la raíz del repositorio, generar el par en staging:

```bash
stage=$(mktemp -d /tmp/carbon-wofi-segmented.XXXXXXXX)
python -B dotfiles/.config/carbon/scripts/generate-theme.py \
  --input dotfiles/.config/carbon/theme.json --target wofi-segmented \
  --output "$stage/candidates"
```

Los candidatos `config` y `style.css` corresponden a `~/.config/wofi/` con el XDG verificado. La copia de `dotfiles/` conserva la línea base. Para instalar en otra sesión, verificar los destinos, respaldar ambos archivos y sustituirlos con Wofi cerrado. [Despliegue y restauración de Wofi](WOFi-REDESIGN.md#carbon-005-b2--despliegue-de-carbon-launcher-segmented)

## Rofi Carbon Power Grid

Carbon Power Grid es el tema aprobado del menú de energía. Desde la raíz del repositorio, generar y validar el Rasi en staging:

```bash
stage=$(mktemp -d /tmp/carbon-power-grid.XXXXXXXX)
python -B dotfiles/.config/carbon/scripts/generate-theme.py \
  --input dotfiles/.config/carbon/theme.json --target power-grid \
  --output "$stage/candidate"
rofi -no-config -rasi-validate "$stage/candidate/power-menu.rasi"
```

El destino habitual es `~/.config/rofi/power-menu.rasi`. El script usa `XDG_CONFIG_HOME` cuando está definido. En un despliegue autorizado, verificar el destino efectivo, respaldar el original y sustituir solo el Rasi con Rofi cerrado. Para validar el tema, usar el lanzador seguro con salida de índices. [Validación y rollback de Power Grid](POWER-MENU-REDESIGN.md#carbon-005-c2--validación-nativa-y-despliegue-de-grid)

## Mako Carbon Notifications Compact

Compact es la variante oficial. Desde la raíz del repositorio, generar su configuración en staging:

```bash
stage=$(mktemp -d /tmp/carbon-mako-compact.XXXXXXXX)
python -B dotfiles/.config/carbon/scripts/generate-theme.py \
  --input dotfiles/.config/carbon/theme.json --target mako-compact \
  --output "$stage/candidate"
```

El destino de esta instalación es `~/.config/mako/config`. Comprobar la precedencia de `~/.mako/config` y el XDG del daemon antes de un despliegue autorizado. Registrar la presencia o ausencia previa, instalar por renombre y aplicar una recarga con la cola vacía. El prototipo HTML permanece en staging. Kitty conserva su configuración independiente. [Despliegue, validación y rollback de Mako](MAKO-REDESIGN.md#carbon-005-d2--despliegue-de-carbon-notifications-compact)

## Preferencia GTK Dark

Para reproducir la apariencia aprobada en una instalación nueva, aplicar la preferencia en una terminal de la sesión gráfica Wayland del usuario. El esquema `org.gnome.desktop.interface` debe estar disponible y la clave debe ser escribible. El frontend `xdg-desktop-portal` debe responder mediante el backend GTK de Settings. La preferencia vive en GSettings de usuario y se aplica aparte de la copia de dotfiles. Los CSS, las fuentes, los iconos y las configuraciones de aplicaciones se conservan. [Diagnóstico, validación y compatibilidad](GTK4-CONTRAST-FIX.md#carbon-006-a--cierre-técnico)

Antes de aplicar, comprobar que la sesión y el portal son los previstos. Guardar en un directorio privado el override explícito, el valor efectivo y la respuesta del portal. Un archivo `explicit` vacío representa una clave ausente. Conservar la ruta impresa para recuperación.

```bash
schema=org.gnome.desktop.interface
key=color-scheme
path=/org/gnome/desktop/interface/color-scheme

portal_color() {
    busctl --user --auto-start=no call org.freedesktop.portal.Desktop \
        /org/freedesktop/portal/desktop org.freedesktop.portal.Settings Read ss \
        org.freedesktop.appearance color-scheme
}

test "$(gsettings writable "$schema" "$key")" = true &&
    backup=$(mktemp -d "$HOME/carbon-gtk-dark-before.XXXXXXXX") &&
    (umask 077
     dconf read "$path" > "$backup/explicit" &&
         gsettings get "$schema" "$key" > "$backup/effective" &&
         portal_color > "$backup/portal") &&
    printf '%s\n' "$backup"
```

Tras revisar el respaldo, aplicar el único ajuste y comprobar los resultados. La lectura de GSettings debe devolver `'prefer-dark'` y la del portal debe terminar en `u 1`. Comprobar la cabecera, el título y los controles en GTK 4 y libadwaita. Si la señal tarda en propagarse, volver a consultar antes de decidir el rollback.

```bash
gsettings set org.gnome.desktop.interface color-scheme 'prefer-dark'
gsettings get org.gnome.desktop.interface color-scheme
portal_color
```

Para revertir, comprobar que el backup corresponde a esa instalación. Revisar también que el override actual siga siendo `'prefer-dark'`. Si la clave tenía un valor explícito, restaurar el GVariant guardado. Si la clave estaba ausente, retirar el override mediante `gsettings reset`.

```bash
(
    set -e -o pipefail
    test -r "$backup/explicit" && test -r "$backup/effective" &&
        test -r "$backup/portal" || exit 1
    test "$(dconf read "$path")" = "'prefer-dark'"
    test "$(gsettings get "$schema" "$key")" = "'prefer-dark'"
    if test -s "$backup/explicit"; then
        gsettings set "$schema" "$key" "$(cat "$backup/explicit")"
    else
        gsettings reset "$schema" "$key"
    fi
    dconf read "$path" | cmp "$backup/explicit" -
    gsettings get "$schema" "$key" | cmp "$backup/effective" -
    portal_color | cmp "$backup/portal" -
)
```

Verificar por separado el override, la preferencia publicada y la apariencia de ventanas abiertas y nuevas. El portal puede tardar en publicar el valor anterior. Cualquier reinicio requiere autorización independiente. La guía aplica la preferencia de forma manual por usuario. [Rollback ensayado](GTK4-CONTRAST-FIX.md#despliegue-mínimo-y-recuperación)
