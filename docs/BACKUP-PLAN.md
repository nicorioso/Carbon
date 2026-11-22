# Plan de respaldo y restauración

El punto de recuperación debe preceder a cada tanda de cambios. Guardar el respaldo fuera del repositorio con permisos privados y, cuando corresponda, una segunda copia en almacenamiento cifrado. Validar el manifiesto y ensayar la extracción antes de tocar una ruta activa.

## Alcance

- Respaldar configuraciones nativas de Hyprland, Waybar, Wofi, Rofi, Mako si existe, Kitty, GTK 3/4, KDE, asociaciones, esquema Carbon y futuro directorio Carbon. Incluir los scripts propios modificados y los enlaces de habilitación de usuario. Conservar permisos y enlaces sin desreferenciarlos.
- Guardar por separado los recursos privados que necesitan Hyprlock y Hyprpaper, así como la copia SDDM del HOME si se desea conservar. La imagen de perfil, el fondo y la TTF se guardan como archivos de recuperación privados. Excluir capturas, respaldos históricos salvo selección expresa, el historial de portapapeles y la caché, credenciales, bases y registros de IA.
- Fuera de HOME, el respaldo administrado debe contemplar `/etc/sddm.conf.d/90-carbon.conf` y el tema Carbon de `/usr/share/sddm/themes/carbon/` con archivos, permisos y propietarios. Inventariar por separado PAM de SDDM/Hyprlock, unidades de usuario de proveedor, enlaces de `/etc/systemd/user`, entradas Wayland, autostart y archivos D-Bus/portales. Para archivos de paquete, registrar versiones y propietarios con `pacman -Qo`. Registrar las personalizaciones de sistema que se descubran y requieran recuperación. Mantener la configuración privada de NetworkManager, Bluetooth y PAM fuera del repositorio.
- Un snapshot Btrfs puede ampliar la cobertura. Verificar primero subvolúmenes, montajes, permisos y espacio. HOME y el sistema pueden requerir puntos de recuperación distintos. La creación, restauración y conservación de snapshots requerirán autorización separada.

## Comandos propuestos para el respaldo privado de usuario

Ejemplo para Bash y GNU tar. Elegir una ubicación aprobada para el respaldo. El ejemplo crea un destino único dentro de HOME y usa las rutas observadas. Confirmar cualquier XDG distinto antes de usarlo. La lista incluye imágenes referenciadas; tratar el archivo como privado. El ejemplo conserva la configuración de Dolphin y AI Usage, sin incluir sus datos de ejecución.

```bash
set -euo pipefail
umask 077
backup=$(mktemp -d "$HOME/carbon-backup.XXXXXXXX")
cd "$HOME"
paths=(
  .config/hypr/{hyprland.lua,hyprlock.conf,hypridle.conf,hyprpaper.conf}
  .config/waybar/{config.jsonc,style.css}
  .config/wofi/{config,style.css} .config/rofi/power-menu.rasi
  .config/mako/config .config/kitty/kitty.conf
  .config/gtk-{3,4}.0/{settings.ini,gtk.css}
  .config/{kdeglobals,dolphinrc,mimeapps.list}
  .config/carbon/theme.json
  .config/systemd/user/cliphist.service
  .config/systemd/user/graphical-session.target.wants/{waybar,hypridle,hyprpaper}.service
  .local/bin/{ai-usage,dolphin-carbon,change-workspace-relative.sh,power-menu.sh,save-screenshot.sh}
  .local/share/color-schemes/Carbon.colors
  .local/share/sddm/themes/carbon/{Main.qml,metadata.desktop,NotoSans-Regular.ttf,ado1.jpg,ado-perfil.jpeg}
  imagenes/{wallpapers/ado1.jpg,perfil/ado-perfil.jpeg}
)
# Añadir scripts y archivos nuevos por nombre tras revisar su contenido.
for path in "${paths[@]}"; do
  if [[ -f $path || -L $path ]]; then
    printf '%s\0' "$path" >> "$backup/present.nul"
  else
    printf '%s\0' "$path" >> "$backup/absent.nul"
  fi
done
tar --create --file="$backup/home.tar" --null --verbatim-files-from \
    --no-recursion --files-from="$backup/present.nul"
tar --list --verbose --file="$backup/home.tar" > "$backup/archive.txt"
pacman -Q > "$backup/packages.txt"
(
  cd "$backup"
  sha256sum home.tar > SHA256SUMS
  sha256sum -c SHA256SUMS
)
```

Revisar la lista de archivos, identificar si hay paths que deben respaldarse por separado y transferir el respaldo a su destino cifrado si aplica. Para respaldar el perfil del sistema, un administrador autorizado puede construir un tar aparte con `-C /`, la lista exacta de archivos, propietarios numéricos, permisos, ACL y atributos cuando correspondan. Mantenerlo separado del respaldo de usuario y comprobar su extracción en un entorno de pruebas.

## Restauración

1. Identificar la tanda a revertir. Conservar una copia privada del estado posterior, incluyendo cambios del usuario desde el respaldo.
2. Validar el hash, revisar los miembros del archivo y sus destinos, y extraer únicamente a un directorio privado vacío. Revisar enlaces y sus destinos antes de copiar; los del target gráfico apuntan a unidades de proveedor. Comparar con el manifiesto y con los archivos actuales.

   ```bash
   (cd "$backup" && sha256sum -c SHA256SUMS)
   staging=$(mktemp -d "$backup/restore.XXXXXXXX")
   tar --extract --file="$backup/home.tar" --directory="$staging" \
       --no-same-owner --same-permissions
   ```

3. Restaurar solo destinos aprobados. Copiar cada archivo o enlace desde staging a un temporal del mismo directorio de destino, conservar modo, verificarlo y renombrarlo al destino. Si el destino figuraba como ausente, mover el candidato a cuarentena y registrar el cambio. Ante conflicto con una edición posterior, detener ese destino para resolución explícita.
4. Comparar archivos restaurados con staging y revisar la presencia o ausencia esperada. Validar parsers. La recarga o reactivación de servicios y la prueba de la sesión se autorizan por separado.
5. Para SDDM, recuperar QML, metadatos, recursos y selección como conjunto desde un entorno de mantenimiento autorizado. Verificar propietarios y permisos y mantener un acceso alternativo disponible. Probar el inicio en un entorno controlado antes de depender del greeter restaurado.

Estos comandos se proponen para una etapa posterior. En CARBON-001 se creó únicamente la documentación.
