# Changelog

Todos los cambios destacados de Bitty Mascot. El historial se agrupó por bloques de trabajo a partir de las sesiones de desarrollo; las versiones anteriores a `1.8.1` no se publicaron como releases.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

---

## [2.5.5] - 2026-11-24 - recetas reutilizables y bocadillo que no mueve a Bitty

### Añadido
- **Recetas de Bitty** (`bitty/recipes.py`, `plugin/src/shared/recipes.ts`, tool `bitty_recipe`): memoria local de planes visuales en `BittyMascot/recipes.json`, con `guardar`, `listar`, `ejecutar` y `olvidar`. Esquema cerrado: solo Brave, HTTPS de `mail.google.com`/`accounts.google.com`, 1–12 pasos de tipos `open`, `navigate`, `look`, `click` y `verify`, pistas de hasta 60 caracteres. Sin usuario, contraseña, tokens ni comandos.
- **Nuevos endpoints del puente**: `GET /recipes` (con token) y `POST /recipes` para guardar/listar/olvidar sin tocar el escritorio; `POST /launch` (con acuerdo y whitelist) abre Brave, opcionalmente en una URL permitida. `/launch` y las acciones siguen pasando por `on_gate`.
- **Permiso nativo nuevo** `bitty.recipe`, siempre `ask`, sin `save`. El orden sigue siendo acuerdo → permiso → acción.

### Corregido
- **«Cuadro mal dibujado» en la ventana flotante**: era la cola del bocadillo, un `drawRect(QRect(12, 200, 10, 8))` vacío. Ahora se dibuja con `QPainter.drawPolygon` como una cola triangular que apunta a Bitty desde arriba, abajo, izquierda o derecha.
- **Bitty se movía al abrir la conversación en una esquina**: `_update_location` probaba las cuatro esquinas del bocadillo y elegía la que cabía sin reescribir el ancla. Si se abre hacia abajo, el panel baja 84 px y la ventana crece 44 px; la mascota y su cursor se quedan donde estaban.

### Verificado
- 34/34 tests Python y 16 tests Node; `typecheck`, build del plugin y build del `.exe` en verde.
- Prueba real del `.exe` con `state.json` en `(60,60)` y paseo pausado: antes `(18,18) 84×84`, después de `> HABLAR` `(20,18) 340×344`, ancla y ventana del cursor inalteradas.
- Recetas rechazan claves extra, correos en la etiqueta, `http://`, dominios ajenos, credenciales en la URL y pistas con secretos.

---

## [2.5.4] - 2026-11-24 - acuerdo en la instalación y puerta reforzada

### Añadido
- **`ACUERDO.md` en los cuatro paquetes**: `build.py` lo copia junto al binario (o en `Contents/Resources` en macOS) y el workflow lo añade al zip de Fedora. `install-fedora.sh` lo muestra al instalar, espera 3 s y lo copia a `~/.local/share/BittyMascot/ACUERDO.md`.
- **Puerta central del acuerdo en el puente** (`on_gate`): `/cursor`, `/click` y `/capture` la ejecutan antes de cualquier acción, sin depender de que el plugin haya llamado antes a `/agreement`. Los callbacks siguen comprobándolo como segunda capa.

### Corregido
- **Fallaba la comprobación de `/capture`**: se llamaba a `on_capture()` sin el callback que espera; la excepción se tragaba y una petición directa con token podía capturar sin acuerdo. Ahora `Bridge.capture()` pasa el trabajo correctamente y convierte un rechazo en HTTP 403.
- **El acuerdo no aparecía en llamadas directas**: `_gate_action` encolaba el diálogo sin callback y `_apply_bridge_queue` fallaba al abrirlo. La acción se bloqueaba, pero Bitty no mostraba el acuerdo; ya se encola bien y hay un test que lo verifica.
- **Tests HTTP estables en Windows**: se consumen todas las respuestas (401/400/403) para reutilizar la conexión sin `ConnectionAbortedError`.

