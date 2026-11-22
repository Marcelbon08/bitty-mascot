#!/usr/bin/env bash
# Instalador de Bitty Mascot v2 para macOS y Linux.
# Uso: bash install.sh [--no-autostart]
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
TARGET="${HOME}/.local/share/BittyMascot"
AUTOSTART=1
[ "${1:-}" = "--no-autostart" ] && AUTOSTART=0

PYTHON=""
for candidate in python3 python; do
  if command -v "$candidate" >/dev/null 2>&1; then
    if "$candidate" -c 'import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)' 2>/dev/null; then
      PYTHON="$candidate"; break
    fi
  fi
done
if [ -z "$PYTHON" ]; then
  echo "Necesitas Python 3.9 o superior. https://www.python.org/downloads/" >&2
  exit 1
fi

echo "Instalando Bitty Mascot en $TARGET"
mkdir -p "$TARGET"
cp -R "$ROOT/bitty" "$TARGET/"
cp "$ROOT/run_bitty.py" "$ROOT/requirements.txt" "$TARGET/"

if [ ! -x "$TARGET/venv/bin/python" ]; then
  echo "Creando entorno virtual..."
  "$PYTHON" -m venv "$TARGET/venv"
fi
echo "Instalando dependencias..."
"$TARGET/venv/bin/python" -m pip install --quiet --upgrade pip
"$TARGET/venv/bin/python" -m pip install --quiet -r "$TARGET/requirements.txt"

AGENT="${HOME}/.config/opencode/agents/bitty.md"
if [ ! -f "$AGENT" ] && [ -f "$ROOT/agent/bitty.md" ]; then
  mkdir -p "$(dirname "$AGENT")"
  cp "$ROOT/agent/bitty.md" "$AGENT"
  echo "Agente creado: $AGENT"
fi

cat > "$TARGET/run-bitty.sh" <<EOF
#!/usr/bin/env bash
cd "$TARGET"
exec "$TARGET/venv/bin/python" -m bitty
EOF
chmod +x "$TARGET/run-bitty.sh"

if [ "$AUTOSTART" = 1 ]; then
  if [ "$(uname -s)" = "Darwin" ]; then
    PLIST="${HOME}/Library/LaunchAgents/com.bitty.mascot.plist"
    mkdir -p "$(dirname "$PLIST")"
    cat > "$PLIST" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>com.bitty.mascot</string>
  <key>ProgramArguments</key>
  <array><string>$TARGET/run-bitty.sh</string></array>
  <key>RunAtLoad</key><true/>
</dict></plist>
EOF
    launchctl unload "$PLIST" 2>/dev/null || true
    launchctl load "$PLIST"
    echo "Arranque automático configurado (LaunchAgent)."
  else
    SERVICE="${HOME}/.config/systemd/user/bitty.service"
    mkdir -p "$(dirname "$SERVICE")"
    cat > "$SERVICE" <<EOF
[Unit]
Description=Bitty Mascot for OpenCode
[Service]
ExecStart=$TARGET/run-bitty.sh
Restart=on-failure
[Install]
WantedBy=default.target
EOF
    systemctl --user daemon-reload 2>/dev/null || true
    systemctl --user enable bitty.service 2>/dev/null || true
    systemctl --user start bitty.service 2>/dev/null || true
    echo "Arranque automático configurado (systemd --user)."
  fi
fi

echo "Listo. Ctrl+Alt+B abre el bocadillo; clic derecho cambia el tema."
