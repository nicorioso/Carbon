# Wofi Carbon · CARBON-005-B.1

## Configuración y comportamiento actuales

Wofi 1.5.3-1 usa GTK 3. Los archivos activos `~/.config/wofi/config` y `~/.config/wofi/style.css` coincidían byte a byte con la copia versionada. El lanzador y el historial comparten una ventana nominal de 460 × 360 px, centrada por defecto, con el campo «Buscar», imágenes habilitadas e iconos de 24 px. La hoja usa Noto Sans de 13 px, superficie `#1b1b1b`, campo `#151515` y el mismo borde claro para la ventana y para el foco del campo. La selección clara con texto negro ya tiene buen contraste. La búsqueda y el borde exterior compiten por énfasis y la lista apenas se distingue del panel.

| Entrada | Contrato observado |
|---|---|
| Super + Espacio | El Lua activo ejecuta `wofi --show drun`. Wofi enumera archivos `.desktop`, busca sus metadatos y usa el tema de iconos de GTK. Return activa la entrada. La entrada local de Dolphin conserva `dolphin-carbon %u`. |
| Super + Shift + V | El Lua invoca `cliphist-menu.sh`. El auxiliar entrega el listado por stdin a `wofi --dmenu`, exige una fila presentada, decodifica completamente en un temporal y solo después llama a `wl-copy`. Dmenu usa stdout para devolver la fila. |
| Escape y fallos | Escape usa el cierre nativo. El auxiliar considera la salida 1 con stdout vacío como cancelación. Ese código también puede acompañar un fallo silencioso y en ambos casos se omite la copia. La comprobación de la fila y el manejo de fallos siguen en el auxiliar aprobado. |

