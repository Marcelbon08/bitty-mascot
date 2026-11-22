#requires -Version 5.1
<#
  Instalador de Bitty Mascot v2 (Windows).
  Uso: powershell -ExecutionPolicy Bypass -File .\install.ps1

  Si el equipo tiene Python 3.12, crea un entorno virtual e instala las
  dependencias. Si hay un binario ya construido en dist\Bitty, lo usa
  directamente (es lo que trae el ZIP del release).
#>
$ErrorActionPreference = 'Stop'

$root = $PSScriptRoot
$target = Join-Path $env:LOCALAPPDATA 'BittyMascot'
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$shortcut = Join-Path $startup 'Bitty Mascot.lnk'
$exeBundle = Join-Path $root 'dist\Bitty\Bitty.exe'

Write-Host "Instalando Bitty Mascot en: $target"

# 1) Detener una instancia anterior (el nombre del proceso puede ser Bitty o python).
Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*bitty-mascot.ps1*' -or $_.CommandLine -like '*-m bitty*' -or $_.Name -eq 'Bitty.exe' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
Start-Sleep -Milliseconds 600

New-Item -ItemType Directory -Path $target -Force | Out-Null

if (Test-Path -LiteralPath $exeBundle) {
    # Instalación desde el ZIP del release: copiar el binario ya compilado.
    Copy-Item -LiteralPath (Join-Path $root 'dist\Bitty\*') -Destination $target -Recurse -Force
    $runTarget = Join-Path $target 'Bitty.exe'
    $runArgs = ''
    Write-Host "Usando el ejecutable empaquetado."
} else {
    # Instalación desde el repositorio: copiar código y crear el venv.
    Copy-Item -LiteralPath (Join-Path $root 'bitty') -Destination $target -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $root 'run_bitty.py'),(Join-Path $root 'requirements.txt') -Destination $target -Force

    $pythonExe = $null
    $pythonPrefix = @()
    foreach ($candidate in @('python','python3','py -3.12','py -3')) {
        $parts = $candidate -split ' '
        $cmd = Get-Command $parts[0] -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $probe = @()
        if ($parts.Count -gt 1) { $probe = @($parts[1..($parts.Count-1)]) }
        $probe += '--version'
        try { $ver = & $cmd.Source @probe 2>&1 } catch { continue }
        if ("$ver" -match 'Python 3\.(9|10|11|12|13)') {
            $pythonExe = $cmd.Source
            $pythonPrefix = $probe[0..($probe.Count-2)]
            break
        }
    }
    if (-not $pythonExe) {
        Write-Warning 'No se encontró Python 3.9+. Instálalo desde https://www.python.org/downloads/ y vuelve a ejecutar este instalador.'
        exit 1
    }

    $venv = Join-Path $target 'venv'
    if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) {
        Write-Host 'Creando entorno virtual...'
        $venvArgs = @()
        if ($pythonPrefix.Count -gt 0) { $venvArgs += $pythonPrefix }
        $venvArgs += @('-m','venv',$venv)
        & $pythonExe @venvArgs | Out-Null
    }
    $venvPython = Join-Path $venv 'Scripts\python.exe'
    Write-Host 'Instalando PySide6, Pillow y pynput...'
    & $venvPython -m pip install --upgrade pip | Out-Null
    & $venvPython -m pip install -r (Join-Path $target 'requirements.txt')

    $runTarget = Join-Path $venv 'Scripts\pythonw.exe'
    $runArgs = '-m bitty'
    Write-Host "Usando Python desde $venv"
}

# 2) Acceso directo en Inicio -> Programas -> Inicio.
try {
    New-Item -ItemType Directory -Path $startup -Force | Out-Null
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($shortcut)
    $sc.TargetPath = $runTarget
    if ($runArgs) { $sc.Arguments = $runArgs }
    $sc.WorkingDirectory = $target
    $icon = Join-Path $target 'bitty.ico'
    if (Test-Path -LiteralPath $icon) { $sc.IconLocation = "$icon,0" }
    $sc.Description = 'Bitty - mascota flotante de OpenCode'
    $sc.Save()
    Write-Host "Acceso directo creado: $shortcut"
} catch {
    Write-Warning "No se pudo crear el acceso directo: $($_.Exception.Message)"
}

# 3) El agente de identidad se crea solo al arrancar, pero lo adelantamos.
$agentFile = Join-Path $env:USERPROFILE '.config\opencode\agents\bitty.md'
if (Test-Path -LiteralPath (Join-Path $root 'agent\bitty.md')) {
    if (-not (Test-Path -LiteralPath $agentFile)) {
        New-Item -ItemType Directory -Path (Split-Path $agentFile) -Force | Out-Null
        Copy-Item -LiteralPath (Join-Path $root 'agent\bitty.md') -Destination $agentFile -Force
        Write-Host "Agente creado: $agentFile"
    }
}

Write-Host 'Arrancando Bitty...'
if ($runArgs) {
    Start-Process -FilePath $runTarget -ArgumentList $runArgs -WorkingDirectory $target -WindowStyle Hidden
} else {
    Start-Process -FilePath $runTarget -WorkingDirectory $target -WindowStyle Hidden
}

Write-Host 'Listo. Ctrl+Alt+B abre el bocadillo; clic derecho cambia el tema.'
