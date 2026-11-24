// Memoria de recetas de Bitty: guarda pasos visuales, nunca credenciales.
// La validación es la misma que en bitty/recipes.py (Puente Python).

export const RECIPE_HOSTS = ["mail.google.com", "accounts.google.com"] as const
export const RECIPE_KINDS = ["open", "navigate", "look", "click", "verify"] as const

export type RecipeKind = typeof RECIPE_KINDS[number]

export interface RecipeStep {
  kind: RecipeKind
  hint?: string
}

export interface Recipe {
  id: string
  label: string
  account?: string
  url?: string
  steps: RecipeStep[]
}

const FORBIDDEN_WORDS = [
  "password", "passwd", "contraseña", "contrasena",
  "token", "clave", "secret", "credencial", "pin",
]
const ID_RE = /^[a-z0-9][a-z0-9_-]{0,63}$/
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/
const ALLOWED_KEYS = ["id", "label", "account", "url", "steps"]

function forbidden(text: string): boolean {
  const lower = text.toLowerCase()
  return text.includes("@") || FORBIDDEN_WORDS.some((word) => lower.includes(word))
}

export function validateUrl(raw: unknown): string | undefined {
  if (raw === undefined || raw === null) return undefined
  if (typeof raw !== "string" || raw.length < 1 || raw.length > 300) {
    throw new Error("URL no válida")
  }
  let url: URL
  try {
    url = new URL(raw)
  } catch {
    throw new Error("URL no válida")
  }
  if (url.protocol !== "https:" || url.username || url.password) {
    throw new Error("solo HTTPS sin credenciales")
  }
  if (!(RECIPE_HOSTS as readonly string[]).includes(url.hostname.toLowerCase())) {
    throw new Error("dominio no permitido")
  }
  if (url.port && url.port !== "443") {
    throw new Error("puerto no permitido")
  }
  return raw
}

function validateStep(raw: unknown): RecipeStep {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error("paso no válido")
  }
  const step = raw as Record<string, unknown>
  const extra = Object.keys(step).filter((key) => key !== "kind" && key !== "hint")
  if (extra.length) throw new Error("clave no permitida en el paso")
  if (typeof step.kind !== "string" || !(RECIPE_KINDS as readonly string[]).includes(step.kind)) {
    throw new Error("tipo de paso no permitido")
  }
  let hint: string | undefined
  if (step.hint !== undefined) {
    if (typeof step.hint !== "string" || step.hint.length < 1 || step.hint.length > 60) {
      throw new Error("pista no válida")
    }
    if (forbidden(step.hint)) throw new Error("la pista no puede contener credenciales")
    hint = step.hint
  }
  return { kind: step.kind as RecipeKind, ...(hint ? { hint } : {}) }
}

export function validateRecipe(raw: unknown): Recipe {
  if (!raw || typeof raw !== "object" || Array.isArray(raw)) {
    throw new Error("la receta debe ser un objeto")
  }
  const data = raw as Record<string, unknown>
  const extra = Object.keys(data).filter((key) => !ALLOWED_KEYS.includes(key))
  if (extra.length) throw new Error("clave no permitida: " + extra.join(","))

  const id = data.id
  if (typeof id !== "string" || !ID_RE.test(id)) throw new Error("id no válido")

  const label = data.label
  if (
    typeof label !== "string" || label.length < 1 || label.length > 60
    || label.includes("@")
  ) {
    throw new Error("etiqueta no válida")
  }

  let account: string | undefined
  if (data.account !== undefined) {
    if (
      typeof data.account !== "string" || data.account.length > 120
      || !EMAIL_RE.test(data.account)
    ) {
      throw new Error("cuenta no válida")
    }
    account = data.account
  }

  const url = validateUrl(data.url)
  const rawSteps = data.steps
  if (!Array.isArray(rawSteps) || rawSteps.length < 1 || rawSteps.length > 12) {
    throw new Error("la receta necesita entre 1 y 12 pasos")
  }
  const steps = rawSteps.map(validateStep)

  return {
    id,
    label,
    ...(account ? { account } : {}),
    ...(url ? { url } : {}),
    steps,
  }
}

export function describeRecipe(recipe: Recipe): string {
  const header = `> RECETA ${recipe.label} [${recipe.id}]`
  const lines = [
    header,
    recipe.account ? `  Cuenta: ${recipe.account}` : "",
    recipe.url ? `  Web: ${recipe.url}` : "",
    ...recipe.steps.map((step, index) => {
      const hint = step.hint ? ` (${step.hint})` : ""
      return `  ${index + 1}. ${step.kind}${hint}`
    }),
    "  Bitty no escribe contraseñas: si hay login, lo haces tú en Brave.",
  ]
  return lines.filter(Boolean).join("\n")
}
