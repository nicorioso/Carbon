# CARBON-001 · Auditoría técnica

Fecha de observación local: 22 de noviembre de 2026. Las versiones proceden de la base de paquetes instalada. La actividad se comprobó mediante cgroups con `populated 1`, artefactos de ejecución de systemd y sockets. El espacio de procesos expuesto contiene Codex y sus hijos. Los buses de systemd devolvieron «Operation not permitted» y el IPC de Hyprland no respondió. Los cgroups acreditan actividad en las unidades observadas. Los argumentos y el archivo efectivamente cargado por cada proceso requieren confirmación en la sesión.

## Entorno verificado

- Arch Linux, kernel en ejecución `6.18.64-1-lts`, paquete `linux-lts 6.18.64-1`. Btrfs en HOME y en la ruta de /etc. HOME resuelve a su propio punto de montaje.
- Sesión del entorno: `XDG_CURRENT_DESKTOP=Hyprland`, `XDG_SESSION_TYPE=wayland`. Se observaron sockets Wayland, Hyprland y Hyprpaper.
- Dispositivos visibles: `wlp3s0`, `enp2s0f0`, `amdgpu_bl1`, `BAT0` y conector DRM `eDP-1`.
- Fontconfig reconoce Noto Sans y Font Awesome 7 Free Solid/Brands. El alias `monospace` resuelve a Noto Sans Mono en este entorno.

| Función | Paquetes y versiones instaladas |
|---|---|
| Sesión | hyprland 0.57.2-1, sddm 0.21.0-7, hyprlock 0.9.7-3, hypridle 0.1.8-2, hyprpaper 0.8.5-4, systemd 262.2-1 |
| Escritorio | waybar 0.16.0-2, wofi 1.5.3-1, rofi 2.1.1-1 (también satisface rofi-wayland), mako 1.11.0-1, kitty 0.51.0-1, dolphin 26.08.3-1 |
| Audio | pipewire y pipewire-pulse 1:1.6.11-2, wireplumber 0.5.19-1, pavucontrol 1:6.2-2 |
| Red y Bluetooth | networkmanager 1.58.1-3, network-manager-applet y nm-connection-editor 1.36.0-2, bluez y bluez-utils 5.88-1, blueman 2.4.6-2 |
| Fuentes y aplicaciones | noto-fonts 1:2026.11.01-1, otf-font-awesome 7.3.1-1, breeze-icons 6.32.0-1, imv 5.0.1-3, brave-bin 1:1.100.58-1 |
| Qt y portales | qt6-base 6.12.0-5, qt6-declarative 6.12.0-4, qt6-5compat 6.12.0-1, xdg-desktop-portal 1.22.1-2, backends hyprland 1.5.0-1 y gtk 1.15.3-2 |
| Utilidades y desarrollo | cliphist 1:0.7.0-2, wl-clipboard 1:2.3.0-1, grim 1.5.0-2, slurp 1.5.0-2, brightnessctl 0.5.1-3, playerctl 2.4.1-5, libnotify 0.8.9-1, python 3.14.10-1, lua 5.5.1-1, git 2.56.1-1, opencode 2.3.2-1 |

## Archivos y selección

| Ruta | Función observada o selección configurada |
|---|---|
| `~/.config/hypr/hyprland.lua` | Entrada Lua candidata por su ruta y referencias. Usa la API embebida `hl`. Configura entrada, monitor, reglas, animaciones, temas, atajos y evento `hyprland.start`. El ejemplo `require("myColors")` está comentado. Sin imports activos identificados. |
| `~/.config/hypr/{hyprlock,hypridle,hyprpaper}.conf` | Rutas nativas para bloqueo, inactividad y fondo. Inactividad: bloqueo a 300 s, DPMS a 420 s y suspensión a 900 s. Hyprlock consume dos imágenes en HOME y PAM de sistema. Hyprpaper fija `eDP-1` y carga la misma imagen de fondo. |
| `~/.config/waybar/{config.jsonc,style.css}` | Rutas nativas para el servicio. Módulos configurados: espacios Hyprland, reloj, red, Bluetooth, audio PulseAudio, brillo, batería, AI Usage y tray. CPU y memoria están declarados y quedan fuera de las listas de módulos. |
| `~/.config/wofi/{config,style.css}` | Lanzador `drun` y selector `dmenu` del historial. |
| `~/.config/rofi/power-menu.rasi` | Selección explícita con `-no-config -theme` desde el script de energía. |
| `~/.config/kitty/kitty.conf` | Configuración nativa de Kitty, también invocado por AI Usage. |
| `~/.config/gtk-{3,4}.0/{settings.ini,gtk.css}` | Adwaita oscuro, Noto Sans 10 y CSS con esquinas cuadradas. Los CSS actuales son idénticos byte a byte. El resultado por aplicación queda pendiente. |
| `~/.config/{kdeglobals,dolphinrc,mimeapps.list}` | Paleta y fuentes KDE, selección Carbon para Dolphin y asociaciones Brave/imv. Los .desktop referidos existen. La entrada de Dolphin del sistema invoca directamente Dolphin, mientras el atajo de Hyprland utiliza el wrapper. |
| `~/.local/share/color-schemes/Carbon.colors` | Esquema nombrado por `dolphinrc`. Comparte valores con grupos de colores de `kdeglobals`. |
| `~/.config/mako/`, `~/.local/share/systemd/user/` | Ausentes en las rutas consultadas. Tampoco se encontró `/etc/xdg/mako`. Mako está activo y su unidad se suministra en /usr. Revisar la configuración efectiva solo si se requiere personalizarlo. |
| `~/.config/systemd/user/` | Unidad local de cliphist y enlaces para Hypridle, Hyprpaper y Waybar. |
| `/etc/sddm.conf.d/90-carbon.conf`, `/usr/share/sddm/themes/carbon/` | `Current=carbon`. El valor de proveedor apunta a `/usr/share/sddm/themes` y no se observó un `ThemeDir` alternativo. Metadatos apuntan a `Main.qml`, Qt 6. QML carga QtQuick, Controls/Fusion, Layouts y Qt5Compat.GraphicalEffects, una fuente TTF y dos imágenes relativas. |
| `~/.local/share/sddm/themes/carbon/` | Copia completa, incluidos QML, metadatos, imágenes, fuente y respaldo. Los seis archivos coinciden con los del árbol de sistema. Las imágenes de sistema también coinciden con los originales referenciados bajo `~/imagenes`. |

