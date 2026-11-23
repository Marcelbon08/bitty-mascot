// Endurecimiento de la superficie RPC: nada de lo que envíe la TUI o Desktop
// debe poder convertirse en una opción, una ruta arbitraria o un agente ajeno.

const SESSION_ID = /^[A-Za-z0-9_][A-Za-z0-9_-]{0,127}$/
const AGENT = /^[A-Za-z0-9_][A-Za-z0-9_.-]{0,63}$/

/** IDs de sesión aceptados por la CLI de OpenCode. */
export function safeSessionId(value: unknown): string {
  return typeof value === "string" && SESSION_ID.test(value) ? value : ""
}

/** Nombres de agente: letras, números, guiones y puntos, sin espacios. */
export function safeAgent(value: unknown): string {
  return typeof value === "string" && AGENT.test(value) ? value : ""
}

/**
 * Rutas de directorio acotadas. No resolvemos ni abrimos nada aquí: solo
 * recortamos la longitud y rechazamos caracteres de control.
 */
export function safeDirectory(value: unknown): string | undefined {
  if (typeof value !== "string") return undefined
  const text = value.slice(0, 512)
  if (!text || /[\x00-\x1f\x7f]/.test(text)) return undefined
  return text
}
