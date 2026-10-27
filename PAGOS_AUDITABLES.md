# Condiciones de pago con evidencia

El radar conserva todas las oportunidades recuperadas y todas sus primeras detecciones válidas: rubro, monto, modalidad, financiación, vigencia y pago no se usan como filtros comerciales. Este cambio analiza condiciones de pago y ordena las filas. Los campos heredados de estimación comercial permanecen sin cálculo; el reporte no calcula costos ni rentabilidad ni busca proveedores.

## Qué se comprueba

`pagos.py` interpreta cláusulas en el texto de los pliegos/documentos, no una palabra del título ni la respuesta HTTP. Una clasificación VERIFICADO requiere cita, URL de documento y SHA256 de sus bytes; conserva la página cuando la extracción PDF permite identificarla. Los segmentos de boletines y DOCX sin paginación fiable no inventan un número de página.

Distingue contado, contra entrega de bienes, contra presentación de factura, recepción de factura, factura conformada y conformidad de recepción de bienes/servicios. Fecha/emisión de factura no se convierte en presentación ni recepción. Conformidad de una administradora sin especificar qué conforma se mantiene como conformidad no especificada. Conserva el plazo literal de 7, 15, 30, 45, 60, 90 u otros días y si son hábiles, corridos o de unidad no indicada. No convierte mensual a mes vencido en 30 días.

Los formatos de formulario «Cantidad: TREINTA (30); Unidad de tiempo: DÍAS» se leen como 30 días. Los números escritos y entre paréntesis deben coincidir. «Contado a 30 días» no obtiene prioridad inmediata. Las opciones y pagos mixtos conservan sus términos y requieren revisar la cláusula; no prometen que todo se cobre al contado.

Se excluyen del análisis del cobro el costo del pliego, sellados, tasas y garantías. Una remisión a otro pliego no basta para elegir una condición. Las negaciones y opciones hipotéticas tampoco. La palabra canon por sí sola no identifica quién paga. Si el documento dice expresamente que paga el adjudicatario, se indica a su cargo y no recibe prioridad como cobro inmediato.

Si distintos documentos dan condiciones incompatibles, la etiqueta es **Pago no informado** y se guardan ambas citas para revisión. No se presume qué documento prevalece. La ausencia de una cláusula reconocida no demuestra que el pliego no contenga condiciones: significa pendiente de comprobación.

## Definiciones generales y documentos relacionados

La auditoría real #65 recuperó en Reconquista la definición «por pago Contado se entenderá … 10 días hábiles», junto con una remisión a condiciones particulares y un ejemplo hipotético de financiación. Esa definición general no selecciona contado. Si el mismo documento selecciona expresamente contado y existe una única definición compatible, se aplica el plazo definido, conserva la cita de selección y la cita/página de la definición y no obtiene prioridad inmediata. La evidencia original se preserva en `tests/fixtures/reales/pagos-65.json`; sus clasificaciones iniciales son antecedentes, las pruebas recalculan el resultado corregido.

Un código cortado por un salto de línea en PDF se vincula al procedimiento únicamente cuando el código completo observado en la URL oficial del adjunto completa ese prefijo. Se mantienen separadas las series administrativas distintas. Los documentos que nombran otro procedimiento no aportan automáticamente sus condiciones al actual. Los anexos genéricos expresamente enlazados desde la publicación mantienen esa procedencia.

## Reportes y orden

El reporte diario Markdown y las vistas de abiertas/próximas tienen columnas **Condiciones de pago** y **Documento de respaldo**. Después de la tabla se incluyen las citas y páginas. JSON agrega `pago` (estado, clasificación, plazo, unidad, hitos, evidencia y motivo pendiente), `condiciones_pago` y `enlace_condiciones_pago`.

El orden prioriza contado y contra entrega comprobados, destaca desiertas, segundos llamados y reaperturas y usa el plazo publicado como orden secundario. Las filas de 60/90 días, mixtas, históricas, vencidas y desconocidas siguen presentes en el reporte íntegro; su cantidad no se limita. El resumen de pagos cuenta por separado verificadas y pendientes sobre los procedimientos recuperados, nunca sobre licitaciones no observadas de fuentes bloqueadas.

## Recursos y reutilización

La detección de publicaciones mantiene sus procesos aislados y plazos. Los documentos de todos los procedimientos recuperados entran en una cola con cuatro procesos, 15 segundos por documento y 180 segundos globales. Las abiertas y las referencias del año actual se atienden primero; el resto también entra sin tope de cantidad. La cola se reparte entre fuentes. Al agotarse el plazo, cada documento no iniciado y cada oportunidad sin clasificación quedan pendientes visibles; no se eliminan para mejorar porcentajes. Los resultados parciales se guardan en JSONL.

`cache_documentos.py` comparte los bytes, metadatos y textos entre conectores, comprobación de enlaces y análisis de pagos. Reutiliza el documento dentro de cinco minutos cuando hay validadores; después envía If-None-Match/If-Modified-Since y un 304 reutiliza bytes/texto. Si el portal no aporta validadores, reutiliza hasta seis horas y después vuelve a consultar. No puede garantizar que un servidor sin validadores no cambie dentro de ese intervalo: se registra fecha de descarga, estado y antigüedad de cache. Una revalidación fallida no se presenta como correcta sirviendo datos antiguos silenciosamente.

Los bytes se guardan por hash con escrituras atómicas; el texto completo se extrae una vez por contenido. Un cambio de bytes cambia la identidad del texto. El OCR interrumpido no se guarda como extracción completa. Se mantiene la lectura documental acotada a 12 MB y se rechaza por Content-Length antes de descargar si el tamaño declarado excede ese límite. Los PDF escaneados sin texto reutilizable quedan pendientes de OCR en esta etapa; no se ejecuta OCR masivo para buscar pagos. El cache de bytes se mantiene hasta 512 MB con reutilización reciente y evicción; esto limita almacenamiento, no resultados.

El artefacto incluye `comercial/auditoria_pagos.json`, `auditoria_enlaces.json`, `auditoria_documentos_parcial.jsonl` y todos los reportes. Los logs muestran un máximo de tres ejemplos por clasificación para facilitar la lectura; el JSON/Markdown contiene todas las oportunidades y evidencias.

## Preservación

El workflow diario conserva su horario. El PR sólo ejecuta verificación aislada y pruebas. El historial anterior no se reescribe ni se borra: se deriva un índice para deduplicar y las novedades se agregan. Los enriquecimientos actuales quedan en los reportes/artefactos. No se fusiona el PR automáticamente.
