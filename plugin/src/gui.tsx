import {
  Command,
  ComposerPill,
  MenuItem,
  Panel,
  Plugin,
  Slot,
  createKeyed,
} from "@opencode/plugin/gui"
import { createSignal, onCleanup } from "solid-js"
import { BITTY_EVENTS, FACES, moodForEvent, type Mood } from "./shared/faces"

const [mood, setMood] = createSignal<Mood>("idle")

let timer: ReturnType<typeof setTimeout> | undefined
function react(type: string) {
  const next = moodForEvent(type)
  if (!next) return
  if (timer) clearTimeout(timer)
  setMood(next.mood)
  if (next.hold > 0) {
    timer = setTimeout(() => setMood("idle"), next.hold)
  }
}

function BittyPanel() {
  const face = () => FACES[mood()]
  return (
    <div
      style={{
        display: "flex",
        "flex-direction": "column",
        gap: "12px",
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
      <div style={{ "font-size": "11px", opacity: "0.6" }}>Soy Bitty, tu mascota de OpenCode</div>
    </div>
  )
}

export default Plugin.define({
  i18n: {
    en: {
      title: "Bitty",
      "command.open": "Open Bitty mascot",
      "command.group": "Bitty",
      "panel.title": "Bitty",
      "pill.title": "Bitty, your OpenCode mascot",
      "pill.open": "Open Bitty panel",
    },
    es: {
      title: "Bitty",
      "command.open": "Abrir mascota Bitty",
      "command.group": "Bitty",
      "panel.title": "Bitty",
      "pill.title": "Bitty, tu mascota de OpenCode",
      "pill.open": "Abrir panel de Bitty",
    },
  },
  setup(ctx) {
    // Reaccionamos a los eventos del servidor propio de la app de escritorio.
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

    // Panel lateral con la mascota viva.
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

    // Comando en la paleta, en /bitty y atajo mod+alt+b.
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

    // Entrada en el menú "+" del panel lateral.
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

    // Píldora junto al composer: la cara cambia con el estado de la sesión.
    ctx.add(ComposerPill, {
      id: "bitty",
      show: (input) => ({
        label: `Bitty ${FACES[mood()].mini}`,
        icon: "terminal",
        title: ctx.t("pill.title"),
        rows: [
          {
            id: "open",
            label: ctx.t("pill.open"),
            run: () => ctx.layout.open(key(), input.session),
          },
        ],
      }),
    })

    // Presencia discreta en la barra inferior de la ventana.
    ctx.add(Slot, {
      at: "window.bottom",
      render: () => <span>{`Bitty · ${FACES[mood()].label}`}</span>,
    })
  },
})
