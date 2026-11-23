# Bitty Mascot

> Mascota flotante, pixelada y de estilo terminal para [OpenCode](https://opencode.ai/).
> Creada por **Marcelbon** ([@Marcelbon08](https://github.com/Marcelbon08)).
> **Windows · macOS · Linux** · v2.1.0

Bitty es una diminuta terminal de 64×64 píxeles que vive en tu escritorio: pasea, parpadea, cambia de cara según lo que le dices y te permite hablar con OpenCode sin abrir la aplicación. Ahora además **cambia de tema**: en diciembre se pone navideña, en octubre de Halloween, o tú eliges manualmente.

---

## ⚠️ Hecho con IA

**Este proyecto fue creado con inteligencia artificial (IA), bajo supervisión humana.**

El código, los sprites, los textos y la documentación fueron generados con ayuda de un asistente de IA y revisados y probados por el autor. **No es un producto oficial de OpenCode ni está afiliado a él.**

Declaración completa: **[AI_DISCLOSURE.md](AI_DISCLOSURE.md)**.

---

## Descarga

Los binarios de los tres sistemas se generan automáticamente con GitHub Actions al publicar cada versión:

| Sistema | Descarga directa v2.1.0 |
|---|---|
| Windows | [Bitty-Windows.zip](https://github.com/Marcelbon08/bitty-mascot/releases/download/v2.1.0/Bitty-Windows.zip) → ejecuta `Bitty.exe` |
| macOS | [Bitty-macOS.zip](https://github.com/Marcelbon08/bitty-mascot/releases/download/v2.1.0/Bitty-macOS.zip) → arrastra `Bitty.app` a Aplicaciones |
| Linux | [Bitty-Linux.zip](https://github.com/Marcelbon08/bitty-mascot/releases/download/v2.1.0/Bitty-Linux.zip) → ejecuta `Bitty/Bitty` |

👉 **[Página del release v2.1.0](https://github.com/Marcelbon08/bitty-mascot/releases/tag/v2.1.0)** · [Última versión](https://github.com/Marcelbon08/bitty-mascot/releases/latest)

También puedes [descargar el código](https://github.com/Marcelbon08/bitty-mascot/archive/refs/heads/main.zip) e instalar desde fuente con Python.

## Bitty dentro de OpenCode (nuevo en v2.1.0)

Además de la mascota flotante, Bitty es ahora un **plugin de OpenCode**: vive en la terminal y en OpenCode Desktop, como una integración al estilo de la mascota de Claude Code.

- **Terminal**: indicador permanente `Bitty [o_o] HI` en la barra del prompt y panel completo con `Ctrl+Alt+B`, `/bitty` o la paleta de comandos.
- **Desktop**: panel lateral **Bitty**, píldora junto al composer y presencia en la barra inferior. Se abre con `Mod+Alt+B` o `/bitty`.
- **Mascota viva**: cambia de cara con los eventos reales de la sesión: `HI → PIENSA → ESCRIBE/TOOL → LISTO`, además de `ERROR`, `PERMISO` y `ZZZ`.
- **Misma identidad**: sigue siendo *«Soy Bitty, tu mascota de OpenCode»* y trata a **Marcelbon** por su nombre.

Instalación y detalle de eventos: **[plugin/README.md](plugin/README.md)**. Requiere OpenCode v2.3.2+.

```jsonc
// ~/.config/opencode/cli.json (terminal)
{ "plugins": ["C:/Users/marce/Downloads/bitty-mascot/plugin"] }

// ~/.config/opencode/opencode.jsonc (Desktop)
{ "plugins": ["C:/Users/marce/Downloads/bitty-mascot/plugin"] }
```

> Los binarios de escritorio siguen siendo idénticos a los de v2.0.1; esta versión añade el plugin sin cambios en la app flotante.

## Vista previa

| OpenCode | Navidad | Halloween |
|---|---|---|
| ![Bitty original](docs/screenshots/bitty-original.png) | ![Bitty navidad](docs/screenshots/bitty-navidad.png) | ![Bitty halloween](docs/screenshots/bitty-halloween.png) |

![Bitty respondiendo](docs/screenshots/bitty-respuesta.png)

## Novedades de v2.1.0

- **Bitty dentro de OpenCode**: plugin con parte servidor, parte TUI y parte Desktop en un solo paquete (`plugin/`).
- **Integración estilo Claude Code**: mascota siempre visible en la terminal y en la app de escritorio, con panel, comando, atajo y píldora.
- **Reactiva de verdad**: ocho caras gobernadas por los eventos `session.*`, `permission.*` y `form.created`, con retorno automático a `HI`.
- **Bundle versionado**: `plugin/gui-dist/gui-experimental.cjs` se genera con `npm run build` y se incluye en el repo.

## Novedades de v2.0.0

- **Multiplataforma real**: reescrita en **Python + PySide6**. El mismo código corre en Windows, macOS y Linux.
- **Temas de temporada**: `OPENCODE` (original), `NAVIDAD` (gorro rojo, acento rojo) y `HALLOWEEN` (calabaza, acento naranja). Modo `AUTOMÁTICO` por defecto: detecta el mes. Se cambia desde el menú derecho → **> TEMA**.
- **Sin rutas fijas**: sprites junto al código, agente creado solo, `BITTY_WORKDIR` para elegir el directorio de trabajo.
- **Binarios por CI**: `.github/workflows/build.yml` compila y publica los tres paquetes al subir un tag `v*`.

## ¿Qué hace?

- Siempre visible (`WindowStaysOnTopHint`), sin marco ni halo, sobre cualquier ventana.
- Pasea sola en un área pequeña; se arrastra a cualquier monitor y el paseo se puede pausar.
- **Clic izquierdo**: bocadillo integrado; escribes y pulsas `Enter` o **ENVIAR**.
- **Clic derecho**: menú propio (hablar, pausar paseo, copiar, repetir, centrar, **tema**, salir) — sin `MessageBox`.
- **Identidad propia**: si le preguntas quién es, responde *«Soy Bitty, tu mascota de OpenCode»*.
- **Memoria de conversación**: **SEGUIR** continúa en la misma sesión y **ABRIR APP** abre OpenCode en esa sesión. Nunca usa `--continue`.
- Texto completo con scroll, rueda, flechas, `RePag`/`AvPag` e `Inicio`/`Fin`.
- 21 expresiones + accesorios de temporada, reacción según el tono de la respuesta.
- Atajo global `Ctrl+Alt+B` (en macOS también `⌘+Alt+B`), historial con `↑`/`↓`, tooltip y persistencia de posición, pausa, tema y sesión.

## Requisitos

- Windows 10/11, macOS 12+ o Linux con sesión gráfica (X11/Wayland con Qt).
- Para **binarios**: ninguno, vienen empaquetados.
- Para **instalar desde código**: Python 3.9+ y `pip`.
- OpenCode CLI instalado y accesible. Se detecta en las rutas típicas y en `PATH`.

## Instalación

### Desde los binarios (recomendado)

Descarga el ZIP de tu sistema desde el [release](https://github.com/Marcelbon08/bitty-mascot/releases/latest):

- **Windows**: extrae y ejecuta `Bitty.exe`. Para arrancar con Windows, usa `install.ps1` o crea un acceso directo en `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup`.
- **macOS**: extrae, arrastra `Bitty.app` a Aplicaciones. Si macOS la bloquea: `System Settings → Privacy & Security → Open Anyway`.
- **Linux**: extrae y ejecuta `./Bitty/Bitty` (otorga permiso de ejecución si hace falta).

### Desde el código

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

macOS / Linux:

```bash
bash install.sh          # añade arranque automático
bash install.sh --no-autostart
```

El instalador crea un entorno virtual, instala dependencias, copia el agente `bitty.md` y configura el arranque automático (acceso directo en Windows, LaunchAgent en macOS, `systemd --user` en Linux).

Manual:

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
python -m bitty
```

Para desinstalar: `powershell -ExecutionPolicy Bypass -File .\uninstall.ps1` o `bash uninstall.sh`.

### Directorio de trabajo de OpenCode

Por defecto se usa tu carpeta de usuario. Cambia antes de arrancar:

```powershell
$env:BITTY_WORKDIR = 'C:\MisProyectos'   # Windows
```

```bash
export BITTY_WORKDIR="$HOME/MisProyectos"  # macOS/Linux
```

## Uso

| Acción | Resultado |
|---|---|
| Clic izquierdo | Abre/cierra el bocadillo |
| `Enter` o **ENVIAR** | Envía el mensaje a OpenCode |
| `Esc` | Cierra el bocadillo y detiene la respuesta |
| **SEGUIR** | Sigue hablando en la misma conversación |
| **ABRIR APP** | Abre OpenCode en esa sesión |
| **COPIAR** | Copia la última respuesta |
| **CANCELAR** | Detiene la respuesta en curso |
| Rueda / flechas | Recorre la respuesta larga |
| `↑` / `↓` | Historial de mensajes |
| Clic derecho | Menú integrado (incluye **> TEMA**) |
| Arrastrar | Mueve a Bitty por todas las pantallas |
| `Ctrl+Alt+B` / `⌘+Alt+B` | Abre el bocadillo desde cualquier ventana |

Las respuestas reales se muestran **60 s**; los avisos cortos, **9 s**.

## Temas

| Tema | Cuándo | Cambios |
|---|---|---|
| `AUTOMÁTICO` | Por defecto | Diciembre → Navidad, octubre → Halloween, resto → OpenCode |
| `OPENCODE` | Manual | Paleta original en escala de grises con acento azul `#6B8FFF` |
| `NAVIDAD` | Manual/automático | Gorro rojo y pompón, acento rojo, saludo navideño |
| `HALLOWEEN` | Manual/automático | Calabaza sobre la terminal, acento naranja, saludo de truco o trato |

Los 21 sprites base se recolorizan en memoria; no hay 63 PNG duplicados.

## Estructura

```
bitty-mascot/
├── bitty/                    # Código multiplataforma
│   ├── app.py                # Ventana Qt, bocadillo, paseo, menú
│   ├── themes.py             # Paletas, accesorios y tema automático
│   ├── opencode.py           # CLI, agente, sesiones y parseo JSON
│   ├── state.py              # Persistencia portable
│   └── resources/            # 21 sprites + icono
├── agent/bitty.md            # Identidad de Bitty
├── plugin/                   # Plugin para OpenCode TUI y Desktop (v2.1.0)
│   ├── src/index.ts          # Parte servidor
│   ├── src/tui.tsx           # Parte terminal
│   ├── src/gui.tsx           # Parte Desktop
│   ├── src/shared/faces.ts   # Caras y eventos compartidos
│   └── gui-dist/             # Bundle GUI versionado
├── run_bitty.py              # Entry point para PyInstaller
├── build.py                  # Empaquetado local
├── requirements.txt
├── install.ps1 / install.sh  # Instaladores
├── uninstall.ps1 / uninstall.sh
├── .github/workflows/build.yml
├── docs/INSTALACION.md
├── legacy/powershell/        # Versión v1 original (solo histórico)
├── CHANGELOG.md
├── AI_DISCLOSURE.md
└── LICENSE                   # MIT
```

## Desarrollo

```bash
pip install -r requirements.txt pyinstaller
python -m bitty
python build.py     # genera dist/Bitty o dist/Bitty.app

cd plugin
npm install
npm run build       # genera el bundle GUI en plugin/gui-dist/
npm run typecheck
```

## Licencia

MIT. Hecho con IA y supervisado por Marcelbon. No afiliado a OpenCode.
