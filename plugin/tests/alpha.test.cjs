const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")

const build = path.join(__dirname, "..", ".alpha-build")
// El paquete es ESM; marcamos el directorio de compilación como CommonJS.
fs.writeFileSync(path.join(build, "package.json"), '{"type":"commonjs"}\n')
const { CAPACITIES, CAPACITY_IDS, capacityFromText, needsBrowser } = require(path.join(build, "capacities.js"))
const { installCapacity } = require(path.join(build, "install.js"))
const { scanProject, scanToText } = require(path.join(build, "scan.js"))
const { opinionSourceLabel, pushHistory } = require(path.join(build, "opinion.js"))
const { localOpinion, opinionFromModel } = require(path.join(build, "opina.js"))
const { safeSessionId, safeAgent, safeDirectory } = require(path.join(build, "validate.js"))
const {
  forceAsk, INSTALL_ACTION, CURSOR_ACTION, CLICK_ACTION, SCREEN_ACTION,
} = require(path.join(build, "permission.js"))
const { validateConnection, bridgeUrl, readConnection } = require(path.join(build, "bridge.js"))
const { installFromRpc } = require(path.join(build, "handleInstall.js"))
const { browserHint } = require(path.join(build, "hint.js"))

const results = []
function check(name, fn) {
  try {
    fn()
    results.push("PASS " + name)
  } catch (error) {
    results.push("FAIL " + name + " :: " + error.message)
    process.exitCode = 1
  }
}

async function checkAsync(name, fn) {
  try {
    await fn()
    results.push("PASS " + name)
  } catch (error) {
    results.push("FAIL " + name + " :: " + error.message)
    process.exitCode = 1
  }
}

