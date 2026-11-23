# Notas de mejoras

Lista viva de mejoras de Bitty, ordenada por prioridad. Lo ya publicado queda en el [CHANGELOG](CHANGELOG.md).

## Hechas

1. CI con tests y smoke real en Fedora.
2. Binarios más pequeños (recorte real de bibliotecas Qt en v2.4.5).
3. Rechazo de permiso verificado de extremo a extremo.
4. Motor de la opinión visible (heurística local / modelo).
5. Validación de la superficie RPC.
6. Historial de las 5 últimas opiniones.
7. Aviso contextual al detectar una web: distingue si el MCP ya está disponible o si hay que instalarlo.
12. Cursor virtual de Bitty (v2.4.7): segundo cursor pixelado que se mueve a coordenadas con interpolación fluida, sin tocar el ratón real ni hacer clics.
13. Integración del cursor con OpenCode (v2.5.0): herramienta `bitty_cursor` y puente local con token; OpenCode manda coordenadas, Bitty mueve su cursor virtual.
14. Visión de pantalla para OpenCode (v2.5.0): herramienta `bitty_screen` entrega una captura PNG fresca del escritorio real (incluido el Opera de Marcelbon), con permiso nativo cada vez y sin grabación continua.

## Pendientes

> La numeración se conserva aunque las hechas no queden seguidas: es el identificador que usamos en conversación.

### 8. Explicación más clara en OpenCode Desktop (apuntada por Marcelbon)

- Que el Bitty de la app explique **un poco mejor cuál es el problema detectado** y **qué recomienda hacer**, en lugar de limitarse a `Veredicto / Razón / Siguiente`.
- Propuesta: panel con tres bloques cortos — *Problema*, *Por qué lo veo*, *Recomendación* — con lenguaje concreto y accionable.
- La mascota pequeña debe seguir mostrando solo el resumen muy corto (`SIGUE`, `REVISA`, `PARA`). La opinión sigue siendo solo una sugerencia: nunca escribe ni interrumpe la sesión.

### 9. Decidir qué hacer con «Instalar ver el navegador» (duda de Marcelbon)

- Hoy ese botón/`/bitty-instalar` pide permiso nativo y registra el MCP de Playwright (`bitty-navegador`) en la configuración de OpenCode. No captura la pantalla, no instala extensiones de Chrome/Firefox y no ejecuta comandos arbitrarios.
- Si se decide quitarlo, hay que retirar el botón, el comando, el catálogo y el aviso de la mejora 7. Quedaría documentado como capacidad desactivada.

### 10. Más capacidades del catálogo cerrado

- Solo MCP con permiso cada vez; nada de acceso a shell ni a archivos del usuario.

### 11. Tema y sonido

- Los temas Navidad/Halloween/Automático ya existen en la mascota flotante. Estudiar un sonido muy suave y opcional (desactivado por defecto) para eventos como `PERMISO` o `ERROR`.

### 12. Cursor virtual de Bitty → HECHA en v2.4.7

- **Aclaración de Marcelbon**: no quiere mover su cursor real. Quiere **dos cursores**: el suyo y uno propio de Bitty, dibujado en pantalla. El de Bitty es visual (señalar/guiar), sin inyectar clics ni teclas en el sistema.
- **Implementado**: `/cursor x,y` envía el cursor a unas coordenadas; `CursorNavigator` interpola cada 20 ms con tope de 16 px por paso hasta llegar. Ventana siempre encima, transparente a clics y multimonitor. Ruta aleatoria y ocultar/mostrar desde el menú derecho.
- **Fuera de alcance a propósito**: mover el ratón real, hacer clics o escribir, y actuar sobre el Opera del usuario. Eso seguiría siendo una decisión aparte con permiso cada vez; Playwright no controla el navegador real de Marcelbon.

### 13. Cursor compartido con OpenCode → HECHA en v2.5.0

- **Petición de Marcelbon**: «habrá que integrarlo a Bitty y a OpenCode para que puedan hacerlo».
- **Implementado**: Bitty abre un puerto solo en `127.0.0.1` con token aleatorio y el plugin registra `bitty_cursor`. OpenCode manda `x`, `y`; la mascota mueve su puntero y muestra un aviso breve. El ratón real sigue intacto.
- El permiso se pide cada vez y no se guarda; el puente se puede apagar desde el menú derecho.

### 14. Visión en tiempo real de la pantalla → HECHA en v2.5.0

- **Petición de Marcelbon**: «definitivamente necesitamos alguna cosa para que OpenCode pueda tener una visión a tiempo real de la pantalla».
- **Implementado**: `bitty_screen` captura el escritorio real con Qt y se lo adjunta a OpenCode como PNG en **data-URL inline** (la forma que OpenCode 2.3.2 materializa en resultados de tools). Es una imagen fresca bajo demanda cada vez que el modelo la pide, no un vídeo permanente ni una captura silenciosa. Requiere un modelo con visión.
- **Opera real**: esta captura ve la ventana del navegador de Marcelbon, a diferencia del Chromium oculto de Playwright. Para navegar por páginas se mantiene el MCP `bitty-navegador` de Fase 4.
- **Privacidad**: diálogo nativo cada vez, token local, sin grabación, máximo 6 PNG en temporal y borrado al salir.
