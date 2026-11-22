# Bitty Mascot

> Una mascota flotante, pixelada y de estilo terminal para [OpenCode](https://opencode.ai/) en Windows.

Bitty es una diminuta terminal de 64×64 píxeles que vive en tu escritorio: pasea, parpadea, cambia de cara según lo que le dices y te permite hablar con OpenCode sin abrir la aplicación. Todo con la paleta oficial de OpenCode (blanco y negro con un pequeño acento azul).

---

## Descarga rápida

La última versión portable (v1.8.1) se puede descargar ya empaquetada:

**[⬇️ Descargar bitty-mascot-v1.8.1.zip](https://github.com/Marcelbon08/bitty-mascot/releases/download/v1.8.1/bitty-mascot-v1.8.1.zip)**

Descomprime, entra en la carpeta y ejecuta `powershell -ExecutionPolicy Bypass -File .\install.ps1`. También puedes usar el botón verde **Code → Download ZIP** de este repositorio.

---

## ⚠️ Hecho con IA

**Este proyecto fue creado con inteligencia artificial (IA), bajo supervisión humana.**

El código, los sprites, los textos y la documentación fueron generados con la ayuda de un asistente de IA y revisados por el autor. No es un producto oficial de OpenCode ni está afiliado a él. Úsalo bajo tu responsabilidad.

Lee la declaración completa en **[AI_DISCLOSURE.md](AI_DISCLOSURE.md)**.

---

## ¿Qué hace?

- **Siempre visible** (`TopMost`), sin marco ni borde, sobre cualquier ventana.
- **Pasea sola** en un área pequeña alrededor del punto donde la dejas. Se puede arrastrar a cualquier monitor y el paseo se puede pausar desde el menú.
- **Clic izquierdo** abre un bocadillo integrado: escribes y pulsas `Enter` o **ENVIAR** para hablar con OpenCode.
- **Clic derecho** abre un menú propio (sin `MessageBox` de Windows): hablar, pausar/reanudar paseo, copiar respuesta, repetir último mensaje, volver al centro y salir.
- **Identidad propia**: si le preguntas quién es, responde *«Soy Bitty, tu mascota de OpenCode»* gracias a un agente propio (`bitty.md`). No se identifica como el modelo de turno.
- **Conversaciones con memoria**: tras la primera respuesta aparecen **SEGUIR** (misma conversación dentro de Bitty) y **ABRIR APP** (abre OpenCode en esa misma sesión).
- **Sesiones bajo control**: **NUEVA** crea una sesión nueva; el desplegable elige una sesión anterior por su ID. **Nunca se usa `--continue`**, así que Bitty nunca se engancha a tu sesión activa.
- **Respuestas completas y legibles**: el área de texto se dibuja con GDI (no es un `TextBox` de Windows), con scroll oscuro, rueda, flechas, `RePag`/`AvPag` y `Inicio`/`Fin`.
- **21 expresiones** (feliz, sorpresa, duda, error, risa, triste, enfado, enamorada, gafas, cansada, curiosa, etc.) más dos frames de caminata. La cara se elige según el tono de la respuesta.
- **Atajo global** `Ctrl+Alt+B` (o `Ctrl+Alt+J` si está ocupado) para abrir el bocadillo desde cualquier ventana.
- **Historial** con `↑`/`↓`, **tooltip** y guardado de posición, pausa y sesión en `%APPDATA%\BittyMascot\state.json`.
- **Portable**: no hay rutas de usuario grabadas. Detecta OpenCode, usa los sprites junto al script y crea su agente automáticamente.

## Requisitos

- Windows 10 u 11.
- PowerShell 5.1 (viene incluido en Windows).
- [OpenCode CLI](https://opencode.ai/docs/cli/) instalado y accesible. Se detecta automáticamente en:
  - `%APPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`
  - `%LOCALAPPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`
  - `PATH` (si `opencode` es un ejecutable).

## Instalación rápida

1. Descarga y extrae el ZIP de este repositorio.
2. Abre **PowerShell** en la carpeta extraída.
3. Ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

El instalador:

- copia `src\` a `%LOCALAPPDATA%\BittyMascot`,
- crea `~/.config/opencode/agents/bitty.md` si no existe,
- crea un acceso directo en el **Inicio → Programas → Inicio** de Windows,
- y arranca Bitty.

Para desinstalar:

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

## Instalación manual

Copia la carpeta `src` completa (incluido `sprites\`) donde quieras y ejecuta:

```powershell
powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File .\src\bitty-mascot.ps1
```

La mascota crea sola su agente en `~/.config/opencode/agents/bitty.md` si falta.

Si OpenCode está en una ruta distinta, añade al script (o al entorno) la variable `BITTY_WORKDIR` para elegir el directorio de trabajo de OpenCode:

```powershell
$env:BITTY_WORKDIR = 'C:\MisProyectos'
```

## Uso

| Acción | Resultado |
|---|---|
| Clic izquierdo en Bitty | Abre/cierra el bocadillo |
| `Enter` o **ENVIAR** | Envía el mensaje a OpenCode |
| **SEGUIR** | Sigue hablando en la misma conversación |
| **ABRIR APP** | Abre OpenCode en esa sesión |
| **COPIAR** | Copia la última respuesta al portapapeles |
| **CANCELAR** | Detiene la respuesta en curso |
| Rueda / flechas en el panel | Recorre la respuesta larga |
| `↑` / `↓` en el campo | Historial de mensajes |
| `Esc` | Cierra el bocadillo |
| Clic derecho | Menú integrado |
| Arrastrar | Mueve a Bitty por todas las pantallas |
| `Ctrl+Alt+B` | Abre el bocadillo desde cualquier ventana |

Las respuestas se muestran 60 segundos; los avisos cortos, 9 segundos.

## Estructura

```
bitty-mascot/
├── src/
│   ├── bitty-mascot.ps1        # Script principal (UI, sesiones, scroll GDI)
│   ├── generate-sprites.ps1    # Generador de los 21 sprites
│   ├── bitty.ico               # Icono del acceso directo
│   ├── LEEME.txt               # Guía rápida en español
│   └── sprites/bitty-*.png     # 21 expresiones 64×64
├── agent/bitty.md               # Contexto de la identidad de Bitty
├── docs/INSTALACION.md          # Instalación detallada y solución de problemas
├── install.ps1                  # Instalador
├── uninstall.ps1                # Desinstalador
├── CHANGELOG.md                 # Todos los cambios y versiones
├── AI_DISCLOSURE.md             # Declaración de uso de IA
├── LEEME.txt                    # Guía rápida (copia de src)
└── LICENSE                      # MIT
```

## Desarrollo

Para regenerar los sprites:

```powershell
powershell -ExecutionPolicy Bypass -File .\src\generate-sprites.ps1
```

> Detén Bitty antes de regenerar: los PNG están abiertos y no se pueden sobrescribir.

## Licencia

MIT. Hecho con IA y supervisado por marce. No afiliado a OpenCode.
