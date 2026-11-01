# Meta conjunta y auditoría de las tres provincias

**La meta es un promedio de20 oportunidades genuinamente nuevas por día entre Santa Fe, Entre Ríos y Buenos Aires cercana a Rosario juntas. No son20 por provincia ni un límite de resultados.** Depende del volumen real de publicaciones y de la cobertura comprobada. Una prueba con80 novedades sintéticas confirma que se conservan las80: no son80 hallazgos reales.

Validación real:01/11/2026 UTC, con fecha de observación31/10/2026 23:34, hora argentina. Se consultaron11 fuentes en vivo; el piloto comparativo reutilizó además capturas anteriores, hasta reunir48 URLs. **No fue una consulta en vivo completa de las82 fuentes configuradas ni una auditoría exhaustiva de las tres provincias.** No se repitió OCR.

## Resultado comprobado

| Provincia | Nuevas confirmadas | Abiertas observadas en capturas | Abiertas sólo por historial | Vigencia pendiente del catálogo | Pago rápido documentado en abiertas | Omisiones / avisos de control |
|---|---:|---:|---:|---:|---:|---:|
| Santa Fe | 0 | 9 | 99 | 762 | 0 | 2/3 |
| Entre Ríos | 0 | 33 | 21 | 1341 | 2 | 0/2 |
| Buenos Aires dentro del alcance | 0 | 1 | 0 | 234 | 0 | 0/3 |
| Total | **0** | **43** | **120** | **2337** | **2** | **2/8** |

Las43 abiertas tienen fecha futura calculada y fueron observadas en las capturas utilizadas; algunas capturas son anteriores. No se afirma haber revalidado en vivo las43 ni que las120 conservadas por historial sigan vigentes. Los pendientes tampoco se presentan como oportunidades comerciales abiertas.

La primera pasada comparativa produjo4 primeras detecciones sin fecha suficiente,2 modificaciones y18 recuperaciones de línea de base. **Ninguna integra las nuevas confirmadas ni la meta20.** Las4 detecciones requieren revisión: dos referencias históricas de Armstrong, una página general de San Nicolás y una noticia antigua de Seguí. No se anuncian como cuatro convocatorias nuevas genuinas.

Las20 convocatorias abiertas encontradas por el lote en vivo (1UNR y19 de Entre Ríos, unificadas sus referencias compartidas) ya estaban representadas en el catálogo accesible de la etapa anterior. No se vuelven a contar las7 recuperaciones previas como inéditas. No hubo nuevas fuentes validadas en esta etapa.

Hay4 días con ejecuciones disponibles para las métricas: promedio confirmado observado0,0. **El promedio de7 días queda pendiente**, sin imputar los días ausentes como ceros. Esta medición no establece que el volumen oficial haya sido cero: persisten fuentes bloqueadas y publicaciones sin fecha comprobada.

## Muestra manual y omisiones

Se contrastaron8 avisos oficiales, con URLs, fechas, campos comprobados y método conservados en [auditoria_manual.json](auditoria_manual.json) y [CSV de contraste](contraste_manual.csv). Es una muestra dirigida, incluye controles históricos y no permite extrapolar cobertura global.

- Santa Fe: UNR5/2026, obra de aulas, está detectada. El concurso de nomencladores de Cañada de Gómez, recepción10/11/2026 09:00, sigue omitido por HTTP403. RamayónLP01/2026, apertura08/10/2026, sigue omitida por inaccesibilidad del boletín: **es histórica, no una oportunidad vigente**. Las2 omisiones incluyen por tanto1 convocatoria con apertura futura y1 control histórico.
- Entre Ríos: Seguí9/2026 (retroexcavadora, apertura03/11) y El Pingo2/2026 (dos garitas, recepción10/11, apertura11/11) están detectadas. Se reutilizaron textos documentales oficiales de la auditoría anterior, sin descargarlos ni procesarlos otra vez para el control manual.
- Buenos Aires: Colón11/2026, BaraderoLP1/2026 y RojasLP7/2021 están registrados. En Colón se reutilizó el OCR persistido del aviso: terminación de16 viviendas, apertura24/11/2026 10:00, presupuesto publicado$333.031.337,04; el HTML confirma número y publicación19/10. Baradero conserva objeto del servicio alimentario, con vigencia pendiente. Rojas7/2021 es un control histórico. Encontrar los tres no demuestra cobertura actual exhaustiva de esas localidades.

Antes y después de esta mejora, el catálogo accesible reconoce **6/8** avisos de esa muestra. Se corrigió la medición y la rotación; no se declara que esas correcciones hayan recuperado todavía las dos omisiones.

## Consulta real de fuentes

[CSV de las11 consultas en vivo](fuentes_consultadas_en_vivo.csv):

- Operativas en el alcance de extracción ensayado: UNR, BoletínER, Baradero y Rojas (4). Rojas recupera un archivo antiguo y Baradero tiene vigencias pendientes: operativo no equivale a cobertura actual completa.
- Parciales: Seguí, San Nicolás y ColónPBA (3). Persisten adjuntos sin texto, fichas incompletas e imágenes que no se reprocesaron.
- Errores de acceso: BoletínSanta Fe, ComprasSanta Fe, EPE y Cañada de Gómez (4). Timeout, TLS/HTTP500 y HTTP403 permanecen registrados. No se informa «sin novedades» por esas fallas.

