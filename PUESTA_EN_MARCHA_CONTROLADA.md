# Puesta en marcha controlada, sin producción

El código y las auditorías quedan en el PR #1, rama `mejora/radar-auditable`. No se fusiona ni se modifica el historial de producción. La ejecución de `radar.py` exige `RADAR_PRODUCCION_AUTORIZADA=true`; el job de producción exige además `RADAR_PRODUCCION_HABILITADA=true` en el repositorio y ejecutarse desde `main`. Esta etapa no establece esas autorizaciones.

## Línea de base e incremental

`tools/radar_controlado.py` ejecuta las fuentes configuradas y las aprobadas automáticamente mediante el supervisor de procesos existente: cuatro consultas concurrentes, cinco segundos de conexión, diez de lectura, sesenta por fuente y seiscientos globales. El análisis de documentos tiene ciento veinte segundos adicionales por corrida. Cada fuente guarda checkpoints y auditoría, también ante cortes. Los límites de recursos dejan lecturas pendientes; no son filtros comerciales ni límites de oportunidades.

La primera corrida guarda todas las publicaciones como **LINEA_BASE**, con cero alertas de novedades. Una fuente nueva o que todavía no pudo establecer su base tiene una recuperación de línea de base separada, evitando anunciar archivos antiguos como novedades. Las siguientes corridas distinguen:

- Publicación nueva comprobada por fecha posterior al día de la última consulta completa de esa fuente.
- Primera detección con fecha desconocida: se informa sin afirmar que se publicó hoy.
- Recuperación histórica por fecha o año de procedimiento, sin inventar una fecha de publicación.
- Modificación de objeto, apertura, presupuesto, estado publicado, documentos o pago verificado.
- Datos completados cuando antes faltaba una comprobación; se distingue de un cambio editorial.
- Sin cambios: no genera otra alerta.

SQLite conserva el registro actual, versiones inmutables y eventos con la versión exacta correspondiente. Una caída o un campo vacío no borra datos anteriores. La vigencia calculada por el paso del tiempo no es una modificación publicada. Tampoco lo son los contadores de visitas de Timbúes o de descargas de Armstrong comprobados en la auditoría #107; la evidencia original permanece guardada. Pasar de un resumen a una ficha más completa se informa como datos completados, sin afirmar una edición del organismo. Si cambia una versión comprobada de un documento, las condiciones de pago antiguas no se mantienen como actuales sin respaldo. Se conserva su versión histórica.

Una corrida incompleta se identifica como tal. Cero novedades con errores no se presenta como una consulta exitosa sin novedades. Los registros no recuperados hoy permanecen en el catálogo, con fecha de última detección y marca de que no se confirmaron en esta corrida. Abiertas y próximas a vencer se calculan sobre los últimos datos conocidos; hay que verificar las fuentes con incidencias antes de ofertar.

No hay filtros por monto, rubro, modalidad o financiación, ni cálculos de costos/rentabilidad ni búsqueda de proveedores. Se conservan todas las oportunidades, pagos conocidos o desconocidos y los llamados especiales. Los candidatos que todavía no acreditan un procedimiento quedan separados en el archivo de observaciones, sin convertir páginas generales en oportunidades.

## Prueba real doble

En el PR, el workflow existente ejecuta las pruebas automáticas y solicita dos `workflow_dispatch` independientes. La primera importa una semilla auditada cuando el canal de validación está vacío y publica su respaldo incremental en Git. La segunda usa otro runner, restaura esa cadena y consulta nuevamente. Comprueba que no desaparezcan procedimientos ni versiones y que ninguna identidad anterior reaparezca como nueva. El canal de validación permanece separado del diario y de producción. Ver [resultados de persistencia](RESULTADOS_PERSISTENCIA.md).

El modo local `--doble` se conserva como diagnóstico adicional: usa un directorio nuevo, realiza dos consultas reales sobre el mismo SQLite y reproduce el segundo conjunto sin otra consulta de red para comprobar estabilidad semántica. Verifica que la inicialización no alerte registros históricos y que el mismo conjunto produzca cero nuevas detecciones/cambios. La auditoría #116 usó ese modo; la validación actual entre runners está documentada por separado. Ambos mecanismos verifican hashes de los archivos de producción antes/después y conservan sus evidencias.

```bash
python tools/radar_controlado.py --salida work/prueba-doble --doble
```

