// Punto de entrada del RPC de instalación, separado del SDK para poder probarlo
// de extremo a extremo sin servidor: validar -> pedir permiso -> instalar.

import { CAPACITIES, type CapacityId } from "./capacities"
import { installCapacity } from "./install"
import { safeAgent, safeDirectory, safeSessionId } from "./validate"

export interface InstallInput {
  capacity: string
  sessionID: string
  directory?: string
  agent?: string
}

export interface InstallReply {
  ok: boolean
  title: string
  message: string
  denied: boolean
}

function capacityId(value: unknown): CapacityId | undefined {
  if (typeof value !== "string") return undefined
  return Object.prototype.hasOwnProperty.call(CAPACITIES, value) ? (value as CapacityId) : undefined
}

function reject(message: string): InstallReply {
  return { ok: false, title: "Bitty", message, denied: false }
}

/** Devuelve siempre un resultado: ningún dato de la UI llega sin validar. */
export async function installFromRpc(ctx: any, raw: unknown): Promise<InstallReply> {
  const input = (raw ?? {}) as InstallInput
  const id = capacityId(input.capacity)
  if (!id) return reject("Capacidad desconocida: no he instalado nada.")

  const sessionID = safeSessionId(input.sessionID)
  if (!sessionID) return reject("Sesión no válida: no he instalado nada.")

  const result = await installCapacity(ctx, id, {
    sessionID,
    directory: safeDirectory(input.directory),
    agent: safeAgent(input.agent) || undefined,
  })
  return {
    ok: result.ok,
    title: result.capacity.title,
    message: result.message,
    denied: result.denied,
  }
}