async function main() {
  check("catalogo_cerrado", () => {
    assert.deepEqual(CAPACITY_IDS, ["navegador"])
    assert.equal(Object.keys(CAPACITIES).length, 1)
    assert.deepEqual(CAPACITIES.navegador.config.command, ["npx", "-y", "@playwright/mcp@latest"])
    assert.equal(CAPACITIES.navegador.mcpName, "bitty-navegador")
  })

  check("deteccion_de_navegador", () => {
    assert.equal(capacityFromText("mira esta pagina web"), "navegador")
    assert.equal(capacityFromText("https://ejemplo.com"), "navegador")
    assert.equal(capacityFromText("revisa el build"), undefined)
    assert.equal(needsBrowser("abre chrome"), true)
    assert.equal(needsBrowser(""), false)
    assert.equal(capacityFromText(null), undefined)
  })

  // Permiso rechazado: no se toca la configuración ni se conecta nada.
  let transformCalled = false
  let addCalled = false
  let connectCalled = false
  const deniedCtx = {
    permission: {
      async assert() {
        const error = new Error("denied")
        error.code = "PERMISSION_DENIED"
        throw error
      },
    },
    mcp: { async transform() { transformCalled = true }, async reload() {} },
    client: {
      mcp: {
        async add() { addCalled = true },
        async connect() { connectCalled = true },
      },
    },
  }
  const denied = await installCapacity(deniedCtx, "navegador", { sessionID: "ses_test" })
  check("permiso_rechazado_no_instala", () => {
    assert.equal(denied.ok, false)
    assert.equal(denied.denied, true)
    assert.match(denied.message, /Permiso rechazado/)
    assert.equal(transformCalled, false)
    assert.equal(addCalled, false)
    assert.equal(connectCalled, false)
  })

  // Permiso concedido: solo se usa la configuración del catálogo.
  let written = null
  const allowedCtx = {
    permission: { async assert() {} },
    mcp: {
      async transform(callback) {
        callback({ set(name, config) { written = { name, config } } })
      },
      async reload() {},
    },
  }
  const allowed = await installCapacity(allowedCtx, "navegador", { sessionID: "ses_test" })
  check("permiso_concedido_solo_catalogo", () => {
    assert.equal(allowed.ok, true)
    assert.equal(allowed.denied, false)
    assert.equal(written.name, "bitty-navegador")
    assert.deepEqual(written.config.command, ["npx", "-y", "@playwright/mcp@latest"])
  })

  // El escaneo acota sesiones, mensajes y caracteres.
  const rows = Array.from({ length: 50 }, (_, i) => ({ id: "ses_" + i, title: "Sesión " + i }))
  const client = {
    session: {
      async list() {
        return { data: rows, total: 50 }
      },
    },
    message: {
      async list() {
        return { data: Array.from({ length: 50 }, () => ({ text: "x".repeat(500) })) }
      },
    },
  }
  const scan = await scanProject(client, { limit: 6, perSession: 6 })
  const text = scanToText(scan)
  check("escaneo_acotado", () => {
    assert.equal(scan.sessions.length, 6)
    assert.equal(scan.sessions[0].messages.length, 6)
    assert.ok(scan.truncated)
    assert.ok(text.length <= 4200)
    assert.ok(scan.sessions[0].title.length <= 120)
  })

  check("validacion_rpc", () => {
    assert.equal(safeSessionId("ses_123"), "ses_123")
    for (const bad of ["--auto", "-h", "a b", "x".repeat(200), null, 42]) {
      assert.equal(safeSessionId(bad), "", String(bad))
    }
    assert.equal(safeAgent("bitty"), "bitty")
    assert.equal(safeAgent("../../etc"), "")
    assert.equal(safeDirectory("C:/Users/marce/proyecto"), "C:/Users/marce/proyecto")
    assert.equal(safeDirectory("a\x00b"), undefined)
    assert.equal(safeDirectory("x".repeat(1000)).length, 512)
  })

  check("motor_opinion_transparente", () => {
    const fallback = localOpinion({ messages: [{ text: "hola" }] })
    assert.equal(fallback.source, "local")
    assert.equal(opinionSourceLabel(fallback.source), "heurística local")
    const model = opinionFromModel("Veredicto: SEGUIR\nRazón: bien\nSiguiente: sigue", fallback)
    assert.equal(model.source, "model")
    assert.equal(opinionSourceLabel(model.source), "modelo")
    // Si el modelo no respeta el formato, se conserva la heurística y su motor.
    assert.equal(opinionFromModel("respuesta sin formato", fallback).source, "local")
  })

  check("historial_opiniones", () => {
    const first = localOpinion({ messages: [{ text: "hola" }] })
    const second = opinionFromModel("Veredicto: PARAR\nRazón: ya vale\nSiguiente: descansa", first)
    const history = pushHistory(pushHistory([], first), second)
    assert.equal(history.length, 2)
    assert.equal(history[0].opinion.source, "model")
    assert.equal(history[1].opinion.source, "local")
    assert.match(history[0].at, /^\d{1,2}:\d{2}$/)
    let capped = []
    for (let i = 0; i < 9; i += 1) capped = pushHistory(capped, first)
    assert.equal(capped.length, 5)
  })

  check("permiso_siempre_pregunta", () => {
    for (const action of [INSTALL_ACTION, CURSOR_ACTION, CLICK_ACTION, SCREEN_ACTION]) {
      const own = { action }
      forceAsk(own)
      assert.equal(own.effect, "ask")
      assert.ok(own.message.length > 20)
    }
    const cursor = { action: CURSOR_ACTION }
    forceAsk(cursor)
    assert.match(cursor.message, /No moverá tu ratón/)
    const click = { action: CLICK_ACTION }
    forceAsk(click)
    assert.match(click.message, /ratón real no se moverá/)
    const screen = { action: SCREEN_ACTION }
    forceAsk(screen)
    assert.match(screen.message, /capturar tu pantalla/)
    const other = { action: "otra.accion" }
    forceAsk(other)
    assert.equal(other.effect, undefined)
    assert.equal(other.message, undefined)
  })

  // Flujo real del RPC simulado: hook -> validación -> permission.assert -> instalación.
  let evaluateHook = null
  let assertInput = null
  let observedEffect = null
  let touched = false
  const flowCtx = {
    permission: {
      async hook(_name, callback) {
        evaluateHook = callback
      },
      async assert(input) {
        assertInput = input
        const event = { action: input.action }
        if (evaluateHook) await evaluateHook(event)
        observedEffect = event.effect
        // El usuario pulsa "rechazar" en el diálogo nativo.
        throw new Error("denied por el usuario")
      },
    },
    mcp: {
      async transform() { touched = true },
      async reload() {},
    },
    client: {
      mcp: {
        async add() { touched = true },
        async connect() { touched = true },
      },
    },
  }

  // setup(ctx) registra la regla; el RPC solo la usa al pedir permiso.
  await flowCtx.permission.hook("evaluate", async (event) => forceAsk(event))

  const badFlow = await installFromRpc(flowCtx, { capacity: "navegador", sessionID: "--auto" })
  check("flujo_rpc_sesion_invalida_no_pide_permiso", () => {
    assert.equal(badFlow.ok, false)
    assert.equal(badFlow.denied, false)
    assert.equal(assertInput, null)
    assert.equal(touched, false)
  })

  const deniedFlow = await installFromRpc(flowCtx, {
    capacity: "navegador",
    sessionID: "ses_ok",
    agent: "../../etc",
    directory: "C:/tmp\x00raro",
  })
  check("flujo_rpc_rechazo_end_to_end", () => {
    assert.equal(deniedFlow.ok, false)
    assert.equal(deniedFlow.denied, true)
    assert.match(deniedFlow.message, /Permiso rechazado/)
    assert.equal(observedEffect, "ask")
    assert.equal(assertInput.action, INSTALL_ACTION)
    assert.equal(assertInput.sessionID, "ses_ok")
    assert.equal(assertInput.agent, undefined)
    assert.equal(assertInput.directory, undefined)
    assert.equal(touched, false)
    assert.equal(evaluateHook instanceof Function, true)
  })

  check("aviso_web_contextual", () => {
    assert.equal(browserHint("revisa el build", true), "")
    const ready = browserHint("mira https://ejemplo.com", true)
    assert.match(ready, /disponible/)
    assert.doesNotMatch(ready, /instalar/)
    const missing = browserHint("mira https://ejemplo.com", false)
    assert.match(missing, /bitty-instalar/)
    assert.match(missing, /permiso/)
  })

  check("puente_url_y_token", () => {
    const conn = { port: 4321, token: "t".repeat(40), pid: 7 }
    assert.equal(bridgeUrl(conn, "/cursor"), "http://127.0.0.1:4321/cursor")
    assert.equal(bridgeUrl(conn, "/click"), "http://127.0.0.1:4321/click")
    assert.equal(validateConnection(conn).port, 4321)
    assert.equal(validateConnection({ port: 0, token: "t".repeat(40) }), null)
    assert.equal(validateConnection({ port: 70000, token: "t".repeat(40) }), null)
    assert.equal(validateConnection({ port: 1234, token: "corto" }), null)
    assert.equal(validateConnection(null), null)
  })

  check("acuerdo_antes_de_cada_permiso", () => {
    const source = fs.readFileSync(path.join(__dirname, "..", "src", "index.ts"), "utf8")
    const firstAgreement = source.indexOf("await ensureAgreement(")
    const firstAssert = source.indexOf("await ctx.permission.assert(")
    assert.ok(firstAgreement > 0, "falta el acuerdo previo")
    assert.ok(firstAssert > firstAgreement, "el permiso nativo no puede ir antes del acuerdo")
    assert.equal((source.match(/await ensureAgreement\(/g) || []).length, 3)
    assert.match(source, /"\/agreement"/)
  })

  await checkAsync("puente_lee_bridge_json", async () => {
    const tmp = fs.mkdtempSync(path.join(require("node:os").tmpdir(), "bitty-bridge-"))
    const previousAppData = process.env.APPDATA
    const previousXdg = process.env.XDG_CONFIG_HOME
    process.env.APPDATA = tmp
    process.env.XDG_CONFIG_HOME = tmp
    try {
      const dir = path.join(tmp, "BittyMascot")
      fs.mkdirSync(dir, { recursive: true })
      fs.writeFileSync(path.join(dir, "bridge.json"), JSON.stringify({
        port: 8765, token: "a".repeat(40), pid: 42,
      }))
      const conn = await readConnection()
      assert.equal(conn.port, 8765)
      assert.equal(conn.token, "a".repeat(40))
      assert.equal(bridgeUrl(conn, "/capture"), "http://127.0.0.1:8765/capture")
    } finally {
      if (previousAppData === undefined) delete process.env.APPDATA
      else process.env.APPDATA = previousAppData
      if (previousXdg === undefined) delete process.env.XDG_CONFIG_HOME
      else process.env.XDG_CONFIG_HOME = previousXdg
      fs.rmSync(tmp, { recursive: true, force: true })
    }
  })

  console.log(results.join("\n"))
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
