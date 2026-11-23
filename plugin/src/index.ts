import { Plugin } from "@opencode/plugin"
import { installFromRpc } from "./shared/handleInstall"
import { forceAsk } from "./shared/permission"
import { BittyRpc } from "./shared/rpc"

export default Plugin.define({
  id: "bitty",
  async setup(ctx) {
    // Marca de carga para poder comprobar que el plugin se activó en el servidor.
    await ctx.storage.set("loadedAt", new Date().toISOString())

    // Sin una regla explícita, permission.assert autorizaría por defecto.
    // Forzamos `ask` solo para nuestra acción: el diálogo nativo aparece siempre.
    await ctx.permission.hook("evaluate", async (event) => {
      forceAsk(event)
    })

    // Fase 4: el permiso nativo y el registro del MCP ocurren aquí.
    // La TUI y Desktop solo pueden pedirlo a través de este RPC.
    await ctx.rpc.register(BittyRpc, {
      install: async (raw) => installFromRpc(ctx, raw),
    })
  },
})
