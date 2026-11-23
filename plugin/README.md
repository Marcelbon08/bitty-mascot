# Bitty para OpenCode (plugin)

Bitty también vive **dentro de OpenCode**: en la **terminal (TUI)** y en **OpenCode Desktop**. No sustituye a la mascota flotante: la acompaña. Es la misma identidad —*«Soy Bitty, tu mascota de OpenCode»*— y reacciona en tiempo real a lo que hace la sesión. Desde v2.2.0 además **opina**: deja sugerencias breves sin escribir nunca en tu conversación.

> Requiere OpenCode **v2.3.2 o superior**. Es un plugin experimental: usa los puntos de extensión `./tui` y `./gui-experimental`.

## Qué se ve

| Superficie | Dónde aparece Bitty |
|---|---|
| Terminal | Indicador permanente en la barra de inicio y del prompt: `Bitty [o_o] HI` |
| Terminal | Panel completo con `bitty.panel` (paleta, `/bitty` o `Ctrl+Alt+B`), dentro de una sesión |
| Terminal | Opinión con `/bitty-opina` o `Ctrl+Alt+O`; resumen en la barra como `Bitty 💡 REVISA` |
| Desktop | Panel lateral **Bitty**, píldora junto al composer y texto en la barra inferior |
| Desktop | Paleta de comandos, `/bitty` y `Mod+Alt+B`; opinión con `/bitty-opina` o `Mod+Alt+O` |

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
| `[?_?] · OPINANDO` | Mirando la sesión | `/bitty-opina` o sugerencia automática |
| `[^_^] · SIGUE` | Sugerencia: seguir | Veredicto `SEGUIR` |
| `[o_O] · REVISA ESTO` | Sugerencia: revisar | Veredicto `REVISAR` |
| `[>_<] · MEJOR PARAR` | Sugerencia: parar | Veredicto `PARAR` |

Las caras temporales vuelven solas a `HI`. No hay temporizadores que dejen a Bitty «congelada» en un estado anterior.

## Bitty opina (solo sugerencias)

Cuando la sesión se asienta, Bitty calcula una sugerencia **local** y la muestra en dos sitios:

- **En la mascota**: resumen muy corto, `💡 SIGUE`, `💡 REVISA` o `💡 PARA`.
- **En el panel**: tres líneas —`Veredicto`, `Razón` y `Siguiente`— con el detalle.

Puedes pedirla en cualquier momento:

| Superficie | Comando | Atajo |
|---|---|---|
| TUI | `/bitty-opina` | `Ctrl+Alt+O` |
| Desktop | `/bitty-opina` | `Mod+Alt+O` |

También está el botón **Pedir opinión** dentro del panel y la opción en la píldora de Bitty junto al composer.

### Cómo funciona

1. Lee solo la **sesión actual** (últimos mensajes y eventos recientes).
2. Aplica una **heurística local**: detecta fallos, bugs sin verificar, sesiones largas, documentación pendiente o intención de parar.
3. Muestra esa sugerencia al instante. Es gratis, no usa red y funciona aunque no haya cuota.
4. Si pides la opinión de forma explícita, intenta además un **refinado stateless** con el modelo (`experimental.generate.text`, sin sesión ni mensajes nuevos). Si el modelo devuelve 429/502, Bitty conserva la sugerencia local y no muestra error.

> Bitty nunca escribe en tu sesión, nunca cancela tu trabajo y no «verá todo» hasta la Fase 3. La opinión es un consejo, no una orden.

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

En los logs debe aparecer `loading plugin ... opencode-bitty-plugin` y la entrada `gui-experimental.cjs`. En la TUI verás `Bitty [o_o] HI` en la barra de inicio y del prompt. Para ver el panel, entra en una sesión y escribe `/bitty` o pulsa `Ctrl+Alt+B`: el slot `session.panel` solo existe dentro de una sesión. Para comprobar la opinión, escribe `/bitty-opina`: la barra debe pasar a `Bitty 💡 …` y el panel debe mostrar `Veredicto`, `Razón` y `Siguiente`.

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
│   └── shared/
│       ├── faces.ts        # caras y traducción de eventos
│       ├── opinion.ts      # prompt, parser y resumen para la mascota
│       └── opina.ts        # heurística local + refinado con modelo
├── gui-dist/               # bundle GUI versionado
├── scripts/copy-bundle.mjs
└── package.json            # exports: ., ./tui, ./gui-experimental
```

## Hecho con IA

Igual que el resto del proyecto, este plugin fue generado con IA y revisado por Marcelbon. No es un producto oficial de OpenCode. La opinión local no envía nada a ningún servicio; el refinado opcional envía solo un extracto acotado de la sesión actual al modelo configurado en OpenCode. Ver [AI_DISCLOSURE.md](../AI_DISCLOSURE.md).