### Verificado
- 29/29 tests Python, 15 tests Node, `typecheck` y build en verde. `ACUERDO.md` coincide con las 4 líneas del diálogo; se comprueba que se copia al paquete, que el workflow lo incluye en el zip de Fedora y que el instalador lo muestra y lo copia.

---

## [2.5.3] - 2026-11-24 - acuerdo breve antes de usar visión o cursor

### Añadido
- **Acuerdo de Bitty en 4 líneas** (`bitty/agreement.py`, `bitty/agreement_dialog.py`): se muestra antes de `bitty_screen`, `bitty_cursor` y `bitty_click`. El botón `ACEPTO` permanece desactivado 6 s para leerlo sin saltarlo; `RECHAZAR` corta la acción. La versión aceptada se guarda en `state.json` y se puede volver a abrir con `> ACUERDO: LEER`.
- **Endpoint `/agreement` en el puente**: el plugin lo llama antes de `permission.assert`, por lo que el orden es acuerdo → permiso nativo → acción. Un rechazo devuelve HTTP 403 y no pide permiso ni captura.
- **Puerta de seguridad en el puente**: `/cursor`, `/click` y `/capture` devuelven 403 si el acuerdo no está aceptado, aunque se llamen directamente.

### Corregido
- **CI headless**: los tests que importan `bitty.app` fallaban en Ubuntu por falta de `libEGL.so.1`. El workflow instala `libegl1` y fija `QT_QPA_PLATFORM=offscreen` (el CI de v2.5.2 se quedó sin release por esto).

### Verificado
- 24/24 tests Python y 15 tests Node con `typecheck` en verde; build local y `.exe` desplegado con el diálogo visible; rechazo del acuerdo comprobado de extremo a extremo (HTTP 403, sin permiso ni captura).

---

## [2.5.2] - 2026-11-24 - compatibilidad macOS/Linux

### Añadido
- **Atajo híbrido `Ctrl+Alt+B`**: `QShortcut` con contexto de aplicación en la ventana principal y en el atajo de gaming, además de `pynput`. Funciona cuando la app tiene foco aunque `pynput` no pueda registrar un hotkey global (Wayland o macOS sin permiso de accesibilidad). Un filtro de 0,4 s evita la doble acción si ambos disparan.
- **Búsqueda del logo en los cuatro bordes** (`bitty/icon_finder.py`): `find_icon(..., all_edges=True)` mira abajo, arriba, izquierda y derecha. `_bitty_click` lo usa en macOS/Linux, donde el dock o el panel no está necesariamente abajo; Windows mantiene la franja inferior.

### Corregido
- **Estilos de cursor seleccionables**: en v2.5.1 el dict de estilos quedaba sombreado por la ruta `SPRITES` de los PNG, así que `> CURSOR: ESTILO` no cambiaba nada. Se renombró a `CURSOR_STYLES` y se verifica con test.
- Apilado del cursor fuera de Windows: la ruta no-Windows usa `raise_`/`lower` de Qt sin tocar `ctypes.windll`; cubierto por test.

### Verificado
- 22/22 tests Python, tests Node y `typecheck` en verde; build de los cuatro sistemas en CI.

---

## [2.5.1] - 2026-11-24 - clic virtual, gaming y estilos de cursor