Los sufijos `.bak`, `.1.bak` y `.bak.~N~` en Hypr, Waybar, Wofi, GTK, KDE y SDDM se clasifican como respaldos por nombre y ausencia de referencias activas observadas. No se determinó qué revisiones conservan valor histórico. Los CSS GTK actuales difieren de sus respaldos. No se identificaron imports activos en los dotfiles inspeccionados fuera de los imports QML y los enlaces o invocaciones descritos.

## Arranque y evidencia de actividad

| Componente | Mecanismo observado | Evidencia |
|---|---|---|
| Waybar, Hypridle, Hyprpaper | Enlaces en `graphical-session.target.wants` a unidades de `/usr/lib/systemd/user`. Las unidades tienen `PartOf` y orden `After` sobre el target. Waybar usa `Requisite`, Hyprpaper `Requires`; Hyprpaper e Hypridle requieren la variable `WAYLAND_DISPLAY` por condición. | Cgroups poblados para las tres unidades. |
| cliphist | `hyprland.start` solicita `systemctl --user start cliphist.service`. `ExecStart=/usr/bin/wl-paste --type text --watch /usr/bin/cliphist store`. La sección Install admite habilitación por target, sin enlace observado. | Cgroup poblado. El flujo configurado registra texto. |
| Mako | Servicio D-Bus en `/usr/share/dbus-1/services/fr.emersion.mako.service`, apunta a `mako.service`. Unidad de tipo dbus, ligada a la sesión gráfica y condicionada a Wayland. | Cgroup poblado. La causa exacta de esta activación queda pendiente. |
| SDDM y sesión | Entradas de sistema para `start-hyprland` y una variante que invoca UWSM. UWSM no apareció instalado ni en PATH. | Cgroup poblado de SDDM. Verificar entrada seleccionada y proceso padre desde la sesión. |
| Red y Bluetooth | NetworkManager y BlueZ de sistema. El Lua invoca `nm-applet --indicator`. El generador XDG creó además entradas para `nm-applet` y `blueman-applet` desde `/etc/xdg/autostart`. | Cgroups de sistema poblados. La ejecución de las entradas generadas y la cantidad de instancias de los applets quedan pendientes. |
| Audio y portales | Enlaces de `/etc/systemd/user` para sockets PipeWire y WirePlumber. Waybar usa el servidor compatible PulseAudio y los atajos usan `wpctl`. Configuración suministrada de portales bajo `/usr/share/xdg-desktop-portal`. | Cgroups poblados de PipeWire, PipeWire Pulse, WirePlumber y portal Hyprland. |

## Dependencias de scripts e integraciones

