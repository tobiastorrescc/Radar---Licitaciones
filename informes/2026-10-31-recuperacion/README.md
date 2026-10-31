# Recuperación de fuentes y barrido institucional — 31/10/2026

**Resultado comprobado: 7 convocatorias abiertas adicionales a las 21 recuperadas en bd28813.** La etapa sigue **parcial**: Ramayón, EPE, Compras Santa Fe y Cañada de Gómez no quedaron recuperadas automáticamente.

Base: catálogo de 4.621 vistas únicas publicado en la auditoría [41213570935](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41213570935), anterior a esta etapa. No se vuelven a contar sus 21 recuperaciones como nuevas. Nueva para el radar **no significa publicación nueva del día**: las siete carecen de fecha de publicación original comprobada; sí se comprobó su apertura futura en avisos oficiales. La fecha de edición de un boletín y la de creación de una página contenedora no sustituyen esa fecha.

## Resultados de la muestra de esta etapa

| Medida | Resultado |
|---|---:|
| Fuentes efectivamente consultadas en este lote | 12 |
| Operativas sin incidencias en el alcance ensayado | 1 |
| Parciales con procedimientos recuperados | 5 |
| Inaccesibles en Actions | 4 |
| Pendientes sin extracción de compras comprobada | 2 |
| Registros clasificados como procedimientos por el extractor | 203 |
| Abiertas comprobadas documentalmente en la muestra | 19 |
| Abiertas ya conocidas en la base | 12 |
| Abiertas inéditas para el catálogo accesible | **7** |
| Registros vencidos, separados del listado comercial | 123 |
| Registros de vigencia desconocida, conservados | 61 |
| Avisos candidatos que aún requieren validación | 64 |

Los 203 son resultados del extractor, **no 203 expedientes revisados manualmente en su totalidad**. La comparación documental se concentra en las 19 abiertas. En esa muestra comprobada el catálogo anterior contenía 12/19 y el radar corregido recupera 19/19. Esto no es un porcentaje de cobertura territorial ni un censo manual independiente de todos los avisos de esos organismos. También existe una convocatoria de Cañada de Gómez visible manualmente y todavía inaccesible para el conector: se entrega aparte y no se suma a las siete.

## Las siete abiertas inéditas

Las fechas de apertura no se presentan como cierres de recepción si el aviso no establece ese cierre.