### Añadido
- **Herramienta `bitty_click` y endpoint `/click`**: el cursor de Bitty se mueve a unas coordenadas y muestra su propio clic visual (anillo animado). Opcionalmente abre una app de una **whitelist cerrada** (`brave`); nunca se acepta un comando arbitrario. Permiso nativo `bitty.click` cada vez, sin `save`.
- **Clic con visión en la barra de tareas** (`bitty/icon_finder.py`, `bitty/desktop_action.py`): al pedir `open: "brave"`, Bitty captura la pantalla, localiza el logo por correlación de plantilla (FFT por ejes, ~1 s) y lleva su cursor hasta él. La activación del botón se hace en el instante del clic sin mover el puntero del usuario.
- **Cursor aparcado tras Bitty**: antes estaba siempre visible; ahora queda detrás de la mascota y solo sale durante la acción. Al terminar **no desaparece**: vuelve caminando hasta la espalda de Bitty y se queda ahí, bajando de z-order para que el sprite lo tape. Sigue siguiendo a Bitty cuando pasea. Se puede sacar a la vista con `> CURSOR: MOSTRAR`.
- **Cuatro estilos de cursor** (`bitty/cursor_sprite.py`): los cuatro usan la misma flecha clásica **completa** de 16×16 (32×32 px), rellena y con su muesca, y cambian con OPENCODE/NAVIDAD/HALLOWEEN. `CLASICO` (contorno negro, cuerpo blanco, filete del tema y prompt `>`), `NEON` (filo brillante, contorno neón e interior oscuro), `TERMINAL` (cuerpo del tema con líneas de escaneo) y `BITTY` (ojos y prompt en negro). Se eligen en `> CURSOR: ESTILO` del menú derecho y se recuerdan en `state.json`. Por defecto entra `CLASICO`.
- **Vuelta animada del cursor**: tras el clic hay una pausa breve para ver el anillo, luego el cursor regresa describiendo un arco suave y más lento, se atenúa al final y se mete bajo el sprite de Bitty sin desaparecer de golpe.
- **Modo gaming** (`bitty/gaming.py`): nueva opción `> GAMING: ACTIVAR` en el menú del clic derecho que oculta a Bitty y su cursor para no molestar en Steam, Hydra, Epic Games o cualquier partida. Deja un atajo flotante de 48×48 en la esquina: clic izquierdo devuelve a Bitty y abre el bocadillo, clic derecho solo lo devuelve, y se puede arrastrar. `Ctrl+Alt+B` también sale del modo gaming. En gaming el puente ignora `bitty_cursor` y `bitty_click` para no mover nada en pantalla; la visión sigue disponible.
- Comando local `/click x,y [brave]` en el panel de Bitty.
- Plantilla del logo de Brave empaquetada en el binario (`build.py`) y `numpy` añadido a dependencias.

### Verificado
- 17/17 tests Python (incluidos los cuatro estilos de cursor, la búsqueda del logo y el rechazo de app desconocida), tests Node, `typecheck` y build local. Demo real: Bitty vio el logo en `(1149, 1416)`, su cursor fue hasta él, hizo clic y Brave se abrió sin mover el ratón del usuario; el cursor volvió caminando y quedó aparcado detrás de la mascota. En el `.exe`: menú `> GAMING: ACTIVAR` oculta Bitty y su cursor y muestra el atajo de 48×48; el clic en el atajo los devuelve.

## [2.5.0] - 2026-11-23

### Añadido
- **Puente local Bitty ↔ OpenCode** (`bitty/bridge.py`, `plugin/src/shared/bridge.ts`): servidor HTTP solo en `127.0.0.1` con puerto efímero y token aleatorio. El plugin lee `BittyMascot/bridge.json` y nunca acepta una URL externa; las peticiones sin token se rechazan con `401`.
- **Herramientas `bitty_cursor` y `bitty_screen`** (`plugin/src/index.ts`): OpenCode puede mover el cursor virtual de la mascota y pedir una captura PNG del escritorio real. Ambas fuerzan el **diálogo nativo de permisos cada vez**, sin `save` (`bitty.cursor`, `bitty.screen`). El cursor no mueve el ratón del usuario ni hace clics o teclas.
- **Imagen inline compatible con OpenCode 2.3.2**: `bitty_screen` lee el PNG y lo devuelve como `data:image/png;base64,...` (igual que las tools internas `read`/MCP). Un `file://` en el resultado de una tool no se materializa en esta versión; por eso se usa data-URL. Requiere un modelo con visión; si no, OpenCode avisa.
- **Captura con Qt en el hilo correcto** (`bitty/screen.py`): `QScreen.grabWindow` solo se llama desde el hilo de la interfaz; el handler HTTP espera a que el PNG esté listo. Multimonitor: compone todas las pantallas en una imagen.
- **Interruptor del puente** en el menú derecho (`> PUENTE OPENCODE`), guardado en `state.json`. Al desactivarlo o salir, se cierra el puerto, se borra `bridge.json` y se eliminan las capturas.
- Documentación actualizada en `README.md` y `plugin/README.md`: la visión es bajo demanda (imagen fresca, no grabación ni streaming) y el MCP de Playwright sigue siendo solo para páginas web, no para el Opera real.

