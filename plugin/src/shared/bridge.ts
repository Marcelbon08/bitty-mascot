// Cliente del puente local de Bitty. Solo habla con 127.0.0.1 y con token.
// Nunca acepta una URL de la configuración: el puerto sale de bridge.json.

import { readFile } from "node:fs/promises"
import { homedir, platform } from "node:os"
import { join } from "node:path"

export interface BridgeConnection {
  port: number
  token: string
  pid: number
}

export interface BridgeCapture {
  path: string
  uri: string
  width: number
  height: number
  screens: number
}

export interface BridgeCursor {
  ok: boolean
  x: number
  y: number
}

export interface BridgeClick extends BridgeCursor {
  click: boolean
}

/** Valida el fichero de conexión antes de usarlo. */
export function validateConnection(value: any): BridgeConnection | null {
  if (!value || typeof value !== "object") return null
  const port = value.port
  const token = value.token
  if (!Number.isInteger(port) || port < 1 || port > 65535) return null
  if (typeof token !== "string" || token.length < 20) return null
  return { port, token, pid: Number.isInteger(value.pid) ? value.pid : 0 }
}

function configDir(): string {
  const base = platform() === "win32"
    ? process.env.APPDATA || join(homedir(), "AppData", "Roaming")
    : process.env.XDG_CONFIG_HOME || join(homedir(), ".config")
  return join(base, "BittyMascot")
}

/** Lee el puerto y el token que Bitty escribió al arrancar. */
export async function readConnection(): Promise<BridgeConnection | null> {
  try {
    const raw = await readFile(join(configDir(), "bridge.json"), "utf8")
    return validateConnection(JSON.parse(raw))
  } catch {
    return null
  }
}

/** URL completa, aislada para poder comprobarla en tests. */
export function bridgeUrl(connection: BridgeConnection, path: "/ping" | "/agreement" | "/cursor" | "/click" | "/capture"): string {
  return `http://127.0.0.1:${connection.port}${path}`
}

/** Llama al puente. Lanza un error claro si Bitty no está o rechaza la petición. */
export async function callBridge<T>(
  path: "/agreement" | "/cursor" | "/click" | "/capture",
  body: Record<string, unknown>,
  signal?: AbortSignal,
): Promise<T> {
  const connection = await readConnection()
  if (!connection) {
    throw new Error("Bitty no está ejecutándose o su puente local está desactivado.")
  }
  const response = await fetch(bridgeUrl(connection, path), {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-bitty-token": connection.token,
    },
    body: JSON.stringify(body),
    signal,
  })
  if (!response.ok) {
    const detail = await response.text().catch(() => "")
    throw new Error(`Bitty devolvió ${response.status}${detail ? `: ${detail.slice(0, 160)}` : ""}`)
  }
  return (await response.json()) as T
}
