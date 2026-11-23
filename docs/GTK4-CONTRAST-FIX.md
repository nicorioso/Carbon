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
