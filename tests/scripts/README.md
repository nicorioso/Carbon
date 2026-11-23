# Verificación de CARBON-003-C

## Pruebas automatizadas

Reejecución de cierre sobre `7af124e` en Arch Linux. Pasaron **16/16** pruebas de interacciones, **15/15** pruebas de capturas y las comprobaciones de sintaxis de Bash, sh y Lua.

```bash
python tests/scripts/test_interactions.py
python tests/screenshots/test_screenshots.py
```

Las pruebas de interacciones cubren la navegación numérica y sus límites, los errores IPC, la selección y los fallos del historial, la cancelación y las cuatro ramas de energía, y el contrato del wrapper de Dolphin. Los comandos de escritorio se simularon con mocks.

## Validación manual confirmada por el usuario

| Comprobación en Hyprland | Resultado |
|---|---|
| Navegación entre escritorios | Correcto |
| Recuperación del portapapeles | Correcto |
| Cancelación de Wofi | Correcto |
| Menú de energía y cancelación | Correcto |
| Dolphin | Correcto |
| Regresión de atajos principales | Correcto |

El cierre comprobó también que Super+Shift+V usa el auxiliar aprobado en la configuración cargada, que los cuatro archivos instalados coinciden con Git y que `configerrors` está vacío. Los resultados manuales documentan el menú y su cancelación. La cobertura de las acciones de energía corresponde a los mocks. [Estado operativo, integridad y rollback](../../docs/SCRIPTS.md#estado-al-cierre)
