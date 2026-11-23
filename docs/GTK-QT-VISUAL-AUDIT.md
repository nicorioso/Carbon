# CARBON-006-A.1 — Diagnóstico visual de GTK, libadwaita, portales y Dolphin

## Resultado

GTK 3 y GTK 4 reciben **Adwaita Sans 11** en la sesión Wayland aunque ambos `settings.ini` declaran Noto Sans 10. GTK 3 mostró una interfaz oscura en la prueba de widgets. GTK 4 combinó el fondo oscuro del CSS de usuario con cabecera y controles claros. El título claro sobre cabecera clara fue el problema de legibilidad más evidente. libadwaita reportó modo claro, aunque varios controles y la ventana se vieron oscuros por las reglas de usuario. Dolphin mantuvo los colores de la vista de archivos y Breeze Dark con ambos arranques aislados. La fuente Qt sí cambió al omitir el wrapper.

El diagnóstico partió de `main` limpio en `910f716`. Se conservaron las configuraciones vigentes y los servicios de la sesión. Las capturas de esta fase se realizaron en un compositor anidado a escala 1 con instancias de prueba. La consulta de GtkSettings y la lectura de D-Bus de la sesión real se hicieron sin abrir aplicaciones personales.

## Preferencias declaradas, publicadas y efectivas

| Propiedad | Archivos de usuario | GSettings y portal activo | GtkSettings en la sesión Wayland |
| --- | --- | --- | --- |
| Tema | `~/.config/gtk-{3,4}.0/settings.ini` declara Adwaita | Adwaita | Adwaita en ambas consultas |
| Tipografía | Noto Sans 10 | Adwaita Sans 11 | Adwaita Sans 11 en GTK 3 y GTK 4 |
| Variante | `gtk-application-prefer-dark-theme=true` | GSettings `default`, portal `color-scheme=0` | La propiedad local devuelve `true` en ambos. GTK 4 también devuelve `gtk-interface-color-scheme=DEFAULT` |
| Iconos y cursor | Sin overrides en esos archivos | Iconos Adwaita, cursor `default` y tamaño 24 | Adwaita, `default` y 24 en ambas consultas |
| Escala | Sin overrides GTK en esos archivos | Escala de texto 1.0 | DPI lógico 96 en ambas consultas. Superficies de las sondas a escala 1 |

