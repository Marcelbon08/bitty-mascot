# Bitty para OpenCode (plugin)

Bitty también vive **dentro de OpenCode**: en la **terminal (TUI)** y en **OpenCode Desktop**. No sustituye a la mascota flotante: la acompaña. Es la misma identidad —*«Soy Bitty, tu mascota de OpenCode»*— y reacciona en tiempo real a lo que hace la sesión.

> Requiere OpenCode **v2.3.2 o superior**. Es un plugin experimental: usa los puntos de extensión `./tui` y `./gui-experimental`.

## Qué se ve

| Superficie | Dónde aparece Bitty |
|---|---|
| Terminal | Indicador permanente en la barra de inicio y del prompt: `Bitty [o_o] HI` |
| Terminal | Panel completo con `bitty.panel` (paleta, `/bitty` o `Ctrl+Alt+B`), dentro de una sesión |
| Desktop | Panel lateral **Bitty**, píldora junto al composer y texto en la barra inferior |
| Desktop | Paleta de comandos, `/bitty` y `Mod+Alt+B` |

### Caras reactivas

| Cara | Estado | Eventos de OpenCode |
|---|---|---|
| `[o_o] · HI` | Reposo / saluda a Marcelbon | `session.created`, `session.idle`, `permission.replied` |
| `[o_?] · PIENSA` | Pensando | `session.execution.started`, `session.step.started`, compactación |
| `[-_-]> · ESCRIBE` | Escribiendo respuesta | `session.step.first-token`, `session.text.*`, reasoning |
| `[O_o] · TOOL` | Usando herramientas | `session.tool.*`, `session.shell.started` |
| `[^_^] · LISTO` | Terminado | `session.execution.succeeded`, `session.text.ended` |
| `[x_x] · ERROR` | Fallo o reintento | `session.tool.failed`, `session.execution.failed`, `session.retry.scheduled` |
| `[O_O] · PERMISO` | Pide permiso | `permission.asked`, `form.created` |
| `[-_-] · ZZZ` | Interrumpido | `session.execution.interrupted` |

Las caras temporales vuelven solas a `HI`. No hay temporizadores que dejen a Bitty «congelada» en un estado anterior.

## Instalación

Clona el repo y apunta OpenCode a la carpeta `plugin/`:

```bash
git clone https://github.com/Marcelbon08/bitty-mascot.git
cd bitty-mascot/plugin
npm install
npm run build
```

### Terminal

Añade el plugin a `~/.config/opencode/cli.json`:

```json
{
  "$schema": "https://opencode.ai/v2/cli.json",
  "plugins": ["C:/Users/marce/Downloads/bitty-mascot/plugin"]
}
```

Ajusta la ruta a donde hayas clonado el repo. En macOS/Linux usa `/home/usuario/bitty-mascot/plugin`.

### Desktop

Añade el mismo plugin a `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "plugins": ["C:/Users/marce/Downloads/bitty-mascot/plugin"]
}
```

El bundle compilado ya viene versionado en `gui-dist/gui-experimental.cjs`, así que no hace falta compilarlo para usarlo desde el repo.

También puedes instalarlo como paquete cuando se publique en npm:

```bash
opencode plugin add opencode-bitty-plugin
```

## Comprobación

```bash
opencode --standalone --print-logs --log-level debug run "hola"
```

En los logs debe aparecer `loading plugin ... opencode-bitty-plugin` y la entrada `gui-experimental.cjs`. En la TUI verás `Bitty [o_o] HI` en la barra de inicio y del prompt. Para ver el panel, entra en una sesión y escribe `/bitty` o pulsa `Ctrl+Alt+B`: el slot `session.panel` solo existe dentro de una sesión.

## Desarrollo

```bash
npm install
npm run build     # genera dist/ y copia el bundle a gui-dist/
npm run typecheck
```

Estructura:

```
plugin/
├── src/
│   ├── index.ts            # parte servidor
│   ├── tui.tsx             # parte terminal
│   ├── gui.tsx             # parte Desktop
│   └── shared/faces.ts     # caras y traducción de eventos
├── gui-dist/               # bundle GUI versionado
├── scripts/copy-bundle.mjs
└── package.json            # exports: ., ./tui, ./gui-experimental
```

## Hecho con IA

Igual que el resto del proyecto, este plugin fue generado con IA y revisado por Marcelbon. No es un producto oficial de OpenCode. Ver [AI_DISCLOSURE.md](../AI_DISCLOSURE.md).
