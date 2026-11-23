# Declaración de uso de IA

**Bitty Mascot fue creado con inteligencia artificial, con supervisión humana.**

## Qué significa

- El código original en PowerShell (`legacy/powershell/`), la reescritura multiplataforma en Python/PySide6 (`bitty/`), el plugin para OpenCode TUI y Desktop (`plugin/`), los sprites, los textos de la interfaz, la documentación, los instaladores y el workflow de compilación fueron **generados con la ayuda de un asistente de IA**.
- El autor (**Marcelbon**) revisó, probó y ajustó el resultado en su equipo: se verificó la sintaxis, el comportamiento de la interfaz, la lectura UTF-8, las sesiones de OpenCode, el flujo completo de conversación (incluida la identidad «Soy Bitty...»), los tres temas y el ejecutable empaquetado de Windows. El plugin se validó con `npm run build`, `npm run typecheck`, logs de carga del servidor y pruebas en PTY de la TUI con reacciones a eventos y con la opinión de Bitty (`Bitty 💡 REVISA` en la barra y `Veredicto/Razón/Siguiente` en el panel), además del resumen de `/bitty-ver` y del diálogo de permisos de `/bitty-instalar`. La GUI de Desktop solo se validó de forma estructural: la app no está instalada en el equipo del autor. Los paquetes de macOS y Linux se generan en GitHub Actions y no han sido probados en hardware por el autor.
- Los sprites son **dibujados por código** por `generate-sprites.ps1` (GDI+, 64×64, sin assets externos). No se usaron imágenes de terceros.

## Qué no es

- **No es un producto oficial de OpenCode** y no está afiliado, patrocinado ni respaldado por OpenCode AI.
- No contiene código copiado de OpenCode; usa su CLI pública (`opencode run`) y los puntos de extensión documentados de plugins (`@opencode/plugin`) con los argumentos y APIs públicos.
- No recopila datos ni envía información a ningún servidor propio: todo pasa por la instalación local de OpenCode del usuario. La opinión de Bitty funciona primero con heurística local y sin red; si se refina con el modelo, se envía únicamente un extracto acotado de la sesión actual al proveedor ya configurado en OpenCode, sin crear mensajes nuevos ni modificar el historial. `/bitty-ver` lee solo un resumen local de las sesiones del proyecto (máximo 6 sesiones, 6 mensajes y 240 caracteres por mensaje). La capacidad de navegador se instala solo después del diálogo nativo de permisos de OpenCode y no recuerda la aprobación.

## Responsabilidad

El software se entrega **«tal cual»**, sin garantía de ningún tipo. La IA puede cometer errores; aunque se ha probado en Windows 10/11 con PowerShell 5.1 y OpenCode v2.3.2, puede fallar en otras configuraciones. Revisa el código antes de usarlo si eso es importante para ti.

## Transparencia

Si vas a redistribuir o modificar Bitty, conserva esta declaración y la sección «Hecho con IA» del `README.md`. La licencia es MIT (ver `LICENSE`).
