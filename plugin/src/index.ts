import { Plugin } from "@opencode/plugin"

export default Plugin.define({
  id: "bitty",
  async setup(ctx) {
    // Marca de carga para poder comprobar que el plugin se activó en el servidor.
    await ctx.storage.set("loadedAt", new Date().toISOString())
  },
})
