/** @jsxImportSource @opentui/solid */
import { Plugin } from "@opencode/plugin/tui"
import { createSignal, For, Show } from "solid-js"
import {
  BITTY_EVENTS,
  FACES,
  moodForEvent,
  moodFromVerdict,
  type Mood,
} from "./shared/faces"
import {
  EMPTY_OPINION,
  buildOpinionPrompt,
  messagesFrom,
  opinionBadge,
  opinionSourceLabel,
  pushHistory,
  type Opinion,
  type OpinionEntry,
  type OpinionState,
} from "./shared/opinion"
import { localOpinion, opinionFromModel } from "./shared/opina"
import { CAPACITIES } from "./shared/capacities"
import { browserHint } from "./shared/hint"
import { scanProject } from "./shared/scan"
import { BittyRpc } from "./shared/rpc"

/** Cuando la sesión se asienta, Bitty suelta su sugerencia sin que se le pida. */
const SETTLED_EVENTS = new Set([
  "session.idle",
  "session.execution.succeeded",
  "session.execution.failed",
  "session.execution.interrupted",
  "session.step.ended",
  "session.step.failed",
  "session.text.ended",
  "session.tool.success",
  "session.tool.failed",
])

export default Plugin.define({
  id: "bitty.tui",
  setup(context) {
    const [mood, setMood] = createSignal<Mood>("idle")
    const [opinion, setOpinion] = createSignal<OpinionState>(EMPTY_OPINION)
    const [history, setHistory] = createSignal<OpinionEntry[]>([])
    const [note, setNote] = createSignal("")
    const face = () => FACES[mood()]

    const signals: string[] = []
    let sessionID: string | undefined
    let timer: ReturnType<typeof setTimeout> | undefined
    let working = false

    const show = (value: Opinion) => {
      setOpinion({ status: "ready", opinion: value })
      setHistory((previous) => pushHistory(previous, value))
      setMood(moodFromVerdict(value.verdict))
    }

    /** Fase 3: echar un vistazo a las sesiones recientes del proyecto. */
    const viewAll = async () => {
      try {
        const scan = await scanProject(context.client, {
          directory: context.location?.directory,
          limit: 6,
          perSession: 6,
        })
        const titles = scan.sessions.map((session) => `· ${session.title}`).join("\n")
        setNote(
          `He mirado ${scan.sessions.length} sesiones del proyecto:\n${titles || "· (sin sesiones)"}\nSolo leo un resumen; no copio nada.`,
        )
        setMood("done")
      } catch {
        setNote("No he podido leer las sesiones del proyecto ahora mismo.")
        setMood("error")
      }
    }

    const browserAvailable = async () => {
      try {
        const list: any = await context.client.mcp.list(
          context.location?.directory ? { location: { directory: context.location.directory } } : undefined,
        )
        const servers: any[] = Array.isArray(list?.data) ? list.data : []
        return servers.some((server: any) => server?.name === CAPACITIES.navegador.mcpName)
      } catch {
        return false
      }
    }

    /** Fase 4: pedir permiso nativo e instalar una capacidad del catálogo cerrado. */
    const installBrowser = async () => {
      if (!sessionID) {
        setNote("Abre una sesión para poder pedir el permiso.")
        return
      }
      try {
        const result: any = await context.client.rpc(BittyRpc).install({
          capacity: "navegador",
          sessionID,
          ...(context.location?.directory ? { directory: context.location.directory } : {}),
        })
        setNote(result.message)
        setMood(result.ok ? "done" : "error")
      } catch {
        setNote("No se pudo completar la instalación. Revisa el diálogo de permisos.")
        setMood("error")
      }
    }

    /**
     * Opinión en dos niveles: la heurística local aparece al instante y el modelo
     * solo la afina si hay cuota. Nunca se escribe en la sesión de Marcelbon.
     */
    const refresh = async (allowModel: boolean) => {
      if (working) return
      working = true
      setOpinion({ status: "thinking" })
      setMood("opinando")

      const recentSignals = signals.slice()
      let messages: any[] = []
      try {
        if (sessionID) {
          messages = messagesFrom(await context.client.message.list({ sessionID }))
        }
      } catch {
        messages = []
      }

      const fallback = localOpinion({ messages, signals: recentSignals })
      show(fallback)

      // Aviso contextual: si el MCP ya está, ofrezco mirar la web; si no, explico cómo instalarlo.
      const userText = messages.map((m: any) => String(m?.text ?? "")).join(" ")
      if (browserHint(userText, false)) {
        const available = await browserAvailable()
        setNote(browserHint(userText, available))
      }

      if (allowModel) {
        try {
          const result: any = await context.client.experimental.generate.text({
            prompt: buildOpinionPrompt(messages),
          })
          show(opinionFromModel(result?.text ?? "", fallback))
        } catch {
          // Sin modelo seguimos teniendo la sugerencia local: Bitty no se calla.
        }
      }

      working = false
    }

    const react = (type: string) => {
      signals.push(type)
      if (signals.length > 40) signals.shift()

      if (type === "session.created") {
        signals.length = 0
        setOpinion(EMPTY_OPINION)
        setHistory([])
        setNote("")
        setMood("idle")
        return
      }

      const next = moodForEvent(type)
      if (next) {
        if (timer) clearTimeout(timer)
        setMood(next.mood)
        if (next.hold > 0) {
          timer = setTimeout(() => setMood("idle"), next.hold)
        }
      }

      const status = opinion().status
      if (SETTLED_EVENTS.has(type) && status !== "thinking" && status !== "ready") {
        void refresh(false)
      }
    }

    const data = context.data as any
    const stops = BITTY_EVENTS.map((type) => data.on(type, () => react(type)))

    // Paleta, /bitty y /bitty-opina, además de los atajos.
    context.keymap.layer(() => ({
      mode: "global" as const,
      commands: [
        {
          id: "bitty.panel",
          title: "Bitty: abrir mascota",
          group: "Bitty",
          bind: "ctrl+alt+b",
          palette: true,
          slash: { name: "bitty" },
          suggested: true,
          run: () => {
            context.ui.panel.open("bitty.mascota")
          },
        },
        {
          id: "bitty.opinar",
          title: "Bitty: opinar (solo sugerencia)",
          group: "Bitty",
          bind: "ctrl+alt+o",
          palette: true,
          slash: { name: "bitty-opina" },
          suggested: true,
          run: () => {
            void refresh(true)
          },
        },
        {
          id: "bitty.ver",
          title: "Bitty: ver sesiones del proyecto",
          group: "Bitty",
          bind: "ctrl+alt+v",
          palette: true,
          slash: { name: "bitty-ver" },
          suggested: true,
          run: () => {
            void viewAll()
          },
        },
        {
          id: "bitty.instalar",
          title: "Bitty: instalar ver el navegador (con permiso)",
          group: "Bitty",
          bind: "ctrl+alt+i",
          palette: true,
          slash: { name: "bitty-instalar" },
          suggested: true,
          run: () => {
            void installBrowser()
          },
        },
      ],
    }))

    // Bitty siempre visible, también en la pantalla de inicio.
    const unregisterHome = context.ui.slot({
      append: "home.footer.status",
      render: () => <text fg={context.theme.text.base}>{` Bitty ${face().mini} ${face().short}`}</text>,
    })

    const unregisterStatus = context.ui.slot({
      append: "prompt.footer.status",
      render: (input) => {
        if (input.sessionID) sessionID = input.sessionID
        const badge = opinionBadge(opinion())
        return (
          <text fg={context.theme.text.base}>
            {badge ? ` Bitty ${badge}` : ` Bitty ${face().mini} ${face().short}`}
          </text>
        )
      },
    })

    const unregisterPanel = context.ui.slot({
      append: "session.panel",
      render: (panel) => (
        <Show when={panel.name === "bitty.mascota"}>
          <box flexDirection="column" padding={1}>
            <text fg={context.theme.text.base}>{face().art}</text>
            <text fg={context.theme.text.base}>{`Bitty · ${face().label}`}</text>
            <Show when={opinion().status === "ready" && opinion().opinion}>
              <text fg={context.theme.text.base}>{" Sugerencia de Bitty (no modifica tu sesión)"}</text>
              <text fg={context.theme.text.base}>{` Motor: ${opinionSourceLabel(opinion().opinion?.source)}`}</text>
              <text fg={context.theme.text.base}>{opinion().opinion?.label}</text>
            </Show>
            <Show when={history().length > 1}>
              <text fg={context.theme.text.base}>{" Historial (últimas 5)"}</text>
              <For each={history()}>
                {(entry) => (
                  <text fg={context.theme.text.base}>
                    {`  ${entry.at} · ${entry.opinion.short} · ${opinionSourceLabel(entry.opinion.source)}`}
                  </text>
                )}
              </For>
            </Show>
            <Show when={opinion().status === "thinking"}>
              <text fg={context.theme.text.base}>{"Mirando la sesión…"}</text>
            </Show>
            <Show when={opinion().status === "idea"}>
              <text fg={context.theme.text.base}>{"Tengo una idea. Usa /bitty-opina para escucharla."}</text>
            </Show>
            <Show when={note().length > 0}>
              <text fg={context.theme.text.base}>{note()}</text>
            </Show>
            <text fg={context.theme.text.base}>{"/bitty-ver mira sesiones · /bitty-instalar pide permiso · Ctrl+Alt+B cierra"}</text>
          </box>
        </Show>
      ),
    })

    return () => {
      stops.forEach((stop) => stop())
      unregisterHome()
      unregisterStatus()
      unregisterPanel()
      if (timer) clearTimeout(timer)
    }
  },
})
