# Hoja de ruta

| Etapa | Prioridad y dependencias | Criterio de aceptación |
|---|---|---|
| CARBON-001 · Auditoría | P0, línea base | Inventario documentado con actividad observada, fallo de capturas, riesgo de arranque duplicado, límites del sandbox y plan de restauración. |
| CARBON-002 · Línea base reproducible | P0, autorización explícita y auditoría | Confirmar IPC, rutas de sesión y applets. Crear repositorio Git local con selección explícita y sin remoto. Documentar dependencias y ADR inicial. Ensayar backup y restore en staging y verificar exclusiones. |
| CARBON-003 · Correcciones funcionales aisladas | P1, CARBON-002 | En pruebas, captura exitosa escribe, copia y notifica. Cancelación no genera PNG ni cambia el portapapeles. Validar contrato de navegación por espacios y decidir el arranque único del applet con evidencia. Cambios y rollback por separado. |
| CARBON-004 · Generador | P1, CARBON-002 | JSON validado con Python estándar. Dos ejecuciones producen los mismos bytes. Las salidas parsean por consumidor y las divergencias visuales quedan documentadas con su aprobación pendiente. |
| CARBON-005 · Piloto y adopción por componente | P2, respaldo probado y CARBON-004 | Validar en orden Wofi/Rofi, Waybar, Kitty/GTK/Qt y luego Hyprland/Hyprlock. Cada tanda tiene diff, prueba de interacción y restauración verificable. |
| CARBON-006 · Greeter y distribución | P2, piloto y aprobación separada | Validar tema Qt 6 fuera del greeter en uso, dependencias y recursos redistribuibles. Demostrar recuperación de la pantalla de acceso en entorno de prueba antes de considerar despliegue al sistema. |

## Orden y decisiones

Priorizar respaldo y verificación de sesión. La corrección funcional y el generador pueden avanzar independientemente tras CARBON-002. Mantener el rediseño visual sujeto a aprobación específica. Registrar decisiones de arranque, despliegue, excepciones de paleta y tratamiento de datos en ADR. Registrar cambios funcionales y procedimientos actualizados en el changelog.
