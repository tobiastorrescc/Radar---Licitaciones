# Piloto diario sólo con GitHub Actions — propuesta desactivada

Esta opción reemplaza la recomendación de servidor externo para la puesta en marcha solicitada. Es viable sin contratar un servidor, mantener una PC encendida, crear un PAT ni fusionar el PR #1. Los archivos están preparados en `mejora/radar-auditable`; **no se instaló nada en main, no se habilitó ninguna variable ni se activó la programación**.

## Qué se instalaría después de autorización

Únicamente [esta propuesta autocontenida](despliegue/github-actions/programar-piloto.yml.propuesto) se copiaría a `main:.github/workflows/programar-piloto.yml`. No copiar ni fusionar el resto del PR. El workflow sólo coordina API, supervisa y avisa; no hace checkout ni ejecuta código de la rama del piloto con su token privilegiado.

1. **08:00, America/Argentina/Buenos_Aires**: cron nativo con zona IANA, actualmente 11:00 UTC. Comprueba estado y duplicados, sube un pequeño journal de intención y hace un único workflow_dispatch a `radar-diario.yml` sobre `mejora/radar-auditable`.
2. El piloto consulta las fuentes con su workflow y `GITHUB_TOKEN` propios, restaura y actualiza únicamente su historial. El programador termina inmediatamente: no espera durante toda la consulta.
3. Al completar el piloto, `workflow_run` revisa conclusión y pasos de persistencia. Un fallo/cancelación, job omitido o falta de confirmación del respaldo genera alerta.
4. **09:30 de Argentina**: segundo cron verifica que exista y haya terminado la ejecución diaria. Si falta o sigue incompleta, alerta; **no redispara** para evitar duplicados e incertidumbre.

El job exige `RADAR_PILOTO_PROGRAMADOR_HABILITADO == 'true'` y `refs/heads/main`. La variable ausente o false impide actuar incluso si posteriormente se copia el archivo. Hoy la propuesta está fuera de `.github/workflows`, con extensión `.propuesto`: GitHub no la reconoce como workflow instalado.

**Hallazgo de la revisión:** main ya contiene un workflow antiguo `radar-diario.yml` con cron `0 11 * * *` y escritura de su historial. No fue creado ni activado en esta etapa y **no se modificó ni se ejecuta desde el nuevo programador**. La adición propuesta no dispara ese workflow antiguo por push —sus eventos actuales son schedule/workflow_dispatch—. Sus eventos de finalización quedan excluidos por el filtro de rama del supervisor. Desactivar o cambiar ese cron existente sería otra acción, fuera de esta propuesta y pendiente de autorización específica.

## Permisos comprobados y aislamiento

| Permiso del programador | Para qué |
|---|---|
| `actions: write` | workflow_dispatch; leer ejecuciones/jobs y guardar journal de Actions |
| `contents: read` | comprobar índice del respaldo de la rama del piloto |
| `issues: write` | crear/actualizar una alerta diaria en Issues |

No concede `contents: write`, administración, merge, secretos externos ni PAT. Los permisos no mencionados quedan sin acceso. La documentación de GitHub confirma que workflow_dispatch es una excepción: **sí crea una ejecución con GITHUB_TOKEN**. Las dos invocaciones independientes del controlador del PR prueban el mismo endpoint con actions: write. La validación nueva utiliza la entrada del módulo compartido limitada al canal `validacion`, clave SHA y PR propio; no activa el canal diario.

El payload del programador es fijo: mismo repositorio, `radar-diario.yml`, ref `mejora/radar-auditable`, modo `controlado`, canal `piloto`, inicializar=false. No hay inputs para seleccionar producción, main, una semilla u otro repositorio. Se comprueba que el índice de Git exista, sea compatible y no esté vacío; la verificación íntegra de hashes/cadena se realiza dentro del piloto antes de consultar fuentes.

`workflow_run` puede disponer de permisos elevados. Por eso **no descarga artefactos ni checkout del run que lo disparó**, no ejecuta código ni plantillas de esa rama, y vuelve a consultar metadatos por API. Filtra workflow, evento, rama, repositorio de origen y título diario. Los ensayos del PR, forks y el workflow antiguo de main no generan alertas operativas. El código privilegiado está embebido en el archivo de main, revisable y generado desde la misma lógica que se prueba; las acciones de GitHub están fijadas a SHA comprobados.

