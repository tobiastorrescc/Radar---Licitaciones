# Programador 100% GitHub — preparación sin activar

**Estado actualizado:** el piloto ya está instalado y habilitado; ver [instalación y validación real](INSTALACION_PILOTO.md). Las fases de preparación descritas aquí son antecedentes.

Código publicado y probado: `43f349f79704b11a10b9eb2a143105c3253bc6d9`. PR #1 abierto en `mejora/radar-auditable`. No se modificó main, no se habilitó una variable ni se instaló el workflow programador.

La solución es viable sin servidor, computadora encendida, PAT ni suscripción de cron. [Diseño y puesta en marcha posterior](PROGRAMADOR_GITHUB.md), [archivo único propuesto](despliegue/github-actions/programar-piloto.yml.propuesto), [manifiesto con hash y destino pendiente](despliegue/github-actions/manifesto.json).

## Pruebas terminadas

[Actions #137](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40794894587), job 123188854145: **265 Python + 23 JavaScript = 288 pruebas aprobadas, cero omisiones**. El generador confirmó que el workflow autocontenido coincide con la lógica sometida a pruebas. En local también pasaron las 23 JavaScript; 264 Python pasaron y una fue omitida por prohibición de sockets, que sí pasó en el runner nativo.

Las pruebas incluyen respuestas POST perdidas sin reintento; duplicados; padre anterior incierto; rerun de fecha pasada; ausencia o índice vacío; workflow deshabilitado; producción/ref alteradas; ejecuciones canceladas, fallidas o incompletas; job/pasos de persistencia ausentes; forks y ensayos excluidos; alertas por Issue sin duplicados ni modificación de issues humanos; ejecución de los scripts del workflow generado con APIs simuladas. **No se creó un Issue real ni se enviaron avisos de prueba**.

## Preparación comprobable

| Aspecto | Resultado |
|---|---|
| Cron | Propuesta 08:00 y vigilancia 09:30 en America/Argentina/Buenos_Aires |
| Ubicación actual | `despliegue/github-actions/*.propuesto`, no instalada en `.github/workflows` |
| Habilitación | Exige variable explícita true y main; no se cambió esa variable |
| GITHUB_TOKEN | actions:write para dispatch, contents:read para índice, issues:write para alertas |
| Seguridad | Sin checkout, artefactos no confiables ejecutados, PAT o contents:write; acciones fijadas a SHA |
| Aislamiento | Rama fija del piloto; canal diario separado de producción y de validación; inicializar=false |
| Duplicación | Clave diaria, evidencia previa al POST, sin retry incierto y concurrencia sin cancelar activo |
| Fallos | Workflow_run y vigilancia tardía; Issue diario + run fallido, sin redisparo automático |
| Minutos | No queda un monitor esperando toda la consulta; estimación mensual documentada |
| Fuera del alcance de la prueba actual | Cron y workflow_run en main, creación real del Issue con su token y preferencias de correo: requieren instalación/autorización posterior |

Main ya contenía un cron antiguo de producción a las 11:00 UTC: no se lo creó, modificó ni disparó en esta etapa. La propuesta no lo invoca, excluye sus eventos por rama y no necesita fusionar el PR #1. El paso de instalación futuro agregaría solamente el archivo programador, conservando intactos los demás archivos de main.

El respaldo diario preparado permanece con 3.691 procedimientos/3.750 versiones y hash lógico `e91854f7e33c86c6390c21fea9d8e6e1214f85248eb8e34966173142024c3c42`. Los ensayos reales siguientes usan otro canal. No se elimina historial ni se filtran oportunidades; no se incorporan costos o rentabilidad.

## Descubrimiento preservado

La ejecución automática de comprobación [#22](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40794894728) terminó correctamente durante la validación del PR: cien candidatas consultadas, cero incorporadas nuevas, 109 URLs acumuladas y 108 pendientes. Es una prueba del proceso existente, no una declaración de nuevas fuentes operativas ni una activación de cron de descubrimiento en main.

La propuesta generada tiene SHA-256 `114dd474ef96fe58cfee208f22ac27c5547b8974b8fe54845cba808c5dceedd8`, verificado contra el manifiesto. El árbol de main observado contiene únicamente `.github/workflows/radar-diario.yml`; no existe el programador propuesto allí.

## Dos invocaciones reales del nuevo módulo finalizadas

[Controlador #137](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40794894587): **success**. El job 123189010717 declara y registra **Actions: write, Contents: read**; el GITHUB_TOKEN llamó a workflow_dispatch desde la nueva entrada de validación del módulo, sin PAT.

| Ejecución | Procedimientos previos | Procedimientos finales | Versiones finales | Repetidos como nuevos |
|---|---:|---:|---:|---:|
| [#138](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40794952824) | 3.530 | 3.674 | 3.732 | 0 |
| [#139](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40795836919) | 3.674 | 3.691 | 3.758 | 0 |

Ambas terminaron **success**, con 74 fuentes consultadas/finalizadas. El job de producción quedó omitido. La primera importó la semilla auditada #116 y publicó el segmento base del canal aislado. La segunda hizo un nuevo checkout, restauró ese respaldo (`RESTAURADO True`), conservó todas las identidades y versiones anteriores, verificó el incremento mediante restauración completa y lo publicó en la misma rama, sin force.

El SQLite de #139 descargado pasó quick_check. Su hash lógico coincide con el índice persistido: `d5ff1de5336cdbdff4c24ac88c580a1fd9539e583a034ba487e1de5609911a89`. La continuidad fue correcta y las huellas de producción antes/después, idénticas. La cadena está en `piloto_respaldo/validaciones/43f349f79704b11a10b9eb2a143105c3253bc6d9/`.

**El diario y la validación tienen igual cantidad final de procedimientos, pero son estados independientes, con hashes/versiones diferentes. No se reemplazó ni fusionó el diario preparado.** Sigue con su hash e918… y 3.750 versiones; la validación tiene 3.758 versiones.

Las recuperaciones de línea de base no se anuncian como novedades del día. En la primera: 144 recuperaciones históricas y 23 cambios de contenido observado; en la segunda: 16 recuperaciones históricas, nueve datos completados y una primera detección de fecha desconocida. No se afirma que los cambios de extracción sean publicaciones recién editadas por el organismo. No hubo identidades anteriores repetidas como nuevas.

## Estado de fuentes visible en el ensayo final

El proceso terminó **COMPLETA_CON_INCIDENCIAS**: 32 operativas estrictas, 14 parciales, 16 bloqueadas, once pendientes y una sin publicaciones confirmada. Cero fuentes sin iniciar y cero errores internos. Esto no es una declaración de que las 74 fuentes funcionen; las incidencias de cada portal permanecen en el reporte. El supervisor separa fallo de infraestructura/persistencia de una consulta finalizada con portales parciales; no oculta sus errores ni presume ausencia de novedades.

[Artefacto íntegro #139](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40795836919/artifacts/12863987638): descargar radar-controlado y abrir index.html. Conserva 3.691 registros, todas las detecciones/cambios y 383 no observados en esa consulta; 52 abiertas y 22 próximas a vencer son según último dato conocido. Incluye JSON, Markdown, enlaces, pagos y auditoría individual. Sin filtros comerciales ni límites de cantidad ni cálculos de rentabilidad.

## Lo pendiente antes de ponerlo en marcha

1. Autorización para añadir **sólo** el archivo programador a main, sin merge del PR; revisar el hash del manifiesto y que la variable esté false/ausente antes de instalar.
2. Verificar restricciones reales de Actions/Issues y preferencias de avisos; la escritura de Issues con el futuro token de main y el correo no se afirman ensayados en vivo.
3. Autorizar una ventana de prueba manual del programador instalado y su habilitación controlada; observar despacho, respaldo, vigilancia, alerta y cron real.
4. Dejarlo habilitado únicamente tras esa revisión. No se instaló servidor externo ni se requiere contratarlo.

La propuesta no puede garantizar que GitHub ejecute exactamente a las 08:00 ni avisar desde GitHub durante una caída total del propio GitHub. Con esos límites documentados, es una solución viable para el piloto sin servidores adicionales.
