import { copyFileSync, mkdirSync } from "node:fs"

// El plugin GUI de Vite siempre genera dist/gui-experimental.cjs.
// Lo copiamos a gui-dist/ porque el dist/ del repo está reservado a los binarios de Python.
mkdirSync("gui-dist", { recursive: true })
copyFileSync("dist/gui-experimental.cjs", "gui-dist/gui-experimental.cjs")
console.log("Bundle GUI copiado a gui-dist/gui-experimental.cjs")
