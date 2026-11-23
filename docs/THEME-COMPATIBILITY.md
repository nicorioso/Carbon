# Compatibilidad visual con la línea base

Revisión estática del árbol versionado en `4c1da71`. Los estilos, ajustes y esquemas enumerados coincidían byte a byte con las copias activas al comprobarlos. La columna de migración identifica candidatos para una futura tokenización. La decisión visual sigue separada del cambio técnico.

| Componente | Coincidencias | Candidatos a migración | Excepción justificada o aprobación necesaria |
|---|---|---|---|
| Waybar | Superficie `#1b1b1b`, texto `#f5f5f5`, selección `#d6d6d6` con texto negro, radio 0, Noto Sans 12 px y Font Awesome 7. El tooltip usa borde `#333333`. | Barras divisorias `#292929`, hover `#222222`, tooltip `#151515` y rellenos de 5/7 px. | Revisar densidad, urgencia y los estados de AI Usage. Su azul `#4f9dff` comunica un estado existente y el mismo tono se usa para ocupado y error. Validar un indicador distinguible antes de decidir su tratamiento. |
| Wofi | Superficie, texto, selección, negro sobre selección, foco claro, borde de entrada oficial y radio 0. Usa Noto Sans. | Fondo de entrada `#151515`, texto de 13 px y rellenos de 7/10 px. | El borde claro de la ventana delimita el lanzador. Validar su contraste y legibilidad al cambiar fondo, tamaños o bordes. |
| Rofi | Noto Sans, superficie `#1b1b1b`, texto normal `#f5f5f5`, borde de 2 px. | Selección `#454545` con blanco, borde principal `#f5f5f5`, tamaño 11 pt y relleno de filas de 15/16 px. | Conservar el fondo transparente de los elementos internos donde lo usa el tema. Revisar selección y foco, mantener la legibilidad de las cuatro opciones y comprobar la unidad tipográfica antes de usar 12 px. |
| Kitty | Relleno 12. La configuración usa una familia monoespaciada. | Fondo `#202020`, texto `#e2dcd8`, selección `#80442e`/ `#fff4eb`, bordes y acentos de pestañas. | El ancho fijo y ANSI `color0`–`color15` cumplen una función terminal. Cursor, enlace y campana requieren validación de contraste por separado antes de llevarlos a escala de grises. |
| GTK 3 y 4 | Noto Sans 10, radio 0, texto `#f5f5f5`, selección `#d6d6d6` con texto negro y borde de foco claro. | Fondos `#151515` y `#101010`. Los nombres existentes, incluidos `theme_*` y `accent_*`, requieren un mapeo por versión. | Adwaita oscuro es la base actual. Comparar controles y aplicaciones por versión. La aceptación del parser no prueba la precedencia de los estilos ni su aspecto con libadwaita. |
| KDE | Ventana `27,27,27`, texto general `245,245,245`, selección y foco `214,214,214`, fuente de interfaz Noto Sans. | Fondo de vista `23,23,23`, cabecera `32,32,32`, botón `42,42,42`, tooltip `30,30,30` y texto de selección `21,21,21`. | El esquema Carbon y `kdeglobals` asignan distinto texto a la vista. El primero usa blanco y el segundo los tonos de texto general. Verificar contraste de nombres en Dolphin y precedencia de ambos orígenes antes de unificar. Breeze Dark conserva su función de iconos. |

Los pares de colores que ya coinciden admiten un primer piloto por sustitución de literales por referencias con los mismos valores. Para los demás, conservar el valor actual en la primera prueba de paridad y evaluar cada diferencia antes de adoptar la paleta. Los fragmentos de CARBON-004-A sirven como prueba del motor. Los dotfiles existentes conservan sus estilos.

## Piloto Waybar

El candidato oficial de CARBON-004-B es idéntico al CSS original byte a byte. Usa siete colores compartidos y conserva los cinco literales locales, incluida la excepción azul de AI Usage. La geometría y las acciones se mantienen en sus formatos existentes. El usuario confirmó la apariencia y el funcionamiento de la sesión con la hoja original, idéntica al candidato. [Inventario y procedimiento del piloto](WAYBAR-THEME.md)

## Candidatos Wofi

Compact y Segmented conservan Noto Sans de 13 px, iconos de 24 px y selección clara con texto negro. El campo `#151515` pasa al fondo Carbon en Compact y a la superficie elevada en Segmented. En ambos, el contorno exterior oscuro se distingue del foco claro del campo. Segmented añade un contorno a la lista. Estos cambios se prepararon en staging. [Comparación y límites de Wofi](WOFi-REDESIGN.md)

## Candidatos del menú de energía de Rofi

Grid y List generan un Rasi completo. Sustituyen el gris local `#454545` y el borde exterior claro por superficies y contornos Carbon. La selección usa fondo elevado y borde claro, compatible con los iconos blancos que el script inserta mediante Pango. Se mantiene Noto Sans de 11 puntos. [Diseño, cuadrícula y seguridad del menú](POWER-MENU-REDESIGN.md)
