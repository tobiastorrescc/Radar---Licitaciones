# Radar: auditoría real y mejoras del 30/10/2026

Trabajo sobre PR #1, `mejora/radar-auditable`, partiendo de `0b89c24` y comprobando los dos commits automáticos posteriores. No se modifica main, producción ni sus respaldos. No se activa correo. No se calcula rentabilidad ni se recortan oportunidades.

## Ejecución automática y continuidad

La [ejecución diaria 41048293524](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41048293524) terminó correctamente. El despacho ocurrió a las **08:28 de Argentina**, frente al cron solicitado a las 08:00. La supervisión terminó correctamente, aunque GitHub la inició a las **10:32**, frente a las 09:30 previstas. GitHub Actions puede retrasar los cron: no garantiza puntualidad. No se observó una segunda consulta diaria duplicada.

Se conservaron los 3.697 registros de la base anterior: el estado diario contiene **4.450 procedimientos y 4.728 versiones**, sin repeticiones como novedades. El respaldo durable conserva cuatro segmentos; el nuevo segmento es `000003-5cc18ba9256911e9cb1828a8873329926aa83b59d1cb631bb36b28aaff727c42.json.gz`. La auditoría aislada de esta etapa no escribe en ese historial. Se corrigió además el archivado del workflow de auditoría: requiere autorización explícita mediante su parámetro y no sobrescribe la auditoría anterior por defecto.

Resultado diario: **0 publicaciones nuevas con fecha comprobada; 27 primeras detecciones sin fecha; 726 recuperaciones de línea de base; 38 modificaciones; 180 datos completados y 3.166 sin cambios**. Estos números no se sustituyen retroactivamente por los resultados del nuevo analizador.

## Resultados comerciales comprobados

| Indicador | Antes | Después comparable |
|---|---:|---:|
| Fuentes operativas | 38 en auditoría anterior | 39 en corrida diaria |
| Fuentes parciales / bloqueadas / pendientes / sin publicaciones confirmadas | 14 / 14 / 10 / 1 | 13 / 14 / 10 / 1 |
| Pagos verificados, misma ventana de 73 abiertas | 3 (4,1 %) | **7 (9,6 %)** |
| Pagos pendientes, misma ventana | 70 | **66** |
| Contado o contra entrega comprobado | — | **1** |
| Anticipos / plazo numérico hasta 15 días comprobados | — | **0 / 0** |
| Fuentes nuevas incorporadas en esta etapa | — | **0** |

La comparación de pagos usa exactamente la misma ventana del 30/10 a las 16:15, sin ampliar artificialmente el porcentaje. El reporte reunido de todas las capturas contiene **116 oportunidades calculadas como abiertas**, con **7 pagos verificados y 109 pendientes**; no significa que las 116 hayan podido consultarse nuevamente. En la cohorte comparable de 73, **49 fueron observadas en la corrida diaria y 24 se conservaban solamente por historial**. La apertura futura es evidencia temporal, no confirmación de ausencia de suspensión posterior.

Las fichas comparables tienen objeto en 73 casos, cantidades estructuradas en 3, presupuesto en 34 y documentos asociados en 17. Solo **una** tiene simultáneamente objeto, cantidades, presupuesto y documento: sigue siendo una limitación importante.

Se separaron días hábiles/corridos, evento inicial, anticipos y pagos parciales. Una condición verificada sin plazo determinado conserva investigación pendiente. El tiempo efectivo hasta acreditación y recuperación del capital permanece desconocido. Contra entrega no se equipara a acreditación inmediata.

### Ejemplos documentales

