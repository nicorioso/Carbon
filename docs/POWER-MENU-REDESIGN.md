# Carbon Power Menu · CARBON-005-C.1

## Auditoría de la línea base

Arch tenía el paquete `rofi 2.1.1-1`. El ejecutable reportó `2.1.1-dirty` y las comprobaciones de dmenu usaron el backend disponible en la sesión Wayland. Hyprland reportó 0.57.2. Super + Escape figura en el IPC y el Lua activo lo dirige a `~/.local/bin/power-menu.sh`. El script activo y `~/.config/rofi/power-menu.rasi` coincidían byte a byte con sus copias versionadas. El tema original es una lista de cuatro filas de 340 px con borde exterior claro y selección gris local `#454545`.

El script recibe las cuatro filas del orden siguiente y solicita un índice de origen con `rofi -no-config -dmenu -theme … -markup-rows -no-custom -format i`. Resuelve el tema desde `XDG_CONFIG_HOME` o desde `~/.config`. Conserva sus comprobaciones de dependencias y legibilidad. El atajo, el script, las invocaciones y la resolución de acciones quedan en la línea base aprobada. [Procedimiento y pruebas del script](SCRIPTS.md)

| Índice | Etiqueta | Acción existente |
|---:|---|---|
| 0 | Apagar | `systemctl poweroff` |
| 1 | Reiniciar | `systemctl reboot` |
| 2 | Suspender | `systemctl suspend` |
| 3 | Cerrar sesión | `hyprshutdown` si está disponible. En su ausencia, `hyprctl dispatch 'hl.dsp.exit()'`. |

