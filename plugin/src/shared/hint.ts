// Avisos contextuales de Bitty. Solo sugieren: no instalan ni escriben nada.

import { needsBrowser } from "./capacities"

/**
 * Si la sesión habla de una web, el aviso cambia según el MCP ya esté
 * disponible: no se ofrece instalar lo que ya está instalado.
 */
export function browserHint(text: string, available: boolean): string {
  if (!needsBrowser(text)) return ""
  return available
    ? "Veo una web en la sesión. El navegador de OpenCode está disponible: dime qué quieres revisar y usaré sus herramientas para mirarla."
    : "Veo una web en la sesión. Si quieres que la mire, usa /bitty-instalar y acepta el permiso para instalar el MCP de Playwright."
}