- `save-screenshot.sh` usa Bash, `mkdir/date`, `slurp`, `grim`, `wl-copy` y `makoctl`. Escribe bajo `~/imagenes/screenshots`, fuera de `XDG_PICTURES_DIR` que señala `~/Pictures`. Envía el PNG al portapapeles.
- `change-workspace-relative.sh` usa Bash, `sed` y `hyprctl`. Extrae el ID de `activeworkspace -j` por expresión regular. El desplazamiento está definido para espacios 1–10 y delega a `hl.dsp.focus`.
- `power-menu.sh` usa sh, Rofi, Font Awesome, systemd/logind y Hyprland. Resuelve el Rasi vía XDG/HOME. `hyprshutdown` es opcional y no apareció en PATH. La salida tiene alternativa por IPC de Hyprland.
- `dolphin-carbon` usa sh, `/usr/bin/dolphin`, `QT_QPA_PLATFORMTHEME=gtk3` y `GTK_THEME=Adwaita:dark`. Existe el plugin `libqgtk3.so` de qt6-base. El esquema Qt efectivo y la reutilización de instancias se verifican en GUI.
- `ai-usage` usa Python estándar (incluidos SQLite y zoneinfo), OpenCode CLI y SQLite de respaldo, registros locales de sesiones Codex, caché privada en HOME, Kitty para el panel y `stty` para la interacción del terminal. Waybar hace sondeo cada 30 s, clic abre panel y clic medio fuerza refresco. La lectura de código confirmó el bloqueo y reemplazo de caché, además de la consulta SQLite en modo de lectura. Se inspeccionó el código sin ejecutar el script ni abrir registros, bases, cachés o credenciales de IA.
- Lua llama también a Kitty, Wofi, Hyprlock, `wpctl`, `brightnessctl`, `playerctl`, `nm-applet`, `systemctl` y la tubería `cliphist | wofi | cliphist | wl-copy`. Hypridle usa `pidof`, `pgrep`, `hyprctl` y `systemctl`. Se verificó la existencia de archivos PAM de Hyprlock y SDDM.
- Waybar usa el IPC de Hyprland y datos de red, sysfs, BlueZ, compatibilidad PulseAudio y bandeja. Los clics apuntan a `nm-connection-editor`, `blueman-manager` y `pavucontrol`, presentes.

## Problemas confirmados

1. `save-screenshot.sh` invoca `makoctl notify`. La ayuda de Mako 1.11.0-1 confirma que ese subcomando no existe. Si la ejecución llega a esa línea, la notificación falla después de escribir y copiar la captura. Se comprobó la interfaz, sin ejecutar una captura.
2. Hay dos rutas configuradas para lanzar `nm-applet`, una en Lua y otra generada por autostart XDG. La duplicación efectiva de procesos sigue sin demostrarse.
3. La apariencia declarada diverge de la paleta aprobada. Kitty incluye acentos naranjas, selección marrón y otros colores ANSI. Waybar emplea azul para estados de AI Usage. Rofi define selección `#454545` y borde `#f5f5f5`. GTK usa `#151515` y `#101010` en fondos; SDDM usa `#606060` en bordes. Son diferencias de configuración, con su efecto visual y las excepciones de producto por decidir.

## Riesgos técnicos e hipótesis

- El nombre de usuario en rutas de Hyprlock/Hyprpaper y en una condición QML vincula Carbon al equipo. Las referencias a `eDP-1`, `wlp3s0` y `amdgpu_bl1` coinciden con el hardware observado, pero requieren parametrización para otro equipo. Las rutas absolutas de `ExecStart` hacia binarios de paquetes son esperables.
- Falla posible de navegación relativa si el JSON cambia de forma, la respuesta IPC está vacía o el ID es especial. Si falla Hyprpaper, Lua permite el fondo de proveedor y conserva el logo habilitado.
- El flujo de portapapeles mantiene datos de usuario fuera de la configuración. Cancelar la selección puede alimentar una entrada vacía a los comandos siguientes. La captura usa nombres con precisión de segundos y una cancelación de Slurp no tiene manejo explícito antes de Grim.
- La copia SDDM del HOME y la de sistema pueden divergir. La entrada UWSM presente en disco requiere un binario que no se encontró. QML, assets y dependencias de autenticación requieren tratamiento independiente por su impacto en el acceso.
- AI Usage depende del formato de datos locales y de OpenCode. El respaldo SQLite agrega contadores acumulados por sesión según la fecha de actualización, por lo que el script marca los resultados como aproximados. El sondeo puede esperar por el bloqueo o por los timeouts de CLI. Su portabilidad y la privacidad del tooltip requieren revisión antes de versionarlo.
- La precedencia real de GTK/Qt y las asociaciones de aplicaciones puede variar por modo de lanzamiento. Mako depende de la activación D-Bus y de la importación del entorno gráfico. No hay otra ruta de arranque de sus daemons identificada en el árbol inspeccionado.

## Verificación manual de solo lectura

Desde una terminal de la sesión, consultar `hyprctl version`, `hyprctl configerrors` y `hyprctl monitors`. Revisar localmente los argumentos de Hyprland y Waybar antes de compartirlos. Usar `systemctl --user show` con propiedades `ActiveState,SubState,MainPID,FragmentPath,DropInPaths` para el target y las unidades, y `systemctl --user list-dependencies graphical-session.target`. Consultar `pgrep -cx nm-applet`, `pgrep -cx blueman-applet` y los daemons relevantes. Usar `loginctl show-session "$XDG_SESSION_ID" -p Type -p Desktop -p Service` si la variable está definida. Revisar localmente el historial de arranque de SDDM y el backend del greeter con acceso autorizado. Evitar exportar journals, entornos completos, listas de portapapeles o estados de aplicaciones privadas. Verificar visualmente fuentes y paleta por aplicación en una sesión de pruebas futura.
