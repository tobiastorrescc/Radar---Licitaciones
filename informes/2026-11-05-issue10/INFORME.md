# Issue #10 — resultados comprobados del Radar

Trabajo sobre PR #1, rama `mejora/radar-auditable`. Sin merge ni cambios en `main`, producción o programador. El respaldo automático del 5/11 se conservó al publicar sobre su commit `94bf5fc`.

## Resultado comercial al cierre

**36 oportunidades vigentes, inéditas respecto del historial diario del 2/11**, sin duplicados, todas con objeto y enlace oficial al pliego. Ocho tienen publicación oficial del **5/11**; las demás fueron publicadas del 2 al 4/11 y se recuperaron tardíamente. No se presentan las 36 como publicaciones de un solo día.

Cálculo de plazos: **2026-11-05T11:52:17.429575-03:00**. Se utilizan observaciones oficiales del mismo día; recalcular la fecha no equivale a otra consulta web. Se retiraron del listado comercial dos convocatorias de la auditoría nocturna ya vencidas, sin borrarlas del historial.

- [Todas las oportunidades vigentes, CSV](nuevas_confirmadas_vigentes.csv).
- [Listado completo con enlaces](nuevas_confirmadas_vigentes.md).
- [Los 64 avisos del último control, incluidos conocidos y pendientes](rosario_control_integral_64.csv).

La unión elimina coincidencias entre auditoría nocturna, corrida diaria y control posterior. Las 25 nuevas del corte nocturno, las 15 publicaciones clasificadas como nuevas en la corrida diaria y las 13 detectadas después **no se suman**. Entre aquellas 15 había dos vencidas y una de vigencia desconocida: el informe publicado ya se corrigió para separarlas.

Todas las nuevas cotizables verificadas de esta entrega corresponden a Santa Fe/Rosario. No se encontraron nuevas cotizables fechadas que puedan sumarse para Entre Ríos o Buenos Aires en estos lotes. Esto **no demuestra falta de publicaciones** en esas provincias: persisten fuentes parciales, inaccesibles y fechas desconocidas.

Las condiciones de pago de las 36 nuevas permanecen pendientes de verificar. No se inventaron anticipos, pago contado, cantidades ni rentabilidad. Los enlaces a pliegos se identifican por el rótulo de la ficha oficial; su publicación no certifica una descarga nueva del documento.

## Mejora efectiva de Rosario

| Medición | Resultado |
|---|---:|
| Fichas distintas en la extracción inicial nocturna | 48 |
| Fichas obtenidas después de corregir navegación | 63 |
| Avisos del control real final | 64 |
| Objetos conservados en ese control | 64 |
| Fichas con fecha de publicación extraída en ese control | 45 |
| Nuevas para el estado diario en el control final | 13 |
| De esas 13, publicadas hoy | 8 |
| De esas 13, rezagadas con publicación anterior al 5/11 | 5 |

La corrida diaria había recuperado 49 avisos de Rosario y agotado sus 60 segundos. Ahora Rosario tiene presupuesto propio de **240 segundos**, manteniendo el límite total de la ejecución. La prueba real final terminó en **236 segundos** y obtuvo 64 avisos. Se mantienen reintentos acotados y hasta tres consultas simultáneas de fichas. La fuente sigue **PARCIAL** por fallos individuales: 19 fichas de ese control no aportaron fecha de publicación.

No se atribuye toda diferencia de cantidad al código: el portal recibió publicaciones entre las consultas. Sí quedan documentadas cinco convocatorias anteriores al 5/11 recuperadas después del escaneo matutino, y ocho publicaciones de hoy.

## Qué se corrigió

