# Declaración de uso de IA

**Bitty Mascot fue creado con inteligencia artificial, con supervisión humana.**

## Qué significa

- El código de `src/bitty-mascot.ps1`, el generador de sprites, los textos de la interfaz, la documentación y los scripts de instalación fueron **generados con la ayuda de un asistente de IA**.
- El autor (**marce**) revisó, probó y ajustó el resultado en su equipo: se verificó la sintaxis, el comportamiento de la interfaz, la lectura UTF-8, las sesiones de OpenCode y el flujo completo de conversación.
- Los sprites son **dibujados por código** por `generate-sprites.ps1` (GDI+, 64×64, sin assets externos). No se usaron imágenes de terceros.

## Qué no es

- **No es un producto oficial de OpenCode** y no está afiliado, patrocinado ni respaldado por OpenCode AI.
- No contiene código copiado de OpenCode; solo llama a su CLI pública (`opencode run`) con los argumentos documentados.
- No recopila datos ni envía información a ningún servidor propio: todo pasa por la instalación local de OpenCode del usuario.

## Responsabilidad

El software se entrega **«tal cual»**, sin garantía de ningún tipo. La IA puede cometer errores; aunque se ha probado en Windows 10/11 con PowerShell 5.1 y OpenCode v2.3.2, puede fallar en otras configuraciones. Revisa el código antes de usarlo si eso es importante para ti.

## Transparencia

Si vas a redistribuir o modificar Bitty, conserva esta declaración y la sección «Hecho con IA» del `README.md`. La licencia es MIT (ver `LICENSE`).
