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

En el PR, el workflow existente `Radar diario de licitaciones` ejecuta las pruebas automáticas y dos consultas reales consecutivas con un estado nuevo bajo `work/controlado/`. No restaura producción ni un piloto anterior. Comprueba que la primera no genere alertas masivas y que ninguna identidad vista en la primera reaparezca como nueva en la segunda. Puede haber datos completados, modificaciones o primeras detecciones adicionales por variación de portales parciales; se registran con su categoría y evidencia.

Después reproduce el segundo conjunto de datos, sin otra consulta de red, para comprobar estabilidad semántica: cero nuevas detecciones y cero cambios ante los mismos datos. Verifica hashes de los cuatro archivos de producción antes y después. El informe `prueba_doble.json` conserva por separado las dos consultas de red y esa reproducción adicional. No se exige que la web permanezca inmóvil entre consultas.

```bash
python tools/radar_controlado.py --salida work/prueba-doble --doble
```

La prueba doble rechaza un directorio que ya tenga estado: no elimina un historial para repetir una prueba. Usar un directorio nuevo.

## Consulta diaria del piloto

En GitHub Actions, abrir el workflow **Radar diario de licitaciones** y su última ejecución controlada. El resumen muestra salud de fuentes, novedades y estado de la corrida. Descargar el artefacto **radar-controlado**, descomprimirlo y abrir **index.html**. No requiere servidor ni servicios externos.

El catálogo incluye búsqueda local y todas las filas, enlaces a publicaciones y pliegos identificados, condiciones de pago y documento de respaldo, apertura, publicación, vigencia y última observación. También están `reporte_diario.md`, `catalogo_completo.json/.md`, `eventos.json`, abiertas, próximas a vencer, auditorías por fuente, SQLite y manifiesto de integridad. No se publica una web ni se envían mensajes automáticamente.

Para ejecutar un día en modo controlado sobre esta rama, el workflow acepta `modo=controlado`. La primera vez debe elegirse `inicializar=true` si no existe estado diario previo. Por ejemplo, con una CLI de GitHub autenticada:

```bash
gh workflow run radar-diario.yml --ref mejora/radar-auditable -f modo=controlado -f inicializar=true
```

En los días siguientes omitir `inicializar` o dejarlo en `false`. El workflow busca el último artefacto **estado-controlado** del mismo workflow y rama, generado por una ejecución manual o programada del piloto, valida SHA-256 y SQLite y continúa desde allí. Las pruebas dobles de PR no se usan como estado diario. No sobrescribe un estado existente por marcar inicializar. Si falta el estado o falla su integridad, detiene la corrida en vez de reiniciar silenciosamente.

Los artefactos se conservan noventa días. Cada nuevo estado contiene todo el historial acumulado, no sólo noventa días de registros. Si el piloto se detiene durante más tiempo, se necesita una copia de respaldo para restaurar; antes de producción hay que definir almacenamiento y respaldos duraderos. No confiar en la caché de Actions para el historial. La caché compartida sólo reutiliza descargas y textos documentales.

## Programación y descubrimiento

Se conserva el horario de las 08:00 Argentina. El job controlado programado exige `RADAR_CONTROLADO_HABILITADO=true`; el de producción tiene una autorización independiente y cerrada por defecto. Esta etapa no establece ninguna variable del repositorio ni activa producción.

**GitHub sólo ejecuta cron desde la rama predeterminada. Mientras no se autorice un mecanismo de programación y este workflow permanezca sólo en la rama del PR, no hay un cron diario activo en esa rama.** Se puede probar manualmente el piloto sin fusionar ni activar producción. La automatización diaria requiere resolver ese punto con autorización, por ejemplo un disparador autorizado que invoque el workflow de la rama; no se modifica `main` de forma indirecta para lograrlo.

El descubrimiento conserva su workflow separado y el padrón territorial. En esta revisión se solicita revisar hasta cien URLs candidatas pendientes, sin esperar siete días, una consulta por URL para no repetir descargas por búsquedas duplicadas. Cada promoción sigue exigiendo identidad, jurisdicción y procedimientos extraídos. Si el presupuesto global se agota, quedan candidatos sin iniciar y se conservan sus turnos. Las consultas regulares mantienen la rotación y reintento diferido. Los cron de descubrimiento también tienen la limitación de rama predeterminada; las ejecuciones del PR y manuales sí prueban el mecanismo real.

## Antes de activar

Revisar los resultados de la prueba doble y las fuentes que siguen parciales, bloqueadas o pendientes; verificar continuidad del estado y respaldos; elegir quién consulta el informe y recibe aviso de ejecuciones incompletas; autorizar la programación del piloto. La producción requiere una aprobación separada y explícita. Un resultado de Actions correcto significa que el proceso terminó y guardó auditoría, no que todas las fuentes funcionen.
