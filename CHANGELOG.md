# Changelog

Todos los cambios destacados de Bitty Mascot. El historial se agrupó por bloques de trabajo a partir de las sesiones de desarrollo; las versiones anteriores a `1.8.1` no se publicaron como releases.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [2.4.0] - 2026-11-23

### Añadido
- **Paquete específico de Fedora**: `Bitty-Fedora.zip`, con el binario compilado dentro de un contenedor `fedora:latest` y un instalador propio (`install-fedora.sh`).
- El zip de Fedora incluye `agent/bitty.md`, para que el agente de OpenCode reconozca a Marcelbon por su nombre y responda siempre en español, igual que la mascota flotante.
- **Nuevo job `fedora`** en `.github/workflows/build.yml`; la release pública ahora adjunta cuatro zips (Windows, macOS, Linux y Fedora).

### Cambiado
- Versión del plugin y de la documentación actualizada a 2.4.0.
- Se regeneran los paquetes de macOS y Linux en la misma release.

### Verificado
- Sintaxis del instalador comprobada con `bash -n`.
- Workflow completo en verde: compilan Windows, macOS, Linux y Fedora, y la release publica los cuatro zips.
- `Bitty-Fedora.zip` revalidado tras la publicación: 388 entradas, `testzip` limpio, binario `Bitty/Bitty`, `agent/bitty.md` con la identidad y el nombre de Marcelbon, e `install-fedora.sh` con la ruta correcta del binario.
- Sin cambios en el código TypeScript: la opinión, la lectura de sesiones y el permiso siguen como en v2.3.0.

### Corregido durante la publicación
- El contenedor Fedora necesitaba `kernel-headers`, `python3-devel` y `gcc` para compilar `evdev`.
- El agente se copiaba a la raíz del paquete en vez de a `agent/`; el zip publicado fue reemplazado con la estructura correcta y el workflow quedó arreglado para futuras versiones.

---

## [2.3.0] - 2026-11-23

### Añadido
- **Fase 3 — mirar sesiones del proyecto**: `/bitty-ver` (atajos `Ctrl+Alt+V` en TUI y `Mod+Alt+V` en Desktop) lee un resumen acotado de hasta 6 sesiones y 6 mensajes por sesión, con 240 caracteres por mensaje, y lo muestra en el panel. No escribe en la conversación ni copia contenido sensible.
- **Fase 4 — instalar capacidades con permiso**: `/bitty-instalar` (atajos `Ctrl+Alt+I` / `Mod+Alt+I`) ofrece un catálogo cerrado con una única capacidad inicial: `navegador` → MCP `bitty-navegador` (`npx -y @playwright/mcp@latest`).
- **Permiso nativo obligatorio**: un hook de evaluación fuerza `ask` para `bitty.install.mcp`, así que aparece el diálogo de OpenCode antes de instalar. No se usa `save`: la aprobación no se recuerda.
- **Aviso contextual**: si la sesión habla de una web y el MCP no está instalado, Bitty sugiere en el panel usar `/bitty-instalar`.
- Botones **Ver sesiones** e **Instalar ver el navegador** en el panel de Desktop y opciones nuevas en la píldora del composer.
- Contrato RPC compartido (`src/shared/rpc.ts`) para que TUI y Desktop pidan la instalación al plugin servidor, que es donde viven `permission.assert` y `mcp.transform`.

### Cambiado
- La documentación aclara que no existe una API genérica de captura de pantalla en OpenCode: «ver el navegador» significa instalar el MCP y que OpenCode lo use con sus herramientas, previo permiso.
- Dependencias declaradas: `@opencode/schema` y `effect`, usadas por el contrato RPC.

### Verificado
- `npm run typecheck` y `npm run build` pasan con `@opencode/plugin` 2.3.2.
- Prueba real en PTY: `/bitty-ver` muestra en el panel `He mirado 6 sesiones del proyecto` y los títulos; `/bitty-instalar` abre el estado `blocked:kind=permission` de OpenCode y, tras la respuesta, conecta `bitty-navegador`.
- Sin `panic` y sin mensajes de error en la TUI.

### Nota
- Los binarios de la mascota flotante son idénticos a los de v2.2.0. La GUI de Desktop se verificó después con capturas reales y OCR de Windows: panel, botones y píldora de Bitty aparecen correctamente.

---

## [2.2.0] - 2026-11-23

