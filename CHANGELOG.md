# Historial de cambios

## CARBON-005-A · Waybar Carbon Segmented aprobado

- Carbon Segmented es el diseño oficial de Waybar para la primera versión de Carbon. El usuario aprobó la apariencia en la sesión real, con 36 px efectivos en `eDP-1`.
- Los indicadores se organizan en conectividad, multimedia, energía, productividad y sistema. Los escritorios 1–5 siguen siendo persistentes y 6–10 aparecen con el ciclo de vida de Hyprland. Se conservan los módulos, formatos, acciones y tooltips.
- El cierre repitió 73 pruebas y comparó los archivos activos con los candidatos aprobados. El primer despliegue recuperó Balanced Refinada tras una consulta prematura al journal. El segundo esperó la confirmación de carga y la capa de Hyprland. El respaldo y la restauración quedaron verificados. [Activación y rollback](docs/WAYBAR-REDESIGN.md#carbon-005-a3--activación-controlada-de-carbon-segmented)

## CARBON-005-A.1 · Refinamiento de Waybar Balanced

- Reloj con superficie elevada y más espacio horizontal. Agrupación visual de conectividad, multimedia, energía, productividad y sistema mediante CSS.
- Compact y Balanced comparten plantilla. Escritorios, JSONC y tokens globales intactos. Candidato generado y probado en staging. [Refinamiento Waybar](docs/WAYBAR-REDESIGN.md#carbon-005-a1--refinamiento-de-reloj-e-indicadores)

## CARBON-005-A · Propuesta de rediseño Waybar

- Variantes Carbon Compact y Balanced en una plantilla común, con control de densidad y estados de escritorios diferenciados.
- Configuración versionada con escritorios 1–5 persistentes y ciclo de vida nativo para los demás. Se conservan el reloj centrado, los módulos y sus acciones.
- Candidatos validados en staging. Validación gráfica y despliegue pendientes de autorización. [Propuesta y rollback](docs/WAYBAR-REDESIGN.md)

## CARBON-004-B · Piloto Waybar validado

- Destino de prueba Waybar con plantilla completa y candidato idéntico al CSS actual. Validación GTK 3 y pruebas de paridad, determinismo y confinamiento. El usuario confirmó el funcionamiento y la apariencia en la sesión real. La igualdad byte a byte permitió conservar el CSS activo sin recarga. [Piloto Waybar](docs/WAYBAR-THEME.md)

## CARBON-004-A · Tokens y motor de temas

- Esquema Carbon v1 con los seis colores oficiales, semántica, tipografía, geometría, espaciado y opacidad.
- Motor Python estándar con plantillas GTK CSS y Rasi, validación estricta y publicación conjunta de fragmentos de prueba.
- Cierre técnico tras repetir 20 pruebas del motor, 16 de interacciones y 15 de capturas. Los fragmentos deterministas pasaron validación nativa GTK 3/4 y Rasi. Se conservó la configuración visual activa.

## CARBON-003-C · Robustez de scripts e interacciones

- Validación de JSON e IPC en la navegación relativa de escritorios.
- Auxiliar de historial Wofi que protege el portapapeles en cancelaciones y errores, con cambio de una línea en el Lua versionado.
- Validación de entradas y dependencias en el menú de energía. Wrapper Dolphin conservado y probado.
- Cierre tras instalar `7af124e` y verificar los cuatro destinos. Pasaron 16 pruebas de interacciones, 15 de capturas y las seis comprobaciones manuales. Hyprland 0.57.2 quedó sin errores de configuración y con la recarga automática habilitada. [Guía de scripts](docs/SCRIPTS.md) · [Resultados de pruebas](tests/scripts/README.md)

## CARBON-003-B · Auditoría de arranque

- Cierre documental de la auditoría. En la sesión observada se confirmó un solo `nm-applet` y no se detectaron procesos duplicados.
- Se aprobó conservar los mecanismos de arranque actuales. La prueba de regresión queda pendiente para el próximo inicio normal. [Auditoría y comprobaciones](docs/STARTUP-AUDIT.md)

## CARBON-003-A · Capturas de región

- Separación de cancelación y errores de selección, guardado exclusivo de PNG y copia con MIME explícito.
- Notificación con libnotify. Los fallos posteriores al guardado conservan la imagen.
- Instalación de `9f61874` y cierre funcional tras 15 pruebas automatizadas y seis comprobaciones manuales satisfactorias en Hyprland. Respaldo previo verificado y rollback documentado.

## CARBON-002 · Línea base reproducible

- Inicialización de un Git local y selección explícita de 22 dotfiles sin modificaciones de contenido.
- Verificación parcial de la sesión y registro de los comandos pendientes para una terminal gráfica.
- Respaldo privado de 34 entradas, verificado con SHA-256, y restauración comprobada en staging.
- Documentación de instalación futura, dependencias y cuatro decisiones arquitectónicas. El despliegue, las correcciones y el generador permanecen pendientes.

## CARBON-001 · Auditoría

- Inventario del entorno Arch y Hyprland, configuraciones, dependencias y mecanismos de arranque.
- Identificación del fallo de notificaciones de capturas, dos rutas de lanzamiento de nm-applet y divergencias en la paleta.
- Documentación de arquitectura, hoja de ruta y plan de respaldo.