Además se comprobó el enlace oficial de San Nicolás a `http://www.sannicolas.gov.ar:8080/portalcompras/`. La conexión agotó5,63segundos en [Actions41266080077](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41266080077). Queda en la cola persistente de candidatas con su evidencia; no se incorpora como fuente fiable ni se elude ninguna restricción.

El piloto comparativo reúne48URLs, incluyendo capturas previas:26 deSantaFe,17 deEntreRíos y5 deBuenosAires. En ellas hay19,9 y3 incidencias respectivamente; **estas cifras no son31 fallas en una consulta diaria nueva de48 fuentes**. Los errores concretos y la fecha de cada captura están en las auditorías del artefacto.

## Qué cambió

1. Se fijó el alcance permanente de las tres jurisdicciones y la meta comercial conjunta en [ALCANCE_Y_METRICAS.md](../../ALCANCE_Y_METRICAS.md) y en la política del radar. Se preservan las82 fuentes y el padrón territorial (364 registrosSF,239ER y51BA); el padrón no prueba cobertura y las distancias viales pendientes siguen pendientes.
2. El descubrimiento periódico mantiene también las localidades con un conector operativo en la rotación, y revisa sus portales institucionales. Un archivo histórico extraído correctamente ya no basta para excluir una localidad de la búsqueda de fuentes complementarias. Se conserva la cola y los límites existentes.
3. El informe diario HTML, Markdown, JSON y correo preparado incluye total y desglose de nuevas confirmadas; abiertas observadas y retenidas; omisiones de la muestra; pago rápido documentado; fuentes con incidencias y vigencias pendientes. Los CSV incorporan provincia y localidad.
4. El contador usa todas las ejecuciones del día argentino, deduplica por identidad y exige `NUEVO_CONFIRMADO` con fecha publicada comprobada reciente. Históricas, cambios y primeras detecciones sin fecha no computan. Con fecha sin hora se incluye completo el día inicial de la ventana reciente, sin inventar una hora.
5. Los días sin ejecución se distinguen de días observados con cero confirmadas. El promedio semanal queda pendiente si faltan días; no se promete volumen editorial ni recuperación inmediata de capital.
6. Las auditorías se componen por URL, preservando la última captura cuando una candidata pasa a tener ID de fuente incorporada. Una ejecución intermedia detectó el choque de la claveSQLite al combinar ambos IDs; se corrigió y se agregó una regresión con INSERT real en una base temporal. No se modificó el historial de producción.

## Pago documentado reutilizado

Se cuentan Chajarí19/2026 (contado contra entrega, cláusula del pliego conservada, páginas4/6) y LaPaz39/2026 (10días hábiles desde entrega y presentación de factura, apertura04/11). El respaldo de Chajarí incluye la descarga pública POST `return_file` y su hash, conservados en la ficha: la URL de la página no es por sí sola el PDF. Se reutiliza evidencia existente, no una nueva validación comercial. Diez días hábiles no son diez días corridos ni garantía de acreditación bancaria inmediata. No se calculó rentabilidad.

## Validación y conservación

- [Barrido real de11 fuentes41265639687](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41265639687).
- [Piloto y métricas finales41266487895](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41266487895), sobre la base publicada41237677685. Se abrió y revisó el informe generado, no sólo el estado verde deActions.
- Primera pasada:2442 observaciones,24 eventos, de los que6 son detecciones inciertas o modificaciones y18 recuperaciones. Segunda pasada: **0 novedades y0 eventos repetidos**. Se conservan5479 filas históricas. El contador genuino es0 en ambas y no se reinicia al repetir el informe.
-385 pruebas automatizadas; localmente384 aprobadas y1 omitida por dependencia opcional. Actions instala las dependencias y ejecuta la suite completa. Incluye80 novedades sintéticas sin recorte, separación de categorías, reloj argentino, pago con evidencia, omisiones por provincia, siglas documentadas y persistencia al cambiar ID de candidata.
- `produccion_intacta=true` y `respaldo_intacto=true`. Main, programador, workflow diario y respaldos no se alteran; el PR#1 permanece abierto. Sólo se ajustó el workflow aislado de auditoría para seleccionar correctamente la última base. Sin envío de correo, credenciales, servicios pagos, OCR nuevo ni análisis de costos/rentabilidad.

## Entrega y próximos pasos

[Resumen por provinciaCSV](resumen_provincias.csv) · [Todos los24 eventosCSV](oportunidades.csv) · [Eventos y categoríasJSON](oportunidades.json) · [Informe diario generado](informe_diario_generado.md) · [MétricasJSON](metricas_territoriales.json) · [Resultado de repetición](piloto_comparativo.json). El artefacto de la ejecución contiene el árbol completo de fichas y documentos auxiliares enlazados por el informe. Los CSV no se recortan a20 ni excluyen rubros, montos o pagos.

La meta comercial no está acreditada. Falta recuperar especialmente el portal/BoletínSantaFe que publica Ramayón, EPE y Cañada; ampliar el control manual independiente en cada jurisdicción; resolver las fuentes parciales bonaerenses y comprobar fuentes complementarias actuales donde sólo aparece archivo. La programación existente generará las nuevas métricas en las siguientes ejecuciones del piloto; no se declara cobertura exhaustiva alcanzada ni se activa producción.
