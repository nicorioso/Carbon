# Mako Carbon · CARBON-005-D.1

## Instancia y precedencia

Arch tenía `mako 1.11.0-1` y `libnotify 0.8.9-1`. El único proceso de Mako pertenecía a la unidad de proveedor `mako.service`, activa y deshabilitada para arranque por enlace. El descriptor `fr.emersion.mako.service` asocia `org.freedesktop.Notifications` con la unidad. Es de tipo D-Bus, forma parte de la sesión gráfica y comprueba `WAYLAND_DISPLAY`. El proceso observado poseía el nombre del bus y se ejecutaba como `/usr/bin/mako` sin argumentos ni drop-ins. `GetServerInformation` proporciona la versión de protocolo 1.2 y el literal de servidor `0.0.0` de este código. La versión instalada se identificó con el paquete. El único modo observado era `default`. [Activación auditada](STARTUP-AUDIT.md) · [Datos de servidor en Mako 1.11.0](https://github.com/emersion/mako/blob/v1.11.0/dbus/xdg.c)

El binario busca primero `~/.mako/config` y después `$XDG_CONFIG_HOME/mako/config` con respaldo en `~/.config`. Usa el primer archivo existente. La opción `-c` permite elegir otro y los parámetros CLI reconocidos se aplican tras el archivo. En el entorno del daemon faltaban ambos archivos de usuario y no existían archivos Mako versionados. La configuración efectiva corresponde a los valores de fábrica, contrastados con el manual y el código del paquete. [Resolución y valores de configuración](https://github.com/emersion/mako/blob/v1.11.0/config.c)

## Inventario funcional y visual

| Área | Estado efectivo de la línea base |
|---|---|
| Paleta | Fondo azul `#285577`, texto `#ffffff`, borde `#4c7899` y progreso `#5588aa`. |
| Tipografía | `monospace 10`, título en negrita, cuerpo en la línea siguiente y marcado Pango habilitado. |
| Geometría | Ancho de 300 px, alto máximo de 100 px, relleno de 5 px, margen de 10 px, margen exterior de superficie 0, borde de 2 px y radio 0. Los márgenes de notificaciones apiladas se colapsan al mayor de los dos adyacentes. |
| Posición | Arriba a la derecha en la salida enfocada, capa `top`. El compositor decide la colocación efectiva respecto de zonas exclusivas, como Waybar. |
| Duración | `default-timeout=0`, `ignore-timeout=0`. Se respeta el tiempo del cliente. Sin tiempo positivo resultante, Mako deja la notificación hasta su cierre. |
| Urgencia | Baja, normal y crítica se aceptan. La configuración de fábrica actual carece de reglas que alteren su estilo, orden o duración. |
| Acumulación | Hasta cinco avisos visibles, orden descendente por tiempo y `group-by=none`. Los sobrantes pueden aparecer como contador. El estilo agrupado nativo sigue disponible cuando se configura. |
| Historial | Habilitado y limitado a cinco avisos. La cola se mantiene en memoria. |
| Iconos | A la izquierda, máximo de 64 px, radio 0 e `icon-path` vacío. El servidor anunció `icon-static`. Mako admite imágenes del cliente y busca por nombre en hicolor y pixmaps, con rutas adicionales configurables. Admite parte de la resolución XDG de iconos. La herencia de temas GTK y las rutas de padres requieren configuración explícita. |
| Clic y acciones | Clic izquierdo invoca la acción predeterminada si existe y cierra el aviso. Derecho descarta, central no tiene acción y toque descarta. Las acciones D-Bus siguen habilitadas. `makoctl` ofrece invocación y selector externo. |
| Modos | Solo `default` en la sesión observada. Los modos adicionales son criterios condicionales que requieren reglas. |

`notify-send` sigue utilizando `org.freedesktop.Notifications`. El script de capturas activo lo invoca con nombre de aplicación e icono. La copia, la captura y el historial no formaron parte de la auditoría. Se consultaron únicamente el propietario del nombre del bus, las capacidades, la información de servidor y el modo. No se listaron notificaciones o historial ni se enviaron mensajes. [Manual nativo de Mako](https://github.com/emersion/mako/blob/v1.11.0/doc/mako.5.scd) · [Comportamiento de la notificación de capturas](SCREENSHOTS.md)

## Propuestas y compatibilidad

| | Carbon Notifications Compact | Carbon Notifications Segmented |
|---|---|---|
| Geometría | 320 px de ancho, máximo de 112 px de alto. Relleno y margen de 8 px. | 376 px de ancho, máximo de 144 px de alto. Relleno y margen de 12 px. |
| Superficie y contorno | `surface` en toda la tarjeta y borde de 1 px. | `surfaceRaised` en toda la tarjeta y borde de 2 px. |
| Jerarquía | Noto Sans de 10 pt. Título en negrita y cuerpo con `textSecondary`. | Noto Sans de 11 pt. El título en negrita recibe además el tamaño relativo `large` de Pango. |
| Urgencia crítica | Borde `selection` de 1 px. | Borde `selection` de 2 px. |

Las dos variantes mantienen el anclaje superior derecho, la capa y la selección automática de salida. Los márgenes cambian de 10 px a 8 o 12 px para ajustar el desplazamiento desde el borde y la separación. Las tarjetas son opacas, con radio 0. La capa del progreso usa 15 % de alfa con `selection` para indicar avance sin tapar el texto. Solo el borde cambia para urgencia crítica. Las duraciones, orden, agrupación, modos, historial, iconos, acciones y bindings siguen heredando sus valores nativos.

Mako dibuja una superficie, un contorno y un layout de Pango por notificación. El encabezado y el cuerpo admiten tratamiento tipográfico con `format`, pero comparten la superficie. Segmented usa tamaño y contraste para crear jerarquía. Las dos variantes conservan el texto aportado por la aplicación y el marcado válido del cuerpo puede aportar su propio estilo. Un criterio para cuerpo vacío evita una línea adicional. El formato del contador de excedentes y el formato agrupado conservan la precedencia nativa. No se añaden botones, divisores ni tarjetas internas. Mako ajusta y elide con Pango cuando se alcanza el límite de altura. [Renderizado de Mako 1.11.0](https://github.com/emersion/mako/blob/v1.11.0/render.c) · [Criterios y Pango](https://github.com/emersion/mako/blob/v1.11.0/doc/mako.5.scd)

**Recomendación.** Compact para la primera prueba de sesión. Tiene una jerarquía visible, se acerca a la huella actual y deja más espacio cuando se acumulan varios avisos. Segmented sirve cuando se prioriza la lectura de textos largos y una separación más evidente. Una pila de cinco tarjetas Segmented puede ocupar más altura y ocultar más contenido de las ventanas subyacentes.

## Motor y prototipos

```bash
cd ~/carbon
stage=$(mktemp -d /tmp/carbon-mako.XXXXXXXX)
for variant in compact segmented; do
  python -B dotfiles/.config/carbon/scripts/generate-theme.py \
    --input dotfiles/.config/carbon/theme.json --target "mako-$variant" \
    --output "$stage/$variant"
done
```

`mako-compact` y `mako-segmented` publican `config` y `preview.html` en staging. Comparten las plantillas `mako.conf.tmpl` y `mako-preview.html.tmpl`, los tokens, la validación y la publicación segura del motor. Los tamaños de Pango en puntos y la anchura y altura de tarjeta son ajustes locales.

Cada HTML es autocontenido y muestra cinco casos ficticios simultáneos, incluida una tarjeta de solo título, un cuerpo largo, una urgencia crítica y un icono. Incluye un lienzo de 1920 × 1080 y una vista al 100 %. El glifo de carpeta representa un icono proporcionado por una aplicación. El navegador aproxima los saltos y la elisión. No representa la colocación sobre la sesión ni el renderizado de Mako.

## Pruebas

La regresión pasa **94 pruebas**. Son 63 de temas, 16 de interacciones y 15 de capturas. Las siete nuevas comprueban determinismo e idempotencia, geometría y tokens, la lista permitida de propiedades visuales, confinamiento y protección de Kitty, prototipos autocontenidos, el parser de Mako y el marcado de Pango.

Mako procesa la configuración antes de abrir D-Bus o Wayland. Se apuntaron ambos al aislamiento de staging, con sockets inexistentes. Una opción desconocida produjo un error de parseo. Los dos candidatos alcanzaron el fallo esperado de conexión al bus. Esto valida la aceptación del archivo por el binario sin iniciar un servidor en la sesión. La comprobación Pango es independiente y usa texto ficticio. Brave comprobó los cinco casos y ambas escalas de presentación. Los metadatos y hashes de archivos activos, los atajos y la invocación de Mako siguieron iguales. [Orden de inicialización de Mako 1.11.0](https://github.com/emersion/mako/blob/v1.11.0/main.c)

Kitty fue auditada en CARBON-005-D.0 y se conserva como personalización independiente. La integración queda pospuesta. El SHA-256 de la copia activa y la versionada siguió siendo `37a00a094dfbfe4e9081802f9742ee6615b9c4de6ef865c7713ccd9eec58ff2c`. Bash, las fuentes y las instancias de Kitty se conservaron.

## Despliegue y rollback futuros

1. Obtener autorización para la variante. Confirmar que la ruta de usuario sigue ausente o identificar cualquier archivo nuevo y su precedencia. Validar el candidato Mako desde el commit aprobado.
2. Registrar la presencia previa del archivo y del directorio, más propietario, modo y SHA-256 si existe un original. Guardar ese estado en privado fuera de Git. Preparar un temporal en el directorio de destino y publicar `config` mediante renombre atómico.
3. En una ventana acordada de pruebas, aplicar con `makoctl reload`. Una recarga vuelve a aplicar criterios y recompone superficies de la cola activa. Puede modificar la presentación de avisos abiertos. El código conserva cola e historial en el proceso y rechaza un archivo inválido antes de sustituir la configuración en memoria. Reiniciar libera cola e historial y puede interrumpir la entrega de avisos.
4. Para revertir, cotejar primero el archivo desplegado. Restaurar el original verificado por renombre o mover el archivo a cuarentena cuando el estado inicial era ausente. Comprobar que la ruta anterior y su precedencia se han recuperado. Aplicar una recarga autorizada para volver a los valores anteriores. [Recarga y reaplicación](https://github.com/emersion/mako/blob/v1.11.0/dbus/mako.c) · [Plan de respaldo](BACKUP-PLAN.md)

### Plan de validación en Wayland

Confirmar en Wayland, con datos ficticios y tras autorización, posición junto a Waybar, altura, tipografía, elisión, carga de iconos por nombre y ruta, distinción de urgencia, progreso, expiración solicitada, límite visible, clic y conservación de la cola durante el rollback. Comprobar el flujo de captura con su mecanismo habitual cuando el usuario lo autorice.

## CARBON-005-D.2 · Despliegue de Carbon Notifications Compact

Se instaló **Compact** desde `ab850a0` en `~/.config/mako/config`. La geometría declara 320 px de ancho, 112 px de altura máxima, 8 px de relleno y Noto Sans de 10 pt. El SHA-256 instalado es `bf5bcadc4c261fb3170dadc2ba049651725e258d22315e066d98b9045d95af1d`. El archivo es de modo `0600` y el directorio nuevo, de modo `0700`. Ambos pertenecen al usuario de la sesión.

Antes del cambio estaban ausentes el archivo, el directorio y el archivo alternativo `~/.mako/config`. El [estado previo](BACKUP-PLAN.md) quedó registrado en el manifiesto privado `~/carbon-mako-compact-recovery.CPnsjqzi/manifest.txt`. Ese directorio contiene también el estado anterior y posterior de la unidad, el candidato aprobado y su manifiesto SHA-256. El respaldo documenta la ausencia original y permite verificar el candidato.

Dos generaciones independientes coincidieron con el candidato aprobado. Pasaron las 94 pruebas automatizadas y el parser de Mako aceptó Compact con conexión D-Bus y Wayland bloqueadas en staging. Se consultó el límite exterior del arreglo de avisos en D-Bus. La cola estaba vacía antes de publicar y justo antes de aplicar. La comprobación descartó el mensaje sin entrar en sus diccionarios y no abrió el historial. La recarga puede recomponer avisos que aparezcan entretanto.

El archivo se publicó por renombre atómico desde un temporal adyacente. Una única llamada a `makoctl reload` terminó correctamente. `mako.service` siguió activo con un solo proceso, PID `28875`, propietario D-Bus `:1.30`, la misma invocación de systemd y cero reinicios. El intervalo de recarga quedó sin advertencias ni diagnósticos de configuración en el filtro del journal. Se verificaron el hash activo y el modo `default`. Kitty conservó el SHA-256 `37a00a094dfbfe4e9081802f9742ee6615b9c4de6ef865c7713ccd9eec58ff2c` en sus copias activa y versionada. Bash, los atajos y los demás componentes comprobados conservaron su estado.

### Recuperar el estado sin configuración de usuario

Elegir un momento sin avisos importantes. El comando verifica el candidato instalado y la ausencia de la ruta alternativa. Solo mueve el archivo de este despliegue a una cuarentena privada. Conserva el directorio de Mako y cualquier otro archivo.

```bash
(
  set -euo pipefail
  umask 077
  backup="$HOME/carbon-mako-compact-recovery.CPnsjqzi"
  config="$HOME/.config/mako/config"
  legacy="$HOME/.mako/config"
  (cd "$backup" && sha256sum -c SHA256SUMS)
  test "$(realpath -- "${config%/*}")" = "${config%/*}"
  test -f "$config" && test ! -L "$config" && test -O "$config"
  test ! -e "$legacy" && test ! -L "$legacy"
  cmp -- "$config" "$backup/compact-approved.config"
  systemctl --user is-active --quiet mako.service
  pid=$(systemctl --user show mako.service -p MainPID --value)
  owner() {
    busctl --user call org.freedesktop.DBus /org/freedesktop/DBus \
      org.freedesktop.DBus GetNameOwner s org.freedesktop.Notifications
  }
  original_owner=$(owner)
  quarantine=$(mktemp -d "$backup/rollback.XXXXXXXX")
  cmp -- "$config" "$backup/compact-approved.config"
  mv -T --no-clobber -- "$config" "$quarantine/config"
  test ! -e "$config" && test ! -L "$config"
  test ! -e "$legacy" && test ! -L "$legacy"
  cmp -- "$quarantine/config" "$backup/compact-approved.config"
  makoctl reload
  systemctl --user is-active --quiet mako.service
  test "$(systemctl --user show mako.service -p MainPID --value)" = "$pid"
  test "$(owner)" = "$original_owner"
)
```

Al completar el comando, la búsqueda de configuración devuelve ambas rutas ausentes y Mako reaplica sus valores de fábrica. Si la recarga falla, conservar la copia en cuarentena y revisar el estado del servicio. Un reinicio requiere autorización separada.

### Aprobación funcional y visual

El usuario aprobó **Carbon Notifications Compact** como variante oficial y confirmó las siguientes seis comprobaciones:

| Validación manual | Resultado |
|---|---|
| Diseño | Correcto. |
| Posición | Correcto. |
| Texto | Correcto. |
| Comportamiento | Correcto. |
| Urgencia | Correcto. |
| Integridad | Correcto. |

En el cierre se repitieron las 94 pruebas automatizadas. Dos generaciones desde `ab850a0` coincidieron entre sí y con el archivo activo y la copia del manifiesto. El binario de Mako volvió a aceptar el candidato en aislamiento. `mako.service` se mantuvo activo con PID `28875`, una sola instancia, cero reinicios y `:1.30` como propietario de `org.freedesktop.Notifications`. Se verificaron la integridad del manifiesto y la copia aprobada. El cierre no recargó el servicio. Kitty, Bash y los demás componentes comprobados conservaron su estado.

La aprobación cubre la sesión examinada. La geometría, la elisión y el contraste con otras resoluciones, fuentes o escalas quedan fuera de esa validación. El procedimiento de rollback al estado sin archivo se ensayó en staging con recarga simulada.