El menú espera a que Rofi termine. Un estado 1 con salida vacía se trata como Escape. Una salida vacía con estado 0 también termina sin acción. Un índice desconocido o una salida de varias líneas se rechaza, y otros estados de error se propagan con diagnóstico. Los tests comprueban las cuatro filas en orden, los argumentos de Rofi, los casos de cancelación y error, las cuatro acciones y el fallback. Rofi, systemctl, hyprshutdown y hyprctl están sustituidos por mocks en esas pruebas. [Formato de índices de dmenu](https://github.com/davatorium/rofi/blob/2.1.1/doc/rofi-dmenu.5.markdown)

## Propuestas

| | Carbon Power Grid | Carbon Power List |
|---|---|---|
| Disposición | Dos filas y dos columnas con texto e icono centrados. Arriba Apagar y Reiniciar. Abajo Suspender y Cerrar sesión. | Cuatro filas en una columna con texto e icono alineados a la izquierda. Mantiene el orden vertical actual. |
| Anchura declarada | 408 px | 320 px |
| Altura medida del prototipo web | 126 px | 190 px |
| Espaciado | 8 px entre bloques y 12 px de relleno vertical. | 4 px entre bloques y 8 px de relleno vertical. |
| Teclado | ↑/↓ mueven por filas. ←/→ recorren horizontalmente el orden visual. | ↑/↓ recorren las opciones en el orden de la línea base. |

Ambas variantes usan el fondo `background`, bloques `surface`, contorno `border` y texto `text`. La selección combina `surfaceRaised` con un borde `selection` de 1 px. El interior oscuro conserva el contraste de los iconos blancos. La fuente Noto Sans de 11 puntos se conserva. El script inserta los glifos de Font Awesome 7 y su color blanco mediante Pango. El diseño mantiene ese tratamiento como excepción local para preservar el script y evita un fondo claro bajo los glifos blancos. Los iconos nativos se dibujan como parte de `element-text`.

Durante el diseño se recomendó List como primera opción por su recorrido vertical conocido y su menor ancho. Grid aprovecha mejor el espacio vertical y distingue los cuatro bloques. Al pasar a Grid, ↓ desde Apagar lleva a Suspender por posición. Ese recorrido se verificó en la prueba aislada de despliegue.

### Cuadrícula nativa y asignación de teclas

Rofi 2.1.1 admite `listview` con `columns: 2`, `lines: 2`, `fixed-columns: true` y `flow: horizontal`. `layout: vertical` mantiene el widget de lista y `flow` coloca las entradas por filas. `layout: horizontal` seleccionaría el estilo dmenu de una sola banda. El cambio de colocación conserva las cuatro entradas originales. El binario devolvió los índices 0, 1, 2 y 3 para las etiquetas esperadas con ambos Rasi en una prueba `-dump -filter` que solo escribe índices. [Opciones de listview](https://github.com/davatorium/rofi/blob/2.1.1/doc/rofi-theme.5.markdown#listview-widget) · [Colocación y navegación de Rofi 2.1.1](https://github.com/davatorium/rofi/blob/2.1.1/source/widgets/listview.c)

El mapa por defecto usa Ctrl+RePág y Ctrl+AvPág para moverse entre columnas. En Grid, el bloque `configuration` del tema añade ←/→ a esas acciones y conserva Ctrl+B/Ctrl+F para mover el cursor de edición. `rofi -no-config -theme … -dump-config` confirmó que el binario aplica estas asignaciones desde el tema. List conserva los enlaces predeterminados. Escape y las acciones de aceptación no cambian en ninguno. El navegador ilustra hover con un borde discreto. Rofi distingue la selección mediante su estado nativo y conserva desactivado `hover-select`. [Acciones y teclas de Rofi](https://github.com/davatorium/rofi/blob/2.1.1/doc/rofi-keys.5.markdown)

### Confirmación de acciones

Una confirmación para apagar, reiniciar o cerrar sesión reduciría la posibilidad de aceptar una acción por reflejo al cambiar de disposición. Añadiría un paso de teclado, otro estado de Escape y pruebas independientes de que cancelar devuelve el control sin ejecutar el comando. La decisión se mantiene separada y no se añadió ningún diálogo de confirmación. Suspender conserva su tratamiento actual.

## Generación y revisión

```bash
cd ~/carbon
stage=$(mktemp -d /tmp/carbon-power-menu.XXXXXXXX)
for variant in grid list; do
  python -B dotfiles/.config/carbon/scripts/generate-theme.py \
    --input dotfiles/.config/carbon/theme.json --target "power-$variant" \
    --output "$stage/$variant"
  env -u DISPLAY -u WAYLAND_DISPLAY -u WAYLAND_SOCKET \
    rofi -no-config -rasi-validate "$stage/$variant/power-menu.rasi"
done
```

Cada objetivo publica `power-menu.rasi` y `preview.html` juntos en staging. Dos plantillas comparten el renderizador, los tokens, la validación, el escapado y la publicación protegida de Carbon Theme Engine. Abrir los HTML en Brave para comparar dimensiones y simular las teclas. El prototipo usa glifos de una fuente local. Su altura corresponde al modelo web con una línea por acción. La altura efectiva, la alineación del texto y el foco de Rofi dependen de Pango, la escala y el backend Wayland.

Para una comprobación visual posterior autorizada, invocar solo Rofi con el Rasi de staging y las cuatro etiquetas de prueba. El resultado queda en stdout, fuera de cualquier script de energía. Para Escape, comprobar salida vacía y estado 1. Para flechas y Enter, comprobar el índice devuelto sin conectarlo a ningún comando. Usar el objetivo elegido como ruta:

```bash
printf '<span font_family="Font Awesome 7 Free Solid" foreground="#ffffff">%s</span>   %s\n' \
  '' 'Apagar' '' 'Reiniciar' '' 'Suspender' '' 'Cerrar sesión' |
  rofi -no-config -dmenu -theme "$stage/grid/power-menu.rasi" -markup-rows -no-custom -format i
```

### Resultados

Rofi 2.1.1 validó ambos Rasi con `-rasi-validate` y mostró sus dimensiones y opciones con `-dump-theme`. La prueba nativa con filas de ejemplo confirmó los cuatro índices en los dos diseños. Brave comprobó geometría, iconos, navegación, Enter simulado y Escape de ambos HTML. La regresión comprende 56 pruebas de temas, 16 de interacciones y 15 de capturas. Las seis pruebas nuevas cubren geometría, contraste, determinismo, publicación, maquetas y validación nativa. La integración del script con acciones y fallos se probó únicamente con mocks. Queda pendiente probar el aspecto y el recorrido interactivo del Rasi en Wayland con la invocación aislada.

## Instalación futura y rollback

1. Tras autorización, elegir Grid o List, generar el objetivo desde el commit aprobado y comprobar el Rasi y la ruta XDG. Revisar que el original coincide con el aprobado al respaldar y cerrar el menú antes de instalar.
2. Guardar `power-menu.rasi` fuera de Git con propietario, modo y SHA-256. Verificar la copia. Preparar un temporal adyacente con el contenido aprobado y los metadatos originales.
3. Renombrar el temporal sobre el tema, cotejar hash y modo, y verificar el tema en la siguiente apertura usando primero solo Rofi con entradas de prueba. El despliegue contempla un único destino.
4. Para volver a la línea base, cerrar el menú, verificar los hashes del tema instalado y del respaldo, preparar un temporal adyacente con los metadatos del original y restaurarlo por renombre. Comparar bytes y modo. El original se leerá en la próxima invocación. [Plan de respaldo](BACKUP-PLAN.md)

## CARBON-005-C.2 · Validación nativa y despliegue de Grid

El usuario seleccionó **Carbon Power Grid** para el despliegue de `c43c1ec`. El lanzador aislado envió cuatro filas de prueba con los iconos y las etiquetas originales a Rofi 2.1.1 en un Hyprland 0.57.2 anidado. Solo había una ruta de salida, el índice de dmenu en stdout. La comprobación capturó el borde de selección en la superficie nativa antes de pulsar Enter. La primera preparación del entorno recibió un modificador Super del compositor anfitrión. Se aisló el teclado anfitrión dentro del compositor de prueba y se repitió con flechas sin modificadores. El candidato mantuvo los mismos bytes.

| Entrada de prueba | Selección visual observada | Resultado |
|---|---|---|
| Abrir el menú | Apagar, arriba a la izquierda | El proceso espera entrada y stdout queda vacío. |
| → desde Apagar | Reiniciar, arriba a la derecha | Enter devuelve `1`, estado 0. |
| ↓ desde Apagar | Suspender, abajo a la izquierda | Enter devuelve `2`, estado 0. |
| ← desde Reiniciar | Apagar, arriba a la izquierda | Enter devuelve `0`, estado 0. |
| ↓ desde Reiniciar | Cerrar sesión, abajo a la derecha | Enter devuelve `3`, estado 0. |
| Escape con Reiniciar seleccionado | Se cierra el menú | Stdout vacío, estado 1. |
| ↑ desde Suspender, verificación adicional tras instalar | Apagar, arriba a la izquierda | Enter devuelve `0`, estado 0. |

El recorrido completo pasó antes de instalar con el candidato de staging y después con el Rasi activo. El lanzador no invoca `power-menu.sh`. Pasaron las 87 pruebas automatizadas y el Rasi validó con el parser de Rofi. Dos generaciones independientes coincidieron con el candidato aprobado. La inspección del Rasi confirmó que solo contiene propiedades de tema y asignaciones de navegación.

### Instalación y respaldo

Con Rofi cerrado, se copió el Rasi aprobado a un temporal adyacente, se verificaron su contenido y sus metadatos y se sustituyó el destino por renombre atómico. El único destino activo cambiado fue `~/.config/rofi/power-menu.rasi`. El SHA-256 instalado es `b1816e273f818ce4c442f43e1b58bbce333dea0d26c757f9057da474b9d7bdc6`. El modo quedó en `0644`, UID y GID 1000.

El respaldo privado `~/carbon-power-grid-backup.YEOgEklS` conserva el Rasi anterior en `original/power-menu.rasi`, con SHA-256 `e3091cc7cb725f4caa433468efab9dd6fd619775a4e3b80cc5b452fa0786b5`, manifiesto y estado previo. Se verificó su integridad. El script de energía, el Lua, el atajo y los metadatos de Waybar y Wofi se cotejaron con la línea base. Las invocaciones de los servicios comprobados permanecieron iguales.

### Comprobación visual segura

Desde una terminal de Hyprland, abrir:

```bash
"$HOME/carbon-power-grid-backup.YEOgEklS/rofi-grid-preview.sh"
```

El lanzador verifica el hash instalado y muestra las cuatro opciones de prueba. Enter imprime el índice en la terminal y Escape cierra sin salida. La comprobación mediante Super + Escape se omitió porque el menú real abre con Apagar seleccionado y Enter puede ejecutar la acción.

### Aprobación y cierre

El usuario aprobó **Carbon Power Grid** como diseño del menú de energía y confirmó cinco pruebas manuales mediante el flujo seguro:

| Comprobación manual | Resultado |
|---|---|
| Cuadrícula | Correcto. |
| Identidad visual | Correcto. |
| Navegación | Correcto. |
| Cancelación | Correcto. |
| Integración | Correcto. |

La prueba nativa anterior verificó movimientos horizontales y verticales que devolvieron los índices 0 (Apagar), 1 (Reiniciar), 2 (Suspender) y 3 (Cerrar sesión). Escape devolvió estado 1 con salida vacía. Por separado, los mocks verificaron el despacho de cada índice, las entradas inválidas y el fallback de cierre de sesión. Durante las validaciones se omitieron las acciones reales de energía y cierre de sesión.

En el cierre pasaron las 87 pruebas automatizadas. Rofi volvió a validar el Rasi y la salida del motor para `power-grid` coincidió byte a byte con el tema activo. El script y el Lua coincidieron con la línea base. Se verificaron el atajo Super + Escape en Hyprland y el SHA-256 del respaldo anterior.

La aprobación cubre la sesión y el flujo seguro examinados. La geometría y el contraste con otras escalas o fuentes siguen fuera de la comprobación. El menú real conserva Apagar como selección inicial y la aceptación directa.

### Recuperar el tema anterior

Con Rofi cerrado, ejecutar:

```bash
(
  set -euo pipefail
  backup="$HOME/carbon-power-grid-backup.YEOgEklS"
  theme="$HOME/.config/rofi/power-menu.rasi"
  (cd "$backup" && sha256sum -c SHA256SUMS)
  test "$(realpath -- "$theme")" = "$theme"
  test -f "$theme" && test ! -L "$theme" && test -O "$theme"
  test "$(sha256sum < "$theme")" = 'b1816e273f818ce4c442f43e1b58bbce333dea0d26c757f9057da474b9d7bdc6  -'
  status=0
  pgrep -u "$(id -u)" -x rofi >/dev/null || status=$?
  test "$status" -eq 1
  temporary=$(mktemp -- "${theme%/*}/.carbon-power-restore.XXXXXXXX")
  trap 'if [[ -e "$temporary" ]]; then unlink -- "$temporary"; fi' EXIT
  cp --preserve=all -- "$backup/original/power-menu.rasi" "$temporary"
  cmp -- "$temporary" "$backup/original/power-menu.rasi"
  test "$(stat -c '%a %u %g' "$temporary")" = "$(stat -c '%a %u %g' "$backup/original/power-menu.rasi")"
  mv -T -- "$temporary" "$theme"
  cmp -- "$theme" "$backup/original/power-menu.rasi"
  test "$(stat -c '%a %u %g' "$theme")" = "$(stat -c '%a %u %g' "$backup/original/power-menu.rasi")"
  sha256sum -- "$theme"
  rofi -no-config -theme "$theme" -dump-theme | awk '/width:.*340px|columns:.*1;|lines:.*4;/{print}'
)
```

El volcado de Rofi confirma la carga del tema original de 340 px y cuatro filas, sin abrir el menú habitual. El comando se detiene si el destino ya no tiene el hash de Grid.
