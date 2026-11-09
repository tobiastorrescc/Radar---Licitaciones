# Fase 4: avance comprobado de descubrimiento — 9/11/2026

**Resultado: una compra a proveedores vigente que no estaba en el catálogo, más una convocatoria de venta de bienes municipales. Cero publicaciones recientes nuevas confirmadas. La fase territorial exhaustiva no está completada y no se alcanzó la meta de diez oportunidades diarias.**

## Convocatorias adicionales, sin confundir publicación y descubrimiento

1. **Comuna de María Teresa: concurso de precios para 200 cajas navideñas.** Publicación oficial: 26/10/2026. Recepción: **10/11/2026, 11:00 Argentina**, sobre cerrado, Restituto Alejandre 235. No publica número de procedimiento ni presupuesto. Solicita que el oferente detalle sus condiciones; **no acredita pago contado**. Aviso: https://mariateresa.gob.ar/index.php?pagina=detalle&idp=859 . El lector lo encontró navegando desde la portada institucional, sin depender de un pliego ni de la categoría de licitaciones. Fecha de primera detección en la prueba comparativa: 9/11/2026 09:44 Argentina; no es su fecha de publicación.
2. **Municipalidad de Ceres, Licitación Pública 54/2026: venta y adjudicación de tres lotes municipales.** Recepción: **17/11/2026, 08:30 Argentina**; apertura 09:00. Documento oficial: http://ceres.gob.ar/wp-content/uploads/2026/10/PLIEGO-DE-BASES-Y-COND-VENTA-3-LOTES-LIC-054-2026.docx.pdf . Publicación: desconocida; no se infiere de la carpeta del documento. **Es una venta municipal, no una compra a proveedores: no se utiliza para inflar la métrica de oportunidades de suministro.** Se conserva visible en el catálogo y CSV completos.

Ambos procedimientos estaban ausentes de la copia inicial del historial (6.771 registros) y del índice persistente de auditorías anteriores. Son primeras detecciones vigentes, no publicaciones nuevas de las últimas 72 horas.

Una oportunidad conocida de **Rosario, LP 58/2026**, recuperó comprobación de recepción vigente hasta 16/11/2026 09:00: https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38744 . Se informa como recuperación conocida, nunca como oportunidad inédita.

## Comparación reproducible

La referencia de 94 fuentes/26 oportunidades corresponde a una ejecución anterior. Al comenzar, la rama tenía **96 fuentes efectivas**: el proceso automático anterior ya había añadido los boletines de Colón BA y General Ramírez ER. Esas dos altas no se atribuyen a este trabajo.

| Indicador, mismo barrido nativo y criterios | Antes medido | Después medido |
|---|---:|---:|
| Fuentes configuradas y consultadas | 96 | 101 |
| Operativas, incluida ausencia comprobada | 44 | 47 |
| Parciales | 29 | 31 |
| Inaccesibles | 15 | 15 |
| Pendientes | 8 | 8 |
| Convocatorias con recepción vigente explícita en las capturas | 21 | 23 |
| Compras vigentes inéditas para el catálogo | — | 1 |
| Otras convocatorias vigentes inéditas: venta municipal | — | 1 |
| Publicaciones nuevas recientes confirmadas, 24/48/72 h | — | 0/0/0 |
| Omisiones corregidas en los dos controles nuevos | 0/2 detectados | 2/2 detectados |
| Control Rosario heredado | 53/53 | 53/53 |
| Novedades / eventos repetidos en segunda pasada | — | 0 / 0 |

El informe que combina la observación actual con los campos ya comprobados en el historial contiene **28 convocatorias con recepción vigente**, frente a 25 del último informe diario preservado. Las 21/23 de la tabla son evidencia extraída en las capturas sin esa combinación: son métricas distintas. Los tres casos adicionales son las dos primeras detecciones y la recuperación conocida mencionadas arriba. El número 28 incluye la venta municipal, señalada expresamente.