La prueba doble rechaza un directorio que ya tenga estado: no elimina un historial para repetir una prueba. Usar un directorio nuevo.

## Consulta diaria del piloto

En GitHub Actions, abrir el workflow **Radar diario de licitaciones** y su última ejecución controlada. El resumen muestra salud de fuentes, novedades y estado de la corrida. Descargar el artefacto **radar-controlado**, descomprimirlo y abrir **index.html**. No requiere servidor ni servicios externos.

El catálogo incluye búsqueda local y todas las filas, enlaces a publicaciones y pliegos identificados, condiciones de pago y documento de respaldo, apertura, publicación, vigencia y última observación. También están `reporte_diario.md`, `catalogo_completo.json/.md`, `eventos.json`, abiertas, próximas a vencer, auditorías por fuente, SQLite y manifiesto de integridad. No se publica una web ni se envían mensajes automáticamente.

Para ejecutar un día en modo controlado sobre esta rama, el workflow acepta `modo=controlado`. El estado diario preparado se restaura automáticamente. `inicializar=true` se reserva para un canal sin historial; la semilla opcional permite importar un estado auditado. Por ejemplo, con una CLI de GitHub autenticada:

```bash
gh workflow run radar-diario.yml --ref mejora/radar-auditable -f modo=controlado -f canal=piloto
```

En los días siguientes omitir `inicializar` o dejarlo en `false`. El workflow restaura primero la cadena incremental de **piloto_respaldo/diario/** versionada en Git, comprueba SHA-256 y el contenido lógico completo de SQLite y continúa desde allí. Los artefactos de Actions quedan como copia adicional y para migración de estados anteriores. Las pruebas dobles de PR no se usan como estado diario. No sobrescribe un estado existente por marcar inicializar. Si falta el estado o falla su integridad, detiene la corrida en vez de reiniciar silenciosamente.

Los artefactos se conservan noventa días. Cada nuevo estado contiene todo el historial acumulado, no sólo noventa días de registros. Los segmentos versionados en Git conservan el historial incluso si el piloto se detiene más de noventa días. Hay que conservar índice y segmentos juntos; una copia externa del repositorio añade protección frente a la pérdida del propio repositorio. No confiar en la caché de Actions para el historial. La caché compartida sólo reutiliza descargas y textos documentales.

## Programación y descubrimiento

El horario objetivo del piloto es las 08:00 Argentina. En esta rama el piloto se invoca con `workflow_dispatch`; el job de producción conserva su autorización independiente, cerrada por defecto. Esta etapa no establece ninguna variable de producción ni activa producción.

**GitHub sólo ejecuta cron desde la rama predeterminada. Mientras no se autorice un mecanismo de programación y este workflow permanezca sólo en la rama del PR, no hay un cron diario activo en esa rama.** Se puede probar manualmente el piloto sin fusionar ni activar producción. La automatización diaria requiere resolver ese punto con autorización, por ejemplo un disparador autorizado que invoque el workflow de la rama; no se modifica `main` de forma indirecta para lograrlo.

El descubrimiento conserva su workflow separado y el padrón territorial. En esta revisión se solicita revisar hasta cien URLs candidatas pendientes, sin esperar siete días, una consulta por URL para no repetir descargas por búsquedas duplicadas. Cada promoción sigue exigiendo identidad, jurisdicción y procedimientos extraídos. Si el presupuesto global se agota, quedan candidatos sin iniciar y se conservan sus turnos. Las consultas regulares mantienen la rotación y reintento diferido. Los cron de descubrimiento también tienen la limitación de rama predeterminada; las ejecuciones del PR y manuales sí prueban el mecanismo real.

## Antes de activar

Revisar los resultados de la prueba doble y las fuentes que siguen parciales, bloqueadas o pendientes; verificar continuidad del estado y respaldos; elegir quién consulta el informe y recibe aviso de ejecuciones incompletas; autorizar la programación del piloto. La producción requiere una aprobación separada y explícita. Un resultado de Actions correcto significa que el proceso terminó y guardó auditoría, no que todas las fuentes funcionen.

La validación de continuidad entre ejecuciones independientes y el respaldo duradero se documentan en [PERSISTENCIA_DURADERA.md](PERSISTENCIA_DURADERA.md) y su [informe de resultados](RESULTADOS_PERSISTENCIA.md).
