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
