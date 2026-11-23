/** @jsxImportSource @opentui/solid */
import { Plugin } from "@opencode/plugin/tui"
import { createSignal, Show } from "solid-js"
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
  type Opinion,
  type OpinionState,
} from "./shared/opinion"
import { localOpinion, opinionFromModel } from "./shared/opina"

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
    const face = () => FACES[mood()]

    const signals: string[] = []
    let sessionID: string | undefined
    let timer: ReturnType<typeof setTimeout> | undefined
    let working = false

    const show = (value: Opinion) => {
      setOpinion({ status: "ready", opinion: value })
      setMood(moodFromVerdict(value.verdict))
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
              <text fg={context.theme.text.base}>{opinion().opinion?.label}</text>
            </Show>
            <Show when={opinion().status === "thinking"}>
              <text fg={context.theme.text.base}>{"Mirando la sesión…"}</text>
            </Show>
            <Show when={opinion().status === "idea"}>
              <text fg={context.theme.text.base}>{"Tengo una idea. Usa /bitty-opina para escucharla."}</text>
            </Show>
            <text fg={context.theme.text.base}>{"/bitty-opina afina la sugerencia · Ctrl+Alt+B cierra"}</text>
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
