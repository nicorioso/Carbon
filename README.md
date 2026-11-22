# Carbon 2.0

Carbon personaliza Arch Linux y Hyprland con una identidad monocromática inspirada en Omarchy. Busca funcionalidad, estabilidad y rendimiento con esquinas cuadradas, contraste legible, animaciones discretas y transparencia moderada.

| Rol | Color |
|---|---|
| Fondo | `#121212` |
| Superficies | `#1b1b1b` |
| Superficies elevadas | `#252525` |
| Bordes | `#333333` |
| Selección | `#d6d6d6` |
| Texto principal | `#f5f5f5` |

Noto Sans es la fuente principal y Font Awesome 7 se usa para iconos. El stack auditado combina Hyprland Lua sobre Wayland, systemd, SDDM, Hyprlock, Hypridle, Hyprpaper, Waybar, Wofi, Rofi, Mako, Kitty, Dolphin, PipeWire/WirePlumber, NetworkManager y BlueZ/Blueman. [Inventario de versiones y dependencias](docs/AUDIT.md).

## Repositorio local propuesto

```text
carbon/
  README.md
  CHANGELOG.md
  .gitignore
  docs/
    AUDIT.md
    ARCHITECTURE.md
    ROADMAP.md
    BACKUP-PLAN.md
    INSTALL.md
    DEPENDENCIES.md
    decisions/
  dotfiles/
    .config/
      carbon/
        theme.json
        scripts/
      hypr/
      waybar/
      wofi/
      rofi/
      mako/
      kitty/
      gtk-3.0/
      gtk-4.0/
      systemd/user/
    .local/bin/
    .local/share/color-schemes/
  templates/
  profiles/
    example.json
```

`dotfiles/` refleja destinos de usuario para los archivos seleccionados. `templates/` aloja fuentes del generador. `docs/INSTALL.md` describirá prerequisitos, copia por componente, verificación y rollback. `docs/DEPENDENCIES.md` distinguirá dependencias obligatorias y opcionales y su procedencia. `docs/decisions/` conservará las decisiones y `CHANGELOG.md` el historial.

## Desarrollo preliminar

1. Leer la auditoría y confirmar su línea base en una terminal gráfica.
2. Tras autorización, preparar un repositorio local separado, con Git y Python ya instalados. Incorporar solo archivos revisados y documentar la correspondencia con sus destinos.
3. Ensayar backup y restauración en una ruta privada. Generar y validar temas inicialmente en un directorio temporal. Revisar diffs antes de autorizar un paso hacia el escritorio activo.

Añadir exclusiones para respaldos, cachés, staging, perfiles locales, imágenes y fuentes empaquetadas. Mantener fuera del índice historiales de shell y portapapeles, credenciales, registros de sesiones, bases de datos, datos de Dolphin, configuraciones personales y recursos sin licencia de distribución. Usar una lista explícita de archivos al preparar cada commit. Un recurso binario solo se incorpora con necesidad, licencia y destino documentados.

La entrega actual contiene documentación de CARBON-001. [Arquitectura](docs/ARCHITECTURE.md) · [Hoja de ruta](docs/ROADMAP.md) · [Respaldo](docs/BACKUP-PLAN.md)

## Línea base CARBON-002

El árbol actual contiene una selección de los dotfiles existentes, copiados sin cambios de contenido. La estructura anterior describe el objetivo del proyecto. El generador y los tokens quedan para una etapa posterior. [Instalación y correspondencia](docs/INSTALL.md) · [Dependencias](docs/DEPENDENCIES.md) · [Comprobaciones de sesión y respaldo](docs/BASELINE.md) · [Historial](CHANGELOG.md)
