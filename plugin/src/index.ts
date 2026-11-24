import { readFile } from "node:fs/promises"
import { Plugin } from "@opencode/plugin"
import { callBridge, type BridgeCapture, type BridgeClick, type BridgeCursor } from "./shared/bridge"
import { installFromRpc } from "./shared/handleInstall"
import {
  CLICK_ACTION, CURSOR_ACTION, forceAsk, SCREEN_ACTION,
} from "./shared/permission"
import { BittyRpc } from "./shared/rpc"

export default Plugin.define({
  id: "bitty",
  async setup(ctx) {
    // Marca de carga para poder comprobar que el plugin se activó en el servidor.
    await ctx.storage.set("loadedAt", new Date().toISOString())

    // Sin una regla explícita, permission.assert autorizaría por defecto.
    // Forzamos `ask` solo para nuestras acciones: el diálogo nativo aparece siempre.
    await ctx.permission.hook("evaluate", async (event) => {
      forceAsk(event)
    })

    // Fase 4: el permiso nativo y el registro del MCP ocurren aquí.
    // La TUI y Desktop solo pueden pedirlo a través de este RPC.
    await ctx.rpc.register(BittyRpc, {
      install: async (raw) => installFromRpc(ctx, raw),
    })

    // Puente local: OpenCode puede mover el cursor de Bitty y mirar la pantalla.
    await ctx.tool.transform((editor) => {
      editor.namespace({
        name: "bitty",
        description: "Mascota de OpenCode y visión local del escritorio",
      })

      editor.add({
        name: "cursor",
        description: "Mueve el cursor virtual de Bitty a unas coordenadas de pantalla. No toca el ratón del usuario, no hace clics y no escribe.",
        input: {
          type: "object",
          properties: {
            x: { type: "integer", minimum: -100000, maximum: 100000, description: "Coordenada X absoluta de pantalla" },
            y: { type: "integer", minimum: -100000, maximum: 100000, description: "Coordenada Y absoluta de pantalla" },
          },
          required: ["x", "y"],
          additionalProperties: false,
        },
        options: { namespace: "bitty", codemode: true },
        execute: async (raw, context) => {
          const input = raw as { x: number, y: number }
          await ctx.permission.assert({
            sessionID: context.sessionID,
            agent: context.agent,
            source: { type: "tool", messageID: context.messageID, id: context.id },
            action: CURSOR_ACTION,
            resources: [`${input.x},${input.y}`],
            // Sin `save`: OpenCode pregunta cada vez.
          })
          const result = await callBridge<BridgeCursor>("/cursor", input, context.signal)
          return { content: `Cursor de Bitty movido a (${result.x}, ${result.y}).` }
        },
      })

      editor.add({
        name: "click",
        description: "Mueve el cursor de Bitty, hace su clic visual y puede abrir una app permitida (brave). Nunca mueve el ratón del usuario ni pulsa teclas.",
        input: {
          type: "object",
          properties: {
            x: { type: "integer", minimum: -100000, maximum: 100000, description: "Coordenada X absoluta de pantalla" },
            y: { type: "integer", minimum: -100000, maximum: 100000, description: "Coordenada Y absoluta de pantalla" },
            open: { type: "string", enum: ["brave"], description: "App permitida que Bitty abrirá tras el clic" },
          },
          required: ["x", "y"],
          additionalProperties: false,
        },
        options: { namespace: "bitty", codemode: true },
        execute: async (raw, context) => {
          const input = raw as { x: number, y: number, open?: "brave" }
          await ctx.permission.assert({
            sessionID: context.sessionID,
            agent: context.agent,
            source: { type: "tool", messageID: context.messageID, id: context.id },
            action: CLICK_ACTION,
            resources: [input.open ? `${input.x},${input.y}:${input.open}` : `${input.x},${input.y}`],
            // Sin `save`: OpenCode pregunta cada vez.
          })
          const result = await callBridge<BridgeClick>("/click", input, context.signal)
          return {
            content: `Clic de Bitty en (${result.x}, ${result.y}).`
              + (input.open ? ` Abriendo ${input.open}.` : "")
              + " Tu ratón no se ha movido.",
          }
        },
      })

      editor.add({
        name: "screen",
        description: "Captura la pantalla real del usuario y se la muestra a OpenCode como imagen. Pide permiso antes de mirar. Úsala cuando necesites ver el escritorio o el navegador del usuario.",
        input: {
          type: "object",
          properties: {},
          additionalProperties: false,
        },
        options: { namespace: "bitty", codemode: true },
        execute: async (_input, context) => {
          await ctx.permission.assert({
            sessionID: context.sessionID,
            agent: context.agent,
            source: { type: "tool", messageID: context.messageID, id: context.id },
            action: SCREEN_ACTION,
            resources: ["pantalla"],
            // Sin `save`: OpenCode pregunta cada vez.
          })
          const shot = await callBridge<BridgeCapture>("/capture", {}, context.signal)
          // OpenCode 2.3.2 solo materializa data-URLs en resultados de tools;
          // un file:// no se lee del disco. Leemos el PNG y lo enviamos inline,
          // igual que hacen las tools internas read y MCP.
          const bytes = await readFile(shot.path)
          if (bytes.byteLength > 20 * 1024 * 1024) {
            throw new Error("La captura supera el límite de 20 MB de OpenCode.")
          }
          const dataUrl = `data:image/png;base64,${bytes.toString("base64")}`
          return {
            content: [
              {
                type: "file",
                uri: dataUrl,
                mime: "image/png",
                name: "bitty-pantalla.png",
              } as const,
              {
                type: "text",
                text: `Captura de ${shot.width}x${shot.height} (${shot.screens} pantalla(s)).`,
              } as const,
            ],
            metadata: { path: shot.path, width: shot.width, height: shot.height, screens: shot.screens },
          }
        },
      })
    })
  },
})