No se contabilizan como novedades comerciales los 210 antecedentes recuperados en la comparación incremental, 40 modificaciones ni nueve registros completados. Las 22 primeras detecciones sin publicación comprobada tampoco son automáticamente vigentes: sólo dos superaron la validación de recepción. Ningún resultado se recorta a un top-N.

## Fuentes incorporadas y estado real

| Organismo / ruta oficial | Estado nativo | Resultado y límites |
|---|---|---|
| El Trébol — https://eltrebol.gov.ar/tipo_licitaciones/licitacion-publica/ | Operativa | Extracción comprobada, 203 registros crudos; ninguna recepción vigente nueva comprobada |
| El Trébol — https://eltrebol.gov.ar/licitaciones-y-contrataciones/ | Operativa | Ruta complementaria, 155 registros crudos; deduplicados, no se suman como convocatorias únicas |
| Arrecifes — https://arrecifes.gob.ar/informacion-publica/boletin-oficial/ | Operativa | Boletín institucional con extracción; sin oportunidad vigente inédita comprobada |
| Ceres — https://ceres.gob.ar/compras/ | Parcial | Ocho registros crudos, documento 54/2026 con recepción comprobada; no se declara recorrido completo |
| María Teresa — https://mariateresa.gob.ar/ | Parcial | Dieciséis registros crudos durante el presupuesto de fuente; compra de cajas recuperada desde noticias; navegación pendiente de completar |

Son **cinco rutas y cuatro organismos**, no cinco municipios nuevos: Arrecifes ya tenía otra fuente. Tres rutas se incorporaron mediante la validación automática estricta. Las otras dos se añadieron al monitoreo como parciales después de prueba nativa e identidad oficial, sin llamarlas operativas. No se añadió automáticamente la ficha individual de María Teresa: queda como control, y se monitorea su portada para descubrir avisos futuros.

Los cuatro lotes consultaron 40 URLs candidatas distintas, además del barrido completo de 96 fuentes. Los buscadores aportaron 16 candidatos automáticos nuevos en total; su existencia no acredita identidad, utilidad ni cobertura. La cola queda con 194 URLs únicas, 187 todavía pendientes. Las semillas investigadas explícitamente están separadas en `tools/fase4_semillas.json`. No se declara completada ninguna provincia ni los 19 departamentos por haber generado sus consultas.

## Correcciones que explican los hallazgos

- Tarjetas de Ceres con rótulos abreviados «Lic 054-2026»: adaptador reutilizable, lectura PDF nativa y refinamiento del tipo desde el documento enlazado, conservando número, año, texto y procedencia. Se acota el objeto sin perder el texto documental.
- Noticias comunales sin número ni pliego: lector del artículo municipal completo, recepción explícita y publicación separadas, identidad estable por ficha oficial aunque cambie el orden de parámetros de URL. Se conserva la documentación desconocida como pendiente.
- Validación de identidad mediante portada oficial y enlaces institucionales de ubicación publicados; no se toma el dominio como única prueba. Distancia geodésica no se usa como sustituto de distancia vial para nuevas localidades bonaerenses.
- Búsquedas territoriales: rotación 2 Santa Fe / 1 Entre Ríos / 1 Buenos Aires, consultas de los 19 departamentos y descarte de resultados ajenos a la localidad. Se agregó la descripción del resultado y se mantiene la cola persistente.
- Se detectó y retiró un falso portal automático de Arrecifes: «felicitaciones-titan» coincidía por subcadena con «licitaciones». Ahora se exigen límites de palabra. Se quitó únicamente esa alta de configuración; no se borró ninguna oportunidad del historial.
- Ventanas 24/48/72 h calculadas con precisión temporal explícita: una fecha sin hora no se trata como medianoche inventada. Se separan coincidencias posibles y comprobadas.
- Descubrimiento y revalidación tienen procesos y presupuestos independientes. El último lote dedica 160 s al descubrimiento y difiere la revisión secundaria; no vuelve a consultar indefinidamente los mismos fallos ni bloquea el piloto.

## Bloqueos y cobertura pendiente

