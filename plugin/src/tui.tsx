/** @jsxImportSource @opentui/solid */
import { Plugin } from "@opencode/plugin/tui"
import { createSignal, Show } from "solid-js"
import { BITTY_EVENTS, FACES, moodForEvent, type Mood } from "./shared/faces"

export default Plugin.define({
  id: "bitty.tui",
  setup(context) {
    const [mood, setMood] = createSignal<Mood>("idle")
    const face = () => FACES[mood()]

    let timer: ReturnType<typeof setTimeout> | undefined
    const react = (type: string) => {
      const next = moodForEvent(type)
      if (!next) return
      if (timer) clearTimeout(timer)
      setMood(next.mood)
      if (next.hold > 0) {
        timer = setTimeout(() => setMood("idle"), next.hold)
      }
    }

    // Escuchamos los eventos del servidor conectado, igual que la app de escritorio.
    const data = context.data as any
    const stops = BITTY_EVENTS.map((type) => data.on(type, () => react(type)))

    // Comando global: abre el panel de Bitty desde la paleta, con /bitty o con Ctrl+Alt+B.
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
      ],
    }))

    // Bitty siempre visible, también en la pantalla de inicio.
    const unregisterHome = context.ui.slot({
      append: "home.footer.status",
      render: () => <text fg={context.theme.text.base}>{` Bitty ${face().mini} ${face().short}`}</text>,
    })

    const unregisterStatus = context.ui.slot({
      append: "prompt.footer.status",
      render: () => <text fg={context.theme.text.base}>{` Bitty ${face().mini} ${face().short}`}</text>,
    })

    // Panel lateral con la cara grande.
    const unregisterPanel = context.ui.slot({
      append: "session.panel",
      render: (panel) => (
        <Show when={panel.name === "bitty.mascota"}>
          <box flexDirection="column" padding={1}>
            <text fg={context.theme.text.base}>{face().art}</text>
            <text fg={context.theme.text.base}>{`Bitty · ${face().label}`}</text>
            <text fg={context.theme.text.base}>{"Ctrl+Alt+B para cerrar"}</text>
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