- **Chajarí, Licitación Pública 19/2026**: repuestos originales para trenes de rodaje de excavadoras New Holland y Komatsu; **13 renglones**, presupuesto publicado **$59.500.000**, apertura **19/11/2026 a las 10:00**, pago literal **“Contado contra entrega”** en página 4, artículo 12, y página 6. La revisión visual corrigió un OCR que leía siete rodillos superiores Komatsu: son **cuatro**. [Ficha completa con cantidades y evidencia](chajari_19_2026.md). [Portal oficial](https://licitaciones.chajari.gob.ar/licitaciones?state=para_apertura?id=710). El documento se obtiene mediante el endpoint oficial `return_file`, no mediante una URL estática inventada.
- **Crespo, Pública 6/2026**: **20 días hábiles desde presentación de factura**. [Pliego oficial](https://www.crespo.gob.ar/wp-content/uploads/2026/10/LICITACION-PUBLICA-No-06-26-Pliego.pdf).
- **IAFAS, Pública 5/2026**: **30 días corridos desde recepción de documentación**, con entrega aceptada, factura y aprobación administrativa como condiciones previas; facturación mensual a mes vencido. Se recompuso el artículo 15 entre páginas 5 y 6. [Documento oficial](https://www.iafas.gov.ar/descargas/17685). La especificación solicita seis IP públicas y admite catorce como alternativa: quedan separadas.
- **IAFAS, Privada 8/2026**: entrega aceptada, factura y aprobación administrativa; **plazo numérico no publicado** en la cláusula comprobada. Se separó el mantenimiento opcional del pago de la provisión principal. [Documento oficial](https://www.iafas.gov.ar/descargas/17688).
- **Aeropuerto Rosario, Directa 52/2026**: 30 días desde recepción conforme. [Documento oficial](https://aeropuertorosario.com/wp-content/uploads/2026/10/DOC-2026-00012875-APPSF-ODAeroRos.pdf).

Los siete casos y sus páginas, citas y huellas documentales están en [pagos_verificados.json](pagos_verificados.json). No se aceptó como pago comprobado la frase “Oferta por pago contado” de Concepción del Uruguay: puede ser una opción de oferta, no una obligación del organismo.

## Nuevas detecciones, fuentes y duplicados

Rosario pasó de **34 fichas en la captura diaria a 67 en la revisión puntual**, mediante modalidades comprobadas y normalización de paginación. Continúa parcial: respuestas y detalles pendientes impiden declarar cobertura completa. De las 43 identidades ausentes en el estado diario, 34 ya figuraban en la auditoría anterior y **nueve son primeras detecciones respecto de ambas bases**. Ninguna tiene fecha de publicación comprobada: no se declaran nueve publicaciones nuevas. Todos los casos, objetos, fechas de apertura y enlaces se conservan en [recuperacion_rosario.json](recuperacion_rosario.json).

De las **65 detecciones sin fecha** de la auditoría anterior, **21 reaparecieron en el estado diario y 44 solo constaban en aquella captura**. Se conservaron sus evidencias y primeras/últimas observaciones. Además, diez recuperaciones clasificadas anteriormente por la línea de base carecían de evidencia suficiente para considerarlas históricas: la nueva regla las reconoce como primera detección con fecha pendiente, sin reescribir eventos antiguos ni volver a alertarlos.

Se revisaron seis unificaciones de Federación: **cinco están justificadas documentalmente**. La restante corresponde al mismo expediente 8/2026, pero el propio documento contiene fechas de apertura contradictorias; se conserva el conflicto y no se elige una fecha. Las circulares de VGG 26/2026 se vinculan al procedimiento original, conservando registros y documentos. Un cambio de huella del documento invalida datos extraídos anteriormente hasta su nueva comprobación, conservando el valor previo.

**EPE sigue devolviendo HTTP 500 y Compras Santa Fe agota el tiempo.** No se declara que carezcan de publicaciones, ni que el error sea un bloqueo permanente. Los restantes estados y sus causas individualizadas están en el [informe por organismo](cobertura_organismos.csv), con fecha y origen de cada observación. Se inventarían 79 portales de 73 organismos; 77 fuentes están monitoreadas. No equivale a cobertura territorial exhaustiva.

Se reconsultaron **114 URLs candidatas únicas** en dos lotes disjuntos de 100 y 14: **cero nuevas validadas, cero incorporadas, 114 pendientes**. El inventario contiene 115 URLs únicas, incluida una previamente validada. El buscador exigió verificación humana; no se eludió. No se agregaron fuentes por responder HTTP sin probar publicaciones. [Detalle de candidatas](revision_candidatas.json).

## Validación y consulta diaria

Se ejecutaron pruebas de regresión para cláusulas, caché OCR, fechas, documentos modificados, cantidades alternativas, duplicación y salida de procesos sin bloqueos. La prueba local final pasó **328 pruebas, con una omitida por restricción de sockets del entorno**; la validación completa de GitHub Actions queda vinculada al commit de cierre del PR.

La [auditoría documental real 41114667560](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41114667560) terminó correctamente: siete pagos verificados. Reprocesó evidencia capturada en la [auditoría 41113619206](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41113619206), **sin red ni OCR nuevos**, sin escribir el historial. Las consultas reales adicionales constan en las ejecuciones 41110430956, 41108048884 y 41112640791. El acceso a internet del entorno local estaba restringido; las comprobaciones de portales se hicieron desde Actions.

Consultar [todas las abiertas de las capturas](abiertas_todas_las_capturas.md), [sus fichas completas](fichas_todas_las_capturas.md), [métricas](metricas.json) y el reporte diario habitual en `piloto_reportes/ultimo`. No se limita a un top. Los informes separan nuevas comprobadas, primeras detecciones sin fecha, modificaciones, recuperaciones históricas y próximos vencimientos. Se conserva la preparación de correo `.eml` con adjuntos completos, **sin destinatarios, credenciales ni envío activados**. El envío futuro puede utilizar una cuenta SMTP ya disponible desde Actions, sujeto a autorización y límites de su proveedor; no requiere servidor contratado.

## Pendiente para un funcionamiento plenamente operativo

Recuperar las 14 fuentes bloqueadas o inaccesibles, 13 parciales y 10 pendientes; comprobar documentos en las 109 abiertas sin pago verificado del conjunto reunido; conseguir fechas de publicación y vigencia actual de los registros no reobservados; resolver la fecha contradictoria de Federación; mejorar la búsqueda oficial sin depender del buscador bloqueado y validar territorialmente municipios, comunas y organismos sectoriales faltantes. No hay evidencia para declarar cobertura completa ni garantía de puntualidad exacta del cron de GitHub.
