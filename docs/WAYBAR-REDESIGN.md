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
| Relleno horizontal de cada indicador derecho | 4 px por lado | 8 px por lado |
| Escritorios | 20 px de ancho mínimo, 4 px de relleno por lado y margen vertical de 4 px | Igual |
| Reloj, altura y orden de módulos | Mismos valores en las dos variantes | Igual |
| Cuándo elegirla | Cuando el ancho disponible es limitado o los estados de la derecha crecen con frecuencia | Para uso habitual si todos los indicadores caben sin presionar el centro |

**Recomendación: Carbon Balanced.** Da más separación a estados que cambian de longitud, como AI Usage y red. En esta configuración de siete módulos a la derecha, supondría hasta 56 px extra de relleno respecto de Compact si todos se muestran. Probar esa holgura con la bandeja visible. Si el reloj pierde espacio, Compact conserva el mismo contraste y los mismos estados con menos relleno.

`--target waybar-compact` y `--target waybar-balanced` usan la misma plantilla `templates/theme/waybar-redesign.css.tmpl` y el mismo motor del piloto. Se selecciona `spacing.unit` o `spacing.small` para los indicadores. El objetivo anterior `--target waybar` conserva el CSS del piloto. El JSONC versionado de la rama es común a ambas variantes y se revisa por separado del CSS generado.

## Tokens y estados

- Fondo base `#121212`, superficies `#1b1b1b`, tooltip elevado `#252525` y separadores `#333333`. La plantilla toma los colores y los anchos de borde de los tokens, con radio 0 y tipografía de 12 px.
- Vacío, texto secundario `#b3b3b3`. Ocupado e inactivo, fondo de superficie, texto principal y un indicador inferior de 1 px. Activo, selección `#d6d6d6`, texto negro y negrita.
- Hover usa la superficie elevada. El foco tiene un contorno de 2 px, claro sobre fondo oscuro y negro sobre selección. La urgencia usa un indicador de 2 px, con contraste adaptado al estado activo.
- Estados apagados o silenciados conservan el tono atenuado. Los estados críticos de batería ganan peso de fuente. El único color local fuera de la escala de grises es `#4f9dff` de AI Usage, conservado para ocupado y error. La distinción entre ambos sigue dependiendo del módulo.
- Las variantes usan superficies opacas y las únicas sombras nuevas son líneas interiores usadas como indicadores. El fondo sin relleno de los botones vacíos deja ver la barra.

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

Los dos CSS se compararon con el parser nativo `GtkCssProvider` de GTK 3.24.52 sin inicializar una sesión gráfica. Las ocho pruebas de rediseño verifican generación, geometría declarada, política de escritorios, módulos, comandos, iconos, sintaxis GTK 3 y confinamiento de salida. Las pruebas existentes verifican que el CSS del piloto todavía se genera con paridad. La altura resultante, los selectores en widgets reales, el centrado, la legibilidad y la desaparición de escritorios altos requieren Waybar en una sesión autorizada. Esta etapa produjo CSS y JSONC de prueba.

## Instalación futura y rollback

1. Con autorización explícita, elegir una variante, confirmar las rutas efectivas de Waybar y verificar que no haya ediciones locales posteriores. Respaldar individualmente CSS y JSONC con modos, propietarios y SHA-256. Mantener también una referencia visual privada.
2. Validar la pareja en staging. Preparar temporales junto a los dos destinos y verificar sus hashes. Reemplazar cada archivo por renombre atómico y aplicar una única recarga autorizada después de verificar ambos. Revisar si hay recarga automática de estilos antes de sustituir el primer archivo. Los dos renombres son independientes, por lo que se debe conservar la relación de los archivos ya aplicados.
3. Si falla una sustitución o la comprobación visual, verificar los respaldos y descartar conflictos con ediciones posteriores. Restaurar los archivos afectados desde temporales con sus permisos originales, verificar sus hashes y aplicar el mecanismo de recarga aprobado. Confirmar que se restablecen la barra anterior y sus diez botones persistentes. [Respaldo general](BACKUP-PLAN.md) · [Verificación de rutas del piloto](WAYBAR-THEME.md#verificación-de-la-sesión-activa)

## Validación manual propuesta

- Medir la capa de 32 px y comprobar esquinas, foco de teclado, hover, urgencia y contraste. Comparar Compact y Balanced con el mismo monitor y escala.
- Confirmar que 1–5 aparecen una sola vez, incluidos los vacíos. Entrar en 6 con un atajo existente, salir con 6 vacío, y repetir con una ventana abierta. Verificar que 6 solo desaparece cuando deja de estar activo y queda vacío. Repetir el límite alto con 10 y comprobar los clics. Si se usa más de un monitor, revisar el comportamiento por barra.
- Verificar que el reloj no se desplaza al cambiar la longitud de los indicadores. Revisar Wi-Fi, Bluetooth, volumen, brillo, batería, AI Usage y bandeja, sin forzar errores ni desconexiones. Confirmar tooltips, iconos y acciones normales.
