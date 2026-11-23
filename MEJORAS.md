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
