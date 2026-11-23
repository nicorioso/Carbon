# Waybar Carbon 2.0 · CARBON-005-A

El piloto anterior validó el motor reproduciendo la hoja activa. Esa hoja conserva diez botones persistentes, rellenos de 5 y 7 px, fondo de barra `#1b1b1b` y colores locales para hover, tooltip y separadores. El botón activo se distingue bien, pero un escritorio vacío y uno ocupado en segundo plano comparten el estilo base. La propuesta reduce los botones que ocupan espacio sin perder acceso por teclado a los escritorios altos. Usa la jerarquía monocromática de Carbon para separar grupos y estados.

## Distribución

| Zona | Propuesta |
|---|---|
| Izquierda | Escritorios numerados. Los botones de 1–5 son persistentes en Waybar. Los de 6–10 dependen del ciclo de vida de los escritorios reales. Se conserva el clic de activación. |
| Centro | Reloj y fecha con formato compacto y tooltip existentes. `fixed-center: true` mantiene el reloj centrado respecto de la barra, con peso tipográfico 600. |
| Derecha | Wi-Fi, Bluetooth, volumen, brillo, batería, AI Usage y bandeja en el mismo orden y con sus acciones y estados. AI Usage tiene superficie y separador propios. |

Se mantienen la posición superior, los 32 px declarados, los grupos de módulos, las fuentes Noto Sans y Font Awesome 7, los formatos, iconos, tooltips, intervalos y umbrales. `fixed-center` hace que Waybar use el widget central de GtkBox. En pantallas estrechas o con textos excepcionalmente largos, comprobar que los grupos laterales dejan espacio suficiente para el centro. [Distribución de Waybar 0.16.0](https://github.com/Alexays/Waybar/blob/0.16.0/src/bar.cpp#L804-L818)

## Escritorios dinámicos

`config.jsonc` cambia únicamente la lista persistente y el orden. Waybar 0.16.0 documenta `persistent-workspaces: {"*": [1, 2, 3, 4, 5]}` y `sort-by: "number"`. Esta última opción sustituye el campo anterior `sort-by-number`, que la versión instalada no lee. Los botones persistentes permiten enfocar un escritorio vacío por clic. Para 6–10, los eventos de Hyprland crean el botón al existir el escritorio y lo retiran al destruirse. Los atajos actuales siguen permitiendo entrar en uno vacío, que aparece al activarse. Los botones se identifican por dirección. Un placeholder que pasa a existir adopta la dirección real en lugar de duplicarse. [Opciones y ejemplos de Waybar 0.16.0](https://github.com/Alexays/Waybar/blob/0.16.0/man/waybar-hyprland-workspaces.5.scd) · [Ciclo de vida y reconciliación](https://github.com/Alexays/Waybar/blob/0.16.0/src/modules/hyprland/workspaces.cpp)

La regla para 6–10 depende de que Hyprland descarte sus escritorios numerados no persistentes al quedar vacíos y dejar de estar visibles. Un escritorio enfocado y vacío sigue teniendo botón. Un escritorio con ventanas sigue visible mientras exista. Al abandonar uno vacío puede haber un intervalo durante la transición y el procesamiento de IPC. Una futura regla de Hyprland que mantenga un escritorio alto con vida alteraría esta política. La configuración actual carece de esas reglas. Los tests comprueban la configuración y la elegibilidad para los eventos nativos. La secuencia efectiva queda para la prueba gráfica. [Persistencia en Hyprland 0.57.2](https://github.com/hyprwm/Hyprland/blob/v0.57.2/src/workspace/RegularWorkspace.cpp) · [Estados CSS y clic de Waybar 0.16.0](https://github.com/Alexays/Waybar/blob/0.16.0/src/modules/hyprland/workspace.cpp)

## Dos variantes, una plantilla

| Aspecto | Carbon Compact | Carbon Balanced |
|---|---|---|
| Relleno horizontal exterior de indicadores | 4 px por lado | 8 px por lado. Los lados internos de cada pareja se reducen a 4 px. |
| Escritorios | 20 px de ancho mínimo, 4 px de relleno por lado y margen vertical de 4 px | Igual |
| Reloj, altura y orden de módulos | Mismos valores en las dos variantes | Igual |
| Cuándo elegirla | Cuando el ancho disponible es limitado o los estados de la derecha crecen con frecuencia | Para uso habitual si todos los indicadores caben sin presionar el centro |

**Recomendación: Carbon Balanced.** Da más separación a estados que cambian de longitud, como AI Usage y red. En esta configuración de siete módulos a la derecha, supone hasta 40 px extra de relleno respecto de Compact si todos se muestran. Los lados internos de las dos parejas usan 4 px en ambas variantes. Probar esa holgura con la bandeja visible. Si el reloj pierde espacio, Compact conserva el mismo contraste y los mismos estados con menos relleno.

`--target waybar-compact` y `--target waybar-balanced` usan la misma plantilla `templates/theme/waybar-redesign.css.tmpl` y el mismo motor del piloto. Se selecciona `spacing.unit` o `spacing.small` para los indicadores. El objetivo anterior `--target waybar` conserva el CSS del piloto. El JSONC versionado de la rama es común a ambas variantes y se revisa por separado del CSS generado.

## Tokens y estados

- Fondo base `#121212`, superficies `#1b1b1b`, tooltip elevado `#252525` y separadores `#333333`. La plantilla toma los colores y los anchos de borde de los tokens, con radio 0 y tipografía de 12 px.
- Vacío, texto secundario `#b3b3b3`. Ocupado e inactivo, fondo de superficie, texto principal y un indicador inferior de 1 px. Activo, selección `#d6d6d6`, texto negro y negrita.
- Hover usa la superficie elevada. El foco tiene un contorno de 2 px, claro sobre fondo oscuro y negro sobre selección. La urgencia usa un indicador de 2 px, con contraste adaptado al estado activo.
- Estados apagados o silenciados conservan el tono atenuado. Los estados críticos de batería ganan peso de fuente. El único color local fuera de la escala de grises es `#4f9dff` de AI Usage, conservado para ocupado y error. La distinción entre ambos sigue dependiendo del módulo.
- Las variantes usan superficies opacas y las únicas sombras nuevas son líneas interiores usadas como indicadores. El fondo sin relleno de los botones vacíos deja ver la barra.

## CARBON-005-A.1 · Refinamiento de reloj e indicadores

El usuario confirmó que el diseño de escritorios, los botones y las acciones de Balanced funcionan correctamente. El reloj y la zona derecha seguían pareciéndose demasiado a la barra anterior. El refinamiento conserva byte a byte las reglas de escritorios y deja intactos el JSONC y los tokens.

| Zona | Tratamiento |
|---|---|
| Reloj | Superficie elevada `#252525`, relleno horizontal de 12 px en lugar de 8 px y margen vertical de 4 px. Conserva el peso 600, el formato actual y el centrado por `fixed-center`. |
| Conectividad | Wi-Fi y Bluetooth forman una pareja, con 4 px en cada lado interno. |
| Multimedia | Volumen y brillo forman una pareja con el mismo espacio interno. Un separador antes del volumen señala su inicio. |
| Energía | Un separador identifica la batería. Sus estados conservan los estilos existentes. |
| Productividad | AI Usage usa la superficie elevada y un separador. El acento funcional permanece. |
| Sistema | Un separador antes de la bandeja la distingue del módulo de productividad. Los iconos conservan sus reglas. |

Waybar 0.16.0 admite contenedores `group/<nombre>` con una lista `modules` y orientación horizontal explícita. El CSS es suficiente para esta separación y conserva el árbol de widgets y las interacciones. El diseño recurre a líneas de 1 px y reserva los fondos elevados para el reloj y AI Usage. Si un módulo inicial se oculta por su estado habitual, su separador desaparece junto con él. No se agregan contenedores, cajones ni caracteres decorativos. [Grupos nativos de Waybar 0.16.0](https://github.com/Alexays/Waybar/blob/0.16.0/man/waybar.5.scd.in#L317-L342)

Los módulos con clic reciben un hover discreto y un contorno de foco donde el widget lo admita. Waybar y GTK siguen determinando qué módulos son enfocables. El CSS no añade dimensiones fijas a los indicadores ni limita la longitud de sus etiquetas. Los porcentajes y tooltips permanecen en el JSONC existente.

Con los siete módulos a la vista, Balanced recupera 16 px de relleno dentro de las dos parejas y añade 3 px netos de separación. El balance nominal reduce unos 13 px a la derecha y añade 8 px de relleno al reloj. Compact mantiene su relleno interno anterior y añade los mismos 3 px netos de separación. Son cálculos del CSS, sin medición gráfica. Los 32 px siguen declarados y el margen vertical de 4 px no añade relleno vertical. La altura efectiva y el centrado con textos largos dependen de la asignación de GTK. Balanced sigue siendo el candidato principal.

## Generación y pruebas

```bash
cd ~/carbon
stage=$(mktemp -d /tmp/carbon-waybar-redesign.XXXXXXXX)
for variant in compact balanced; do
  python dotfiles/.config/carbon/scripts/generate-theme.py \
    --input dotfiles/.config/carbon/theme.json \
    --target "waybar-$variant" --output "$stage/$variant"
done
cp dotfiles/.config/waybar/config.jsonc "$stage/config.jsonc"
python -m json.tool "$stage/config.jsonc" >/dev/null
env -u DISPLAY -u WAYLAND_DISPLAY -u WAYLAND_SOCKET \
  python -B -m unittest discover -s tests/theme -v
python -B tests/scripts/test_interactions.py
python -B tests/screenshots/test_screenshots.py
```

Los dos CSS se compararon con el parser nativo `GtkCssProvider` de GTK 3.24.52 sin inicializar una sesión gráfica. Las diez pruebas de rediseño verifican generación, geometría declarada, política de escritorios, módulos, comandos, iconos, sintaxis GTK 3 y confinamiento de salida. Las pruebas existentes verifican que el CSS del piloto todavía se genera con paridad. La altura resultante, los selectores en widgets reales, el centrado, la legibilidad y la desaparición de escritorios altos requieren Waybar en una sesión autorizada. Esta etapa produjo CSS y JSONC de prueba.

La regresión de A.1 totaliza 67 pruebas satisfactorias. La salida refinada tiene SHA-256 `6d23dafd666c04631638c187f820d4bf3b5c1165b888e2ccb90e4ef241446904` para Balanced y `2489c9cdb3e711b0580662b0d35310b41996753527f87962f5a025315dc594b2` para Compact. Se comprobó que los ocho bloques CSS de escritorios, los valores del tema, el JSONC activo y la invocación de Waybar conservaron su estado anterior.

## Instalación futura y rollback

1. Con autorización explícita, elegir una variante, confirmar las rutas efectivas de Waybar y verificar que no haya ediciones locales posteriores. Respaldar individualmente CSS y JSONC con modos, propietarios y SHA-256. Mantener también una referencia visual privada.
2. Validar la pareja en staging. Preparar temporales junto a los dos destinos y verificar sus hashes. Reemplazar cada archivo por renombre atómico y aplicar una única recarga autorizada después de verificar ambos. Revisar si hay recarga automática de estilos antes de sustituir el primer archivo. Los dos renombres son independientes, por lo que se debe conservar la relación de los archivos ya aplicados.
3. Si falla una sustitución o la comprobación visual, verificar los respaldos y descartar conflictos con ediciones posteriores. Restaurar los archivos afectados desde temporales con sus permisos originales, verificar sus hashes y aplicar el mecanismo de recarga aprobado. Confirmar que se restablecen la barra anterior y sus diez botones persistentes. [Respaldo general](BACKUP-PLAN.md) · [Verificación de rutas del piloto](WAYBAR-THEME.md#verificación-de-la-sesión-activa)

### Despliegue y rollback específicos de A.1

Con autorización explícita, confirmar que Waybar sigue cargando `~/.config/waybar/style.css` y que el CSS en disco coincide con la Balanced instalada de `46f1162`. El JSONC de esa versión debe seguir intacto. Respaldar **la Balanced original actualmente instalada** con `cp -p`, registrar su SHA-256 y modo y verificar su integridad. El respaldo anterior al rediseño conserva otra línea base.

El callback de apariencia del portal puede releer el CSS aun con la vigilancia de archivo desactivada. Para controlar el momento de activación, detener solo `waybar.service` con autorización, confirmar que no queden instancias, instalar exclusivamente el CSS Balanced refinado por renombre atómico y verificar su hash y permisos. Arrancar el servicio con autorización y comprobar el PID, las rutas cargadas y la altura efectiva. [Recarga por apariencia en Waybar 0.16.0](https://github.com/Alexays/Waybar/blob/0.16.0/src/client.cpp)

Para revertir, detener la unidad, comprobar que el CSS activo sigue siendo el candidato y que el respaldo de la Balanced original es válido. Restaurar el CSS desde un temporal con contenido y modo igual al respaldo. Verificar el hash antes de iniciar Waybar. Conservar el JSONC actual y los respaldos durante todo el procedimiento.

## Validación manual propuesta

- Medir la capa de 32 px y comprobar esquinas, foco de teclado, hover, urgencia y contraste. Comparar Compact y Balanced con el mismo monitor y escala.
- Confirmar que 1–5 aparecen una sola vez, incluidos los vacíos. Entrar en 6 con un atajo existente, salir con 6 vacío, y repetir con una ventana abierta. Verificar que 6 solo desaparece cuando deja de estar activo y queda vacío. Repetir el límite alto con 10 y comprobar los clics. Si se usa más de un monitor, revisar el comportamiento por barra.
- Verificar que el reloj no se desplaza al cambiar la longitud de los indicadores. Revisar Wi-Fi, Bluetooth, volumen, brillo, batería, AI Usage y bandeja, sin forzar errores ni desconexiones. Confirmar tooltips, iconos y acciones normales.

Para A.1, comparar contra Balanced de `46f1162` con la misma escala. Comprobar el reloj con una fecha larga y la separación de los cinco grupos cuando cambian los textos. Revisar que el hover y el foco resulten legibles y que los 32 px efectivos se mantengan. Si un módulo derecho no está disponible, comprobar que el grupo contiguo siga siendo distinguible.

## CARBON-005-A.2 · Dos composiciones para revisión

El usuario aprobó las interacciones y el diseño de los escritorios en Balanced Refinada. El reloj elevado y los indicadores separados por líneas conservaban una composición muy cercana a la barra anterior. Las dos propuestas cambian la relación entre el reloj, la barra y los indicadores. Ambas conservan los ocho bloques de estilos de escritorios, los cinco botones persistentes, los escritorios dinámicos, la posición superior y el formato completo de cada módulo.

| Zona | Carbon Segmented | Carbon Omarchy Refined |
|---|---|---|
| Altura declarada | 36 px. Los 4 px adicionales dan aire a los bloques. | 32 px, la altura actual. |
| Reloj | Negrita 700 con una línea inferior de 1 px en `selection`. Relleno horizontal de 8 px por lado y margen vertical de 4 px. | Negrita 700 sobre el fondo de la barra, con 4 px de relleno por lado. La tipografía marca el centro. |
| Derecha | Cinco grupos nativos. Cada bloque usa `surface`, con `surfaceRaised` reservado a AI Usage. Los bloques están separados por 6 px adicionales a la separación general de 2 px. | Una fila plana. Las parejas quedan próximas y el primer módulo de cada grupo posterior tiene 8 px de margen adicional. Batería y AI Usage ganan peso tipográfico para facilitar la lectura. |
| Estados | Subrayado en hover para los módulos con clic. | Contraste de texto en hover para los mismos módulos. |
| Cambios de configuración | Mueve Wi-Fi y Bluetooth a conectividad, volumen y brillo a multimedia, batería a energía, AI Usage a productividad y bandeja a sistema. | Conserva byte a byte el JSONC de Balanced Refinada. |

Ambas propuestas usan `background` para el fondo, `border` para el borde inferior y `text` para el texto base. Conservan Noto Sans, Font Awesome 7, esquinas cuadradas, contraste de estados y la excepción azul `#4f9dff` del módulo AI Usage. El contorno de foco se aplica donde GTK permite enfocar el módulo. Los grupos de Segmented usan `group/<nombre>`, `orientation: "horizontal"` y `modules`. Waybar 0.16.0 asigna al contenedor el identificador del grupo, que usa la plantilla CSS. Los módulos conservan su definición completa y su orden. [Manual de Waybar](https://github.com/Alexays/Waybar/blob/0.16.0/man/waybar.5.scd.in#L317-L342) · [Implementación de grupos](https://github.com/Alexays/Waybar/blob/0.16.0/src/group.cpp)

### Espacio y centrado

La barra activa de referencia medía **1920 × 32 px lógicos** en el monitor interno. Pango midió los textos de prueba a 12 px con Noto Sans y los glifos de Font Awesome. Se usaron datos ficticios y se sumaron los rellenos, márgenes y separaciones de cada diseño. A la bandeja se le asignaron 3 o 4 iconos de 16 px con sus separaciones configuradas de 6 px.

| Elemento | Uso habitual | Contenido largo |
|---|---:|---:|
| Escritorios de la izquierda, estimación con 5 o 10 botones | 140 px | 280 px |
| Wi-Fi, Bluetooth, audio, brillo y batería, suma de etiquetas | 172 px | 233 px |
| AI Usage, etiqueta ficticia | 76 px | 107 px |
| Bandeja estimada | 60 px | 82 px |
| Reloj en negrita, antes de relleno | 112 px | 121 px |
| Zona derecha en Balanced Refinada | 420 px | 534 px |
| Zona derecha en Segmented | 436 px | 550 px |
| Zona derecha en Refined | 408 px | 522 px |
| Ancho mínimo para centrar Segmented, aproximado | 1000 px | 1237 px |
| Ancho mínimo para centrar Refined, aproximado | 936 px | 1173 px |

El cálculo usa `2 × max(ancho_izquierdo, ancho_derecho) + ancho_del_reloj`, incluido el relleno del reloj y con unos pocos píxeles adicionales sujetos a GTK. A 1920 px hay margen según el modelo. A 1280 px, Segmented se acerca al límite con textos largos. A 1024 px ambos diseños pueden perder el centrado con ese escenario. AI Usage, el estado de red y la cantidad de iconos de bandeja explican buena parte de la variación. También cambian los porcentajes, las conexiones Bluetooth y la fecha localizada. Los escritorios altos amplían la zona izquierda a medida que aparecen. El CSS conserva las etiquetas completas y el JSONC mantiene `fixed-center`. La asignación del widget central sigue dependiendo del espacio que ocupen los laterales en GTK. [Centrado en Waybar 0.16.0](https://github.com/Alexays/Waybar/blob/0.16.0/src/bar.cpp#L804-L818) · [Comportamiento de GtkBox](https://docs.gtk.org/gtk3/method.Box.set_center_widget.html)

**Recomendación.** Probar primero Omarchy Refined porque la jerarquía del reloj y los espacios entre grupos cambian la composición con menor demanda horizontal. Conserva los 32 px y el JSONC actual. Segmented ofrece límites visuales más claros entre conectividad, multimedia, energía, productividad y sistema. Es una candidata apropiada si se prefiere esa separación en la pantalla de 1920 px y se acepta reservar 4 px verticales adicionales.

### Prototipos y candidatos

```bash
cd ~/carbon
stage=$(mktemp -d /tmp/carbon-waybar-concepts.XXXXXXXX)
python -B prototypes/waybar/build.py --output "$stage/candidates"
python -m json.tool "$stage/candidates/segmented.jsonc" >/dev/null
python -m json.tool "$stage/candidates/refined.jsonc" >/dev/null
```

Abrir `segmented.html` y `refined.html` en un navegador. Cada documento es autocontenido y muestra la barra completa en un escenario habitual de 1280 px y otro largo de 1024 px con iconos de bandeja y texto de AI Usage ficticios. El navegador utiliza las fuentes locales. El prototipo adapta la composición mediante CSS web; la altura de widgets, el centrado y las transiciones del compositor requieren validación con Waybar.

El preparador reutiliza el validador de tokens, el renderizador de plantillas y la publicación confinada del motor Carbon. Toma las reglas de escritorios y los estados comunes de la plantilla de Balanced, y combina cada una con su plantilla conceptual. La salida es un único lote con `segmented.css`, `segmented.jsonc`, `segmented.html`, `refined.css`, `refined.jsonc` y `refined.html`. El directorio padre debe existir. Una segunda generación en el mismo destino solo se acepta si todo el lote coincide.

```bash
env -u DISPLAY -u WAYLAND_DISPLAY -u WAYLAND_SOCKET \
  python -B -m unittest discover -s tests/theme -v
python -B tests/scripts/test_interactions.py
python -B tests/screenshots/test_screenshots.py
git diff --check
```

Las seis pruebas nuevas verifican los cambios permitidos de configuración, incluidas las acciones y tooltips; los ocho bloques de escritorios; las diferencias de composición; los prototipos completos; la generación determinista e idempotente; y el rechazo de salidas hacia XDG o mediante enlaces. `GtkCssProvider` de GTK 3.24.52 aceptó ambas hojas sin sesión gráfica. El JSONC pasó la validación JSON y la comparación estructural con la línea base. La compatibilidad de las agrupaciones con los selectores se confirma en el código de Waybar 0.16.0; su geometría e interacción requieren una comprobación gráfica autorizada.

### Instalación posterior y recuperación

Con autorización, verificar las rutas efectivas y la identidad de Balanced Refinada antes de desplegar. Respaldar individualmente las versiones activas con modos, propietarios y SHA-256. Segmented requiere sustituir `~/.config/waybar/style.css` y `~/.config/waybar/config.jsonc`. Refined solo requiere sustituir `~/.config/waybar/style.css`. Aplicar el relevo atómico de archivos con Waybar detenido en una ventana autorizada y arrancar únicamente `waybar.service` tras cotejar los hashes. La recarga de CSS por el portal de apariencia sigue siendo relevante.

Si se necesita revertir, detener la unidad y cotejar tanto los archivos desplegados como el respaldo. Restaurar desde temporales adyacentes con los permisos y propietarios originales, verificar hashes y arrancar la misma unidad. La referencia de rollback para ambas propuestas es **Balanced Refinada**, la versión activa de A.1.

En una validación autorizada, comprobar la altura efectiva, el centrado con cinco y diez escritorios, el foco, los clics, los tooltips y la alineación con etiquetas largas. En Segmented, comprobar también que un módulo oculto por su estado habitual no deje un bloque vacío visible. A esta etapa pertenecen los prototipos y los candidatos de staging. La barra activa sigue usando Balanced Refinada.
