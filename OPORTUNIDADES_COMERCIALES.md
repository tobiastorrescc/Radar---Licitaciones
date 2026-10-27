# De publicaciones a oportunidades verificables

Punto de partida: auditoría individual de Actions #43 (36 fuentes; 18 con publicaciones sin incidencias, 1 listado vacío, 8 parciales, 9 sin resultados utilizables). Los contadores de publicaciones no equivalen a oportunidades abiertas. Se revisan los errores/URLs guardados por ese run, sin importar sus resultados al historial de producción.

## Datos y evidencia

`oportunidades.py` normaliza número, tipo, organismo, localidad, provincia, objeto, presupuesto explícito, fechas y enlace identificado como pliego. Los campos ausentes son `null`, y `campos_desconocidos` los enumera. `evidencias_campos` conserva fragmento y URL. No se usa el año del procedimiento como fecha de publicación ni la localidad de la oficina de compras como ubicación de la obra. Organismo/localidad/provincia provienen del registro oficial configurado; cuando la convocatoria no publica la ubicación de ejecución no se infiere.

Importes: representación decimal sin pérdida; moneda desconocida para `$` ambiguo. Cifras con separadores inconsistentes permanecen desconocidas (ejemplo real Crespo `$79.500.00,00`). El costo del pliego no es presupuesto. Tablas Crespo utilizan las cabeceras de cada columna y no su posición accidental. Los adjuntos generales se conservan en `documentos`; solamente un vínculo explícitamente titulado pliego alimenta `enlace_pliego`.

`NUEVA_DETECCION` significa desconocida para el historial, no recién publicada. Publicación anterior al día de consulta se marca histórica; la fecha de publicación desconocida sigue desconocida. `ABIERTA` requiere apertura futura y ninguna situación de cierre; `VENCIDA` exige fecha pasada o estado publicado adjudicada/finalizada/desierta/en evaluación. El día de apertura sin hora validada queda de vigencia desconocida. Una reapertura/segundo llamado se conserva como evento separado; una adjudicación no crea por sí sola una oportunidad nueva.

## Persistencia y reporte

La identidad comercial usa organismo, provincia, localidad, tipo, número anual y evento. No depende del enlace a un anexo ni del estado de adjudicación. Sin número anual suficiente se mantiene una identidad conservadora de fuente/registro para no fusionar procedimientos distintos. Se deriva un índice de las entradas antiguas; no se borra ni reescribe ninguna. Los nuevos registros se agregan; datos enriquecidos de entradas previas se consultan en el artefacto de verificación (no se silencian registros antiguos ni se los reemplaza por datos incompletos).

`radar.py` genera `licitaciones_nuevas.json` y `licitaciones_nuevas.md` con todas las primeras detecciones, incluidas históricas y desconocidas, sin filtros por rubro, monto, financiación o cantidad. Orden orientativo: pago contado/contra entrega explícito, llamados especiales y vigencia. Desierta, segundo llamado y reapertura tienen indicadores separados. No se estima rentabilidad a partir del presupuesto: hacen falta costos propios, cantidades y precio comprobable. Hoy no hay datos suficientes para calcularla.

`tools/reportar_oportunidades.py` genera las mismas vistas en `work/verificacion/comercial`, comparando con una copia en memoria del historial. El JSON completo y Markdown quedan en el artefacto; los ejemplos impresos en Actions están elegidos por completitud, sin truncar los archivos ni filtrar el reporte. Una simulación sobre una base antigua puede producir muchas primeras detecciones históricas; no se cuentan como nuevas convocatorias abiertas.

## Conectores prioritarios

- Aeropuerto y Roldán: se leen fichas antes de continuar la paginación de archivos. Se extraen fechas del texto individual; no se usan fechas ajenas del resto del listado.
- DPV ER: fichas antes del archivo. La presencia de un control cargar más sólo se considera resuelta si existe un siguiente enlace observado; no se construyen páginas por suposición.
- Crespo: objeto, fecha y presupuesto de columnas identificadas; links acta/pliego separados. El PDF histórico 404 sigue siendo una incidencia, no se inventa una ruta alternativa.
- Federación, Rosario del Tala y San Nicolás: OCR acotado con `OMP_THREAD_LIMIT=1`, evitando sobrecarga entre workers. Todo texto extraído correctamente se guarda por hash de los bytes del documento. Cada ejecución vuelve a descargar el documento y verifica su contenido; no reutiliza respuestas HTTP antiguas. Un documento modificado se lee otra vez. Cache Actions compartida entre ejecuciones; un OCR cortado nunca se almacena como lectura completa.
- Villaguay: se conserva el recorrido de todos los años, sin excluir archivos antiguos. La paginación deja paso a fichas/documentos; si el plazo no alcanza la fuente permanece parcial. El cache permite avanzar en ejecuciones posteriores sin repetir el OCR de bytes idénticos.
- Compras Santa Fe, Judicial SF, Santa Fe capital y ENERSA: se consultan nuevamente con los mismos plazos y TLS validado. No se cambian certificados, identidad ni permisos para evitar timeout/403/TLS. Un fallo sigue registrado como fallo.

Los plazos absolutos por fuente y global no se aumentaron. Un listado completo no significa que todos los datos comerciales estén completos: eso se informa en los contadores de calidad, independiente de OPERATIVA/PARCIAL. El workflow diario mantiene su horario y sólo persiste producción en main; esta rama ejecuta verificación aislada y pruebas.
