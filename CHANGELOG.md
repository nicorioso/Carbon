# Historial de cambios

## CARBON-006-A · Preferencia GTK Dark aprobada

- Se adoptó `org.gnome.desktop.interface color-scheme=prefer-dark` como preferencia de usuario. Corrige el bajo contraste entre el título claro del CSS existente y el gradiente claro de Adwaita en GTK 4. La validación Wayland llevó el contraste de la muestra de **1,35:1 a 13,52:1**. Se conservaron las hojas CSS, fuentes, iconos y configuraciones vigentes.
- El usuario aprobó GTK 4, libadwaita, Wofi, Dolphin, Kitty y el resto del escritorio en la sesión examinada. El portal principal publicó `1`, los servicios conservaron su estado y los 17 archivos protegidos coincidieron con sus hashes. Pasaron 94 pruebas de Carbon, cinco comprobaciones causales y la matriz Wayland aislada. [Auditoría inicial](docs/GTK-QT-VISUAL-AUDIT.md) · [Resultados y recuperación](docs/GTK4-CONTRAST-FIX.md#carbon-006-a--cierre-técnico)
- Las instalaciones nuevas aplican este ajuste desde la sesión del usuario y registran si la clave tenía un valor explícito para poder restaurarlo. [Instalación de GTK Dark](docs/INSTALL.md#preferencia-gtk-dark)

## CARBON-005-D · Mako Carbon Notifications Compact aprobado

- Compact es la variante oficial de Mako. Carbon Theme Engine genera la configuración de 320 px de ancho, 112 px de altura máxima y relleno de 8 px. La urgencia crítica se distingue mediante el borde y las opciones funcionales se heredan de Mako.
- El usuario confirmó seis validaciones manuales. Se repitieron 94 pruebas automatizadas y se verificó que la configuración activa coincide byte a byte con el candidato. El despliegue aplicó una sola recarga y conservó el PID y el propietario D-Bus.
- El manifiesto privado registra la ausencia previa de configuración de usuario y el procedimiento para recuperar los valores de fábrica. Kitty conserva su personalización independiente. [Despliegue, aprobación y rollback](docs/MAKO-REDESIGN.md#carbon-005-d2--despliegue-de-carbon-notifications-compact)

## CARBON-005-C · Rofi Carbon Power Grid aprobado

- Carbon Power Grid se adopta como tema del menú de energía. Carbon Theme Engine genera la cuadrícula de 2 × 2 y 408 px de ancho para Rofi 2.1.1. Se conservan el script, el atajo y los índices de las cuatro acciones.
- El usuario confirmó las cinco comprobaciones del flujo seguro. La prueba nativa cotejó la selección visible con los índices y confirmó Escape con salida vacía. Las acciones del script se probaron con mocks. Se repitieron las 87 pruebas automatizadas.
- Se verificaron el SHA-256 del Rasi instalado y la integridad del respaldo anterior. [Despliegue, validación y rollback](docs/POWER-MENU-REDESIGN.md#carbon-005-c2--validación-nativa-y-despliegue-de-grid)

## CARBON-005-B · Wofi Carbon Segmented aprobado

- Wofi Carbon Segmented se adopta para el lanzador y el historial con 540 × 396 px declarados. Carbon Theme Engine genera la configuración y el CSS con los tokens compartidos.
- El usuario confirmó seis pruebas manuales en Hyprland, incluidas la apertura de Dolphin y la cancelación segura de cliphist con Escape. Se repitieron las 81 pruebas automatizadas y se verificó la coincidencia byte a byte de los dos archivos activos.
- El respaldo de ambos originales sigue verificado y el procedimiento restaura el par. [Despliegue, pruebas y rollback](docs/WOFi-REDESIGN.md#carbon-005-b2--despliegue-de-carbon-launcher-segmented)

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
