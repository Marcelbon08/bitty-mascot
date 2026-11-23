// Fase 4: instalación de capacidades cerradas.
// Solo se registran servidores MCP del catálogo, nunca comandos arbitrarios.
// El permiso se pide siempre con el diálogo nativo de OpenCode (sin guardarlo).

import { CAPACITIES, type Capacity, type CapacityId } from "./capacities"
import { INSTALL_ACTION } from "./permission"

export interface InstallResult {
  ok: boolean
  capacity: Capacity
  message: string
  /** true cuando el permiso fue rechazado o no se pudo confirmar. */
  denied: boolean
}

function reason(capacity: Capacity): string {
  return capacity.permissionReason
}

/**
 * Pide permiso y registra el MCP en la ubicación indicada.
 * `ctx` debe exponer `permission.assert`, `mcp.transform`/`mcp.reload` y `client.mcp.*`.
 * Devuelve siempre un resultado: Bitty nunca lanza el error al usuario.
 */
export async function installCapacity(
  ctx: any,
  id: CapacityId,
  input: { sessionID: string; directory?: string; agent?: string },
): Promise<InstallResult> {
  const capacity = CAPACITIES[id]
  const resources = [`mcp:${capacity.mcpName}`, capacity.config.command.join(" ")]

  try {
    // Cada vez: no se pasa `save`, así que OpenCode no recuerda la aprobación.
    await ctx.permission.assert({
      sessionID: input.sessionID,
      agent: input.agent,
      action: INSTALL_ACTION,
      resources,
      metadata: {
        title: capacity.title,
        description: capacity.description,
        reason: reason(capacity),
      },
    })
  } catch {
    return {
      ok: false,
      capacity,
      message: `Permiso rechazado: no he instalado ${capacity.title}.`,
      denied: true,
    }
  }

  try {
    // Vía preferida: transform oficial del SDK, aplicable a la ubicación actual.
    if (typeof ctx.mcp?.transform === "function") {
      await ctx.mcp.transform((editor: any) => {
        if (typeof editor?.get === "function" && editor.get(capacity.mcpName)) return
        if (typeof editor?.set === "function") {
          editor.set(capacity.mcpName, capacity.config)
        } else if (typeof editor?.add === "function") {
          editor.add(capacity.mcpName, capacity.config)
        }
      })
      if (typeof ctx.mcp?.reload === "function") await ctx.mcp.reload()
      return {
        ok: true,
        capacity,
        message: `${capacity.title} listo: servidor MCP '${capacity.mcpName}' añadido.`,
        denied: false,
      }
    }

    // Alternativa del cliente experimental cuando el transform no está disponible.
    const existing: any = await ctx.client?.mcp?.list?.(
      input.directory ? { location: { directory: input.directory } } : undefined,
    )
    const servers: any[] = Array.isArray(existing?.data) ? existing.data : []
    if (!servers.some((server) => server?.name === capacity.mcpName)) {
      await ctx.client.mcp.add({
        server: capacity.mcpName,
        ...(input.directory ? { location: { directory: input.directory } } : {}),
        config: capacity.config,
      })
    }
    await ctx.client.mcp.connect({
      server: capacity.mcpName,
      ...(input.directory ? { location: { directory: input.directory } } : {}),
    })
    return {
      ok: true,
      capacity,
      message: `${capacity.title} listo: servidor MCP '${capacity.mcpName}' añadido.`,
      denied: false,
    }
  } catch (error) {
    return {
      ok: false,
      capacity,
      message: `No pude instalar ${capacity.title}: ${String((error as Error)?.message ?? error)}`,
      denied: false,
    }
  }
}