Las combinaciones se verificaron en el IPC de Hyprland. Los comandos y la referencia de Dolphin se comprobaron en los archivos activos. La lectura se limitó a configuración y código. [Auxiliar y pruebas de interacción](SCRIPTS.md) · [Modos nativos de Wofi](https://man.archlinux.org/man/wofi.7)

### Opciones y hoja de estilo

- Wofi admite `width` y `height` en píxeles o porcentaje, `location` para anclar la ventana y offsets según el anclaje. Las propuestas conservan el centrado y una columna. `lines` y `dynamic_lines` admiten otra política de tamaño. Se mantuvo una altura fija para que el campo permanezca en una posición estable con pocos resultados.
- El modo de búsqueda se mantiene por defecto, `contains`, con búsqueda nativa de metadatos en drun. `insensitive`, `matching`, `exec_search` y `no_custom_entry` están disponibles. Los candidatos mantienen sus valores actuales y preservan ↑, ↓, Return y Escape. Wofi tiene una acción nativa de copia con Ctrl+C que queda fuera de las pruebas y del cambio.
- Se mantienen `allow_images=true` e `image_size=24` para ambos modos. Drun resuelve iconos de los `.desktop` mediante GTK. Dmenu muestra la fila que proporciona el productor y puede procesar secuencias de imagen. Los candidatos no añaden imágenes ni alteran su salida.
- Los selectores documentados que usa la plantilla son `#window`, `#outer-box`, `#input`, `#scroll`, `#entry`, `#text` y `#img`. Los estados GTK `:hover`, `:focus` y `:selected` definen el énfasis. El foco real depende de qué widget tenga el teclado. Los modos comparten el árbol base y la hoja, y el argumento existente elige el modo. [Configuración y selectores de Wofi](https://man.archlinux.org/man/wofi.5) · [Árbol GTK de Wofi](https://man.archlinux.org/man/wofi.7#WIDGET_LAYOUT)
- Los manuales de la versión instalada describen la carga por capas desde `/usr/etc/wofi`, `/etc/wofi` y el directorio XDG del usuario. En este equipo se comprobó el par de usuario. `--conf` y `--style` permiten apuntar a archivos de staging. `style` y `stylesheet` resuelven rutas relativas de forma distinta. GTK CSS admite `@import`. Los candidatos generan una hoja completa para evitar dependencias y ambigüedad de rutas. [Capa de configuración y opciones de Wofi](https://man.archlinux.org/man/wofi.1) · [Gramática GTK 3 CSS](https://docs.gtk.org/gtk3/css-overview.html)

## Propuestas

| | Carbon Launcher Compact | Carbon Launcher Segmented |
|---|---|---|
| Tamaño declarado | 440 × 324 px | 540 × 396 px |
| Búsqueda | Campo sobre fondo Carbon y margen inferior de 4 px. | Campo elevado y margen inferior de 8 px. |
| Lista | Integrada en el panel. Filas con relleno vertical de 4 px por lado. | Superficie enmarcada por un borde de 1 px. Filas con relleno vertical de 8 px por lado. |
| Panel | Superficie `#1b1b1b` con 8 px de margen interior. | Fondo `#121212` con 12 px de margen interior. El contraste distingue las dos zonas. |
| Selección y foco | Selección `#d6d6d6` con texto negro. Foco claro en búsqueda y contorno en filas enfocables. | Mismos estados. El mayor ancho reduce los saltos en nombres largos. |

Ambas usan los seis colores Carbon en sus respectivos roles, los tokens de hover y foco, radio cero y los espaciados compartidos. Compact prescinde del borde interior. Segmented aplica el contorno discreto y el contraste entre superficies de la referencia Waybar. Los 13 px de texto y los iconos de 24 px son ajustes locales heredados de Wofi. Los iconos Font Awesome representan aplicaciones en la maqueta. Wofi real conserva los iconos del tema GTK. **Se recomienda Segmented** para el monitor actual y para las entradas largas del historial. Compact reduce la ocupación cuando prima la densidad o se usa una pantalla más pequeña.

## Generación y prototipos

```bash
cd ~/carbon
stage=$(mktemp -d /tmp/carbon-wofi.XXXXXXXX)
for variant in compact segmented; do
  python -B dotfiles/.config/carbon/scripts/generate-theme.py \
    --input dotfiles/.config/carbon/theme.json --target "wofi-$variant" \
    --output "$stage/$variant"
done
```

Cada variante produce `config`, `style.css` y `preview.html` en un único lote. Los objetivos del motor comparten tres plantillas bajo `templates/theme/` y usan su validador de tokens, el escapado del renderizador y la publicación protegida. La maqueta se abre como un HTML autocontenido con estilos y comportamiento local. El texto de aplicaciones y portapapeles es ficticio. Los controles de escenarios y el mensaje de lista vacía aparecen en la página de revisión. En Wofi real se conserva el campo de búsqueda y la lista nativa vacía, sin añadir widgets ni encabezados.

Las propuestas usan `line_wrap=word_char`, opción de la versión instalada. El navegador demuestra el ajuste del texto en ambas anchuras. El salto exacto por idioma, el scroll y la geometría efectiva bajo layer-shell siguen sujetos a las métricas de GTK y al escalado de Hyprland. La maqueta conserva los iconos de ejemplo a una escala constante y usa su propia representación del foco. El estado de interacción real lo controla GTK.

## Pruebas

```bash
env -u DISPLAY -u WAYLAND_DISPLAY -u WAYLAND_SOCKET \
  python -B -m unittest discover -s tests/theme
python -B tests/scripts/test_interactions.py
python -B tests/screenshots/test_screenshots.py
git diff --check
```

Se añadieron ocho pruebas de objetivos y validación del motor, configuración, selectores, geometría, prototipos, contratos de invocación, bloqueo de salidas y preservación de una base ficticia. `GtkCssProvider` de GTK 3.24.52 aceptó ambas hojas. Wofi 1.5.3 abrió ambos candidatos en drun y dmenu usando GTK Broadway privado, una entrada `.desktop` ficticia y filas de ejemplo. Se usó `--normal-window` en esa prueba de arranque y se deshabilitaron caché, ejecución de la aplicación y copia. Brave verificó ambos tamaños de maqueta, los cinco escenarios, envoltura sin scroll horizontal y las acciones simuladas de selección y cancelación. El arranque aislado no valida el posicionamiento layer-shell ni el ciclo completo de aceptación y cancelación en Hyprland real. Las pruebas de interacciones siguen cubriendo los fallos mediante mocks.

## Despliegue futuro y recuperación

1. Con aprobación explícita, repetir la generación del objetivo elegido y validar la pareja de archivos. Resolver `XDG_CONFIG_HOME` y confirmar que los atajos leen los destinos esperados. Comparar los originales con el registro previo a sustituirlos.
2. Guardar solo `config` y `style.css` en un respaldo privado fuera de Git con presencia, propietario, permisos y SHA-256. Verificar los hashes y ensayar la restauración en staging.
3. Con el lanzador cerrado, preparar temporales adyacentes, conservar metadatos y sustituir los dos destinos por renombre. Comparar con el candidato antes de abrir Wofi. La siguiente invocación carga los archivos. El HTML permanece en staging.
4. Ante un fallo, cerrar Wofi, cotejar los hashes activos y del respaldo, restaurar ambos originales mediante temporales adyacentes y verificar permisos y hashes. Si un destino era nuevo, poner el candidato a cuarentena. Volver a abrir Wofi con el atajo normal para confirmar la recuperación. [Respaldo general](BACKUP-PLAN.md)

### Plan de validación en Hyprland

- Revisar posición, anchura, altura, contraste, foco, selección, scroll y texto largo con la escala real. Probar pocos resultados y lista vacía.
- Confirmar Super + Espacio, flechas, Return, Escape y apertura de Dolphin con su wrapper. Confirmar la procedencia visual de los iconos.
- Tras autorización, probar Super + Shift + V con datos de prueba controlados y verificar que Escape conserva el portapapeles y que una selección válida recupera el contenido de prueba. Registrar solo el resultado.

## CARBON-005-B.2 · Despliegue de Carbon Launcher Segmented

Se instaló **Carbon Launcher Segmented** de `62cdabc` con Wofi cerrado. La configuración declara **540 × 396 px**, posición central, iconos de 24 px y `line_wrap=word_char`. Wofi cargará el par de usuario en la próxima invocación. Se verificó el directorio XDG efectivo de Hyprland y la ausencia de archivos de configuración o estilo de Wofi en las rutas de sistema consultadas. Se mantuvieron las invocaciones de drun y dmenu, el auxiliar de cliphist y el acceso a Dolphin mediante su entrada `.desktop` local.

| Destino | SHA-256 | Modo y propietario |
|---|---|---|
| `~/.config/wofi/config` | `b1c67101e412a74d979acb72644b7c5e1cfa151ab136fe7a8273ded93ec8847b` | `0644`, UID 1000 y GID 1000 |
| `~/.config/wofi/style.css` | `23a569642f15f4cc08a61e009a0dbc71d7c6c6763f69b713f40b8745d2691e62` | `0644`, UID 1000 y GID 1000 |

Dos generaciones independientes coincidieron entre sí y con el lote revisado. Pasaron 50 pruebas de temas, Wofi y Waybar, 16 de interacciones y 15 de capturas. `GtkCssProvider` de GTK 3.24.52 aceptó la hoja. Se ensayaron instalación y restauración en staging. Un fallo simulado del segundo renombre recuperó el par previo con sus hashes y metadatos. La instalación real se completó sin fallos. Las verificaciones posteriores conservaron los hashes y metadatos de los demás componentes inspeccionados y los PID e invocaciones de los servicios comprobados.

### Respaldo y restauración conjunta

El directorio privado `~/carbon-wofi-segmented-backup.Q56vPPHs` contiene las dos copias individuales en `original/`, el manifiesto `files.tsv`, el estado previo y los dos manifiestos SHA-256. Se verificó la integridad de ambos originales y se conservaron los respaldos previos.

Para restaurar, cerrar Wofi y ejecutar:

```bash
backup="$HOME/carbon-wofi-segmented-backup.Q56vPPHs"
(cd "$backup" && sha256sum -c SHA256SUMS) &&
  python -B "$backup/wofi-pair.py" restore
```

El comando verifica los dos hashes activos y los originales. Si detecta una edición posterior o una instancia de Wofi abierta, se detiene. Prepara ambos originales en temporales adyacentes y los restaura por renombre con Wofi cerrado. Cada renombre es atómico y el procedimiento recupera el par anterior si falla una sustitución. Verifica hashes, modos y propietarios al terminar. La siguiente apertura de Wofi usará los originales.

### Aprobación funcional y visual

El usuario aprobó **Carbon Launcher Segmented** en Hyprland y confirmó estos seis resultados:

| Prueba manual | Resultado |
|---|---|
| Apertura y geometría | Correcto con el tamaño objetivo de 540 × 396 px. |
| Búsqueda y navegación mediante teclado | Correcto. |
| Apariencia Segmented | Correcto. |
| Aplicaciones y Dolphin desde el lanzador | Correcto. |
| Historial de cliphist mediante dmenu | Correcto. |
| Cancelación segura del historial con Escape | Correcto. El portapapeles conservó su contenido. |

En el cierre se repitieron 81 pruebas automatizadas. GTK 3.24.52 aceptó el CSS y se verificaron las opciones del archivo de configuración. Ambos archivos activos coincidieron byte a byte con la salida `wofi-segmented` de Carbon Theme Engine en `62cdabc`. Las invocaciones `wofi --show drun` y `wofi --dmenu` y el wrapper de Dolphin conservaron su configuración. Se verificaron nuevamente los dos originales del respaldo.

La aprobación cubre la sesión examinada. La geometría indicada es el objetivo declarado. El ajuste del texto y el tamaño efectivo pueden variar con el escalado de Hyprland y las métricas de GTK en otras pantallas.
