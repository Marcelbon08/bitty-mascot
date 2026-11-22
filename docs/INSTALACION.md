# Instalación detallada y solución de problemas (v2.0.0)

## Opción A: binario ya compilado (lo más fácil)

Descarga el paquete de tu sistema desde [releases](https://github.com/Marcelbon08/bitty-mascot/releases/latest).

### Windows

1. Descomprime `Bitty-Windows.zip`.
2. Ejecuta `Bitty.exe`.
3. Para que arranque con Windows: `powershell -ExecutionPolicy Bypass -File .\install.ps1` desde la carpeta descomprimida (crea el acceso directo), o crea tú un acceso directo en:

   ```
   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
   ```

   con destino `Bitty.exe` y directorio de trabajo la carpeta donde está.

### macOS

1. Descomprime `Bitty-macOS.zip`.
2. Arrastra `Bitty.app` a **Aplicaciones**.
3. Si macOS impide abrirla: **System Settings → Privacy & Security → Open Anyway** (o clic derecho → *Open*).
4. Para arrancar con la sesión, usa `install.sh` desde el repositorio (crea un LaunchAgent), o añade `Bitty.app` a **System Settings → General → Login Items**.

### Linux

1. Descomprime `Bitty-Linux.zip`.
2. `chmod +x Bitty/Bitty && ./Bitty/Bitty`.
3. Necesitas un entorno de escritorio con Qt (X11 o Wayland). En Wayland puede hacer falta `QT_QPA_PLATFORM=wayland`.
4. Para arrancar con la sesión: `install.sh` crea `~/.config/systemd/user/bitty.service` y lo habilita.

## Opción B: desde el código fuente

Necesitas **Python 3.9+**.

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

macOS / Linux:

```bash
bash install.sh            # con arranque automático
bash install.sh --no-autostart
```

Manual:

```bash
python -m venv venv
# Windows: venv\Scripts\activate ; macOS/Linux: source venv/bin/activate
pip install -r requirements.txt
python -m bitty
```

El agente `~/.config/opencode/agents/bitty.md` se crea automáticamente al arrancar si no existe.

## Solución de problemas

### No encuentro OpenCode

Bitty busca la CLI en este orden:

1. Windows: `%APPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`
2. Windows: `%LOCALAPPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`
3. macOS: `/opt/homebrew/bin/opencode`, `/usr/local/bin/opencode`
4. Linux: `/usr/bin/opencode`, `~/.local/bin/opencode`, `~/.opencode/bin/opencode`
5. El `opencode` que haya en `PATH`

Instala la CLI siguiendo <https://opencode.ai/docs/cli/>.

### El atajo global no funciona

- Windows/Linux: prueba `Ctrl+Alt+B`.
- macOS: `⌘+Alt+B` o `Ctrl+Alt+B`.

Si otra app usa esa combinación, Bitty no podrá registrarla; el menú derecho sigue funcionando. En macOS puede hacer falta conceder permiso de **Accesibilidad** a la app para escuchar atajos globales.

### La mascota no aparece en Linux con Wayland

Prueba `QT_QPA_PLATFORM=wayland ./Bitty/Bitty` o, si falla, `QT_QPA_PLATFORM=xcb`. También puede hacer falta `libxcb` / `libxkbcommon`.

### El binario de macOS dice «dañado» o «no verificado»

Es un binario firmado sin identificador de desarrollador. Clic derecho → **Open**, o **System Settings → Privacy & Security → Open Anyway**.

### Los sprites salen con un cuadro oscuro

Los PNG originales tienen fondo `0C0C0C`; el código lo convierte a transparente. Si ves un cuadro, comprueba que usas v2.0.0 y que la carpeta `resources/sprites` está completa (21 PNG).

### Quiero regenerar los sprites

La versión PowerShell histórica incluye `generate-sprites.ps1` en `legacy/powershell/`. Detén Bitty antes de ejecutarlo: los PNG están abiertos.

### Posición, pausa, sesión y tema

Se guardan en:

- Windows: `%APPDATA%\BittyMascot\state.json`
- macOS/Linux: `~/.config/BittyMascot/state.json` (o `$XDG_CONFIG_HOME/BittyMascot/state.json`)

Borrando ese archivo, Bitty vuelve al centro con el tema automático.

### Cambiar el directorio de trabajo de OpenCode

```powershell
$env:BITTY_WORKDIR = 'C:\MisProyectos'   # Windows
```

```bash
export BITTY_WORKDIR="$HOME/MisProyectos"  # macOS/Linux
```

Para hacerlo permanente, configura la variable en el perfil de tu shell o en el servicio/LaunchAgent.

## Desinstalar

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

```bash
bash uninstall.sh
```

Preguntan antes de borrar la carpeta instalada, la posición guardada y el agente.
