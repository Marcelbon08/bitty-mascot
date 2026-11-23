// Caras de Bitty compartidas por la TUI y la app de escritorio.
// Se dibujan con ASCII para que funcionen igual en terminal, macOS, Linux y Windows.

import type { Verdict } from "./opinion"

export type Mood =
  | "idle"
  | "thinking"
  | "working"
  | "writing"
  | "done"
  | "error"
  | "ask"
  | "sleepy"
  | "opinando"
  | "seguir"
  | "revisar"
  | "parar"

export interface Face {
  mini: string
  art: string
  label: string
  /** Texto corto para la barra de estado de la terminal. */
  short: string
}

export const FACES: Record<Mood, Face> = {
  idle: {
    mini: "[o_o]",
    label: "HOLA MARCELBON",
    short: "HI",
    art: " .------. \n| o  o |\n|  --  |\n '------' ",
  },
  thinking: {
    mini: "[o_?]",
    label: "PENSANDO",
    short: "PIENSA",
    art: " .------. \n| o  o |\n|  ~~  |\n '------' ",
  },
  working: {
    mini: "[O_o]",
    label: "TRABAJANDO",
    short: "TOOL",
    art: " .------. \n| O  o |\n|  ==  |\n '------' ",
  },
  writing: {
    mini: "[-_-]>",
    label: "ESCRIBIENDO",
    short: "ESCRIBE",
    art: " .------. \n| -  - |\n|  /\\  |\n '------' ",
  },
  done: {
    mini: "[^_^]",
    label: "LISTO",
    short: "LISTO",
    art: " .------. \n| ^  ^ |\n|  \\/  |\n '------' ",
  },
  error: {
    mini: "[x_x]",
    label: "UPS",
    short: "ERROR",
    art: " .------. \n| x  x |\n|  oo  |\n '------' ",
  },
  ask: {
    mini: "[O_O]",
    label: "PERMISO?",
    short: "PERMISO",
    art: " .------. \n| O  O |\n|  ??  |\n '------' ",
  },
  sleepy: {
    mini: "[-_-]",
    label: "DESPIERTA?",
    short: "ZZZ",
    art: " .------. \n| -  - |\n|  __  |\n '------' ",
  },
  opinando: {
    mini: "[?_?]",
    label: "OPINANDO",
    short: "OPINA",
    art: " .------. \n| ?  ? |\n|  ..  |\n '------' ",
  },
  seguir: {
    mini: "[^_^]",
    label: "SIGUE, MARCELBON",
    short: "SIGUE",
    art: " .------. \n| ^  ^ |\n|  \\/  |\n '------' ",
  },
  revisar: {
    mini: "[o_O]",
    label: "REVISA ESTO",
    short: "REVISA",
    art: " .------. \n| o  O |\n|  ~~  |\n '------' ",
  },
  parar: {
    mini: "[>_<]",
    label: "MEJOR PARAR",
    short: "PARA",
    art: " .------. \n| >  < |\n|  __  |\n '------' ",
  },
}

export interface Reaction {
  mood: Mood
  /** Milisegundos que se mantiene la cara. 0 = hasta otro evento. */
  hold: number
}

/** Traduce un evento de OpenCode a una cara de Bitty. */
export function moodForEvent(type: string): Reaction | undefined {
  switch (type) {
    case "session.created":
    case "permission.replied":
    case "session.idle":
      return { mood: "idle", hold: 0 }

    case "session.execution.started":
    case "session.step.started":
    case "session.compaction.started":
      return { mood: "thinking", hold: 8000 }

    case "session.step.first-token":
    case "session.text.started":
    case "session.text.delta":
    case "session.reasoning.started":
      return { mood: "writing", hold: 6000 }

    case "session.tool.called":
    case "session.tool.input.started":
    case "session.tool.progress":
    case "session.shell.started":
      return { mood: "working", hold: 6000 }

    case "session.tool.success":
    case "session.text.ended":
    case "session.step.ended":
    case "session.execution.succeeded":
      return { mood: "done", hold: 5000 }

    case "session.tool.failed":
    case "session.step.failed":
    case "session.execution.failed":
    case "session.retry.scheduled":
    case "session.compaction.failed":
      return { mood: "error", hold: 6000 }

    case "permission.asked":
    case "form.created":
      return { mood: "ask", hold: 0 }

    case "session.execution.interrupted":
      return { mood: "sleepy", hold: 4000 }

    default:
      return undefined
  }
}

/** Cara que corresponde al veredicto de una opinión. */
export function moodFromVerdict(verdict: Verdict): Mood {
  if (verdict === "seguir") return "seguir"
  if (verdict === "parar") return "parar"
  return "revisar"
}

/** Eventos que Bitty escucha. Se usan en TUI y en Desktop. */
export const BITTY_EVENTS = [
  "session.created",
  "session.idle",
  "session.execution.started",
  "session.execution.succeeded",
  "session.execution.failed",
  "session.execution.interrupted",
  "session.step.started",
  "session.step.first-token",
  "session.step.ended",
  "session.step.failed",
  "session.text.started",
  "session.text.delta",
  "session.text.ended",
  "session.tool.called",
  "session.tool.input.started",
  "session.tool.progress",
  "session.tool.success",
  "session.tool.failed",
  "session.shell.started",
  "session.compaction.started",
  "session.compaction.failed",
  "session.retry.scheduled",
  "permission.asked",
  "permission.replied",
  "form.created",
] as const
