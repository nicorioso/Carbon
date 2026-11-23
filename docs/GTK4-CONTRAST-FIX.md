# CARBON-006-A.2 — Diagnóstico causal del contraste GTK 4

El defecto se reproduce cuando **la variante clara de Adwaita y el CSS de usuario coinciden**. El CSS cambia el color del título a `#f5f5f5` y el `background-color` de la cabecera, pero la imagen de fondo de Adwaita sigue dibujando un gradiente claro sobre ese color. Con portal oscuro y el CSS intacto, el título pasa de **1,28:1 a 13,52:1** en el ensayo. El mejor candidato experimental cambia únicamente la preferencia de color de un perfil temporal. El escritorio activo conserva su configuración.

El diagnóstico previo está documentado en `c6dd7f4:docs/GTK-QT-VISUAL-AUDIT.md`, en `feature/carbon-006-gtk-qt-audit`. Esta rama parte de `main` en `910f716` y toma el informe anterior como referencia sin incorporar sus commits.

## Diseño experimental

Cada fila usó un `HOME` temporal, directorios XDG separados, un bus D-Bus propio y procesos reales de `xdg-desktop-portal` y `xdg-desktop-portal-gtk`. `GSETTINGS_BACKEND=keyfile` guardó las preferencias únicamente en el perfil de esa fila. Bubblewrap aisló procesos y red, ocultó `/home` y `/run` reales, montó el sistema en lectura y dejó staging como destino de escritura. Broadway escuchó solo en el loopback aislado. Los procesos de prueba carecían de acceso a los sockets Wayland y D-Bus de la sesión del usuario.

Hyprland 0.57.2 no arrancó en el intento sin compositor padre ni dispositivo DRM. La matriz se ejecutó con **widgets GTK 4.24.1 y libadwaita 1.10.0 reales, sobre Broadway**, con capturas nativas del árbol de render GTK. Se mantuvieron fijos widgets, escala lógica, fuente Adwaita Sans 11 y orden de estados. Los estados `FOCUSED` y `BACKDROP` se estimularon y verificaron en GTK. Las capturas excluyen el efecto del compositor en la opacidad de ventanas y el cambio real de foco de Hyprland. La fila original se compara con la reproducción Wayland de CARBON-006-A.1 como referencia independiente.

