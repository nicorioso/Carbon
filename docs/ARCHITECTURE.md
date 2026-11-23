# Arquitectura de Carbon 2.0

## Estado actual

SDDM selecciona un tema de sistema y ofrece entradas Wayland. Hyprland concentra política de escritorio y atajos en Lua. systemd de usuario ejecuta los servicios gráficos observados. D-Bus ofrece activación de Mako. Waybar, Wofi, Rofi y GTK consumen hojas propias. Dolphin aplica un esquema KDE y un wrapper Qt/GTK en el acceso por atajo. Hyprlock y Hyprpaper leen imágenes externas y SDDM usa copias locales al tema. Los valores visuales se mantienen a mano en varios formatos. [Inventario y evidencia](AUDIT.md).

## Estructura aprobada

| Ruta de ejecución | Responsabilidad |
|---|---|
| `~/.config/carbon/theme.json` | Fuente de tokens compartidos. |
| `~/.config/carbon/scripts/` | Generación y validación de temas, invocadas explícitamente. |
| `~/.config/hypr/` | Compositor, bloqueo, inactividad y fondo en sus formatos nativos. |
| `~/.config/{waybar,wofi,rofi,mako,kitty}/` | Cada componente conserva su configuración nativa y consume los valores que le correspondan. |
| `~/.config/{gtk-3.0,gtk-4.0}/` | Ajustes y CSS específicos de cada generación de GTK. |
| `~/.config/{kdeglobals,dolphinrc,mimeapps.list}` | Preferencias KDE y asociaciones por usuario. Control selectivo por claves tras revisar el estado personal. |
| `~/.local/bin/` | Herramientas interactivas y wrappers invocados por atajos o módulos. |
| `~/.config/systemd/user/`, `~/.local/share/color-schemes/` | Unidades propias y esquemas KDE respectivamente. Mantener unidades de proveedor en el sistema. |
| `/etc/sddm.conf.d/`, `/usr/share/sddm/themes/` | Selección y distribución del tema del greeter, con ciclo propio de pruebas y aprobación. |

## Generación de temas

CARBON-004-A incorpora la fuente JSON en `dotfiles/.config/carbon/theme.json`, el motor bajo `dotfiles/.config/carbon/scripts/` y plantillas de prueba bajo `templates/theme/`. La primera entrega genera únicamente fragmentos GTK CSS y Rasi en un directorio de pruebas explícito. [Motor y esquema](THEME-ENGINE.md) · [Identidad Carbon](DESIGN-SYSTEM.md) · [Compatibilidad visual](THEME-COMPATIBILITY.md)

Modelar roles `background`, `surface`, `surfaceRaised`, `border`, `selection`, `text` y fuente de interfaz en JSON versionado. Para adopción fiel, identificar valores actuales de cada consumidor, contrastarlos con la paleta aprobada y documentar desviaciones con un valor transitorio por consumidor. La convergencia visual exige una decisión explícita. El color de texto seleccionado, ANSI, iconos, opacidad y estados tendrán política propia cuando corresponda.

Usar Python estándar, ya instalado. Validar esquema, claves desconocidas, tipos, colores hexadecimales y escapado de cadenas. Usar plantillas versionadas con sustitución estricta y salidas deterministas. Generar primero en un árbol privado separado con un manifiesto de destinos relativos, validar, comparar los diffs y repetir para comprobar idempotencia. Fijar el esquema y las pruebas antes de habilitar una instalación. Los ajustes de hardware y rutas de imágenes pertenecen a un perfil local de ejemplo o sin versionar, según contenido.

| Consumidor | Salida propuesta |
|---|---|
| Waybar y Wofi | CSS GTK con colores literales o fragmento nativo de colores importado después de probarlo con cada aplicación. Conservar reglas y selectores. |
| GTK 3 y 4 | Hoja por generación con plantillas compartidas cuando coincidan. Conservar los nombres de color existentes al extraerlos y probar aplicaciones representativas. GTK 4 admite propiedades CSS personalizadas desde 4.16. [Documentación GTK](https://docs.gtk.org/gtk4/css-properties.html) |
| Rofi | Rasi con bloque de propiedades y referencias de color, o archivo completo generado. Comprobar la carga con los flags reales del script y el manual de la versión instalada. [Manual upstream de temas Rasi](https://github.com/davatorium/rofi/blob/next/doc/rofi-theme.5.markdown) |
| Hyprland | Módulo Lua que devuelva una tabla con cadenas y números en los formatos que espera `hl`. Probar resolución de módulos y errores con un compositor aislado compatible con la versión local. |
| Hyprlock y Mako | Sintaxis nativa y conversiones explícitas de color y alfa. Mako requiere aprobar primero una configuración propia. Hyprpaper conserva el perfil de monitor y recursos por máquina. |
| Kitty y KDE | Directivas Kitty y fragmento para `Carbon.colors` con tripletas RGB. Separar ANSI y preferencias personales de Dolphin. |
| SDDM | Posible bloque QML generado tras validar Qt, paridad y assets en un entorno de pruebas. El despliegue al sistema será una operación independiente. |

## Adopción y rollback

1. Verificar la sesión y ensayar restauración en un staging privado. Preparar el repositorio con una lista explícita de archivos revisados.
2. Extraer tokens en una copia y generar candidatos con paridad de valores. Medir cambios por componente y llevar a revisión cualquier diferencia visual.
3. Con autorización posterior, pilotar una hoja de bajo impacto. Adquirir un bloqueo de despliegue, resolver destinos por lista permitida, detectar cambios desde el respaldo y preservar permisos y enlaces. Preparar temporales junto a sus destinos y reemplazar por renombre después de validar.
4. Registrar antes de aplicar qué destinos existen, sus hashes y archivos de respaldo. Cada renombre es atómico por archivo. Si una tanda se interrumpe, el manifiesto permite revertir los destinos ya aplicados. Para un destino nuevo, retirar el candidato a cuarentena sin borrarlo.
5. Probar por separado lo relativo a servicios de sesión, compositor, bloqueo y SDDM. Restituir archivos desde el respaldo y verificar su contenido antes de autorizar cualquier recarga o prueba de arranque. [Procedimiento de restauración](BACKUP-PLAN.md).
