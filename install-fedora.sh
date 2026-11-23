#!/usr/bin/env bash
# Instalador específico de Bitty Mascot para Fedora.
# Uso: bash install-fedora.sh [--no-autostart]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="${HOME}/.local/share/BittyMascot"
AUTOSTART=1
[ "${1:-}" = "--no-autostart" ] && AUTOSTART=0

if [ ! -x "$ROOT/Bitty/Bitty" ]; then
  echo "No encuentro el binario en $ROOT/Bitty/Bitty" >&2
  exit 1
fi

echo "Instalando Bitty para Fedora en $TARGET"
mkdir -p "$TARGET"
cp -R "$ROOT/Bitty" "$TARGET/"
chmod +x "$TARGET/Bitty/Bitty"

# El agente de OpenCode reconoce a Marcelbon por su nombre.
AGENT="${HOME}/.config/opencode/agents/bitty.md"
mkdir -p "$(dirname "$AGENT")"
if [ -f "$ROOT/agent/bitty.md" ]; then
  cp "$ROOT/agent/bitty.md" "$AGENT"
  echo "Agente Bitty instalado: $AGENT"
fi

if [ "$AUTOSTART" = 1 ]; then
  SERVICE="${HOME}/.config/systemd/user/bitty.service"
  mkdir -p "$(dirname "$SERVICE")"
  cat > "$SERVICE" <<EOF
[Unit]
Description=Bitty Mascot for OpenCode (Fedora)

[Service]
ExecStart=$TARGET/Bitty/Bitty
Restart=on-failure

[Install]
WantedBy=default.target
EOF
  systemctl --user daemon-reload 2>/dev/null || true
  systemctl --user enable bitty.service 2>/dev/null || true
  systemctl --user start bitty.service 2>/dev/null || true
  echo "Arranque automático configurado (systemd --user)."
fi

echo "Listo, Marcelbon: Bitty te reconoce en OpenCode y en el escritorio."
echo "Si usas Wayland, los atajos globales pueden necesitar permisos adicionales."
