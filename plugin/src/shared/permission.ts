// Regla de permiso de Bitty: para su propia acción SIEMPRE se pregunta.
// Sin esta regla, permission.assert dejaría pasar la acción por defecto.

export const INSTALL_ACTION = "bitty.install.mcp"
export const CURSOR_ACTION = "bitty.cursor"
export const SCREEN_ACTION = "bitty.screen"

export interface PermissionEvent {
  action?: string
  effect?: string
  message?: string
}

export function forceAsk(event: PermissionEvent): void {
  if (event.action === INSTALL_ACTION) {
    event.effect = "ask"
    event.message = "Bitty quiere añadir un servidor MCP. Revisa qué se instala antes de aceptar."
    return
  }
  if (event.action === CURSOR_ACTION) {
    event.effect = "ask"
    event.message = "Bitty quiere mover su cursor virtual a unas coordenadas. No moverá tu ratón ni hará clics."
    return
  }
  if (event.action === SCREEN_ACTION) {
    event.effect = "ask"
    event.message = "Bitty quiere capturar tu pantalla para que OpenCode la vea. Revisa qué hay visible antes de aceptar."
  }
}
