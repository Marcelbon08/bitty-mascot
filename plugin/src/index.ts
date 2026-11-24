import { readFile } from "node:fs/promises"
import { Plugin } from "@opencode/plugin"
import {
  callBridge, type BridgeCapture, type BridgeClick, type BridgeCursor,
  type BridgeLaunch, type BridgeRecipes,
} from "./shared/bridge"
import { installFromRpc } from "./shared/handleInstall"
import {
  CLICK_ACTION, CURSOR_ACTION, forceAsk, RECIPE_ACTION, SCREEN_ACTION,
} from "./shared/permission"
import { describeRecipe, validateRecipe, type Recipe } from "./shared/recipes"
import { BittyRpc } from "./shared/rpc"

// Antes del permiso nativo: Bitty muestra el acuerdo corto y solo sigue si se
// acepta. Rechazarlo corta la acción sin llegar a pedir permiso ni a mirar.
async function ensureAgreement(signal?: AbortSignal): Promise<void> {
  await callBridge("/agreement", {}, signal)
}

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
          await ensureAgreement(context.signal)
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
          await ensureAgreement(context.signal)
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
          await ensureAgreement(context.signal)
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

      editor.add({
        name: "recipe",
        description: "Memoria de recetas de Bitty. Guarda, lista, prepara u olvida planes visuales reutilizables (por ejemplo abrir Brave en Gmail y elegir una cuenta). Solo Brave, solo HTTPS de Gmail/Google, sin contraseñas ni tecleo.",
        input: {
          type: "object",
          properties: {
            action: {
              type: "string",
              enum: ["guardar", "listar", "ejecutar", "olvidar"],
              description: "guardar: aprende una receta; listar: recetas guardadas; ejecutar: abre la web y devuelve el plan y una captura; olvidar: borra una receta",
            },
            id: { type: "string", pattern: "^[a-z0-9][a-z0-9_-]{0,63}$", description: "Identificador corto de la receta" },
            label: { type: "string", minLength: 1, maxLength: 60, description: "Nombre legible, sin correos ni secretos" },
            account: { type: "string", maxLength: 120, description: "Correo de la cuenta ya iniciada; nunca contraseña" },
            url: { type: "string", maxLength: 300, description: "HTTPS de mail.google.com o accounts.google.com" },
            steps: {
              type: "array",
              minItems: 1,
              maxItems: 12,
              items: {
                type: "object",
                properties: {
                  kind: { type: "string", enum: ["open", "navigate", "look", "click", "verify"] },
                  hint: { type: "string", minLength: 1, maxLength: 60, description: "Pista visual corta, sin correos ni credenciales" },
                },
                required: ["kind"],
                additionalProperties: false,
              },
            },
          },
          required: ["action"],
          additionalProperties: false,
        },
        options: { namespace: "bitty", codemode: true },
        execute: async (raw, context) => {
          const input = raw as {
            action: "guardar" | "listar" | "ejecutar" | "olvidar"
            id?: string
            label?: string
            account?: string
            url?: string
            steps?: unknown
          }
          await ensureAgreement(context.signal)
          await ctx.permission.assert({
            sessionID: context.sessionID,
            agent: context.agent,
            source: { type: "tool", messageID: context.messageID, id: context.id },
            action: RECIPE_ACTION,
            resources: [input.action, input.id || ""],
            // Sin `save`: OpenCode pregunta cada vez.
          })

          if (input.action === "listar") {
            const result = await callBridge<BridgeRecipes>("/recipes", { action: "listar" }, context.signal)
            const text = result.recipes.length
              ? result.recipes.map(describeRecipe).join("\n\n")
              : "> No hay recetas guardadas todavía."
            return { content: text }
          }

          if (input.action === "olvidar") {
            if (!input.id) throw new Error("Falta el id de la receta.")
            await callBridge<BridgeRecipes>("/recipes", { action: "olvidar", id: input.id }, context.signal)
            return { content: `Receta ${input.id} olvidada.` }
          }

          if (input.action === "guardar") {
            const recipe = validateRecipe(input)
            await callBridge<BridgeRecipes>(
              "/recipes", { action: "guardar", recipe }, context.signal,
            )
            return { content: `Receta guardada: ${recipe.label} [${recipe.id}].\n${describeRecipe(recipe)}` }
          }

          const listed = await callBridge<BridgeRecipes>("/recipes", { action: "listar" }, context.signal)
          const recipe: Recipe | undefined = listed.recipes.find((item) => item.id === input.id)
          if (!recipe) throw new Error("No existe esa receta. Usa bitty_recipe con action=listar.")

          // La parte segura de la receta: abrir Brave en la web permitida.
          // Los pasos visuales siguen con bitty_screen / bitty_click, cada uno
          // con su propio permiso nativo.
          if (recipe.url) {
            await callBridge<BridgeLaunch>(
              "/launch", { app: "brave", url: recipe.url }, context.signal,
            )
          } else if (recipe.steps.some((step) => step.kind === "open")) {
            await callBridge<BridgeLaunch>("/launch", { app: "brave" }, context.signal)
          }

          const shot = await callBridge<BridgeCapture>("/capture", {}, context.signal)
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
                name: "bitty-receta.png",
              } as const,
              {
                type: "text",
                text: `${describeRecipe(recipe)}\n\nBrave está abierto en la web de la receta. Continúa los pasos visuales con bitty_screen y bitty_click; cada uno pedirá permiso. Tu ratón no se mueve y Bitty no escribe credenciales.`,
              } as const,
            ],
            metadata: {
              id: recipe.id,
              path: shot.path,
              width: shot.width,
              height: shot.height,
              screens: shot.screens,
            },
          }
        },
      })
    })
  },
})