| Organismo | Procedimiento y objeto | Recepción / apertura comprobadas | Presupuesto publicado | Enlace oficial |
|---|---|---|---|---|
| Comuna de Aldea Salto | LP 02/2026. Ejecución del Museo Comunal y Galpón para Maquinarias | Cierre no comprobado. Apertura 02/11/2026, 10:00 | $179.184.800,60 | [Boletín 16/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/16-10-26.pdf) |
| Municipalidad de Seguí | LP 09/2026. Una máquina retroexcavadora 0 km | Cierre no comprobado. Apertura 03/11/2026, 10:00 | $150.000.000 | [Pliego municipal](https://www.segui.gob.ar/sitio/wp-content/uploads/2025/01/MUNICIPALIDAD-DE-SEGUI-Pliegos-Lic-Publica-09-2026-1.pdf) · [Boletín 20/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/20-10-26.pdf) |
| Instituto Autárquico Becario Provincial | LP 11/2026. Transporte escolar rural para establecimientos de Diamante, Feliciano, Islas, Nogoyá y Victoria, del 16/11/2026 al 31/08/2027, con opción de renovación | Cierre no comprobado. Apertura 03/11/2026, 08:30 | No comprobado en el aviso | [Boletín 27/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/27-10-26.pdf) |
| Municipalidad de Santa Ana | LP 06/2026. Mano de obra, materiales, maquinarias y herramientas para pavimento asfáltico | Cierre no comprobado. Apertura 06/11/2026, 10:00 | $610.000.000 | [Boletín 16/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/16-10-26.pdf) |
| Municipalidad de El Pingo | LP 02/2026. Dos garitas de colectivos sobre Av. 9 de Julio | Recepción 10/11/2026, 12 hs. Apertura 11/11/2026, 10 hs | $16.868.978,35 | [Boletín 30/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/30-10-26.pdf) |
| Municipalidad de Basavilbaso | Licitación privada 03/2026. 1.200 toneladas de material base 0/30 y traslado desde cantera a estación de carga de trenes de Yuquerí, Concordia | Cierre no comprobado. Apertura 12/11/2026, 08:00 | $39.500.000 | [Boletín 30/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/30-10-26.pdf) |
| Comuna de Colonia Tunas | LP 03/2026. Adquisición de triturador de ramas | Recepción 25/11/2026, 09:45. Apertura 25/11/2026, 10:00 | $27.000.000 | [Boletín 30/10](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/30-10-26.pdf) |

Basavilbaso publica pago a **30 días desde presentación de factura**. En Seguí el pliego general menciona factura y recepción conforme, con alternativas condicionadas a la decisión municipal o al particular: no se promete contado ni acreditación inmediata. El rótulo automático «Pago mixto» debe leerse con esa salvedad. En las demás, pago pendiente de verificar. No se ejecutó una nueva investigación de pagos ni cálculos de rentabilidad.

## Fuentes recuperadas y límites

- **Boletín Oficial de Entre Ríos: recuperado en el alcance ensayado.** El sitio oficial publica en su cliente JavaScript el índice JSON público `https://testing54.entrerios.gov.ar/boletin/factura/inicio/get_buscador`. El nombre del host no se tomó como garantía: se contrastó su uso en los archivos oficiales `8931.31563bf3.chunk.js` y `5326.824a7ea1.chunk.js` de `portal.entrerios.gov.ar`. Este último publica la regla de enlaces a PDF. La prueba real leyó **44 respuestas, incluidas 43 ediciones PDF de los últimos 60 días**, extrajo **107 procedimientos por fuente principal** y terminó sin incidencias. Con la caché ya disponible tardó 9,55 segundos, frente a 36,64 segundos en la prueba anterior. No hubo OCR. La cobertura corresponde a las secciones y estructuras reconocidas, no a todas las contrataciones provinciales.
- **Carcarañá: recuperación parcial, 10 registros históricos.** El HTML institucional publica los servicios delegados `qx.com.ar/clientes/munic/boletines.php?cols=si` y `noticias.php`. Se implementó la paginación POST `limiteInfConsulta=0,6,...` y su fin explícito. Se visitaron 160 páginas antes del límite. Persisten PDF sin texto y recorrido incompleto. No se demostró una convocatoria abierta nueva.
- **Ramallo: recuperación parcial, 21 registros históricos.** Se reemplazó como punto único de entrada el PDF de abril de 2024 por el portal municipal vigente y su enlace oficial a [SIBOM, municipio 102](https://sibom.slyt.gba.gob.ar/cities/102). Se siguen los formularios GET reales de boletines y sus contenidos. La prueba alcanza el límite de tiempo; no se declara cubierto todo el archivo ni se presentan adjudicaciones antiguas como convocatorias abiertas.
- **Viale, Oro Verde y Seguí: tres fuentes municipales incorporadas, todas parciales.** Antes eran candidatos; ahora tienen extracción real comprobada y configuración reutilizable. Viale: 36 registros del extractor, sin apertura futura confirmada en esta muestra. Oro Verde: 2 procedimientos tras ampliar la navegación, con recorrido histórico incompleto. Seguí: 28 procedimientos según fuente principal; LP09/2026 comprobada en PDF y boletín, unificada entre ambas fuentes. Quedan un plano PDF sin texto y enlaces cuyo número/año difiere del documento: no se inventa una correspondencia.
- **Esperanza:** navegación institucional y buscador publicados consultados; sin extracción de compras comprobada antes del límite. Pendiente, no «sin publicaciones».

El inventario configurado pasa de **79 a 82 fuentes**. Esta cifra no es cobertura territorial: las tres nuevas siguen parciales. No se dieron altas masivas ni se declararon validadas fuentes por responder HTTP200.

## Las seis prioridades solicitadas

| Fuente | Estado real | Obstáculo y alternativas contrastadas |
|---|---|---|
| Ramayón | ERROR DE ACCESO / pendiente | No se localizó un sitio comunal independiente verificable. El aviso oficial conocido está en el Boletín de Santa Fe. HTML, PDF de impresión y rutas públicas de recursos, variantes oficiales `gov/gob` y HTTP/HTTPS agotaron la conexión en Actions. LP01/2026 de tractor abrió el 08/10: está vencida y no se cuenta como oportunidad actual. LP02/2026 de desmalezadora requiere recuperar el aviso completo; no se inventa apertura. |
| Carcarañá | PARCIAL | AJAX delegado y paginación ya funcionan; resultados comprobados históricos. Falta completar documentos sin texto y contrastar publicaciones actuales. |
| Cañada de Gómez | ERROR DE ACCESO | Índice, JSON público y PDF devuelven403 en Actions, también mediante curl con TLS validado. La lectura web permite comprobar concurso de nomencladores, Decreto7839/26, recepción10/11 09:00 y apertura10:00. Está en `control_manual_pendiente.csv`, sin sumarlo a la recuperación automática. No se ensayaron proxies, cookies ni evasión. |
| Las Parejas | PENDIENTE | `/index_news` es la ruta real; `/index_noticias` devuelve404. El PDF enlazado en `/index_boletin` contiene Lorem ipsum. Las páginas accesibles no demuestran extracción de contrataciones ni ausencia de ellas. |
| EPE | ERROR DE ACCESO | Índice con y sin `www`: EOF de TLS; rutas institucionales, fichas y documento público: HTTP500/cierre remoto; HTTP:503. curl con máximo TLS1.2 conserva validación del certificado y obtiene500, por lo que cambiar el transporte no recupera la fuente. Las publicaciones indexadas por buscadores prueban que no corresponde declarar «sin novedades», pero no sustituyen extracción real. |
| Compras Santa Fe | ERROR DE ACCESO | Compras `gob/gov`, sistema legado de gestiones y ficha oficial conocida: timeout. Sin endpoint público alternativo demostrado. No se eludieron desafíos ni autenticación. |

## Qué se corrigió

1. Barrido de menús institucionales, noticias, boletines, transparencia y cuentas claras, incluyendo enlaces fuera del bloque principal. Se usan únicamente buscadores GET publicados por el propio sitio y feeds oficiales; no se inventan rutas de búsqueda.
2. AJAX delegado sólo cuando su URL está publicada por el organismo, paginación acotada, detección de páginas repetidas y conservación de resultados parciales.
3. Formularios GET de SIBOM, lectura liviana de PDF de avisos y numeraciones explícitas como «32 de 2026» o correlativos de cotejos de Viale, sin inventar año.
4. Extracción del Boletín de Entre Ríos por sección e identificador de aviso, sin mezclar organismos con quiebras o designaciones. Nombres con espacios tipográficos se contrastan de forma exacta con el padrón. Identificadores ENERSA `2026-0841` se conservan literalmente.
5. Las cláusulas generales de un pliego sobre una eventual declaración de desierta ya no cierran automáticamente la convocatoria Seguí09/2026. Las referencias a Ley de Contabilidad Pública5140 y calle Pública26 no se crean como procedimientos adicionales.
6. Un feed de una página contenedora antigua no fecha todos sus nuevos adjuntos con2018. La fecha de publicación de Seguí09/2026 queda desconocida.
7. La vinculación de un aviso complementario exige organismo, modalidad, número, misma apertura y concordancia del objeto; sólo se aplica con un antecedente único. Se conserva la convocatoria y el ámbito departamental. Procedimientos distintos con igual número no se fusionan por ese dato solo. El índice evita recorrer todo el catálogo por cada aviso.
8. Se corrigió el diagnóstico que interpretaba PDF como HTML y llamaba bloqueo al error de extracción. El índice auxiliar incorpora130 identidades de auditorías ya publicadas para evitar falsas novedades; no sustituye ni modifica SQLite de producción ni respaldos.

## Pruebas, piloto y evidencias

- [Prueba real y piloto comparativo41236909527](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41236909527): fuenteER operativa, Seguí parcial; comparación más amplia de44 fuentes con capturas previas. No es una nueva consulta en vivo a los44 organismos.
- Primera pasada comparativa: 2.239 observaciones;62 primeras detecciones sin fecha,27 modificaciones,14 datos completados y113 recuperaciones de línea de base. **103 novedades/cambios no significan103 licitaciones inéditas.** La comparación comercial encuentra las7 abiertas nuevas mencionadas.
- Segunda pasada independiente sobre el mismo estado: **0 novedades y0 eventos repetidos**;5.136 filas históricas y5.117 vistas únicas conservadas. Estado completo con incidencias de fuentes, no consulta completa sin errores.
- El informe se abrió y revisó. Sus162 abiertas son un cálculo sobre el catálogo retenido; no se presentan como162 vigencias revalidadas en vivo en este lote. Las19 de la muestra sí tienen aviso y apertura comprobados.
- `produccion_intacta=true`, `respaldo_intacto=true`, OCR nuevo0. `main` conserva `dfca1a52c5371929ce6c07741a88fd209a7da852`. No cambió el programador ni el workflow del piloto diario; sólo el workflow de auditoría aislada de esta rama.
- Regresión local:376 pruebas,375 aprobadas y1 omitida por dependencia opcional. Actions verifica todas las dependencias instaladas. Se incluyen regresiones de AJAX, feeds, búsqueda institucional, boletín, Seguí, no procedimientos legales y persistencia sin duplicados.
- Incidencia de publicación: un commit intermedio transmitió truncado el índice auxiliar base64; CI lo detectó antes del cierre. Se republicó mediante blob completo, con SHA Git comprobado `e4ffb12ec6a0d220c6c2e4dc671a4dc1911b22be`. Ningún historial ni respaldo de producción fue alterado. [Regresión final41237677541](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41237677541) y [auditoría/repetición final41237677685](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41237677685) completadas correctamente. Esta última entrega todos los CSV como artefacto y reproduce los mismos7 hallazgos, sin red a portales ni OCR.

## Descargas y reproducción

- [Las7 abiertas inéditas](abiertas_ineditas.csv).
- [Las19 abiertas comprobadas de la muestra](abiertas_comprobadas.csv).
- [203 procedimientos extraídos, incluidos históricos y de vigencia desconocida](publicaciones_completas.csv).
- [64 avisos candidatos pendientes de validar](avisos_pendientes_validacion.csv).
- [Cobertura individual de12 fuentes](cobertura_fuentes.csv) y [fuentes todavía pendientes o parciales](fuentes_pendientes.csv).
- [Control manual aún no automatizado](control_manual_pendiente.csv).
- [Todos los eventos del piloto, sin recorte](eventos_piloto_completos.csv).
- [Resumen reproducible](resumen.json), [evidencia de abiertas](evidencia_abiertas.json) y [resultado del piloto](piloto_comparativo.json).

`tools/informar_recuperacion.py --base <catalogo-bd28813> --captura <resultado-del-barrido> --complemento <captura-inicial> --complemento <captura-navegacion> --salida work/informe-recuperacion` reproduce el lote y los CSV sin red ni OCR. El workflow de auditoría también entrega esos archivos como artefacto, con hashes y registros por fuente. Los CSV conservan textos y enlaces completos; no se aplicó top ni filtro comercial.

## Pendiente para la próxima etapa

Recuperar primero Ramayón y las alternativas institucionales del Boletín Santa Fe; mantener EPE y Compras Santa Fe como errores de acceso hasta demostrar procedimientos reales. Resolver el403 de Cañada únicamente por vías permitidas por el organismo. Completar documentos puntuales de Carcarañá y Seguí y localizar la publicación real de compras en Las Parejas y Esperanza. Extender después el mismo contraste a más comunas y a SIBOM/municipios bonaerenses; los candidatos aún no ensayados permanecen en la cola persistente. No se declara cobertura completa de ninguna provincia.
