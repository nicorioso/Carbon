# Historial de cambios

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