GITHUB_TOKEN tiene ámbito del repositorio, no de una sola rama/endpoint. El programador no puede escribir contenidos con sus permisos, pero actions: write permite otras operaciones de Actions. El aislamiento se aplica mediante código fijo y condiciones, no mediante una supuesta restricción de rama del token. Mantener revisión y protección de los cambios en main. El piloto mantiene su permiso separado de escritura para publicar respaldos en su rama; el programador no lo hereda ni modifica esa configuración.

## Duplicados y manejo de fallos

- Clave por fecha argentina y título determinista; comparte la clave con la alternativa externa, que **debe permanecer desactivada**. Un hijo ya activo o exitoso evita otro POST; uno fallido/cancelado se señala sin repetirlo.
- El programador se serializa con `cancel-in-progress:false`. Los eventos de supervisión tienen su propio grupo para no interrumpir despachos. El grupo del piloto `radar-${github.ref}` conserva la serialización de su estado, sin cancelar un piloto activo. GitHub conserva sólo un run pendiente por grupo: un pendiente puede ser reemplazado; el supervisor informa esa cancelación.
- Se sube el journal **antes del POST**. Si subirlo falla, no se despacha. Si se pierde la respuesta del POST, no hay retry automático. Un rerun del programador o un segundo padre en la misma fecha, sin hijo confirmado, exige revisión. No se depende únicamente de un artefacto descargable para decidir si reenviar.
- Los runs de control y el journal de 90 días conservan evidencia. No borrar runs ni journals durante una incidencia: eliminar deliberadamente ambos controles invalida su evidencia de deduplicación. No se aceptan reruns para despachar fechas pasadas.
- Cinco páginas máximo por listado, respuestas API gestionadas por SDK y tiempo total de job de cinco minutos. No mantiene un runner esperando 40 minutos ni reintenta un POST por errores de red. Si la propia API/GitHub falla, puede fallar también la creación del issue: quedan el run fallido y las notificaciones nativas, cuando GitHub vuelva a estar disponible.

## Historial y respaldos

El estado diario preparado continúa en `piloto_respaldo/diario/` con **3.691 procedimientos y 3.750 versiones**, independiente de producción y de los canales de validación. Su hash lógico anterior es `e91854f7e33c86c6390c21fea9d8e6e1214f85248eb8e34966173142024c3c42`. No se inicializa una base vacía si falta la cadena.

El piloto conserva metadatos, procedimientos, versiones, eventos y auditorías en base e incrementos gzip versionados, con hash SHA-256, enlace al segmento previo y hash lógico del estado. Antes de publicar cada incremento ensaya restauración completa y exige continuidad. Si el respaldo o push falla, la ejecución falla; se conservan resultados parciales en artefactos, pero no se anuncia persistencia duradera exitosa. Las fuentes fallidas no borran datos anteriores.

El supervisor exige éxito del job del piloto y de sus pasos de restauración, continuidad, exportación y persistencia; success de un job ajeno u omitido no sirve. Los artefactos de informes duran 90 días; los segmentos Git no dependen de esa caducidad. Todo sigue dependiendo de GitHub: esta solución no promete una copia fuera del proveedor. No hay servidor externo ni almacenamiento contratado.

## Alertas y consulta diaria

Cada día con incidencia crea un Issue `[Radar piloto] Revisar ejecución del AAAA-MM-DD`, con enlace al run y motivo. Incidencias posteriores actualizan o reabren ese issue; el mismo run no crea otro aviso. No se modifica un issue humano aunque copie el título o marcador del bot. La propuesta no ha creado ni enviado alertas reales todavía: los fallos se prueban con API simulada.

Para avisos en GitHub/correo: revisar Watch del repositorio para Issues y Actions y las preferencias personales de notificación antes de habilitar. La configuración de correo del usuario no se cambia desde el workflow ni se garantiza entrega de email. Los issues y runs son la evidencia principal. Un error por portal con una auditoría global conservada puede concluir `COMPLETA_CON_INCIDENCIAS` y no equivale a un fallo de infraestructura: sus causas siguen visibles en el informe completo.

