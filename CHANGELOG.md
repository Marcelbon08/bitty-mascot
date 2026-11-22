# Changelog

Todos los cambios destacados de Bitty Mascot. El historial se agrupó por bloques de trabajo a partir de las sesiones de desarrollo; las versiones anteriores a `1.8.1` no se publicaron como releases.

Formato basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/).

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