### Corregido
- `QToolTip.showText` pasaba el tiempo como argumento posicional y fallaba en PySide6 actual; ahora usa `msecShowTime=...`.

### Verificado
- 14/14 tests Python y 14/14 alpha tests Node, `typecheck` y `build` de plugin.
- Smoke offscreen de extremo a extremo: el cursor llega a (640, 480), la petición `/capture` devuelve un PNG válido desde el hilo de Qt, y al salir desaparece `bridge.json`.

---

## [2.4.7] - 2026-11-23

### Añadido
- **Cursor virtual de Bitty** (`bitty/virtual_cursor.py`, `bitty/cursor_view.py`): segundo puntero pixelado con ventana propia, siempre visible y `click-through`. `CursorNavigator` interpola hacia las coordenadas objetivo cada 20 ms con tope de 16 px/tick y desaceleración suave; `clamp_point` respeta la unión de pantallas.
- Control del cursor: comandos `/cursor x,y`, `/cursor demo` y `/cursor para` en el bocadillo, más tres entradas en el menú derecho (ruta aleatoria, ir al centro, ocultar/mostrar). El tema del cursor cambia con el de Bitty.
- Tres tests nuevos (`VirtualCursorTests`): movimiento gradual sin salto, ausencia de overshoot con cambio de objetivo a mitad del vuelo, clamp multimonitor y parseo de comandos.

### Verificado
- 13/13 tests Python, 12/12 alpha tests Node, `typecheck` y `build` de plugin.
- Smoke real offscreen: la ventana arranca, el cursor viaja de (799, 782) a (700, 400) y llega, la ruta aleatoria cambia de destino, ocultar/mostrar funciona y `_quit()` cierra sin errores.

---

## [2.4.6] - 2026-11-23

### Añadido
- **Aviso web contextual** (`src/shared/hint.ts`): `browserHint(text, available)` devuelve un aviso distinto según el MCP `bitty-navegador` ya esté disponible. Se usa en TUI y Desktop y se comprueba antes de consultar `mcp.list`.
- **[MEJORAS.md](MEJORAS.md)**: notas de mejoras pendientes, con la explicación más clara del problema en Desktop y la revisión de «Instalar ver el navegador» apuntadas por Marcelbon.

### Verificado
- 12/12 alpha tests Node (nuevo `aviso_web_contextual`), 10/10 tests Python, `typecheck` y `build`.

---

## [2.4.5] - 2026-11-23

### Corregido
- `--exclude-module` de PyInstaller solo evita importar módulos Python: las DLLs/SOs de PySide6 seguían copiándose al bundle. `build.py` ahora llama a `prune_unused_qt()` y retira `Qt6Pdf`, `Qt6Qml*`, `Qt6Quick` y `Qt6VirtualKeyboard` del directorio generado (Windows y Linux; macOS intacto).
- Zips publicados v2.4.4 → v2.4.5: Windows 59,6 → 50,9 MB (−15 %), Linux 137,1 → 128,2 MB, Fedora 118,6 → 109,7 MB. macOS sin cambios. (46,8 MB fue una medición local, no el artefacto de la release.)

### Añadido
- `tests/test_alpha.py::BundleTests::test_prune_unused_qt_keeps_required_libraries`: comprueba que se eliminan las bibliotecas sobrantes y que `QtWidgets` permanece. 10/10 tests Python.

### Verificado
- Reconstrucción local con el recorte activo y arranque del binario: `ALIVE=True`, log vacío.

---

## [2.4.4] - 2026-11-23

### Añadido
- **Cierre del rechazo de permiso**: `src/shared/permission.ts` centraliza la regla `forceAsk()` y `src/shared/handleInstall.ts` el flujo completo del RPC. `index.ts` delega en ambos, de modo que la misma lógica se ejecuta en producción y en los tests.
- **3 tests nuevos** (`permiso_siempre_pregunta`, `flujo_rpc_sesion_invalida_no_pide_permiso`, `flujo_rpc_rechazo_end_to_end`): cubren la regla `ask`, que un ID inválido ni siquiera pide permiso, y que un rechazo no llama a `transform`, `add` ni `connect`.

