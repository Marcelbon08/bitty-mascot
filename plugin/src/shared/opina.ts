// Motor de la opinión de Bitty. Funciona en dos niveles:
//   1) heurística local: siempre disponible, sin coste y sin red;
//   2) modelo: si hay cuota, se pide una sugerencia más natural y se parsea.
// En ambos casos es SOLO una sugerencia: nunca escribe en la sesión de Marcelbon.

import { parseOpinion, type Opinion } from "./opinion"

export interface OpinionRequest {
  messages: readonly any[]
  /** Eventos recientes de la sesión: herramientas fallidas, reintentos, permisos… */
  signals?: readonly string[]
}

const SIGNAL_LIMIT = 24

/** Convierte señales técnicas en pistas legibles para la heurística. */
function describe(signals: readonly string[]): string[] {
  const out: string[] = []
  for (const raw of signals.slice(-SIGNAL_LIMIT)) {
    const s = String(raw)
    if (/error|fail|failed|denied|reject/i.test(s)) out.push("ha habido fallos o rechazos")
    else if (/retry|compaction|compact/i.test(s)) out.push("la sesión ha necesitado reintentos o compactación")
    else if (/permission|form\.created/i.test(s)) out.push("OpenCode ha pedido permiso o información")
    else if (/tool|shell|bash|write|edit/i.test(s)) out.push("se están usando herramientas")
    else if (/text\.|step\.|execution\./i.test(s)) out.push("la sesión está avanzando")
  }
  return [...new Set(out)]
}

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

/** Opinión determinista, útil también cuando el modelo no está disponible. */
export function localOpinion(request: OpinionRequest): Opinion {
  const messages = request.messages.slice(-14)
  const hints = describe(request.signals ?? [])
  const userText = messages
    .map((m: any) => (m?.info?.role === "user" || m?.role === "user" || m?.type === "user" ? textOf(m) : ""))
    .filter(Boolean)
    .join(" ")
    .toLowerCase()

  const hasErrors = hints.some((h) => /fallos|rechazos|reintentos/.test(h))
  const longSession = messages.length >= 12
  const mentionsBug = /bug|error|fallo|roto|arregl|fix|debug/.test(userText)
  const mentionsTest = /prob|test|verif|comprob/.test(userText)
  const mentionsDocs = /readme|document|doc|changelog/.test(userText)
  const giveUp = /no sirve|no merece|abandonar|descartar|detener|mejor parar/.test(userText)

  let verdict: Opinion["verdict"] = "seguir"
  let reason = "El rumbo es claro y la sesión avanza con normalidad."
  let next = "Da el siguiente paso y compruébalo al terminar."
  let short = verdict === "seguir" ? "SIGUE" : verdict === "parar" ? "PARA" : "REVISA"

  if (messages.length === 0 && hints.length === 0) {
    verdict = "revisar"
    reason = "Todavía no veo mensajes en esta sesión, así que hablo desde la prudencia."
    next = "Cuéntame qué estás haciendo y te digo algo más concreto."
    short = "MIRA"
  } else if (giveUp) {
    verdict = "parar"
    reason = "Lo que veo no parece merecer más esfuerzo ahora mismo."
    next = "Guárdalo, descansa un momento y vuelve con otro enfoque."
  } else if (hasErrors) {
    verdict = "revisar"
    reason = "Han aparecido fallos o rechazos; conviene mirarlos antes de seguir."
    next = "Aísla el último fallo y corrígelo antes de ampliar el alcance."
  } else if (mentionsBug && !mentionsTest) {
    verdict = "revisar"
    reason = "Estás arreglando algo, pero todavía no veo una comprobación clara."
    next = "Añade una prueba o una verificación pequeña antes de cerrar el bug."
  } else if (longSession) {
    verdict = "revisar"
    reason = "La sesión es larga; merece un repaso antes de seguir acumulando cambios."
    next = "Resume qué está hecho y qué queda, y continua por lo más importante."
  } else if (mentionsDocs) {
    reason = "Tienes el trabajo encaminado y ahora toca dejarlo documentado."
    next = "Actualiza README y changelog, y cierra con una versión clara."
  }

  // El resumen debe seguir al veredicto final, no al inicial.
  if (!(messages.length === 0 && hints.length === 0)) {
    short = verdict === "seguir" ? "SIGUE" : verdict === "parar" ? "PARA" : "REVISA"
  }

  return {
    verdict,
    reason,
    next,
    short,
    label: `Veredicto: ${short}\nRazón: ${reason}\nSiguiente: ${next}`,
  }
}

/** Combina la heurística con el modelo: si el modelo falla, la heurística responde igual. */
export function opinionFromModel(text: string, fallback: Opinion): Opinion {
  try {
    const parsed = parseOpinion(text)
    // Si el modelo no respetó el formato, conservamos la heurística.
    if (!/Veredicto\s*:/i.test(text)) return fallback
    return parsed
  } catch {
    return fallback
  }
}