`gsettings-desktop-schemas` 51.0-1 declara `'Adwaita Sans 11'` y `'default'` en el esquema `org.gnome.desktop.interface`. No hubo valor de dconf escrito por el usuario para ninguna de esas dos claves y el backend de GSettings en memoria devolvió los mismos valores. El código de xdg-desktop-portal-gtk lee el GSettings correspondiente, publica la fuente en su espacio de nombres y convierte el esquema de color en el número de `org.freedesktop.appearance`. El código `0` declara ausencia de preferencia. `settings.ini` aporta valores a GTK y el portal obtiene sus preferencias de GSettings. Eso explica que ambos resultados coexistan. [Código de Settings en xdg-desktop-portal-gtk 1.15.3](https://github.com/flatpak/xdg-desktop-portal-gtk/blob/1.15.3/src/settings.c) · [GtkSettings GTK 3](https://docs.gtk.org/gtk3/class.Settings.html) · [GtkSettings GTK 4](https://docs.gtk.org/gtk4/class.Settings.html)

Los dos `gtk.css` aportan fondo `#151515`, texto `#f5f5f5`, selección `#d6d6d6` con texto negro y radio 0. Los proveedores del tema, las propiedades de estilo de cada nodo y las reglas de aplicación determinan qué se termina dibujando. En GTK 4.24 la preferencia oscura histórica sigue presente, pero está obsoleta desde 4.20. La medición distingue su valor de la variante que usa el proveedor CSS. libadwaita gestiona su política mediante `AdwStyleManager`. [Propiedad GTK 4](https://docs.gtk.org/gtk4/property.Settings.gtk-application-prefer-dark-theme.html) · [Estilos de libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/styles-and-appearance.html)

## Pruebas visuales

Se vinculó cada binario instalado a su toolkit mediante las dependencias ELF. El perfil temporal HOME/XDG recibió copias de los archivos visuales pertinentes y usó un D-Bus separado, GSettings en memoria y el socket Wayland anidado. Las sondas GTK usaron widgets nativos sin CSS propio, una entrada enfocada, texto seleccionado, un botón deshabilitado, un icono simbólico y dos filas ficticias. Los tamaños siguientes son píxeles lógicos y los colores muestreados en PNG incluyen la composición.

| Prueba | Medición y observación |
| --- | --- |
| GTK 3.24.52 y Wofi 1.5.3 | La sonda Pango reportó Adwaita Sans 11. Fondo `#151515`, entrada oscura alrededor de `#2c2c2c` y altura de 34 px. Texto secundario y botón deshabilitado atenuados. Resaltados claros sobre texto oscuro en la selección de texto y en la fila. El foco dejó visible un contorno azul de Adwaita. Wofi en modo dmenu con copia de su configuración Segmented mostró la búsqueda, lista y selección previstas con dos textos ficticios. |
| GTK 4.24.1 y pavucontrol 6.2 | Pango reportó Adwaita Sans 14.667 px, equivalente a 11 pt a 96 DPI. Fondo `#151515`, entrada de 34 px alrededor de `#f8f8f8`, botones y fila sin seleccionar claros. La cabecera clara dejó el título de bajo contraste. Selección y foco siguieron identificables. pavucontrol confirmó una ventana GTK 4 con fondo oscuro y texto legible en su vista de conexión. El audio de la sesión se aisló y no se evaluaron sus controles. |
| libadwaita 1.10.0 y Zenity 4.2.2 | La sonda devolvió `Adwaita-empty`, `AdwStyleManager.dark=false`, política predeterminada y fuente Pango Adwaita Sans 14.667 px. Se vieron cabecera y botones oscuros, una fila clara sin seleccionar y texto deshabilitado atenuado. El icono simbólico y la selección eran visibles. Zenity mostró un diálogo oscuro de bordes cuadrados con una pregunta ficticia y dos botones legibles. |
| Portal FileChooser | `OpenFile` abrió el backend GTK 3 en el entorno aislado y `Request.Close` canceló la solicitud sin elegir un archivo. Se vieron cabecera y lista oscuras, fila seleccionada clara, iconos, foco y botón de acción azul. La captura se limitó al área de trabajo del diálogo y excluyó la barra lateral. |
| Dolphin 26.08.3, Qt 6.12.0 y KDE Frameworks 6.32.0 | La captura aislada mostró archivo y carpeta ficticios reconocibles, iconos con contraste y nombres legibles. La telemetría de Qt se detalla en la siguiente sección. |

Los bordes rectos se observaron en ambas sondas GTK y en los diálogos probados. Las alturas de entrada coincidieron, aunque el texto y los fondos cambiaron. Al enfocar un diálogo ficticio de Zenity sobre la sonda GTK 4, Hyprland confirmó el cambio de ventana activa. La cabecera de GTK 4 se volvió oscura, el borde exterior y el texto se atenuaron, desapareció el contorno azul de la entrada y siguió distinguiéndose la fila seleccionada. La observación combina el estado inactivo de GTK y la opacidad del compositor. La ventana de `pavucontrol` no permite inferir el color de todas sus pestañas a partir de la pantalla de conexión. Quedan pendientes la inspección sistemática de hover y menús, el contraste de toda la matriz de estados, el escalado fraccional, XWayland y la comparación entre clientes que usan FileChooser y clientes con diálogo propio. No se evaluaron preferencias persistentes ni la apertura de archivos reales.

## Portal activo y prueba de FileChooser

`xdg-desktop-portal` 1.22.1 y los backends GTK 1.15.3 e Hyprland 1.5.0 estaban activos. La configuración del proveedor prioriza `hyprland;gtk`. GTK anuncia Settings y FileChooser. Hyprland anuncia, entre otras, Screenshot y ScreenCast. Las sondas consultaron Settings en la sesión real y en la aislada con igual resultado para fuente y esquema de color. El diálogo visual fue el del bus aislado. La petición se hizo directamente por D-Bus con una ruta ficticia, sin seleccionar fichero ni introducir el estado de las carpetas reales en el diagnóstico. Un primer intento de la activación privada heredó el socket Wayland principal. Conservó el perfil temporal. Se corrigió el entorno de activación del bus privado y se repitió la prueba en el compositor anidado. Solo se conservó como evidencia la captura de esa repetición. [API FileChooser](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.FileChooser.html)

## Dolphin

Al inicio no había una instancia de Dolphin. Se ejecutaron dos arranques nuevos en el mismo entorno temporal, uno mediante el wrapper y otro con `/usr/bin/dolphin`. Se copiaron `Carbon.colors` y `kdeglobals` y se creó un `dolphinrc` sintético con solo `[UiSettings] ColorScheme=Carbon`. No se cargó el estado de vistas del Dolphin personal. Una sonda Qt de solo lectura registró la paleta después de iniciar la ventana.

| Medición Qt | Wrapper | Binario directo |
| --- | --- | --- |
| Variables específicas | `QT_QPA_PLATFORMTHEME=gtk3` y `GTK_THEME=Adwaita:dark` | Sin esas asignaciones |
| QPA y QStyle | `wayland`, `QFusionStyle` | `wayland`, `QFusionStyle` |
| Fuente devuelta por Qt | Adwaita Sans 11 pt | Familia genérica Sans Serif 9 pt |
| Iconos KDE | `breeze-dark` | `breeze-dark` |
| Ventana, vista y nombres | `#1b1b1b`, `#171717`, `#ffffff` activo e inactivo | Mismos valores |
| Selección | `#d6d6d6` con `#151515` | Mismos valores |

La entrada de usuario `org.kde.dolphin.desktop` vincula Wofi en modo drun con el wrapper y le pasa `%u`. El enlace de Hyprland para `Super + Shift + F` invoca el mismo wrapper. La ruta desde Wofi se comprobó por configuración. No se probó lanzar Dolphin desde Wofi ni reutilizar una ventana existente, porque el aislamiento de ambos procesos nuevos permite medir la diferencia sin tocar una instancia personal. Los colores de vista y selección medidos coinciden con `Carbon.colors`. Conviene conservar `#ffffff` para nombres activos e inactivos de la vista aunque el token general de texto sea `#f5f5f5`.

| Archivo | Modo observado | Cobertura verificada |
| --- | --- | --- |
| `~/.local/bin/dolphin-carbon` | `0755` | Git y respaldo privado, iguales al activo |
| `~/.local/share/color-schemes/Carbon.colors` | `0644` | Git y respaldo privado, iguales al activo |
| `~/.config/kdeglobals` | `0644` | Git y respaldo privado, iguales al activo |
| `~/.config/dolphinrc` | `0600` | Fuera de Git. Coincide con la copia del respaldo privado verificado |
| Entrada `org.kde.dolphin.desktop` de usuario | `0755` | Fuera de Git. No figura en el respaldo base examinado |
| `~/.config/hypr/hyprland.lua` | `0644` | Versionado e incluido en el respaldo base |

## Protección y regresión

Se verificaron por SHA-256 antes y después las configuraciones GTK, Kitty, Dolphin, Hyprland, Waybar, Wofi, Rofi y Mako. También se comprobaron la entrada de escritorio, el wrapper, el esquema Carbon y `kdeglobals`. Los servicios de Waybar, Mako y los tres procesos de portal conservaron estado, PID e identificador de invocación. La integridad del archivo tar y su manifiesto de respaldo privados pasó la comprobación. No se publicaron capturas ni se añadieron a Git. La galería y los PNG se entregan como evidencia temporal local.

La regresión existente pasó **94 pruebas**. Son 63 del motor y los temas, 16 de interacciones y 15 de capturas. Los ensayos visuales se hicieron aparte y no cuentan como pruebas unitarias. Las capturas corresponden a Wayland a escala 1, con una salida anidada observada de 931 × 1000. La decoración anidada reprodujo el borde, radio y opacidades del perfil Carbon para acotar la comparación. La geometría observada no certifica escalas o resoluciones diferentes.

## Estrategia para Carbon v1

1. **A. Conservar.** Mantener Kitty, Dolphin, wrapper, iconos, cursores, portal y componentes aprobados. Puede tolerarse la diferencia de familias entre toolkits si los controles siguen siendo legibles.
2. **B. Preferencias.** Evaluar primero la señal de preferencia oscura en otro perfil desechable y comparar el título GTK 4, los controles, Zenity y un diálogo del portal. La fuente debe tratarse por separado. Adwaita Sans es coherente entre GTK y Dolphin con wrapper en las pruebas actuales. La auditoría no mostró que cambiarla a Noto Sans mejore la legibilidad de esos casos.
3. **C. CSS independiente.** Si B no soluciona el bajo contraste, preparar un candidato GTK 4 de alcance pequeño en el Theme Engine. Revisar nodos de cabecera y fondos por estado. Mantener GTK 3 como referencia y ampliar su integración únicamente si se demuestra una mejora.
4. **D. Esquema KDE.** Posponer la generación de `.colors`. Si se retoma, conservar el texto blanco en la vista de Dolphin, efectos inactivos, selección y contraste. Excluir `dolphinrc` del generador y respaldar aparte la entrada de escritorio antes de una intervención en el lanzador.

La prioridad para v1 es resolver el título claro sobre cabecera clara en GTK 4 y conservar lo que ya funciona. Los acentos azules nativos del foco y del botón del portal siguen comunicando estado. Su paso a monocromo requiere una comprobación de contraste por estado. La fase de diagnóstico no selecciona ni despliega candidatos.
