# Piloto Waybar · CARBON-004-B

El piloto genera una hoja GTK CSS completa desde `theme.json` y la plantilla `templates/theme/waybar.css.tmpl`. La opción `--target waybar` selecciona `style.css` mediante el registro del motor. Reutiliza la validación de tokens, el escapado, la sustitución estricta y la publicación en un destino de pruebas. El destino predeterminado `preview` conserva sus dos fragmentos.

## Línea base y alcance

La hoja original establece tipografía y geometría global, barra, botones de escritorios, espaciado y estados de los módulos, efectos de bandeja, tooltip y estados de AI Usage. Los selectores, declaraciones y su orden se mantienen. Los fondos transparentes que ya existían siguen en la plantilla y el alfa de superficie del tema se reserva para otros destinos.

`config.jsonc` conserva la altura declarada de 32 px, la posición superior y el reparto de módulos. También conserva escritorios 1–10, reloj, Wi-Fi, Bluetooth, audio, brillo, batería, AI Usage, bandeja e iconos, así como acciones de clic, intervalos y umbrales. Las dimensiones CSS, los rellenos de 5/7 px y el indicador de urgencia de 2 px siguen siendo literales de la línea base. Esto fija la geometría del piloto aun si se experimenta con tamaños globales.

## Inventario de colores

| Valor original | Uso en Waybar | Origen del candidato |
|---|---|---|
| `#1b1b1b` | Fondo de barra y AI Usage | `colors.surface` |
| `#f5f5f5` | Texto de barra, tooltip y AI Usage | `colors.text` |
| `#292929` | Separadores de barra y AI Usage | Transitorio para preservar contraste. |
| `#b3b3b3` | Texto de escritorios | `semantic.textSecondary` |
| `#222222` | Fondo de hover | Transitorio. Sustituirlo por `semantic.hover` produciría `#252525`. |
| `#ffffff` | Texto de hover y urgencia | Transitorio para preservar énfasis. |
| `#d6d6d6` | Escritorio activo, indicador urgente y estados de batería/Bluetooth | `colors.selection`, como equivalencia de valor. La semántica de cada selector permanece local. |
| `#000000` | Texto de escritorios activos | `semantic.textOnSelection` |
| `#a0a0a0` | Red desconectada, Bluetooth inactivo y audio en silencio | `semantic.textDisabled`, como equivalencia de valor. Los módulos conservan sus estados. |
| `#151515` | Fondo del tooltip | Transitorio para conservar su separación visual. |
| `#333333` | Borde del tooltip | `colors.border` |
| `#4f9dff` | AI Usage ocupado o con error | Excepción funcional. Se conserva el acento y su interpretación actual. |

`typography.family`, `typography.iconsSolid` y `typography.iconsBrands` aportan Noto Sans y Font Awesome 7. La familia final `sans-serif`, los 12 px y el resto de la geometría permanecen explícitos en la plantilla. Los valores transitorios se mantienen en dicha plantilla y el tema global queda intacto.

## Generación y comparación

```bash
cd ~/carbon
stage=$(mktemp -d /tmp/carbon-waybar.XXXXXXXX)
theme=dotfiles/.config/carbon/theme.json
engine=dotfiles/.config/carbon/scripts/generate-theme.py
python "$engine" --input "$theme" --target waybar --output "$stage/candidate"
cmp dotfiles/.config/waybar/style.css "$stage/candidate/style.css"
sha256sum dotfiles/.config/waybar/style.css "$stage/candidate/style.css"
python -B -m unittest discover -s tests/theme -v
python -B tests/scripts/test_interactions.py
python -B tests/screenshots/test_screenshots.py
```

Con los tokens oficiales, `cmp` confirma igualdad **byte a byte** y el SHA-256 es `02b35d4abbc023a7b5d06971b1888f42d52e8597b092e9ab43881bf2d3a95a0f`. Todas las diferencias están en el código fuente de la plantilla, donde los literales seleccionados se expresan como referencias a tokens. Los archivos nativos del repositorio se conservan como referencia.

Se validaron original y candidato con `GtkCssProvider` de GTK 3.24.52 fuera de una sesión gráfica. Los tests incluyen igualdad completa, aplicación de tokens sin alterar reglas locales, determinismo, idempotencia, errores de esquema, rechazo de destinos inseguros y compatibilidad con los fragmentos previos. El parser comprueba sintaxis y el diff comprueba la hoja generada. Sigue pendiente observar Waybar 0.16.0 en una sesión autorizada, donde influyen la ruta cargada, los estilos GTK, las fuentes disponibles, la escala y el estado de los módulos. [Hojas de estilo de Waybar](https://github.com/Alexays/Waybar/blob/master/man/waybar-styles.5.scd.in) · [Validación con GTK CSS](https://docs.gtk.org/gtk3/signal.CssProvider.parsing-error.html)

## Validación visual futura y rollback

1. Con autorización explícita, confirmar qué ruta CSS carga Waybar y si existe una variante clara u oscura que tenga precedencia. Tomar una referencia visual con la misma pantalla, escala y estados de módulos. Verificar que la hoja activa coincide con la línea base y guardar una copia privada con permisos, propietario y SHA-256.
2. Preparar un temporal junto a la hoja activa, copiar el candidato, comprobar hash y permisos y reemplazar el CSS por renombre atómico. Si la unidad efectiva sigue anunciando `CanReload=yes` y `ExecReload` con SIGUSR2, aplicar con `systemctl --user reload waybar.service` tras la autorización. Confirmar que el servicio sigue activo y que carga la hoja prevista.
3. Comparar altura de 32 px, anchura de escritorios, hover, activo y urgente. Revisar tipografía, iconos, reloj y tooltip, los estados disponibles de Wi-Fi/Bluetooth, volumen, brillo, batería, AI Usage y bandeja. Probar los clics sin alterar los ajustes del equipo y verificar que siguen ejecutando las acciones habituales.
4. Si cambia el resultado o se detecta un fallo, comprobar el hash del respaldo y que el CSS activo todavía corresponde al candidato instalado. Restaurar el original desde un temporal con los permisos respaldados, comprobar su SHA-256, aplicar el mecanismo de recarga aprobado y revisar nuevamente Waybar. Si hubo una edición concurrente, conservarla para revisión antes de restaurar. [Plan de respaldo](BACKUP-PLAN.md)