1. Se conectó el lector de fichas Drupal de Rosario al descubrimiento cotidiano; antes sólo se utilizaba en una revisión documental manual.
2. Se separó la cola de fichas de la paginación, se siguen páginas reales sin el antiguo supuesto de cuatro páginas y se compara lo extraído con los contadores por modalidad.
3. Se reconocen timeouts envueltos en `URLError`, conservando resultados parciales. Un portal fallido nunca equivale a «sin novedades».
4. El objeto publicado se conserva aunque falle la ficha. El identificador del listado no se presenta como número de contratación comprobado; permanece pendiente hasta leer la ficha.
5. La identidad por ficha oficial mantiene el historial al corregir expediente/número y evita oportunidades separadas por anexos. No fusiona dos fichas diferentes con igual número.
6. Se siguen los botones «Ver detalle» del nuevo portal del Concejo. Extrae dos procedimientos vencidos; ninguno se ofrece como novedad vigente. El sitio antiguo continúa con error de certificado.
7. Planeamiento ER separa avisos estructurados y registra presupuestos/fechas sin exigir número o PDF. Recepción de cotizaciones es límite de presentación, no fecha de apertura.
8. Se sincronizó el inventario que realmente consulta el piloto: cinco rutas configuradas antes no se ejecutaban. Se mantiene un alias de Compras Ágiles dentro del conector principal para evitar otro organismo duplicado.
9. Se reparó el descubrimiento territorial: una entrada de Chabás sin `codigo` detenía todo el proceso. Se usa una clave interna estable, sin inventar códigos oficiales ni alterar los existentes.
10. Se corrigió `preparar_entrega.py`, que genera el informe realmente publicado: nuevas vencidas/inciertas y antecedentes quedan en auditoría, con CSV/JSON íntegros. El informe principal sólo muestra convocatorias con plazo abierto. Los llamados especiales se ordenan primero.
11. La validación HTML no depende de instalar OCR. Una instalación documental agotó cuatro minutos; el control se repitió en modo liviano con capacidades explícitas y sin fingir extracción PDF/XLS donde faltan lectores.

## Corrida automática real del 5/11

[Run 42021794797](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42021794797): despacho 08:47 ART, resumen del escaneo 08:55 ART. El cron de GitHub se retrasó respecto de las 08:00 configuradas. No se cambió su programación.

| Cobertura estricta | 2/11, antes | 5/11, corrida diaria |
|---|---:|---:|
| Fuentes consultadas | 83 | 88 |
| Operativas | 40 | 41 |
| Parciales | 23 | 25 |
| Inaccesibles | 12 | 14 |
| Pendientes | 7 | 7 |
| Sin publicaciones confirmada | 1 | 1 |

Las dos inaccesibles adicionales son rutas antes no consultadas: el Concejo antiguo (TLS) y Gestiones de Compras (timeout). No son dos fuentes antes operativas que se hayan perdido.

El **job de escaneo y respaldo terminó correctamente**: 4.823 registros anteriores, 5.920 posteriores, cero IDs/versiones perdidos y cero repeticiones como nuevas. Se guardó el segmento incremental `000007-3d682cb432feee02eb60eccda8f054cd5abd3402b90b49635ce09853e3b3c3a0.json.gz`.

El workflow completo quedó en rojo por el job posterior de descubrimiento (`KeyError: codigo`). Las alertas de finalización/supervisión se ejecutaron y señalaron ese fallo. La corrección ya está publicada y el descubrimiento real aislado terminó correctamente. **Falta confirmar una próxima corrida diaria integral en verde**; no se cambia retroactivamente el estado del run fallido.

