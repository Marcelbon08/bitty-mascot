#!/usr/bin/env bash
# Desinstalador de Bitty Mascot v2 (macOS/Linux).
set -euo pipefail

TARGET="${HOME}/.local/share/BittyMascot"

if [ "$(uname -s)" = "Darwin" ]; then
  PLIST="${HOME}/Library/LaunchAgents/com.bitty.mascot.plist"
  [ -f "$PLIST" ] && launchctl unload "$PLIST" 2>/dev/null || true
  rm -f "$PLIST"
else
  systemctl --user stop bitty.service 2>/dev/null || true
  systemctl --user disable bitty.service 2>/dev/null || true
  rm -f "${HOME}/.config/systemd/user/bitty.service"
  systemctl --user daemon-reload 2>/dev/null || true
fi

pkill -f 'python -m bitty' 2>/dev/null || true

if [ -d "$TARGET" ]; then
  read -r -p "¿Eliminar $TARGET y la posición guardada? [s/N] " answer
  case "$answer" in
    s|S) rm -rf "$TARGET"; rm -rf "${HOME}/.config/BittyMascot"; echo "Archivos eliminados." ;;
    *) echo "Se conservan los archivos." ;;
  esac
fi

AGENT="${HOME}/.config/opencode/agents/bitty.md"
if [ -f "$AGENT" ]; then
  read -r -p "¿Eliminar también el agente bitty.md? [s/N] " answer
  case "$answer" in s|S) rm -f "$AGENT"; echo "Agente eliminado." ;; esac
fi

echo "Bitty se ha desinstalado."