- **EPE:** reinicio de conexión y EOF durante negociación TLS en las rutas oficiales configuradas; cero procedimientos actuales extraídos en esta prueba. No se desactiva TLS ni se declaran vigentes los antecedentes pendientes.
- **Gestiones de Compras:** agotamiento del tiempo en el portal y ruta oficial de exportación configurada; cero procedimientos extraídos. El importador CSV/HTML existente sigue disponible.
- **Boletín Oficial Santa Fe:** timeout también al intentar las ediciones oficiales configuradas; cero avisos extraídos automáticamente en esta prueba. Los importadores oficiales HTML/PDF siguen disponibles. Ramayón continúa como regresión histórica, no como convocatoria vigente.
- **Compras UNR y Cañada de Gómez:** HTTP 403. No se eluden restricciones ni se afirma ausencia de convocatorias.
- **Aeropuerto Rosario:** extracción parcial, 153 registros antes del límite de 120 s. **ASSA** y **Poder Judicial ER** sí conservaron extracción nativa operativa (4 y 59 registros crudos, respectivamente).
- El buscador alternativo devuelve desafíos de verificación humana y el buscador RSS devuelve resultados insuficientes o ajenos. Se registran los fallos, sin eludir el desafío. Esto limita el descubrimiento completamente autónomo; no se atribuye automáticamente el bajo volumen a falta de publicaciones.
- No hay altas nuevas operativas de Entre Ríos en estos lotes. Larroque, Urdinarrain, Ibicuy y otras candidatas conservan el estado individual que figura en el CSV. Buenos Aires añadió una ruta complementaria de Arrecifes, no una cobertura territorial completa.
- Las **112 aperturas pendientes** se conservan separadas en CSV. No se les atribuye vigencia comercial ni se afirma que fueron resueltas en este lote.
- La muestra manual nueva comprende dos casos de Santa Fe y el control heredado de Rosario. **No equivale a una auditoría manual exhaustiva de siete días de las tres provincias.** La siguiente iteración debe ampliar ese control, priorizar las fuentes críticas con archivos oficiales y revisar las candidatas con extracción parcial verificable.

## Evidencia y ejecución

- Barrido de las 96 fuentes: https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42615182790
- Primer lote territorial: https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42616347170
- Extracción Ceres y altas automáticas: https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42617716565
- Controles y depuración de falso portal: https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42618519935
- Extracción nativa María Teresa: https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42619310716 . Su tarea de descubrimiento fue correcta; la tarea secundaria diferida falló al escribir un directorio inexistente. Fue corregido y tiene regresión específica.
- Comparación final nativa, pruebas y segunda pasada: https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42621183825

La primera ejecución del cierre no tenía instaladas las dependencias PDF y XLS usadas por las pruebas existentes. Se corrigió el workflow aislado; no se relajaron los tests ni se instaló OCR nuevo. El cierre nativo 42621183825 terminó **correctamente**, con 490 pruebas Python (una omitida) y 28 pruebas Node aprobadas. El artefacto `fase4-comparacion-42621183825` fue descargado y comprobado: mismas dos convocatorias adicionales, una compra y una venta; segunda pasada con cero novedades y cero eventos.

Archivos entregados: `nuevas_verificadas.json` (evidencias por campo), `nuevas_vigentes_completo.csv`, `convocatorias_vigentes_completo.csv` y Markdown, `fuentes_consultadas.csv`, `candidatas_revisadas.csv`, `control_omisiones.json`, `control_rosario.json`, `pendientes_revalidacion_112.csv`, `resultado.json`, `lotes_descubrimiento.json` y `proteccion.json`.

Se reutilizaron exclusivamente capturas y documentos ya obtenidos para el contraste y las segundas pasadas. Cero OCR nuevo. La restauración se realiza en `work/`; no sobrescribe respaldos ni datos del piloto. Se comprueba el árbol inicial completo y se enumeran las únicas modificaciones de archivos preexistentes. `main` permanece en `c4c44de`; producción, informes del piloto, respaldos, despliegue y workflows anteriores no cambian. Los nuevos workflows son aislados, sin cron. El PR #1 permanece abierto y no fusionado.
