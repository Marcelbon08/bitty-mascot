# Instalación detallada y solución de problemas

## Instalación automática

```powershell
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

El instalador copia `src\` a `%LOCALAPPDATA%\BittyMascot`, crea el agente de identidad, añade el acceso directo de inicio y arranca Bitty. Se puede volver a ejecutar sin problemas (sobrescribe los archivos pero conserva tu `bitty.md` si lo has editado).

## Instalación manual

1. Copia **toda** la carpeta `src` (el subdirectorio `sprites\` es imprescindible) a donde quieras, por ejemplo `C:\Herramientas\Bitty`.
2. Ejecuta:

   ```powershell
   powershell -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File C:\Herramientas\Bitty\bitty-mascot.ps1
   ```

3. Si quieres que arranque con Windows, crea un acceso directo a `powershell.exe` en:

   ```
   %APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup
   ```

   con estos argumentos:

   ```
   -NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\Herramientas\Bitty\bitty-mascot.ps1"
   ```

La mascota crea sola `~/.config/opencode/agents/bitty.md` si no existe.

## Solución de problemas

### «No encuentro el ejecutable de OpenCode»

Bitty busca la CLI en este orden:

1. `%APPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`
2. `%LOCALAPPDATA%\npm\node_modules\@opencode\cli\bin\opencode.exe`
3. `%ProgramFiles%\opencode\opencode.exe`
4. El `opencode` que haya en `PATH`

Instala la CLI con `npm install -g opencode-ai` o sigue la documentación oficial: <https://opencode.ai/docs/cli/>.

### Los acentos se ven mal («Ã³»)

El script lleva BOM UTF-8. Si lo has editado con un editor que lo quitó, vuelve a guardarlo como **UTF-8 con BOM** o restaura el original.

### El atajo `Ctrl+Alt+B` no funciona

Otra aplicación puede estar usando esa combinación. Bitty prueba varios IDs de reserva y, como último recurso, registra `Ctrl+Alt+J`. Mira el tooltip de la mascota para saber cuál quedó activo.

### Se oye un parpadeo o aparece un borde oscuro

Comprueba que los 21 PNG de `sprites\` están presentes y que no se ha escalado la ventana. Los sprites son de 64×64 y se dibujan a tamaño natural con `NearestNeighbor`.

### Quiero regenerar los sprites

```powershell
powershell -ExecutionPolicy Bypass -File .\src\generate-sprites.ps1
```

**Detén Bitty antes**: los PNG están abiertos y no se pueden sobrescribir.

### Bitty no recuerda dónde estaba

La posición se guarda en `%APPDATA%\BittyMascot\state.json` al moverla, pausar el paseo o cambiar de sesión. Si borras ese archivo, vuelve al centro.

### Cambiar el directorio de trabajo de OpenCode

Por defecto se usa tu carpeta de usuario (`%USERPROFILE%`). Si quieres que OpenCode trabaje en otro sitio, define antes de arrancar:

```powershell
$env:BITTY_WORKDIR = 'C:\MisProyectos'
```

Para que sea permanente, añade esa línea a tu perfil de PowerShell o configura el acceso directo para que la ejecute antes del script.

## Desinstalar

```powershell
powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
```

Pregunta antes de borrar la carpeta instalada, la posición guardada y el agente.