### Añadido
- **Bitty opina**: sugerencias sobre la sesión actual, siempre como consejo y nunca escritas en la conversación de Marcelbon.
- Comando `/bitty-opina` y atajos `Ctrl+Alt+O` (TUI) y `Mod+Alt+O` (Desktop), además del botón «Pedir opinión» en el panel y de la opción en la píldora del composer.
- **Resumen muy corto en la propia mascota**: la barra/píldora muestra `Bitty 💡 SIGUE`, `Bitty 💡 REVISA` o `Bitty 💡 PARA`; el panel muestra el detalle completo en tres líneas: **Veredicto**, **Razón** y **Siguiente**.
- **Aviso automático al terminar la sesión**: cuando OpenCode se asienta, Bitty calcula una sugerencia local y la deja lista. No interrumpe ni escribe nada.
- Cuatro caras nuevas: `[?_?] OPINANDO`, `[^_^] SIGUE`, `[o_O] REVISA ESTO` y `[>_<] MEJOR PARAR`.
- Motores compartidos `src/shared/opinion.ts` y `src/shared/opina.ts` para TUI y Desktop.

### Cambiado
- La opinión funciona en dos niveles: **heurística local** inmediata y sin coste, y refinado opcional con el modelo. Si el modelo no tiene cuota (429/502), Bitty conserva la sugerencia local en vez de mostrar un error.
- La sugerencia se basa solo en la sesión actual. «Ver todo» (varias sesiones/proyectos) queda para la Fase 3, cuando existan las APIs de observabilidad previstas.

### Verificado
- `npm run typecheck` y `npm run build` pasan con `@opencode/plugin` 2.3.2.
- Prueba real en PTY: `Bitty [o_o] HI` al iniciar, `Bitty 💡 REVISA` al terminar una sesión sobre un bug, y panel con `Veredicto: REVISA`, razón y siguiente paso.
- Sin mensajes de error, sin `panic` y sin escrituras en la conversación de la sesión.

### Nota
- Los binarios de la mascota flotante no cambian respecto a v2.0.1. La GUI de Desktop sigue pendiente de prueba visual porque la app no está instalada en el equipo de desarrollo.

---

## [2.1.0] - 2026-11-23

### Añadido
- **Bitty como plugin de OpenCode**, con las tres partes en un mismo paquete: servidor (`src/index.ts`), terminal (`src/tui.tsx`) y Desktop (`src/gui.tsx`).
- **Integración estilo Claude Code**: indicador permanente en la barra del prompt de la TUI, panel de mascota, comando `bitty.panel` con `Ctrl+Alt+B` y `/bitty`; en Desktop, panel lateral, píldora del composer, entrada en el menú, comando con `Mod+Alt+B` y presencia en la barra inferior.
- **Mascota reactiva**: 8 caras ASCII (`HI`, `PIENSA`, `TOOL`, `ESCRIBE`, `LISTO`, `ERROR`, `PERMISO`, `ZZZ`) traducidas desde eventos reales de OpenCode (`session.*`, `permission.*`, `form.created`), con retorno automático a `HI`.
- `plugin/gui-dist/gui-experimental.cjs` versionado y `scripts/copy-bundle.mjs` para regenerarlo tras `npm run build`.
- `plugin/README.md` con instalación en `cli.json` (terminal) y `opencode.jsonc` (Desktop), tabla de eventos y comprobación de carga.
- `node_modules/` añadido a `.gitignore`.

### Verificado
- `npm run build` y `npm run typecheck` pasan con `@opencode/plugin` 2.3.2 y OpenCode 2.3.2.
- Logs de `--standalone --print-logs --log-level debug`: el servidor carga `src/index.ts` y `gui-dist/gui-experimental.cjs`.
- Prueba en PTY de la TUI: aparece `Bitty [o_o] HI` en inicio y prompt, se observa la secuencia `PIENSA → ESCRIBE/TOOL → LISTO` al enviar un mensaje y `/bitty` abre el panel dentro de una sesión.

### Nota
- Los binarios de la mascota flotante no cambian; los ZIP de este release son los mismos de v2.0.1. La GUI de Desktop no se pudo probar visualmente porque la app no está instalada en el equipo de desarrollo.

---

## [2.0.1] - 2026-11-23

### Cambiado
- El agente de Bitty conoce ahora el nombre del usuario: **Marcelbon**, y lo trata por su nombre. Se actualizó tanto el archivo instalado (`~/.config/opencode/agents/bitty.md`) como el texto de respaldo que crea la aplicación.
- Autoría del proyecto actualizada a **Marcelbon** en README, licencia, aviso de IA y guía rápida.

