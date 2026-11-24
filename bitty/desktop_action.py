"""Activación real de un botón de la barra de tareas sin mover el ratón.

El cursor de Bitty hace el gesto visible; la activación se hace con UI
Automation (Windows). En otros sistemas se usa la app permitida directamente.
Solo se aceptan nombres de la whitelist de Bitty: nunca comandos del exterior.
"""

from __future__ import annotations

import subprocess
import sys

ALLOWED = frozenset({"brave"})

# Script fijo: el único dato externo es un nombre validado contra ALLOWED.
_UIA_SCRIPT = r'''
param([string]$App)
Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes
$root = [System.Windows.Automation.AutomationElement]::RootElement
$cond = New-Object System.Windows.Automation.PropertyCondition(
  [System.Windows.Automation.AutomationElement]::ClassNameProperty, "Shell_TrayWnd")
$tray = $root.FindFirst([System.Windows.Automation.TreeScope]::Children, $cond)
if (-not $tray) { exit 1 }
$all = $tray.FindAll([System.Windows.Automation.TreeScope]::Descendants,
  [System.Windows.Automation.Condition]::TrueCondition)
foreach ($e in $all) {
  if ($e.Current.ClassName -eq "Taskbar.TaskListButtonAutomationPeer" -and
      $e.Current.Name -like "*$App*") {
    $pattern = $e.GetCurrentPattern([System.Windows.Automation.InvokePattern]::Pattern)
    $pattern.Invoke()
    exit 0
  }
}
exit 2
'''


def invoke_taskbar_button(app: str) -> bool:
    """Pulsa el botón de la app en la barra de tareas. No toca el puntero."""
    if app not in ALLOWED or sys.platform != "win32":
        return False
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
    try:
        result = subprocess.run(
            [
                "powershell.exe", "-NoProfile", "-NonInteractive",
                "-WindowStyle", "Hidden", "-Command", _UIA_SCRIPT, "-App", app,
            ],
            capture_output=True,
            timeout=15,
            creationflags=flags,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return False
    return result.returncode == 0


__all__ = ["invoke_taskbar_button", "ALLOWED"]
