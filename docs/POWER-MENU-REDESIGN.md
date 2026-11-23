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

**Recomendación.** Usar List como primera opción de validación en la sesión. Conserva el recorrido vertical conocido en acciones sensibles y requiere menos ancho. Grid aprovecha mejor el espacio vertical y distingue los cuatro bloques. Al pasar a Grid, ↓ desde Apagar lleva a Suspender por posición. Confirmar este recorrido con la vista aislada antes de considerar su despliegue.

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
