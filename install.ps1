#requires -Version 5.1
<#
  Instalador de Bitty Mascot.
  Uso: powershell -ExecutionPolicy Bypass -File .\install.ps1
#>
$ErrorActionPreference = 'Stop'

$src = Join-Path $PSScriptRoot 'src'
$target = Join-Path $env:LOCALAPPDATA 'BittyMascot'
$agentDir = Join-Path $env:USERPROFILE '.config\opencode\agents'
$agentFile = Join-Path $agentDir 'bitty.md'
$startup = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup'
$shortcut = Join-Path $startup 'Bitty Mascot.lnk'

if (-not (Test-Path -LiteralPath (Join-Path $src 'bitty-mascot.ps1'))) {
    Write-Error "No se encontro src\bitty-mascot.ps1 junto a este instalador."
    exit 1
}

Write-Host "Instalando Bitty Mascot en: $target"

# Si ya estaba corriendo, se detiene para poder sobrescribir los PNG.
$running = @(Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*-File*bitty-mascot.ps1*' })
if ($running.Count -gt 0) {
    Write-Host "Deteniendo $($running.Count) instancia(s) de Bitty..."
    foreach ($p in $running) { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 700
}

New-Item -ItemType Directory -Path $target -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $src '*') -Destination $target -Recurse -Force

# Agente de identidad: no se sobrescribe si el usuario ya tiene uno propio.
if (-not (Test-Path -LiteralPath $agentFile)) {
    New-Item -ItemType Directory -Path $agentDir -Force | Out-Null
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'agent\bitty.md') -Destination $agentFile -Force
    Write-Host "Agente creado: $agentFile"
} else {
    Write-Host "El agente ya existe, se conserva: $agentFile"
}

# Acceso directo en Inicio -> Programas -> Inicio.
try {
    New-Item -ItemType Directory -Path $startup -Force | Out-Null
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($shortcut)
    $sc.TargetPath = 'powershell.exe'
    $sc.Arguments = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "' + (Join-Path $target 'bitty-mascot.ps1') + '"'
    $sc.WorkingDirectory = $target
    $sc.IconLocation = (Join-Path $target 'bitty.ico') + ',0'
    $sc.Description = 'Bitty - mascota flotante de OpenCode'
    $sc.Save()
    Write-Host "Acceso directo creado: $shortcut"
} catch {
    Write-Warning "No se pudo crear el acceso directo: $($_.Exception.Message)"
}

# OpenCode se detecta solo, pero avisamos si no esta instalado.
$exe = Join-Path $env:APPDATA 'npm\node_modules\@opencode\cli\bin\opencode.exe'
if (-not (Test-Path -LiteralPath $exe) -and -not (Get-Command opencode -ErrorAction SilentlyContinue)) {
    Write-Warning "No se encontro OpenCode. Instala la CLI: https://opencode.ai/docs/cli/"
}

Write-Host "Arrancando Bitty..."
Start-Process powershell.exe -ArgumentList @(
    '-NoProfile', '-WindowStyle', 'Hidden', '-ExecutionPolicy', 'Bypass',
    '-File', (Join-Path $target 'bitty-mascot.ps1')
) -WindowStyle Hidden

Write-Host "Listo. Usa Ctrl+Alt+B para abrir el bocadillo desde cualquier ventana."
