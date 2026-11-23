import { Plugin } from "@opencode/plugin"
import { CAPACITIES, type CapacityId } from "./shared/capacities"
import { installCapacity } from "./shared/install"
import { BittyRpc } from "./shared/rpc"
import { safeAgent, safeDirectory, safeSessionId } from "./shared/validate"

function capacityId(value: string): CapacityId | undefined {
  return Object.prototype.hasOwnProperty.call(CAPACITIES, value) ? (value as CapacityId) : undefined
}

interface InstallInput {
  capacity: string
  sessionID: string
  directory?: string
  agent?: string
}

export default Plugin.define({
  id: "bitty",
  async setup(ctx) {
    // Marca de carga para poder comprobar que el plugin se activó en el servidor.
    await ctx.storage.set("loadedAt", new Date().toISOString())

    // Sin una regla explícita, permission.assert autorizaría por defecto.
    // Forzamos `ask` solo para nuestra acción: el diálogo nativo aparece siempre.
    await ctx.permission.hook("evaluate", async (event) => {
      if (event.action === "bitty.install.mcp") {
        event.effect = "ask"
        event.message = "Bitty quiere añadir un servidor MCP. Revisa qué se instala antes de aceptar."
      }
    })

    // Fase 4: el permiso nativo y el registro del MCP ocurren aquí.
    // La TUI y Desktop solo pueden pedirlo a través de este RPC.
    await ctx.rpc.register(BittyRpc, {
      install: async (raw) => {
        const input = raw as InstallInput
        const id = capacityId(input.capacity)
        if (!id) {
          return {
            ok: false,
            title: "Bitty",
            message: "Capacidad desconocida: no he instalado nada.",
            denied: false,
          }
        }

        const sessionID = safeSessionId(input.sessionID)
        if (!sessionID) {
          return {
            ok: false,
            title: "Bitty",
            message: "Sesión no válida: no he instalado nada.",
            denied: false,
          }
        }

        const result = await installCapacity(ctx, id, {
          sessionID,
          directory: safeDirectory(input.directory),
          agent: safeAgent(input.agent) || undefined,
        })
        return {
          ok: result.ok,
          title: result.capacity.title,
          message: result.message,
          denied: result.denied,
        }
      },
    })
  },
})
