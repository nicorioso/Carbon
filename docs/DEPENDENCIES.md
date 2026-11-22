# Dependencias

Inventario de referencia para reproducir la sesión auditada. Las versiones instaladas y los mecanismos efectivos observables se registran en la [auditoría](AUDIT.md).

| Clase | Dependencias y alcance |
|---|---|
| Núcleo del escritorio | Arch Linux, systemd y logind, Hyprland con API Lua compatible con 0.57.2, Wayland, Hyprlock, Hypridle, Hyprpaper, Waybar, Wofi, Rofi, Mako, Kitty y Dolphin. SDDM es necesario si se reproduce el inicio gráfico actual. |
| Servicios y módulos | PipeWire, PipeWire Pulse y WirePlumber para audio. NetworkManager y su applet, BlueZ y Blueman para módulos de conectividad. Portal Hyprland y backend GTK para integraciones de escritorio. |
| Integraciones opcionales | pavucontrol, nm-connection-editor y blueman-manager para acciones de Waybar. Brave e imv para MIME. playerctl para MPRIS y brightnessctl para teclas de brillo. hyprshutdown es opcional y la línea base tiene una alternativa por hyprctl. UWSM solo aplica a la entrada de sesión alternativa y no se encontró instalado. |
| Scripts incluidos | Bash, sh, sed y coreutils. Navegación con hyprctl. Captura con grim, slurp y wl-clipboard. Aviso mediante notify-send de libnotify, opcional para guardar y copiar. [Capturas](SCREENSHOTS.md). Menú de energía con Rofi y systemctl. Wrapper de Dolphin con el plugin Qt gtk3 de qt6-base. |
| Portapapeles | cliphist y wl-clipboard para historial y selección. Los datos son locales. |
| AI Usage, integración local | Python con SQLite y zoneinfo, Kitty, stty y OpenCode CLI o SQLite local. Lee metadatos de registros Codex. El código se conserva en el respaldo privado. |
| Visuales | Noto Sans, Font Awesome 7 Free Solid/Brands, Adwaita, Breeze Dark, GTK 3/4 y el esquema KDE Carbon. SDDM Carbon usa Qt 6 Declarative/Controls/Fusion y Qt5Compat.GraphicalEffects, una TTF y dos imágenes privadas. |
| Desarrollo y recuperación | Git, Python estándar para validación y generación futura, Bash, tar y sha256sum. |
| Hardware | `eDP-1` en Hyprpaper, `wlp3s0` y `amdgpu_bl1` en Waybar y `BAT0` observado. Adaptar identificadores por equipo cuando se autorice la portabilidad. |
