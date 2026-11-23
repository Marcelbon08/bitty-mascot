import {
  Command,
  ComposerPill,
  MenuItem,
  Panel,
  Plugin,
  Slot,
  createKeyed,
} from "@opencode/plugin/gui"
import { createSignal, onCleanup, Show } from "solid-js"
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

const [mood, setMood] = createSignal<Mood>("idle")
const [opinion, setOpinion] = createSignal<OpinionState>(EMPTY_OPINION)
const signals: string[] = []

let timer: ReturnType<typeof setTimeout> | undefined

export default Plugin.define({
  i18n: {
    en: {
      title: "Bitty",
      "command.open": "Open Bitty mascot",
      "command.opine": "Bitty: give an opinion (suggestion only)",
      "command.group": "Bitty",
      "panel.title": "Bitty",
      "pill.title": "Bitty, your OpenCode mascot",
      "pill.open": "Open Bitty panel",
      "pill.opine": "Ask Bitty for an opinion",
      "opinion.ask": "Ask Bitty",
      "opinion.title": "Bitty's suggestion (does not change your session)",
      "opinion.hint": "I have an idea. Ask me and I'll tell you briefly.",
      "opinion.thinking": "Looking at the session…",
      "panel.footer": "/bitty-opina refines it · Mod+Alt+B closes",
    },
    es: {
      title: "Bitty",
      "command.open": "Abrir mascota Bitty",
      "command.opine": "Bitty: opinar (solo sugerencia)",
      "command.group": "Bitty",
      "panel.title": "Bitty",
      "pill.title": "Bitty, tu mascota de OpenCode",
      "pill.open": "Abrir panel de Bitty",
      "pill.opine": "Pedir una opinión a Bitty",
      "opinion.ask": "Pedir opinión",
      "opinion.title": "Sugerencia de Bitty (no modifica tu sesión)",
      "opinion.hint": "Tengo una idea. Pídemela y te la digo en corto.",
      "opinion.thinking": "Mirando la sesión…",
      "panel.footer": "/bitty-opina afina la sugerencia · Mod+Alt+B cierra",
    },
  },
  setup(ctx) {
    let working = false

    const show = (value: Opinion) => {
      setOpinion({ status: "ready", opinion: value })
      setMood(moodFromVerdict(value.verdict))
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

    /** Heurística al instante; el modelo solo afina si hay cuota. Nunca escribe en la sesión. */
    const refresh = async (allowModel: boolean, sessionID?: string) => {
      if (working) return
      working = true
      setOpinion({ status: "thinking" })
      setMood("opinando")

      const id = sessionID ?? ctx.sessions.current()?.id
      const recentSignals = signals.slice()
      let messages: any[] = []
      try {
        if (id) messages = messagesFrom(await ctx.client.message.list({ sessionID: id }))
      } catch {
        messages = []
      }

      const fallback = localOpinion({ messages, signals: recentSignals })
      show(fallback)

      if (allowModel) {
        try {
          const result: any = await ctx.client.experimental.generate.text({
            prompt: buildOpinionPrompt(messages),
          })
          show(opinionFromModel(result?.text ?? "", fallback))
        } catch {
          // Sin modelo la sugerencia local sigue en pie.
        }
      }

      working = false
    }

    createKeyed(
      () => ctx.servers.get("sidecar")?.data,
      (data) => {
        const serverData = data as any
        const stops = BITTY_EVENTS.map((type) => serverData.on(type, () => react(type)))
        return onCleanup(() => {
          stops.forEach((stop) => stop())
          if (timer) clearTimeout(timer)
        })
      },
    )

    const key = () => `${ctx.id}:mascota`

    function BittyPanel() {
      const face = () => FACES[mood()]
      return (
        <div
          style={{
            display: "flex",
            "flex-direction": "column",
            gap: "10px",
            padding: "16px",
            "align-items": "center",
          }}
        >
          <pre
            style={{
              margin: "0",
              "font-family": "monospace",
              "font-size": "14px",
              "line-height": "1.1",
            }}
          >
            {face().art}
          </pre>
          <div style={{ "font-size": "12px", opacity: "0.8" }}>{`Bitty · ${face().label}`}</div>
          <button
            style={{
              cursor: "pointer",
              padding: "4px 10px",
              "font-family": "inherit",
            }}
            disabled={opinion().status === "thinking"}
            onClick={() => void refresh(true)}
          >
            {ctx.t("opinion.ask")}
          </button>
          <Show when={opinion().status === "ready" && opinion().opinion}>
            <div
              style={{
                width: "100%",
                border: "1px solid var(--border-base, currentColor)",
                padding: "8px",
                "font-size": "12px",
                "white-space": "pre-wrap",
              }}
            >
              <div style={{ opacity: "0.7", "margin-bottom": "4px" }}>{ctx.t("opinion.title")}</div>
              <div>{opinion().opinion?.label}</div>
            </div>
          </Show>
          <Show when={opinion().status === "thinking"}>
            <div style={{ "font-size": "12px", opacity: "0.8" }}>{ctx.t("opinion.thinking")}</div>
          </Show>
          <Show when={opinion().status === "idea"}>
            <div style={{ "font-size": "12px", opacity: "0.8" }}>{ctx.t("opinion.hint")}</div>
          </Show>
          <div style={{ "font-size": "11px", opacity: "0.6" }}>Soy Bitty, tu mascota de OpenCode</div>
          <div style={{ "font-size": "10px", opacity: "0.5" }}>{ctx.t("panel.footer")}</div>
        </div>
      )
    }

    const tab = {
      id: "mascota",
      get title() {
        return ctx.t("panel.title")
      },
      closable: "compact" as const,
      fallback: true,
    }

    ctx.add(Panel, {
      id: "mascota",
      region: "side",
      width: "narrow",
      mobile: {
        get title() {
          return ctx.t("panel.title")
        },
        order: 45,
        kind: "menu",
        icon: "terminal",
      },
      list: (input) => (input.open.includes("mascota") ? [tab] : []),
      render: () => <BittyPanel />,
    })

    ctx.add(Command, (): Command => ({
      id: "mascota",
      title: ctx.t("command.open"),
      keywords: "bitty mascota",
      group: ctx.t("command.group"),
      bind: "mod+alt+b",
      slash: { name: "bitty" },
      featured: true,
      run: () => {
        const session = ctx.sessions.current()
        if (session) ctx.layout.toggle(key(), session)
      },
    }))

    ctx.add(Command, (): Command => ({
      id: "opinar",
      title: ctx.t("command.opine"),
      keywords: "bitty opinion sugerencia",
      group: ctx.t("command.group"),
      bind: "mod+alt+o",
      slash: { name: "bitty-opina" },
      featured: true,
      run: () => {
        void refresh(true)
      },
    }))

    ctx.add(MenuItem, (): MenuItem => {
      const session = ctx.sessions.current()
      return {
        menu: "session.panel",
        id: "mascota",
        title: ctx.t("panel.title"),
        icon: "terminal",
        keybind: `${ctx.id}.mascota`,
        opened: !!session && ctx.layout.state(key(), session) !== "closed",
        run: () => {
          if (session) ctx.layout.open(key(), session)
        },
      }
    })

    ctx.add(ComposerPill, {
      id: "bitty",
      show: (input) => {
        const badge = opinionBadge(opinion())
        return {
          label: badge ? `Bitty ${badge}` : `Bitty ${FACES[mood()].mini}`,
          icon: "terminal",
          title: ctx.t("pill.title"),
          rows: [
            {
              id: "open",
              label: ctx.t("pill.open"),
              run: () => ctx.layout.open(key(), input.session),
            },
            {
              id: "opine",
              label: ctx.t("pill.opine"),
              run: () => void refresh(true, input.session.id),
            },
          ],
        }
      },
    })

    ctx.add(Slot, {
      at: "window.bottom",
      render: () => {
        const badge = opinionBadge(opinion())
        return <span>{badge ? `Bitty ${badge}` : `Bitty · ${FACES[mood()].label}`}</span>
      },
    })
  },
})