Broadway devuelve `UNSUPPORTED` para `gtk-interface-color-scheme`. En la sonda **GTK 4 sin libadwaita** se leyó el resultado del portal privado y se pasó a esa propiedad con el mismo mapeo que usa GDK Wayland. GTK 4 enlaza la propiedad con el proveedor CSS del tema y el de usuario. En **libadwaita** se dejó que `AdwStyleManager` consultara por sí mismo el bus privado. Registró política predeterminada y cambió su propiedad `dark` al variar la preferencia. La lectura del portal y la reacción de libadwaita se observaron de extremo a extremo. La ruta del backend GDK Wayland se comprobó en el código de la versión instalada. [GDK Wayland 4.24.1](https://github.com/GNOME/gtk/blob/4.24.1/gdk/wayland/gdksettings-wayland.c) · [GtkSettings 4.24.1](https://github.com/GNOME/gtk/blob/4.24.1/gtk/gtksettings.c) · [AdwStyleManager y preferencias](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/styles-and-appearance.html)

## Matriz observada

La razón de contraste usa el color del título que reporta GTK, una muestra de la cabecera enfocada y luminancia relativa sRGB. El gradiente varía en altura. Las razones son mediciones del par muestreado y sirven para comparar filas.

| Escenario | Valor del portal | Título / cabecera GTK 4 | Ventana / entrada GTK 4 | Resultado libadwaita |
| --- | ---: | --- | --- | --- |
| Original · sin preferencia y CSS actual | 0 | `#f5f5f5` / `#dddad6` · **1,28:1** | `#151515` / `#ffffff` | `dark=false`. Cabecera y entrada oscuras por estilos, con una fila de lista clara. |
| A · claro y CSS actual | 2 | `#f5f5f5` / `#dddad6` · **1,28:1** | `#151515` / `#ffffff` | `dark=false`. Mantiene la mezcla del original. |
| B · oscuro y CSS actual | 1 | `#f5f5f5` / `#282828` · **13,52:1** | `#151515` / `#2d2d2d` | `dark=true`. Cabecera y entrada siguen oscuras y la fila sin seleccionar se oscurece. |
| C · claro y sin CSS de usuario | 2 | `#2e3436` / `#dddad6` · **9,08:1** | `#f6f5f4` / `#ffffff` | `dark=false`. La apariencia nativa es clara. |
| D · oscuro y sin CSS de usuario | 1 | `#eeeeec` / `#282828` · **12,69:1** | `#353535` / `#2d2d2d` | `dark=true`. La apariencia nativa es oscura. |

La fila **A** demuestra que el CSS actual conserva la inconsistencia cuando el entorno solicita claro explícitamente. En **C**, la misma cabecera clara tiene texto oscuro. En **B**, con el mismo CSS y texto claro, el fondo de cabecera, los botones y la entrada pasan a colores oscuros. Esta comparación atribuye el defecto a la interacción de ambos factores. El código `0` no obliga a usar tema claro. El resultado original coincide con A para las propiedades medidas porque el toolkit eligió la variante clara de forma predeterminada.

Se comprobó además una intervención de una línea, `headerbar { background-image: none; }`, con A como base. La cabecera pasó a `#151515`, el título conservó `#f5f5f5` y alcanzó **16,75:1**. La entrada permaneció blanca. Esta prueba identifica la capa que oculta el fondo de usuario. Corregir solo esa capa repararía el título y conservaría la mezcla de superficies, por lo que la línea se mantiene como control causal y queda fuera de la propuesta de despliegue. [Cabecera y estado backdrop en Adwaita 4.24.1](https://github.com/GNOME/gtk/blob/4.24.1/gtk/theme/Default/_common.scss) · [Gradiente de cabecera en Adwaita 4.24.1](https://github.com/GNOME/gtk/blob/4.24.1/gtk/theme/Default/_drawing.scss)

## Reglas e interfaces afectadas

| Regla actual | Efecto y alcance |
| --- | --- |
| `*` con radio 0 | Conserva los bordes cuadrados. Las filas sin CSS muestran controles con la geometría nativa del tema. Su alcance merece una revisión separada si se editan las formas más adelante. |
| `window, dialog, headerbar, titlebar` | El título hereda el color claro. El fondo de ventana responde al CSS, pero `background-color` en cabecera no elimina `background-image`. Esta combinación explica el defecto. |
| `entry:focus` | Cambia el color de borde y deja al tema otros elementos de foco. La captura B conserva un indicador azul visible en GTK 4. La sonda distingue los estados por sus flags y por la muestra del borde. El color de borde de una regla sola no explica el indicador entero. |
| `selection, row:selected, treeview.view:selected` | La selección real en la entrada y la fila de prueba se distingue. B conserva el fondo de selección `#d6d6d6` con texto negro. La regla de TreeView no garantiza cobertura para todos los nodos de ListView o ColumnView. |
| `@define-color` para tema y acentos | Su efecto depende de qué variables use cada proveedor. libadwaita distingue sus estilos internos del tema GTK y aplica su política de color, como demuestra su cambio de `dark`. |

Al cambiar a B se mantuvo la altura de 34 px y el ancho de la entrada GTK 4, el texto principal claro, el secundario y el deshabilitado atenuados, y una selección legible. Las capturas también muestran el menú emergente y un diálogo ficticio de cada toolkit. Con B, el texto de las acciones disponibles y el del diálogo siguen legibles. Las acciones deshabilitadas se ven atenuadas. Las comprobaciones no certifican cada combinación de texto e iconos de aplicaciones de terceros. El contraste tabulado corresponde a la cabecera enfocada. La simulación GTK de `BACKDROP` permitió inspeccionar los controles y verificar los estados, pero no reprodujo toda la atenuación de la cabecera observada con el cambio de foco real de Hyprland en A.1.

La ventana de regresión de GTK 3 generó el mismo PNG en el perfil original y en B. Se mantuvieron el fondo oscuro, la fuente y los controles de ese ejemplo. En libadwaita, B alineó el modo efectivo con Carbon y eliminó la fila clara en la sonda. Se observaron las variantes sin CSS para separar el comportamiento propio de cada toolkit. [Política de tema de libadwaita](https://gnome.pages.gitlab.gnome.org/libadwaita/doc/main/styles-and-appearance.html)

## Candidato A · Preferencia oscura coherente

El escenario **B** de la matriz implementa el **candidato A**. El perfil aislado contiene `color-scheme='prefer-dark'` en `B/conf/glib-2.0/settings/keyfile`. Su `gtk.css` es idéntico a la entrada. No introduce capas CSS nuevas, cambios de selección ni ajustes de fuente. Conserva el foco y el contraste en los ejemplos evaluados. Se difiere el candidato CSS GTK 4. El Theme Engine, su salida GTK 3 y `theme.json` no requieren cambios para esta propuesta.

### Reproducción

Desde el repositorio, ejecutar `bash tests/gtk4-contrast/run.sh`. Usa las herramientas presentes en el entorno auditado, incluidas Bubblewrap, GCC, pkg-config, PyGObject, Broadway, GSettings, el portal GTK y FFmpeg. El comando imprime la ruta nueva de staging, corre cinco comprobaciones y genera `results/comparacion.html`. Las capturas, los perfiles, los binarios de prueba y los logs se conservan en esa ruta privada fuera de Git. `verify.py` comprueba las señales del portal, la respuesta de los toolkits, el contraste, el foco, la selección, los tokens y la regresión GTK 3. GTK carga las hojas reales y el verificador comprueba que no notifique errores de sintaxis CSS.

### Despliegue futuro y rollback

1. En una fase autorizada, repetir en un perfil Wayland separado que reciba la preferencia de forma nativa. Confirmar títulos activos e inactivos, selección y foco en una aplicación GTK 4 y una libadwaita reales. Incluir un menú, un diálogo, Wofi, un selector de archivos y Dolphin con el wrapper. Probar cambios de preferencia en ventanas abiertas y tras arranque nuevo.
2. Antes de cambiar la preferencia del usuario, registrar por separado el valor efectivo y la existencia del valor explícito de `/org/gnome/desktop/interface/color-scheme`. Guardar los hashes de hojas GTK y configuraciones protegidas. La posible operación persistente, solo con autorización, sería `gsettings set org.gnome.desktop.interface color-scheme prefer-dark`. El portal debe publicar `1` y la aplicación de referencia debe resolver el contraste.
3. Para revertir, restaurar el valor explícito previo cuando existía. Si la clave estaba ausente, usar `gsettings reset org.gnome.desktop.interface color-scheme` y confirmar que vuelve la misma preferencia del portal y la apariencia anterior. Conservar hojas, fuentes, iconos y cursores. En staging, salir del perfil retira el efecto sin ninguna operación sobre la sesión.

Una preferencia de sistema puede afectar a cualquier cliente que la escuche, también a aplicaciones con ventanas abiertas y a diálogos de portales. Queda pendiente validar el cambio de estado en Wayland nativo, clientes Qt que consuman la preferencia, escalado y políticas que fuerzan claro. Si el alcance global es inaceptable o el contraste falla en esa prueba, volver a estudiar una regla específica de GTK 4 tras reproducir la aplicación afectada.

## Protección y regresión

La batería de Carbon pasó 94 pruebas, 63 de temas, 16 de interacciones y 15 de capturas. Las cinco comprobaciones nuevas corresponden al ensayo aislado. Dos ejecuciones produjeron las mismas razones de contraste. El keyfile, la hoja conservada y las capturas principales de GTK 4 enfocado y desenfocado y de libadwaita enfocada en B coincidieron byte a byte. Se compararon los SHA-256 de 17 archivos protegidos antes y después. También se contrastaron estado, PID e identificador de invocación de Waybar, Mako y los servicios de portal, además del valor publicado por el portal activo. Dolphin y Kitty se verificaron por integridad de sus archivos. No se ejecutaron sus instancias durante esta fase.

## CARBON-006-A.3 — Validación Wayland nativa

### Aislamiento y matriz

La validación ejecutó Hyprland 0.57.2 anidado en una sesión gráfica Wayland. La salida de prueba midió 931 × 1000 px a escala 1. Bubblewrap ocultó HOME, `/run` y el bus originales, aisló red y procesos y dejó el sistema en solo lectura. Solo expuso el socket Wayland padre para iniciar el compositor anidado y el nodo de render, sin dispositivos DRM de control de pantalla. El compositor creó un socket nuevo en el runtime privado. Las sondas comprobaron el nombre efectivo de su display Wayland y las ventanas de Qt, GTK y FileChooser se comprobaron también desde el IPC privado de Hyprland. Wofi se verificó como superficie de capa del compositor anidado. El entorno de activación de D-Bus se ajustó **antes** de arrancar el backend y el frontend privados.

El bus privado usó dconf con HOME, XDG y runtime temporales. Los cuatro archivos GTK que se copiaron coincidían byte a byte con Git y con los activos. A partió de una clave de usuario ausente y el backend publicó `0`. B escribió solo `prefer-dark` y publicó `1`. La fuente se mantuvo en Adwaita Sans 11 y el ensayo conservó la decoración y las opacidades Carbon en el compositor anidado. No inyectó una preferencia en GtkSettings ni usó `GTK_THEME` para GTK o libadwaita. El wrapper de Dolphin sí conservó su override propio. [Recepción nativa en GDK Wayland](https://github.com/GNOME/gtk/blob/4.24.1/gdk/wayland/gdksettings-wayland.c) · [Backend GTK de Settings](https://github.com/flatpak/xdg-desktop-portal-gtk/blob/1.15.3/src/settings.c)

| Componente | Resultado en A y B |
| --- | --- |
| GTK 4.24.1 | La propiedad nativa pasó de `DEFAULT` a `DARK` tras `SettingsChanged`. En la ventana enfocada, el título mantuvo `#f5f5f5` y la muestra local del fondo pasó de `#d8d4d1` a `#282828`, **1,35:1 → 13,52:1**. El valor de A difiere levemente de Broadway por el punto de muestreo y la composición Wayland. En B se distinguieron foco, selección, icono simbólico y texto atenuado. También se capturaron la ventana desenfocada, el menú y el diálogo. |
| libadwaita 1.10.0 | La política de aplicación siguió en `DEFAULT`. `AdwStyleManager.dark` cambió de `false` a `true`. El título ya tenía buen contraste en A y conservó **16,75:1** en B. La fila de lista que aparecía clara en A se oscureció. Se conservaron la legibilidad de entradas, icono, menú y diálogo y la distinción de controles deshabilitados. |
| GTK 3.24.52 | Las dos instancias de prueba mantuvieron Adwaita Sans 11, fondo e inputs oscuros, icono simbólico visible y selección legible. Se observó el contorno de foco en ambas. La cobertura corresponde a la sonda, Wofi y el selector GTK 3 del portal. |
| Wofi 1.5.3 | Segmented conservó campo de búsqueda, icono y selección en `drun`, con una entrada ficticia prefiltrada. `dmenu` recibió dos filas ficticias con formato de historial. Se comprobó la misma invocación visual que utiliza el auxiliar, sin lanzar aplicaciones ni leer, escribir o restaurar el portapapeles. |
| Dolphin 26.08.3 | Dos procesos nuevos mostraron la misma paleta y el mismo estilo. El wrapper mantuvo `QT_QPA_PLATFORMTHEME=gtk3` y `GTK_THEME=Adwaita:dark`. Qt 6.12 utilizó Wayland, Fusion, Adwaita Sans 11 y Breeze Dark. La vista conservó texto blanco sobre `#171717` y selección `#d6d6d6` con texto `#151515`, coherentes con `Carbon.colors`. Se usó un `dolphinrc` mínimo sintético. Queda pendiente comprobar la reutilización de una instancia Qt que ya estuviera abierta. |
| FileChooser de xdg-desktop-portal 1.22.1 y backend GTK 1.15.3 | Se abrió una solicitud Wayland nativa con archivos ficticios en ambos escenarios. El panel principal conservó fondo oscuro, texto, foco de selección e iconos. `Request.Close` cerró ambas solicitudes sin seleccionar archivos. El sistema de documentos FUSE no estaba disponible por aislamiento. La prueba cubre el diálogo y la cancelación. Las capturas omiten la barra lateral. |

En GTK 4 y libadwaita, **el mismo PID** recibió A → B → A y recuperó el esquema, fondo y contraste de A sin relanzar la ventana ni reiniciar el portal. El cambio de foco se confirmó en el compositor y en GTK. Los arranques nuevos repitieron los valores. En la prueba de rollback de una clave explícita se restableció el GVariant guardado de `prefer-light`; el portal volvió a publicar `2`. Al retirar la clave, se comprobó que volvía a publicar `0`. El retroceso a A reproduce intencionalmente el defecto original de GTK 4.

### Evidencias y verificaciones

`bash tests/gtk4-contrast/wayland.sh` vuelve a ejecutar la matriz con herramientas ya instaladas. Usa un socket Wayland padre y el nodo de render disponible en el equipo auditado. El staging privado contiene `results/comparacion.html` y `results/validation.json`. Las capturas muestran ventanas reales con datos ficticios. No se añadieron capturas, binarios ni perfiles a Git. La información del toolkit y de foco se obtiene en los procesos de prueba y el contraste numérico se calcula con el color GTK del título y una muestra del fondo. Las pruebas cubren las señales del portal, el esquema nativo, el área de foco, el contraste, la telemetría de Qt, la integridad de CSS y los dos casos de rollback.

Pasaron las 94 pruebas de Carbon y las cinco comprobaciones causales de A.2. La matriz Wayland se ejecutó en dos perfiles nuevos y reprodujo los contrastes y la respuesta de los toolkits. En la comparación final, los PNG A/B de GTK 3, Dolphin, Wofi en ambos modos y FileChooser coincidieron byte a byte. Los 17 archivos protegidos conservaron sus SHA-256. La clave dconf principal, el resultado del portal principal y el estado, PID e identificador de invocación de los servicios examinados se mantuvieron. Kitty, Waybar, Rofi y Mako se verificaron por integridad. No se lanzaron en la sesión privada.

### Despliegue mínimo y recuperación

La operación persistente mínima, **si se autoriza en otra fase**, es una escritura de GSettings de usuario.

```bash
gsettings set org.gnome.desktop.interface color-scheme prefer-dark
```

dconf almacena la clave. El backend GTK del portal la observa y el frontend emite `org.freedesktop.portal.Settings.SettingChanged` con `org.freedesktop.appearance/color-scheme=1`. GTK 4 recibe la preferencia por GDK Wayland y libadwaita la aplica según la política de cada aplicación. La prueba no necesitó demonios nuevos, variables persistentes, reemplazo de CSS ni reinicios. Aplicaciones que fijan su propio esquema, mantienen caché o usan backends distintos pueden necesitar abrir una ventana nueva o reiniciar únicamente esa aplicación con autorización. [API del portal Settings](https://flatpak.github.io/xdg-desktop-portal/docs/doc-org.freedesktop.portal.Settings.html)

Antes del cambio autorizado, registrar en un respaldo privado tres valores separados. Guardar la escritura explícita con `dconf read /org/gnome/desktop/interface/color-scheme`, el valor resuelto con `gsettings get org.gnome.desktop.interface color-scheme` y la respuesta de `Read` del portal. La sesión examinada partía de una clave explícita ausente, valor resuelto `default` y portal `0`.

Para revertir una clave explícita, pasar el valor GVariant guardado a `gsettings set org.gnome.desktop.interface color-scheme`. Si el respaldo indica ausencia, ejecutar `gsettings reset org.gnome.desktop.interface color-scheme`. Se verifica primero la **configuración** comparando dconf y GSettings con el respaldo. Luego se verifica la **propagación** consultando el portal hasta recibir su código anterior. Por último se verifica la **recuperación visual** en ventanas existentes y en un arranque nuevo. Si una ventana conserva una apariencia obsoleta, probar su reapertura de forma controlada y conservar la evidencia. Cualquier reinicio de un componente queda sujeto a autorización.

**Decisión recomendada.** El candidato queda apto para solicitar autorización de un despliegue de un solo ajuste, con respaldo y verificación inmediata de ventanas abiertas. Quedan fuera de la matriz el escalado fraccional, XWayland, clientes Qt ya abiertos y aplicaciones que fuerzan su propio tema. Si la propagación o una comprobación visual falla, aplicar el rollback documentado antes de estudiar cambios de CSS. La sesión principal no recibió el candidato.
