// Regla de permiso de Bitty: para su propia acción SIEMPRE se pregunta.
// Sin esta regla, permission.assert dejaría pasar la acción por defecto.

export const INSTALL_ACTION = "bitty.install.mcp"
export const CURSOR_ACTION = "bitty.cursor"
export const CLICK_ACTION = "bitty.click"
export const SCREEN_ACTION = "bitty.screen"
export const RECIPE_ACTION = "bitty.recipe"

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
    event.message = "Acuerdo leído en Bitty: permiso para mover su cursor virtual. No moverá tu ratón ni hará clics."
    return
  }
  if (event.action === CLICK_ACTION) {
    event.effect = "ask"
    event.message = "Acuerdo leído en Bitty: permiso para su clic virtual y abrir una app de su lista. Tu ratón real no se moverá."
    return
  }
  if (event.action === SCREEN_ACTION) {
    event.effect = "ask"
    event.message = "Acuerdo leído en Bitty: permiso para capturar tu pantalla ahora. Revisa qué hay visible antes de aceptar."
    return
  }
  if (event.action === RECIPE_ACTION) {
    event.effect = "ask"
    event.message = "Bitty quiere usar una receta guardada: puede abrir Brave en una web de Gmail y mirar la pantalla. Nunca guarda ni escribe contraseñas."
  }
}