### Nota
- La identidad de Bitty no cambia: sigue respondiendo exactamente «Soy Bitty, tu mascota de OpenCode».

---

## [2.0.0] - 2026-11-23

### Añadido
- **Multiplataforma**: reescritura completa en **Python 3 + PySide6**. Bitty funciona ahora en Windows, macOS y Linux con un solo código.
- **Temas**: `NAVIDAD` (gorro rojo con pompón y acento rojo) y `HALLOWEEN` (calabaza y acento naranja), además del original `OPENCODE` y el modo `AUTOMÁTICO` que elige según el mes (diciembre/octubre). Se cambian desde el menú derecho → **> TEMA**.
- Los sprites se recolorizan en memoria con Pillow (21 PNG base, sin duplicados por tema) y el fondo `0C0C0C` pasa a alfa 0 para no dejar cuadro oscuro en Qt.
- `build.py` + `.github/workflows/build.yml`: PyInstaller genera `Bitty-Windows.zip`, `Bitty-macOS.zip` y `Bitty-Linux.zip` al publicar un tag `v*`.
- `install.sh` / `uninstall.sh` para macOS y Linux (venv, LaunchAgent en macOS, `systemd --user` en Linux).
- `run_bitty.py`: entry point con import absoluto, necesario para PyInstaller.
- Atajo `⌘+Alt+B` en macOS además de `Ctrl+Alt+B`.
- Tecla `Esc` para cerrar el bocadillo.

### Cambiado
- La versión PowerShell v1 se movió a `legacy/powershell/` y queda solo como referencia histórica.
- `requirements.txt` con PySide6, Pillow y pynput.
- `state.json` portable: usa `APPDATA` en Windows y `XDG_CONFIG_HOME`/`~/.config` en macOS/Linux; guarda también el tema elegido.
- README y `docs/INSTALACION.md` reescritos para los tres sistemas.

### Corregido
- Fondo opaco de los PNG: ahora se vuelve transparente en Qt.
- El ejecutable empaquetado fallaba al arrancar por el import relativo de `bitty/__main__.py`; se usa `run_bitty.py`.
- Los manejadores de archivos de salida se cierran en el proceso padre tras lanzar la CLI.

---

## [1.8.1] - 2026-11-23

### Añadido
- **Repositorio público y portable**: ya no hay rutas de usuario grabadas en el código.
- `install.ps1` y `uninstall.ps1` para instalar/desinstalar en un paso.
- `Ensure-BittyAgent`: Bitty crea sola `~/.config/opencode/agents/bitty.md` si no existe.
- Detección automática de OpenCode (npm global, `%LOCALAPPDATA%`, ruta del programa y `PATH`).
- Variable de entorno `BITTY_WORKDIR` para elegir el directorio de trabajo de OpenCode.
- `AI_DISCLOSURE.md`, `README.md`, `CHANGELOG.md`, `LICENSE` y `docs/INSTALACION.md`.

### Cambiado
- `SpriteDir` usa `$PSScriptRoot` en lugar de `C:\Users\marce\Downloads\BittyMascot\sprites`.
- `generate-sprites.ps1` genera los PNG junto al script, sin rutas fijas.
- BOM UTF-8 verificado en ambos scripts para que los acentos se lean bien en PowerShell 5.1.

---

## [1.8.0]

### Cambiado
- **Bitty baja 22 px** cuando aparecen **SEGUIR / ABRIR APP / COPIAR** (centro del sprite de 262 a 284; formulario de 300 a 322 px de alto). Antes el sprite quedaba detrás de los botones.
- **ABRIR APP ensanchado** de 66 a 88 px para que el texto no quede estrecho.
- `COPIAR` movido a x=210 para dejar espacio junto al botón ensanchado.
- La ventana crece hacia abajo y el ancla usa el mismo centro, así que el sprite no salta en pantalla al recibir la respuesta.

---

## [1.7.0]

### Añadido
- **SEGUIR**: vuelve al campo de texto dentro de la misma conversación. Captura el `sessionID` del JSON de OpenCode (`--format json`) para conservar el contexto.
- **ABRIR APP**: abre la aplicación de OpenCode con `--session <id>` para continuar en el escritorio.
- Las respuestas reales permanecen visibles **60 segundos** (antes se cerraban a los 9 s y no daba tiempo a pulsar nada).
- Parseo de la salida JSON de OpenCode (`Get-BittyReply`) para extraer texto e ID de sesión.
- Título de sesión automático `BITTY yyyyMMdd-HHmmss`.

