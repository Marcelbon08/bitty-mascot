// Catálogo cerrado de capacidades que Bitty puede instalar por su cuenta.
// Solo servidores MCP: nunca comandos arbitrarios ni extensiones del navegador.
// La decisión se toma con el diálogo nativo de permisos de OpenCode.

export interface McpLocalConfig {
  type: "local"
  command: string[]
  cwd?: string
  environment?: Record<string, string>
  disabled?: boolean
  codemode?: boolean
  timeout?: {
    startup?: number
    catalog?: number
    execution?: number
  }
  protocol?: "legacy" | "auto" | "2026-07-28"
  pool?: boolean
}

export type CapacityId = "navegador"

export interface Capacity {
  id: CapacityId
  title: string
  description: string
  /** Nombre con el que se registrará el servidor MCP en la configuración de OpenCode. */
  mcpName: string
  config: McpLocalConfig
  permissionReason: string
}

export const CAPACITIES: Record<CapacityId, Capacity> = {
  navegador: {
    id: "navegador",
    title: "Ver el navegador",
    description: "Añade el MCP de Playwright para que OpenCode pueda abrir y leer páginas web.",
    mcpName: "bitty-navegador",
    config: {
      type: "local",
      command: ["npx", "-y", "@playwright/mcp@latest"],
      timeout: {
        startup: 60000,
        catalog: 30000,
        execution: 120000,
      },
    },
    permissionReason:
      "Bitty ha detectado que la sesión habla de una web y quiere añadir el servidor MCP 'bitty-navegador' (Playwright). Se instalará en tu configuración de OpenCode. Puedes rechazarlo.",
  },
}

export const CAPACITY_IDS = Object.keys(CAPACITIES) as CapacityId[]

const BROWSER_PATTERN = /navegador|browser|web|p[aá]gina|sitio|http|pantalla|chrome|firefox/i

/** Detecta qué capacidad pide el texto, por ahora solo navegador. */
export function capacityFromText(text: string): CapacityId | undefined {
  const value = String(text ?? "")
  if (!BROWSER_PATTERN.test(value)) return undefined
  return "navegador"
}

/** ¿Esta sesión parece necesitar ver una web? */
export function needsBrowser(text: string): boolean {
  return capacityFromText(text) === "navegador"
}
