# Historial de cambios

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
