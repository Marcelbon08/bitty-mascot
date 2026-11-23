// Opiniones de Bitty. Solo sugerencias: nunca se escriben en la sesión del usuario.
// La generación es stateless (experimental.generate.text), así que no crea sesión,
// no añade mensajes y no altera el historial de OpenCode.

export type Verdict = "seguir" | "revisar" | "parar"

export type OpinionStatus = "idle" | "thinking" | "idea" | "ready" | "error"

export interface Opinion {
  verdict: Verdict
  reason: string
  next: string
  /** Resumen de 5 letras para la mascota pequeña. */
  short: string
  /** Texto completo de la sugerencia para el panel. */
  label: string
}

export interface OpinionState {
  status: OpinionStatus
  opinion?: Opinion
  error?: string
}

export const EMPTY_OPINION: OpinionState = { status: "idle" }

const SYSTEM = `Eres Bitty, la mascota de OpenCode creada por Marcelbon. El usuario se llama Marcelbon; trátalo por su nombre. Hablas siempre en español, de forma breve, concreta y amable.

Te muestran un extracto de una sesión de trabajo. Das TU OPINIÓN como sugerencia, nunca como una orden. No tienes acceso al resto del equipo: basa tu juicio solo en lo que ves y sé honesto sobre la incertidumbre.

Responde en EXACTAMENTE tres líneas, sin encabezados extra, sin listas, sin markdown y sin escribir en la conversación:
Veredicto: SEGUIR|REVISAR|PARAR
Razón: una frase corta explicando por qué
Siguiente: una frase corta con el mejor paso siguiente

Usa SEGUIR si el rumbo es bueno, REVISAR si conviene ajustar algo antes de continuar, y PARAR solo si claramente no merece seguir. Máximo 90 caracteres por línea.`

/** Extrae un texto legible de los mensajes, sin fiarse del formato exacto del schema. */
function messageText(message: any): string {
  if (typeof message?.text === "string") return message.text
  const parts = message?.parts
  if (!Array.isArray(parts)) return ""
  return parts
    .filter((part: any) => part?.type === "text" || typeof part?.text === "string")
    .map((part: any) => String(part.text ?? ""))
    .join(" ")
    .trim()
}

/** Reduce el historial a un extracto acotado para no disparar costes descontrolados. */
export function summarizeMessages(messages: readonly any[], maxChars = 4200): string {
  const usable = messages
    .map((message: any) => ({
      role: message?.info?.role ?? message?.role ?? message?.type ?? (message?.info?.agent ? "assistant" : "mensaje"),
      text: messageText(message),
    }))
    .filter((item) => item.text.length > 0)
    .slice(-14)

  if (usable.length === 0) return "(la sesión todavía no tiene mensajes de texto)"

  const lines = usable.map((item) => `${String(item.role).toUpperCase()}: ${item.text.slice(0, 420)}`)
  let result = lines.join("\n")
  if (result.length > maxChars) result = "…" + result.slice(result.length - maxChars)
  return result
}

export function buildOpinionPrompt(messages: readonly any[]): string {
  return `${SYSTEM}\n\nSESIÓN DE MARCELBON (extracto):\n${summarizeMessages(messages)}`
}

const SHORT: Record<Verdict, string> = {
  seguir: "SIGUE",
  revisar: "REVISA",
  parar: "PARA",
}

/** Convierte la respuesta del modelo en una sugerencia estructurada y tolerante. */
export function parseOpinion(text: string): Opinion {
  const clean = String(text ?? "").replace(/\r/g, "").trim()
  const verdictMatch = clean.match(/Veredicto\s*:\s*(SEGUIR|REVISAR|PARAR)/i)
  const reasonMatch = clean.match(/Raz[oó]n\s*:\s*([^\n]+)/i)
  const nextMatch = clean.match(/Siguiente\s*:\s*([^\n]+)/i)

  let verdict: Verdict = "revisar"
  if (verdictMatch) {
    const value = verdictMatch[1].toLowerCase()
    if (value === "seguir" || value === "parar") verdict = value
  } else {
    const lower = clean.toLowerCase()
    if (/\bparar\b/.test(lower)) verdict = "parar"
    else if (/\bseguir\b/.test(lower)) verdict = "seguir"
  }

  const reason = (reasonMatch?.[1] ?? "No tengo suficiente contexto para asegurarlo.").trim().slice(0, 160)
  const next = (nextMatch?.[1] ?? "Cuéntame un poco más y lo volvemos a mirar.").trim().slice(0, 160)

  return {
    verdict,
    reason,
    next,
    short: SHORT[verdict],
    label: `Veredicto: ${SHORT[verdict]}\nRazón: ${reason}\nSiguiente: ${next}`,
  }
}

/** Texto mini que se muestra en la barra/píldora de la mascota. */
export function opinionBadge(state: OpinionState): string {
  switch (state.status) {
    case "thinking":
      return "💡 OPINANDO"
    case "idea":
      return "💡 TENGO UNA IDEA"
    case "ready":
      return `💡 ${state.opinion?.short ?? "MIRA"}`
    case "error":
      return "💡 NO PUDE"
    default:
      return ""
  }
}

/** Extrae los mensajes de la respuesta de la API, sea cual sea su forma. */
export function messagesFrom(response: any): any[] {
  if (Array.isArray(response)) return response
  if (Array.isArray(response?.messages)) return response.messages
  // Forma real de OpenCode 2.3.2: { data: SessionMessageInfo[], cursor: ... }
  if (Array.isArray(response?.data)) return response.data
  if (Array.isArray(response?.data?.messages)) return response.data.messages
  return []
}
