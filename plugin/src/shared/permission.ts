// Regla de permiso de Bitty: para su propia acción SIEMPRE se pregunta.
// Sin esta regla, permission.assert dejaría pasar la acción por defecto.

export const INSTALL_ACTION = "bitty.install.mcp"

export interface PermissionEvent {
  action?: string
  effect?: string
  message?: string
}

export function forceAsk(event: PermissionEvent): void {
  if (event.action !== INSTALL_ACTION) return
  event.effect = "ask"
  event.message = "Bitty quiere añadir un servidor MCP. Revisa qué se instala antes de aceptar."
}
