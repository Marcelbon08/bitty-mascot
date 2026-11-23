import {
  Command,
  ComposerPill,
  MenuItem,
  Panel,
  Plugin,
  Slot,
  createKeyed,
} from "@opencode/plugin/gui"
import { createSignal, For, onCleanup, Show } from "solid-js"
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
const [history, setHistory] = createSignal<OpinionEntry[]>([])
const [note, setNote] = createSignal("")
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
      "opinion.motor": "Engine",
      "opinion.history": "History (last 5)",
      "command.view": "Bitty: view project sessions",
      "command.install": "Bitty: install browser view (asks permission)",
      "pill.view": "View recent sessions",
      "pill.install": "Install browser view",
      "panel.view": "View sessions",
      "panel.install": "Install browser view",
      "panel.footer": "/bitty-ver · /bitty-instalar · Mod+Alt+B closes",
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
      "opinion.motor": "Motor",
      "opinion.history": "Historial (últimas 5)",
      "command.view": "Bitty: ver sesiones del proyecto",
      "command.install": "Bitty: instalar ver el navegador (pide permiso)",
      "pill.view": "Ver sesiones recientes",
      "pill.install": "Instalar ver el navegador",
      "panel.view": "Ver sesiones",
      "panel.install": "Instalar ver el navegador",
      "panel.footer": "/bitty-ver · /bitty-instalar · Mod+Alt+B cierra",
    },
  },
  setup(ctx) {
    let working = false

    const show = (value: Opinion) => {
      setOpinion({ status: "ready", opinion: value })
      setHistory((previous) => pushHistory(previous, value))
      setMood(moodFromVerdict(value.verdict))
    }

    /** Fase 3: resumen acotado de las sesiones recientes del proyecto. */
    const viewAll = async () => {
      const session = ctx.sessions.current()
      if (!session) {
        setNote("Abre una sesión para poder mirar el proyecto.")
        return
      }
      try {
        const scan = await scanProject(session.server.client, {
          directory: session.location?.directory,
          limit: 6,
          perSession: 6,
        })
        const titles = scan.sessions.map((item) => `· ${item.title}`).join("\n")
        setNote(`He mirado ${scan.sessions.length} sesiones del proyecto:\n${titles || "· (sin sesiones)"}\nSolo leo un resumen; no copio nada.`)
        setMood("done")
      } catch {
        setNote("No he podido leer las sesiones del proyecto ahora mismo.")
        setMood("error")
      }
    }

    /** Fase 4: permiso nativo e instalación del MCP del catálogo cerrado. */
    const installBrowser = async (session: { id: string; location?: { directory: string } } | undefined) => {
      if (!session) {
        setNote("Abre una sesión para poder pedir el permiso.")
        return
      }
      try {
        const result: any = await ctx.client.rpc(BittyRpc).install({
          capacity: "navegador",
          sessionID: session.id,
          ...(session.location?.directory ? { directory: session.location.directory } : {}),
        })
        setNote(result.message)
        setMood(result.ok ? "done" : "error")
      } catch {
        setNote("No se pudo completar la instalación. Revisa el diálogo de permisos.")
        setMood("error")
      }
    }

    const browserAvailable = async (session: { location?: { directory: string } } | undefined) => {
      try {
        const list: any = await ctx.client.mcp.list(
          session?.location?.directory ? { location: { directory: session.location.directory } } : undefined,
        )
        const servers: any[] = Array.isArray(list?.data) ? list.data : []
        return servers.some((server: any) => server?.name === CAPACITIES.navegador.mcpName)
      } catch {
        return false
      }
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

      const userText = messages.map((m: any) => String(m?.text ?? "")).join(" ")
      if (browserHint(userText, false)) {
        const available = await browserAvailable(ctx.sessions.current())
        setNote(browserHint(userText, available))
      }

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
          <div style={{ display: "flex", gap: "6px", "flex-wrap": "wrap", "justify-content": "center" }}>
            <button
              style={{ cursor: "pointer", padding: "4px 10px", "font-family": "inherit" }}
              disabled={opinion().status === "thinking"}
              onClick={() => void refresh(true)}
            >
              {ctx.t("opinion.ask")}
            </button>
            <button
              style={{ cursor: "pointer", padding: "4px 10px", "font-family": "inherit" }}
              onClick={() => void viewAll()}
            >
              {ctx.t("panel.view")}
            </button>
            <button
              style={{ cursor: "pointer", padding: "4px 10px", "font-family": "inherit" }}
              onClick={() => void installBrowser(ctx.sessions.current())}
            >
              {ctx.t("panel.install")}
            </button>
          </div>
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
              <div style={{ opacity: "0.7", "margin-bottom": "4px" }}>
                {ctx.t("opinion.motor")}: {opinionSourceLabel(opinion().opinion?.source)}
              </div>
              <div>{opinion().opinion?.label}</div>
            </div>
          </Show>
          <Show when={history().length > 1}>
            <div
              style={{
                width: "100%",
                border: "1px solid var(--border-base, currentColor)",
                padding: "8px",
                "font-size": "11px",
                opacity: "0.8",
              }}
            >
              <div style={{ "margin-bottom": "4px" }}>{ctx.t("opinion.history")}</div>
              <For each={history()}>
                {(entry) => (
                  <div>
                    {entry.at} · {entry.opinion.short} · {opinionSourceLabel(entry.opinion.source)}
                  </div>
                )}
              </For>
            </div>
          </Show>
          <Show when={opinion().status === "thinking"}>
            <div style={{ "font-size": "12px", opacity: "0.8" }}>{ctx.t("opinion.thinking")}</div>
          </Show>
          <Show when={opinion().status === "idea"}>
            <div style={{ "font-size": "12px", opacity: "0.8" }}>{ctx.t("opinion.hint")}</div>
          </Show>
          <Show when={note().length > 0}>
            <div
              style={{
                width: "100%",
                border: "1px solid var(--border-base, currentColor)",
                padding: "8px",
                "font-size": "12px",
                "white-space": "pre-wrap",
              }}
            >
              {note()}
            </div>
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

    ctx.add(Command, (): Command => ({
      id: "ver",
      title: ctx.t("command.view"),
      keywords: "bitty sesiones proyecto ver",
      group: ctx.t("command.group"),
      bind: "mod+alt+v",
      slash: { name: "bitty-ver" },
      featured: true,
      run: () => {
        void viewAll()
      },
    }))

    ctx.add(Command, (): Command => ({
      id: "instalar",
      title: ctx.t("command.install"),
      keywords: "bitty instalar navegador mcp permiso",
      group: ctx.t("command.group"),
      bind: "mod+alt+i",
      slash: { name: "bitty-instalar" },
      featured: true,
      run: () => {
        void installBrowser(ctx.sessions.current())
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
            {
              id: "view",
              label: ctx.t("pill.view"),
              run: () => void viewAll(),
            },
            {
              id: "install",
              label: ctx.t("pill.install"),
              run: () => void installBrowser(input.session),
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
