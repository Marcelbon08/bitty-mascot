// Fase 3: Bitty puede mirar más allá de la sesión actual.
// Lee solo el proyecto/directorio indicado y devuelve un resumen acotado,
// pensado para sugerencias, nunca para copiar contenido sensible.

export interface ScanSession {
  id: string
  title: string
  messages: readonly any[]
}

export interface SessionScan {
  project?: string
  directory?: string
  sessions: ScanSession[]
  total: number
  truncated: boolean
}

export interface ScanOptions {
  limit?: number
  perSession?: number
}

const DEFAULT_LIMIT = 6
const DEFAULT_PER_SESSION = 6

function textOf(message: any): string {
  if (typeof message?.text === "string") return message.text
  if (Array.isArray(message?.parts)) {
    return message.parts
      .filter((p: any) => p?.type === "text" || typeof p?.text === "string")
      .map((p: any) => String(p.text ?? ""))
      .join(" ")
  }
  return ""
}

function titleOf(session: any): string {
  const value = typeof session?.title === "string" ? session.title : ""
  return value.slice(0, 120) || String(session?.id ?? "sesión")
}

/**
 * Escanea las sesiones recientes de un proyecto.
 * `client` es el cliente de OpenCode inyectado en el plugin; se acepta `any`
 * para no acoplar este módulo a una versión concreta del SDK.
 */
export async function scanProject(
  client: any,
  options: ScanOptions & { directory?: string; project?: string } = {},
): Promise<SessionScan> {
  const limit = Math.max(1, Math.min(options.limit ?? DEFAULT_LIMIT, 20))
  const perSession = Math.max(1, Math.min(options.perSession ?? DEFAULT_PER_SESSION, 20))
  const input: Record<string, unknown> = {
    limit,
    order: "desc",
  }
  if (options.directory) input.directory = options.directory
  if (options.project) input.project = options.project

  const response: any = await client.session.list(input)
  const rows: any[] = Array.isArray(response?.data)
    ? response.data
    : Array.isArray(response)
      ? response
      : []

  const sessions: ScanSession[] = []
  for (const row of rows.slice(0, limit)) {
    const id = String(row?.id ?? "")
    if (!id) continue
    let messages: any[] = []
    try {
      const detail: any = await client.message.list({ sessionID: id })
      messages = (Array.isArray(detail?.data) ? detail.data : Array.isArray(detail) ? detail : []).slice(
        -perSession,
      )
    } catch {
      messages = []
    }
    sessions.push({ id, title: titleOf(row), messages })
  }

  return {
    project: options.project,
    directory: options.directory,
    sessions,
    total: Array.isArray(response?.total) ? response.total : rows.length,
    truncated: rows.length > sessions.length,
  }
}

/** Convierte el escaneo en un texto corto apto para el prompt del modelo. */
export function scanToText(scan: SessionScan): string {
  const lines: string[] = []
  for (const session of scan.sessions) {
    lines.push(`Sesión: ${session.title}`)
    for (const message of session.messages) {
      const role =
        message?.info?.role === "user" || message?.role === "user" || message?.type === "user"
          ? "usuario"
          : "asistente"
      const text = textOf(message).replace(/\s+/g, " ").slice(0, 240)
      if (text) lines.push(`  ${role}: ${text}`)
    }
  }
  return lines.join("\n").slice(0, 4200)
}
