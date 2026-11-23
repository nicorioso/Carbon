# Motor de temas Carbon

CARBON-004-A genera dos fragmentos de prueba sin sesión gráfica. El JSON del repositorio es la única fuente editable de valores. Las rutas nativas de las aplicaciones siguen gestionando sus configuraciones.

| Ruta | Responsabilidad |
|---|---|
| `dotfiles/.config/carbon/theme.json` | Tokens Carbon v1. |
| `dotfiles/.config/carbon/scripts/generate-theme.py` | CLI con entrada y salida explícitas. |
| `dotfiles/.config/carbon/scripts/carbon_theme/schema.py` | Carga UTF-8, errores por ruta de token y validación. |
| `dotfiles/.config/carbon/scripts/carbon_theme/render.py` | Adaptación a las gramáticas y sustitución estricta. |
| `dotfiles/.config/carbon/scripts/carbon_theme/output.py` | Validación de destinos y publicación conjunta. |
| `templates/theme/` | Plantillas GTK CSS y Rasi versionadas. |
| `tests/theme/test_theme.py` | Pruebas estándar de Python. |

## Esquema y validación

Todas las secciones y claves de v1 son obligatorias. Las claves desconocidas y duplicadas producen un error. Los valores se interpretan como datos.

| Sección | Contrato |
|---|---|
| `metadata` | `name` igual a `Carbon`, `schemaVersion` entero igual a 1. |
| `colors` | Seis colores oficiales en `#RRGGBB` con normalización a minúsculas en la salida. |
| `semantic` | Tres colores de texto en `#RRGGBB`; `hover` y `focus` referencian una clave de `colors`. |
| `typography` | Tres familias no vacías de hasta 120 caracteres, sin caracteres de control, formato o separadores de línea. `sizePx` es entero de 1 a 96. |
| `geometry` | Radio entero de 0 a 32, anchos de 1 o 2 px y ancho fuerte igual o mayor al fino. |
| `spacing` | Unidad entera de 1 a 32. Rellenos de 0 a 128, múltiplos de la unidad, en orden ascendente. |
| `opacity` | `surface` es un número finito en [0, 1]. Se convierte a un alfa decimal con un máximo de seis posiciones. |

Las medidas enteras rechazan booleanos y decimales. Las familias se emiten como cadenas entre comillas con escapes de barra y comillas, incluso si contienen signos de puntuación o marcadores de plantilla. `string.Template.substitute` solo interpola variables registradas y señala marcadores inválidos o desconocidos. Se procesan las plantillas del destino antes de abrir la salida. El JSON carece de campos para rutas de recursos o comandos.

## Generación aislada

Desde un checkout, con Python 3.10+ en Linux:

```bash
repo="$HOME/carbon"
testdir=$(mktemp -d /tmp/carbon-theme.XXXXXXXX)
python "$repo/dotfiles/.config/carbon/scripts/generate-theme.py" \
  --input "$repo/dotfiles/.config/carbon/theme.json" \
  --output "$testdir/generated"
```

Se generan `carbon-preview.css` y `carbon-tokens.rasi`. El CSS declara colores GTK y se limita a widgets con la clase optativa `.carbon-preview`. El Rasi declara propiedades con prefijo `carbon-` para referenciarlas en un tema de prueba. El script encuentra las plantillas del checkout sin depender del directorio de trabajo. Para una copia independiente, pasar su directorio de plantillas confiables mediante `--templates`. [Cargador CSS de GTK](https://docs.gtk.org/gtk3/method.CssProvider.load_from_data.html) · [Manual de temas Rasi](https://github.com/davatorium/rofi/blob/next/doc/rofi-theme.5.markdown)

El destino optativo `--target waybar` produce un `style.css` completo en su propio directorio de pruebas. El destino predeterminado `preview` produce los mismos dos fragmentos. [Piloto de paridad Waybar](WAYBAR-THEME.md)

## Alcance de escritura

- Crear primero el directorio padre de pruebas y elegir un nombre hijo nuevo. Los fragmentos se preparan en un temporal privado del mismo padre y se publican juntos mediante `renameat2(RENAME_NOREPLACE)`. El destino existente se acepta solo si contiene exactamente los archivos regulares previstos con bytes idénticos. Se conservan sus fechas y modos.
- Se rechazan segmentos `..`, enlaces en el recorrido y los árboles activos de configuración HOME/XDG y de sistema reconocidos por el motor. El recorrido y las operaciones usan descriptores de directorio. Usar un padre de pruebas bajo control del usuario, como el creado con `mktemp -d`.
- Un fallo de escritura controlado retira el temporal y deja intacto cualquier destino previo. Un cierre abrupto puede dejar un directorio oculto `.carbon-preview-*` hermano del destino. La publicación requiere un kernel, libc y sistema de archivos con renombre exclusivo. Destinos en montajes administrados o configuraciones que se ubiquen fuera de las raíces estándar deben revisarse antes de usarlos.
- La salida es UTF-8 con LF y depende solo del JSON validado y de las plantillas. Carece de rutas de despliegue o acciones sobre procesos.

## Pruebas y extensibilidad

```bash
python -B tests/theme/test_theme.py -v
env -u DISPLAY -u WAYLAND_DISPLAY -u WAYLAND_SOCKET \
  rofi -no-config -rasi-validate "$testdir/generated/carbon-tokens.rasi"
```

La suite cubre lectura, esquema, escapes, ambos formatos, determinismo, idempotencia, destinos inseguros y fallos de publicación simulados. Rofi valida la gramática en una prueba automatizada opcional. El CSS también se cargó directamente con `GtkCssProvider` en GTK 3.24.52 y GTK 4.24.1 sin abrir una sesión gráfica. Esto comprueba sintaxis. La apariencia, las clases efectivas y la semántica de un tema importado se validarán por consumidor. [Validador de Rofi](https://github.com/davatorium/rofi/blob/next/doc/rofi.1.markdown)

Para añadir un consumidor, registrar un nombre de archivo y su plantilla, preparar valores escapados para su gramática y agregar pruebas de sintaxis y paridad. La carga de JSON y la publicación permanecen compartidas. Waybar y Wofi pueden compartir fragmentos GTK, con pruebas específicas de selectores y precedencia. GTK 4, Kitty, KDE, Hyprland Lua, Hyprlock, Mako y SDDM requieren adaptadores o plantillas propios y validación individual.

## Despliegue y rollback futuros

Establecer primero una salida por consumidor con paridad de valores respecto de sus archivos actuales. Mantener las excepciones justificadas y revisar cualquier cambio visible con una prueba aislada. Antes de un despliegue autorizado, hacer respaldo por archivo con hash y modo, validar los destinos nativos y aplicar por tandas. Para revertir, restaurar los originales, poner a cuarentena los archivos nuevos y verificar la carga por componente. SDDM y los componentes de sesión requieren pruebas separadas. [Plan de respaldo](BACKUP-PLAN.md) · [Compatibilidad](THEME-COMPATIBILITY.md)
