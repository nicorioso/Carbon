# Evidencia de CARBON-002

## Sesión

- La base local de paquetes registra Hyprland 0.57.2-1. El entorno consultado declara `wayland`, `Hyprland` y `wayland-1`. Se observó el socket Wayland y el cgroup de SDDM.
- Los cgroups de Waybar, Hyprpaper, Hypridle, Mako y cliphist devolvieron `populated 1`. Los enlaces de Waybar, Hyprpaper y Hypridle apuntan a unidades suministradas en /usr. La activación D-Bus configurada de Mako referencia su unidad. Estos datos acreditan actividad de las unidades y las rutas configuradas.
- El IPC de Hyprland devolvió código 2. Los buses de systemd y logind denegaron conexión. El listado de procesos pertenece al sandbox, así que los ceros de pgrep se descartaron. Las unidades XDG generadas de ambos applets estaban presentes. La coexistencia de rutas de arranque de nm-applet sigue siendo solo una condición para investigar.

Comandos mínimos pendientes, desde una terminal gráfica. Los argumentos se revisan localmente antes de compartir resultados.

| Comprobación | Comando |
|---|---|
| Versión, errores y monitor activo | `hyprctl version`, `hyprctl configerrors`, `hyprctl monitors` |
| Origen de la sesión | `loginctl show-session "${XDG_SESSION_ID:-self}" -p Type -p Desktop -p Service -p Leader` |
| Unidades efectivas y PID | `systemctl --user show waybar hyprpaper hypridle mako cliphist graphical-session.target -p Id -p ActiveState -p MainPID -p FragmentPath -p DropInPaths` |
| Variables gráficas del gestor | `systemctl --user show-environment \| grep -E '^(WAYLAND_DISPLAY\|XDG_SESSION_TYPE\|XDG_CURRENT_DESKTOP)='` |
| Recuento de applets | `pgrep -cx nm-applet; pgrep -cx blueman-applet` |
| Padres y argumentos | `ps -C Hyprland,waybar,hyprpaper,hypridle,mako,nm-applet,blueman-applet -o pid,ppid,args` |
| Causa de activación de Mako | `journalctl --user -b -u mako.service -n 15 --no-pager` para revisión local; el journal puede no conservar el disparador. |

## Importación y privacidad

Se revisaron las configuraciones y scripts como texto, con búsqueda de asignaciones sensibles y referencias absolutas. Se conservaron las rutas personales de recursos dentro de los archivos autorizados. El índice contiene 22 archivos regulares de dotfiles. El código de AI Usage tiene dependencias sobre registros Codex, SQLite de OpenCode y caché local, y construye tooltips a partir de datos operativos. Su código se reservó para recuperación privada. Sus datos de ejecución quedaron fuera de ambos conjuntos. Se reservó también `dolphinrc` para recuperación privada porque contiene estado de vista. La copia del tema SDDM del usuario y sus recursos binarios están solo en el respaldo. La copia de sistema exige un respaldo administrado aparte.

## Respaldo y restauración ensayada

- Archivo tar privado y manifiesto protegidos con modo 0600 bajo un directorio 0700. SHA-256 verificado para ambos. El manifiesto registra los modos y hashes de archivos y el destino de cada enlace.
- Se verificaron 34 miembros exactos (31 archivos y 3 enlaces). Dos rutas estaban ausentes: `.config/mako/config` y `.config/carbon/theme.json`.
- Se rechazaron caminos absolutos para miembros, segmentos de ascenso, tipos inesperados y miembros debajo de otros miembros. Los archivos regulares se extrajeron con el filtro de datos de Python. Después se recrearon los enlaces exactos aprobados hacia las unidades de paquete en `/usr/lib/systemd/user`. Esos enlaces apuntan fuera de staging por diseño y jamás se siguieron durante la extracción ni la comparación.
- El árbol aislado coincidió con el conjunto permitido, sus directorios implícitos, los hashes, los modos y los destinos de enlaces. Los mismos atributos coincidieron entre las dos lecturas del HOME. Quedan pendientes las pruebas de recarga y de recuperación de SDDM, que requieren autorización independiente.