### Verificado
- 11/11 alpha tests Node, 9/9 tests Python, `typecheck` y `build` en verde.
- El diálogo nativo real sigue requiriendo prueba manual: lo que se automatiza es la decisión y sus consecuencias, no la pulsación del botón del sistema.

---

## [2.4.3] - 2026-11-23

### Añadido
- **Motor de la opinión visible**: `Opinion.source` (`local` / `model`) y `opinionSourceLabel()`; el panel de TUI y Desktop muestra `Motor: heurística local` o `Motor: modelo`.
- **Historial de opiniones**: `pushHistory()` guarda las 5 últimas sugerencias con hora, veredicto y motor; se muestran en ambos paneles y se limpian al crear sesión nueva.
- **Validación de la superficie RPC** (`src/shared/validate.ts`): IDs de sesión y agentes con formato estricto, directorios sin caracteres de control y longitud acotada. Los valores inválidos se rechazan antes de llamar a `installCapacity`.

### Corregido
- El smoke de Fedora usa `QT_QPA_PLATFORM=offscreen`: Qt 6.12 sigue reclamando `libxcb-cursor` en el contenedor mínimo aunque la librería esté en el bundle. El binario y PySide6 sí arrancan; el workflow completo está en verde y la release se publica con cuatro zips.

### Verificado
- 8/8 alpha tests Node (nuevos: `validacion_rpc`, `motor_opinion_transparente`, `historial_opiniones`), `typecheck` y `build`.
- CI completa en verde: Windows, macOS, Linux, Fedora y publicación de release.

---

## [2.4.2] - 2026-11-23

### Añadido
- **CI con alpha tests**: el workflow ejecuta `python -m unittest discover -s tests -v`, `npm run test:alpha` y `npm run typecheck` en cada push a `main`, PR y tag.
- **Smoke test en Fedora**: dentro del contenedor se arranca el binario con `timeout 20s` y plugin `offscreen` (v2.4.3); si Bitty se cae con error, el job falla.

### Cambiado
- `build.py` excluye módulos PySide6 no utilizados (WebEngine, Pdf, Qml, Quick, Multimedia, Bluetooth, Sql, Charts, etc.).
- Windows: 59,6 MB → 55,2 MB (−4,4 MB). macOS/Linux deberían beneficiarse más.

### Verificado
- Binario Windows recortado arrancado localmente: `ALIVE=True`, log vacío.
- Tests Python y Node en verde; `typecheck` y `build` pasan.

---

## [2.4.1] - 2026-11-23

### Añadido
- **Alpha tests** en `tests/test_alpha.py` (9 pruebas Python) y `plugin/tests/alpha.test.cjs` (5 pruebas Node), ejecutables con `python -m unittest discover -s tests -v` y `npm run test:alpha`.
- Los tests cubren inyección de argumentos, temporales privados, persistencia validada, catálogo cerrado de MCP, permiso rechazado/concedido y acotación del escaneo de sesiones.

### Seguridad
- Un ID de sesión que empieza por `-` o contiene caracteres extraños ya no se pasa a la CLI; `open_app()` también lo rechaza.
- Los mensajes que empiezan por `-` se envían tras `--` para que no puedan interpretarse como opciones.
- La salida de `opencode run` usa ahora directorios temporales privados y únicos (`mkdtemp`), con limpieza de los abandonados hace más de 24 h.
- `state.json` valida tema, modo, ID de sesión, etiqueta, posición y pausa al cargarlo.

### Corregido
- Los propios alpha tests detectaron que la primera expresión regular de ID permitía guiones iniciales (`--auto`); se corrigió antes de publicar.

### Verificado
- Ejecución real de la mascota en Windows: arranca y sigue viva sin errores ni avisos.
- 9/9 tests Python y 5/5 tests Node en verde; `npm run typecheck` y `npm run build` pasan.

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