Consultar el resumen de Actions y el artefacto `radar-controlado`, abrir `index.html`: todas las novedades/cambios y el catálogo, enlaces y documentos, abiertas, próximas a vencer, vencidas/históricas y datos desconocidos. Se mantienen todas las oportunidades, sin filtros por rubro, monto o financiación, ni cálculos automáticos de rentabilidad. Contado/contra entrega sólo se priorizan con respaldo comprobado.

## Consumo y costo

El repositorio es público; la documentación vigente confirma runners estándar de GitHub gratuitos para repositorios públicos. No se requiere un servicio adicional, servidor, PAT o GitHub App. No se contratan runners grandes ni almacenamiento adicional. Verificar cuotas/política de artefactos y cache del propietario antes de habilitar; la retención y el tamaño acumulado importan, aunque los minutos públicos sean gratuitos.

Presupuesto aproximado, **no una medición futura garantizada**: tres jobs breves de control por día —despacho, finalización y vigilancia— suelen redondear a unos tres minutos en total, más el piloto observado de unos 8–9 minutos incluyendo pruebas/lectura documental. Orden de **330–360 minutos de runner al mes** para 30 días, variable con demoras, más descubrimiento/CI del desarrollo. Tope técnico del programador: 5 minutos por job, unos 450 minutos mensuales si los tres agotan ese límite; el piloto tiene sus propios límites, no sumarle un monitor esperando 50 minutos. La ronda de pruebas del PR es un gasto temporal de desarrollo separado del uso diario.

Con artefactos recientes de unos 15 MB de informe y 4 MB de estado, 90 días diarios serían aproximadamente 1,7 GB, sin contar auditorías previas y cache; es una estimación de almacenamiento para revisar, no una compra ni promesa de costo total cero. Los incrementos Git también crecen: medir su crecimiento y preparar compactación/restauración auditada a futuro, sin eliminar historia ahora.

## Límites de GitHub y autorización posterior

GitHub no garantiza inicio exactamente a las 08:00: puede demorar o descartar cron en horas de carga. El reloj de las 09:30 detecta muchos faltantes; si GitHub está completamente caído o deshabilita el workflow, un monitor en el mismo proveedor tampoco puede avisar en ese momento. Los repositorios públicos pueden perder schedules tras 60 días sin actividad; no se promete que los commits de un bot eviten toda deshabilitación. Revisar estado del workflow y notificaciones periódicamente. No existe SLA de puntualidad o alertas independientes en una solución gratuita sólo GitHub.

La solución es viable para este piloto con esas condiciones; no hace falta recurrir a un cron externo gratuito que custodiaría otro token. Si se exigiera puntualidad garantizada o vigilancia independiente de GitHub, se necesitaría otro proveedor y evaluar sus límites; no se lo incorpora ahora.

Después de autorización:

1. Comprobar que main y la rama del piloto siguen donde se auditaron; revisar permisos de Actions e Issues habilitados.
2. Copiar **sólo** el archivo propuesto a main, con la variable de habilitación aún ausente/false. No hacer merge/cherry-pick de todo el PR.
3. Configurar notificaciones y autorizar una prueba manual del programador ya instalado, habilitando la variable en una ventana supervisada. La prueba diaria consume la misma clave por fecha; un cron posterior ese día no debe repetirla.
4. Comprobar hijo, reporte, restauración/respaldo, alertas de prueba autorizadas y vigilancia; recién entonces dejar la habilitación diaria vigente. Desactivar la variable o el workflow detiene futuras solicitudes sin borrar el historial.

**Nada de esta lista se ejecutó sobre main.** El paso de cron/workflow_run real no puede probarse de punta a punta sin instalar el workflow allí; las pruebas preparadas cubren la lógica y los scripts autocontenidos, y las invocaciones reales del PR verifican GITHUB_TOKEN/dispatch y persistencia en el canal aislado.

Fuentes oficiales: [excepción GITHUB_TOKEN/dispatch](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow), [cron, zona horaria y límites](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule), [seguridad workflow_run](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#workflow_run), [costos Actions](https://docs.github.com/en/billing/concepts/product-billing/github-actions).
