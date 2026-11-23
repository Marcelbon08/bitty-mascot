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

## Pendientes

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

### 12. Cursor virtual de Bitty (idea de Marcelbon, sin decidir)

- Idea: Bitty tendría un «cursor» propio para editar cosas en el ordenador o en el navegador.
- **En el navegador ya es posible sin escribir un cursor nuevo**: el MCP de Playwright mueve el foco, hace clic y escribe en campos de la página controlada. La mejora sería visual: resaltar el elemento que Bitty va a tocar y pedir confirmación antes de cada acción.
- **En el escritorio real es delicado**: inyectar ratón/teclado con `pynput` puede afectar a cualquier ventana (incluida la terminal del usuario) y rompe la promesa de «solo sugiere, nunca escribe ni interrumpe». Además, macOS pide permiso de Accesibilidad y Wayland limita la inyección de eventos.
- Propuesta segura si se decide hacerlo: modo explícito y desactivado por defecto, permiso nativo **cada vez**, indicación visible del objetivo, límite de duración y un atajo de cancelación inmediata. Nunca actuar sobre ventanas ajenas sin confirmación.