### Corregido
- El fallo «no puedes preguntarle más»: era el cierre automático a los 9 s, no un problema de envío.

---

## [1.6.0]

### Añadido
- **Identidad propia**: agente `~/.config/opencode/agents/bitty.md` con un contexto corto en español.
- Todos los mensajes se envían con `--agent bitty`. Si le preguntas quién es, responde *«Soy Bitty, tu mascota de OpenCode»* en vez de decir que es otro asistente o modelo (antes contestaba que era Big Pickle).
- El agente no afecta a las sesiones normales del usuario.

---

## [1.5.0]

### Añadido
- Placa **`BITTY`** bajo el sprite en reposo y cabecera `> BITTY / OPENCODE` en el bocadillo.
- Texto de un solo bit para la placa: evita el halo oscuro sobre la ventana transparente.
- Historial de mensajes con `↑`/`↓` (últimos 30).
- Atajo global `Ctrl+Alt+B` (con varios IDs de reserva y fallback a `Ctrl+Alt+J`).
- Persistencia en `%APPDATA%\BittyMascot\state.json`: posición, pausa del paseo y sesión elegida.
- Saludo con cara feliz al arrancar.

### Corregido
- Firma P/Invoke duplicada de `SendMessageW`: se separaron las versiones con `StringBuilder` e `IntPtr` para evitar crashes.

---

## [1.4.0]

### Añadido
- **Texto completo sin recorte**: se eliminó el límite de 100 caracteres.
- **Scroll propio con GDI** en lugar del `TextBox` nativo: fondo `161616`, texto `FAFAFA`, barra `4B4B4B`. Ya no parece un control blanco ajeno al tema.
- Navegación de la respuesta con rueda, flechas, `RePag`/`AvPag`, `Inicio`/`Fin` y clic en la barra.
- **Multimonitor**: el área de paseo cubre todas las pantallas conectadas, calculada una sola vez al arrancar.
- Pausa/reanudación del paseo desde el menú contextual.
- Botones de respuesta movidos a la fila `y=222`, debajo del panel, para no tapar el texto.

### Cambiado
- Panel del bocadillo ampliado a 340×300 con área de respuesta de 296×142.

---

## [1.3.0]

### Añadido
- Selector de sesión: **NUEVA** (por defecto) o elección de una sesión anterior del desplegable (8 más recientes).
- Las sesiones anteriores se abren con `--session <id>` concreto; **nunca `--continue`**, para no engancharse a la conversación activa del usuario.
- Desplegable sin duplicados: `(ultima: <título>)` y sufijo `#<últimos 4 del id>` cuando hay títulos repetidos.
- Aviso con cara de duda cuando no hay sesión anterior.

---

## [1.2.0]

### Añadido
- Botón **COPIAR** (última respuesta al portapapeles) y **CANCELAR** (mata el proceso de OpenCode, muestra `< Cancelado.` con cara de duda).
- `Stop-Waiting()` centralizado: al salir, cancelar, cambiar de modo o enviar otro mensaje se detiene también OpenCode.
- Menú contextual integrado (sin `MessageBox`): hablar, pausar paseo, salir; después ampliado con copiar respuesta, repetir último mensaje y volver al centro.

---

## [1.1.0]

### Añadido
- Estilo visual oficial de OpenCode: paleta `0C0C0C`, `161616`, `1A1A1A`, `4B4B4B`, `8F8F8F`, `AEAEAE`, `DBDBDB`, `FAFAFA` y acento `6B8FFF` solo para foco/estado activo.
- Tipografía `Consolas` y sprites GDI propios de 64×64 dibujados a tamaño natural con `NearestNeighbor` (sin halo oscuro ni escalado).
- Expresiones y reacciones según el tono de la respuesta, caras rotativas en reposo y caras cambiantes mientras espera.
- Dos frames de caminata (`walk1`, `walk2`).
- Lectura UTF-8 de respuestas y títulos (BOM en el script para PowerShell 5.1).

### Corregido
- Eliminado el marco/halo oscuro alrededor del personaje.

---

## [1.0.0]

### Añadido
- Primera versión: mascota flotante `TopMost`, sin marco, que pasea en un área pequeña.
- Clic izquierdo abre un bocadillo integrado con campo de texto, **ENVIAR** y **SALIR**.
- Envío de mensajes a `opencode run` con la ruta absoluta al ejecutable de la CLI.
- Arrastrar por el escritorio y doble buffer para evitar parpadeos.
