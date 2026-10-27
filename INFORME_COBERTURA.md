# Cobertura del radar: ampliación territorial por lotes

Rama `mejora/radar-auditable`, exclusivamente PR #1; no fusionado. Una URL configurada, un HTTP 200 o un padrón cargado **no demuestran cobertura operativa**.

## Alcance de este avance

Se conservan las 36 fuentes activas anteriores. El inventario contiene 75 portales de 72 organismos: 73 incorporados a verificación y dos pendientes de incorporación (Concordia restringida y Ramallo con referencia histórica insuficiente). Se prueban 37 incorporaciones adicionales; su estado real depende de la auditoría, no de esta cifra.

El padrón persistente enumera 655 entradas: 365 santafesinas, 239 entrerrianas y 51 bonaerenses. Georef devolvió 364 gobiernos locales santafesinos, 239 entrerrianos y 51 bonaerenses dentro del radio geodésico; Chabás se conserva además como prioridad previa pendiente de contraste. **No se certifica que el padrón esté actualizado exhaustivamente a 2026.** El export de municipios v2 devolvió 404; el de gobiernos locales sí se descargó. Se conservan URL, fecha y SHA256 de la descarga en `inventario/territorio.json`.

El criterio bonaerense es distancia geodésica desde el centro de Rosario hasta el centroide oficial <=280 km. No es distancia por ruta ni prueba que todos los trayectos cumplan 280 km. La distancia vial permanece desconocida. Municipios, comunas y juntas sin portal se mantienen explícitamente pendientes; los organismos provinciales no sustituyen un portal municipal propio.

## Evidencia real y resultados

La [auditoría inicial #77](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40569030146) consultó las primeras 59 fuentes y aprobó 153 pruebas. Entre las 23 incorporaciones de ese lote: 2 operativas, 5 parciales (incluidos dos recorridos truncados por tiempo), 4 bloqueadas y 12 pendientes. ENAPRO recuperó 18 registros, con las convocatorias 3/2026 (apertura 26/11/2026) y 4/2026 (15/02/2027); Rafaela recuperó 11 registros históricos. Esas cifras corresponden únicamente a #77, antes de las correcciones y el segundo lote.

El resultado posterior se genera desde los checkpoints reales con `tools/informe_cobertura.py` y queda en el artefacto de Actions, carpeta `cobertura/`: JSON con cada fuente, errores, procedimientos, ejemplos y municipio/comuna pendiente, más informe Markdown. El [PR #1](https://github.com/tobiastorrescc/Radar---Licitaciones/pull/1) enlaza la corrida más reciente y resume sus conteos. Los resultados de una corrida aislada no se importan al historial de producción.

## Conectores y comprobación

- Secciones por encabezados, wrappers y adjuntos; formularios con campos y fechas separados; avisos como imágenes y PDF/OCR; tablas y paginación existentes.
- Regresiones reales de #77 para IAFAS, Colón bonaerense y VGG. Se conservan fragmentos originales y procedencia en `tests/fixtures/reales/cobertura77/`.
- VGG: endpoint y parámetros derivados del JavaScript público y de los años/tipos observados; número desconocido si no aparece. Chajarí: redirección pública `/web` observada, pendiente de comprobar extracción.
- Descubrimiento de secciones de contratación sólo por enlaces publicados en el mismo dominio. Los scripts se inspeccionan de forma acotada, sin ejecutarlos; hallar un endpoint no equivale a verificarlo.
- Ante HTTP 429 se pospone el recorrido, se guardan los resultados parciales y no se insiste sobre las páginas restantes. Los demás portales siguen.
- Boletines complementarios: atribución al organismo publicado, manteniendo provincia y convocatoria para evitar fusiones entre organismos homónimos. No se atribuyen automáticamente todos los llamados al editor del boletín. Si el organismo no se reconoce, no se inventa.

Operativa exige procedimientos identificados con objeto y recorrido sin incidencias; parcial conserva procedimientos con incidencias o datos incompletos. Un listado vacío explícito se informa aparte. Plazos: conexión/lectura, 60 segundos por fuente, 600 globales, procesos aislados, checkpoints y logs. Se acota también la instalación de dependencias. La paginación o lectura pendiente queda visible, sin límites comerciales de cantidad.

## Preservación y trabajo pendiente

Se mantienen el workflow diario, la deduplicación persistente, los reportes íntegros y las vistas de abiertas/próximas a vencer. Se conserva la extracción de pago y su documento de respaldo: contado/contra entrega comprobados se priorizan, los demás siguen visibles. No hay filtros por monto, rubro, modalidad, financiación o viabilidad; no se buscan proveedores ni se calcula rentabilidad.

Falta contrastar el padrón contra registros provinciales vigentes y completar las direcciones oficiales de muchos municipios/comunas, incluyendo los pequeños. Falta completar el inventario sectorial de hospitales, SAMCo, universidades, empresas y entes descentralizados. Deben resolverse interfaces dinámicas y recorridos parciales, así como boletines bloqueados y enlaces documentales pendientes. **La cobertura territorial completa sigue pendiente.**