[CSV de cobertura de las 88 fuentes](cobertura_diaria_88.csv). [CSV íntegro guardado automáticamente por el piloto](https://github.com/tobiastorrescc/Radar---Licitaciones/blob/94bf5fc963cf4df81cd09357264206b5727c9976/piloto_reportes/ultimo/oportunidades.csv), con las categorías y vigencias originales. No se sobrescribió ese informe histórico al corregir su generador.

## Descubrimiento periódico y límites

[Validación real 42045949031](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42045949031): 36 candidatas consultadas, una revalidada ya existente y **cero fuentes nuevas incorporadas**. Quedan 147 portales candidatos distintos, dos validados previamente y 145 pendientes. Las búsquedas no incorporaron nuevas fuentes: hubo timeouts, HTTP 500 y desafíos de verificación de buscadores que no se eludieron.

Se conservan 269 referencias de búsqueda/semillas —varias corresponden al mismo portal— sin contarlas como 269 fuentes. Se guardaron las revisiones y la rotación en el estado persistente. No se promovieron las candidatas dudosas. El runner liviano no tenía lectores PDF/XLS: esos casos quedan pendientes, no se declaran operativos por un HTTP 200.

[Resultado y errores de descubrimiento](descubrimiento_validacion.json).

## Fuentes que siguen requiriendo recuperación

- **EPE:** fallo TLS/EOF en aperturas y HTTP 500 en el directorio; sin extracción actual comprobada.
- **Compras y Gestiones de Compras Santa Fe, Boletín Oficial y Poder Judicial SF:** timeouts desde el runner. Se probaron rutas oficiales alternativas y publicaciones por fecha; no se declara bloqueo permanente ni ausencia de avisos.
- **Cañada de Gómez y Santa Fe Ciudad:** HTTP 403. El concurso conocido de nomencladores sigue omitido por el conector; no se cargó manualmente para simular recuperación.
- **Compras UNR:** HTTP 403; obras institucionales aporta antecedentes, sin convocatoria abierta comprobada en el lote inicial.
- **UNER:** HTTP 401. **Concejo antiguo, ENERSA e Instituto Becario:** errores de certificado. Se mantienen las verificaciones TLS y autenticación.
- **San José:** el control nocturno no reconoció avisos, pero la corrida diaria recuperó 152 publicaciones. Acceso intermitente; eso no acredita 152 convocatorias vigentes.
- Casilda, Roldán, Armstrong, Sunchales, Viale, Oro Verde, DPV ER, Victoria, Gualeguaychú, San Nicolás y Ramallo tienen parciales o pendientes concretos detallados en sus auditorías.

ASSA extrae convocatorias reales, y Aeropuerto/Poder Judicial ER recuperan avisos con fechas futuras aunque su cobertura siga parcial. No se interrumpieron las fuentes existentes de Entre Ríos ni Buenos Aires.

## Auditoría manual y verificaciones

La muestra vigente revisada hoy contiene 14 avisos de las tres provincias: **13 con campos de control recuperados y 1 incompleto**. Los 14 avisos se localizan. No es cobertura territorial completa; además permanecen los controles antiguos no recuperados, incluido Cañada y el aviso histórico de Ramayón.

[Contraste por aviso](comparacion_manual_actualizada.json). La revisión de URL, número, publicación y apertura exige la misma ficha oficial, evitando que otro procedimiento de igual número oculte una omisión. Para ER/BA no se inventa fecha de publicación: no se certifica un censo de siete días cuando falta ese dato.

- **416 pruebas ejecutadas: 415 aprobadas, una omisión opcional.** [CI](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42045951990).
- [Control HTTP real de Rosario y descubrimiento](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42045949031), con tiempos, errores y resultados parciales.
- [Primera validación doble en Actions](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41969428731): cero novedades repetidas. Comparación posterior del último control con una copia del estado diario: 13 nuevas confirmadas; repetición idéntica, cero eventos nuevos, sin red ni OCR adicionales.
- Se añadieron **73 referencias comprobadas** al índice derivado de auditorías: 4651 anteriores conservadas sin alteración. En una copia fresca del estado diario, los avisos ya informados no vuelven a producir alertas de primeras detecciones. No se modificó SQLite de producción ni la cadena de respaldo.
- Cero duplicados y cero vencidas en el CSV comercial actualizado. Se conservan todos los antecedentes y las detecciones sin fecha.

[Resultado incremental](comparacion_control_con_diario.json), [continuidad entre auditorías](referencias_auditorias_append.json), [resultado comercial/diario](resultado_diario_y_vigencia_actual.json) y [auditoría nocturna completa](AUDITORIA_INICIAL_0126.md).

## Ejemplos publicados hoy

| Organismo | Procedimiento y objeto | Publicación | Apertura | Enlace |
|---|---|---|---|---|
| Municipalidad de Rosario | 48/2026, limpieza para Desarrollo Económico y Empleo | 5/11 | 16/11 | [Oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38707) |
| Municipalidad de Rosario | 83/2026, instrumental quirúrgico para Salud Animal | 5/11 | 10/11 | [Oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38729) |
| Municipalidad de Rosario / Hospital Carrasco | 66/2026, artículos de librería | 5/11 | 13/11 | [Oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38730) |

## Qué falta

Completar las fichas pendientes de Rosario y verificar la siguiente corrida diaria con el nuevo presupuesto; recuperar los accesos provinciales críticos; corregir los casos PDF/XLS pendientes y ampliar el control de municipios/comunas de las tres jurisdicciones. Ramayón y Cañada siguen como controles obligatorios, sin darlos por resueltos.

El promedio objetivo de 20 nuevas cotizables por día **no está demostrado**. En esta entrega hay ocho publicaciones confirmadas de hoy dentro del listado nuevo; el resto es recuperación reciente. No se atribuye automáticamente la diferencia a falta de volumen publicado ni se ofrece cobertura exhaustiva.

PR #1 abierto, sin merge. No se activó correo, no se contrataron servicios y no se calcula rentabilidad.
