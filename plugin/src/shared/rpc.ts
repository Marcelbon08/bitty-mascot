// Contrato RPC compartido entre el plugin servidor, la TUI y Desktop.
// La TUI y Desktop no tienen permission.assert: lo piden aquí, donde sí existe.

import type { JsonSchema } from "effect"
import { Rpc } from "@opencode/schema/rpc"

// Esquemas JSON portables: funcionan igual en servidor, TUI y Desktop.
const InstallInput = {
  type: "object",
  properties: {
    capacity: { type: "string" },
    sessionID: { type: "string" },
    directory: { type: "string" },
    agent: { type: "string" },
  },
  required: ["capacity", "sessionID"],
} as JsonSchema.JsonSchema

const InstallOutput = {
  type: "object",
  properties: {
    ok: { type: "boolean" },
    title: { type: "string" },
    message: { type: "string" },
    denied: { type: "boolean" },
  },
  required: ["ok", "title", "message", "denied"],
} as JsonSchema.JsonSchema

export const BittyRpc = Rpc.define({
  id: "bitty",
  methods: {
    install: { input: InstallInput, output: InstallOutput },
  },
  events: {},
})
