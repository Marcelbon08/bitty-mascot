const assert = require("node:assert/strict")
const fs = require("node:fs")
const path = require("node:path")

const build = path.join(__dirname, "..", ".alpha-build")
// El paquete es ESM; marcamos el directorio de compilación como CommonJS.
fs.writeFileSync(path.join(build, "package.json"), '{"type":"commonjs"}\n')
const { CAPACITIES, CAPACITY_IDS, capacityFromText, needsBrowser } = require(path.join(build, "capacities.js"))
const { installCapacity } = require(path.join(build, "install.js"))
const { scanProject, scanToText } = require(path.join(build, "scan.js"))

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

  console.log(results.join("\n"))
}

main().catch((error) => {
  console.error(error)
  process.exitCode = 1
})
