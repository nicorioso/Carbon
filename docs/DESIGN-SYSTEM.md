# Sistema de diseño Carbon

Carbon combina el minimalismo funcional y la organización modular inspirada en Omarchy con una identidad monocromática propia. La legibilidad y el estado de los controles tienen prioridad sobre los efectos. Mantener esquinas cuadradas, jerarquía clara, animaciones discretas y transparencia localizada.

## Paleta oficial

| Token | Valor | Uso |
|---|---|---|
| `colors.background` | `#121212` | Fondo base. |
| `colors.surface` | `#1b1b1b` | Paneles y controles. |
| `colors.surfaceRaised` | `#252525` | Superficies elevadas. |
| `colors.border` | `#333333` | Separadores y contornos discretos. |
| `colors.selection` | `#d6d6d6` | Fondo de selección y referencia de foco. |
| `colors.text` | `#f5f5f5` | Texto principal sobre superficies oscuras. |

## Semántica y estados

- `textSecondary=#b3b3b3` distingue información secundaria. `textDisabled=#a0a0a0` comunica atenuación. Ambos proceden de los tonos que Waybar ya utiliza.
- `textOnSelection=#000000` forma pareja con `selection` y coincide con Waybar, Wofi y GTK.
- `hover` referencia `surfaceRaised`. `focus` referencia `selection` y el fragmento CSS lo muestra mediante un contorno de 2 px.
- Un estado activo seleccionable puede reutilizar `selection` y `textOnSelection`. El inactivo usa el texto secundario o un indicador propio según su función. El deshabilitado necesita conservar su significado aunque se vea sin color.
- Error, advertencia y éxito quedan en cada consumidor hasta identificar un significado compartido y una pareja de contraste. Usar texto, iconos o marcadores de estado cuando el color por sí solo sea ambiguo. Los acentos funcionales actuales siguen sujetos a revisión por componente. [Compatibilidad](THEME-COMPATIBILITY.md)

## Tipografía, geometría y opacidad

Noto Sans es la familia de interfaz y 12 px es el tamaño de la vista previa. Font Awesome 7 Free Solid y Brands sirven como respaldo de iconos en el fragmento GTK. La rasterización, la escala y el tamaño siguen dependiendo del consumidor. Kitty conserva una familia monoespaciada para columnas y salida de terminal.

El radio por defecto es 0. Los bordes fino y fuerte tienen 1 y 2 px. La unidad de espaciado es 4 px, con rellenos de 8 y 12 px en la vista previa. Un componente puede justificar una excepción por densidad o accesibilidad.

La opacidad de superficie de prueba es 0,97. Se aplica al fondo y deja el texto opaco. La configuración real puede usar una superficie opaca cuando el fondo compuesto no sea predecible.

## Accesibilidad

Ratios calculados en sRGB con colores sólidos. Son referencias de diseño para revisar el resultado en cada aplicación y escala. Como referencia se usan 4,5:1 para texto normal y 3:1 para indicadores visuales necesarios. [Contraste de texto según W3C](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html) · [Contraste no textual según W3C](https://www.w3.org/WAI/WCAG22/Understanding/non-text-contrast.html)

| Par | Ratio aproximado |
|---|---:|
| Texto principal sobre fondo base | 17,18:1 |
| Texto secundario sobre superficie | 8,21:1 |
| Texto deshabilitado sobre superficie elevada | 5,86:1 |
| Texto negro sobre selección | 14,45:1 |
| Foco claro sobre superficie elevada | 10,55:1 |
| Borde discreto sobre superficie | 1,36:1 |

El borde discreto sirve para separación decorativa. Para identificar controles y foco, usar un indicador que contraste con su entorno. Antes de adoptar un tema, revisar foco de teclado, estados seleccionados y deshabilitados, iconos, texto pequeño y transparencia sobre el fondo real.
