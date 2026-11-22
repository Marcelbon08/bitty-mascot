#requires -Version 5.1
<#
  Desinstalador de Bitty Mascot.
  Uso: powershell -ExecutionPolicy Bypass -File .\uninstall.ps1
#>
$ErrorActionPreference = 'Stop'

$target = Join-Path $env:LOCALAPPDATA 'BittyMascot'
$shortcut = Join-Path $env:APPDATA 'Microsoft\Windows\Start Menu\Programs\Startup\Bitty Mascot.lnk'
$state = Join-Path $env:APPDATA 'BittyMascot\state.json'

Write-Host "Deteniendo Bitty..."
Get-CimInstance Win32_Process -Filter "Name = 'powershell.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like '*-File*bitty-mascot.ps1*' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

if (Test-Path -LiteralPath $shortcut) {
    Remove-Item -LiteralPath $shortcut -Force
    Write-Host "Acceso directo eliminado."
}

if (Test-Path -LiteralPath $target) {
    $answer = Read-Host "Eliminar la carpeta instalada ($target) y tu posicion guardada? [s/N]"
    if ($answer -match '^[sS]') {
        Remove-Item -LiteralPath $target -Recurse -Force
        if (Test-Path -LiteralPath $state) { Remove-Item -LiteralPath $state -Force }
        Write-Host "Archivos eliminados."
    } else {
        Write-Host "Se conservan los archivos en $target."
    }
}

$agent = Join-Path $env:USERPROFILE '.config\opencode\agents\bitty.md'
if (Test-Path -LiteralPath $agent) {
    $answer = Read-Host "Eliminar tambien el agente bitty.md de OpenCode? [s/N]"
    if ($answer -match '^[sS]') {
        Remove-Item -LiteralPath $agent -Force
        Write-Host "Agente eliminado."
    }
}

Write-Host "Bitty se ha desinstalado."
