# Validación del piloto controlado

El desarrollo continúa exclusivamente en el PR #1 y la rama `mejora/radar-auditable`. La producción no se activa y su historial no se modifica. El inventario conserva las 74 fuentes; su configuración no equivale a funcionamiento comprobado.

## Funcionalidades preparadas

- Estado SQLite transaccional separado de producción, con línea de base sin alertas históricas, detección incremental, versiones y auditoría persistentes.
- Distingue publicación nueva comprobada, primera detección sin fecha comprobable, recuperación histórica, modificaciones y datos completados. Fechas desconocidas permanecen desconocidas.
- No borra un procedimiento ante una caída, una página vacía o una recuperación parcial. Cero novedades con incidencias se informa expresamente.
- Supervisor concurrente con plazos por conexión, lectura, fuente y corrida; checkpoints y resultados parciales.
- Catálogo completo, informe diario, abiertas y próximas a vencer, con enlaces oficiales, documentos identificados, condiciones de pago y respaldo. Sin filtros comerciales ni límite de oportunidades; sin análisis de costos, rentabilidad ni proveedores.
- Restauración de estado del piloto mediante artefacto y manifiesto SHA-256, comprobación de SQLite y negativa a reiniciar silenciosamente cuando falta el estado.

## Validación real

Pruebas: **226 aprobadas en Actions**, sin omisiones. Auditoría real: [#116](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40688224634). El job de producción quedó omitido. Ver los resultados exactos, los ejemplos y la cobertura por fuente a continuación.

| Resultado | Primera consulta real | Segunda consulta real |
|---|---:|---:|
| Fuentes consultadas y finalizadas | 74 | 74 |
| Procedimientos en el historial | 3481 | 3530 |
| Novedades/cambios notificados | 0 | 35 |
| Abiertas | 54 | 54 |
| Próximas a vencer | 24 | 24 |

Primera: **3.481 registros de línea de base, cero alertas**. Segunda: **3.050 sin cambios, 49 recuperaciones de línea de base y 35 datos completados**; cero procedimientos nuevos confirmados, cero modificaciones editoriales y **cero identidades repetidas como nuevas**. Las 49 recuperaciones no se anuncian como publicaciones recientes. La reproducción adicional de los mismos datos, sin red, produjo **3.134 sin cambios y cero novedades**. La prueba doble resultó correcta.

El historial final conserva **3.530 procedimientos**, incluyendo **396 no observados en la segunda consulta**. No son 3.530 licitaciones nuevas del día. Hay **54 abiertas, 24 próximas a vencer, 55 con pago comprobado y 3.475 con pago pendiente**. Los candidatos sin procedimiento confirmado están separados: 81 en la primera consulta y 78 en la segunda.

| Cobertura estricta en ambas pasadas | Fuentes |
|---|---:|
| Operativas con procedimientos y objeto | 35 |
| Parciales | 13 |
| Bloqueadas | 12 |
| Pendientes | 13 |
| Sin publicaciones confirmado | 1 |
| Total consultadas y finalizadas | 74 |

La segunda pasada registró **21 fuentes con errores de red y 18 con errores de extracción; dos con ambas categorías**. No sumar estas categorías como fuentes distintas. Hubo diez fuentes con algún timeout, cero errores internos y cero sin iniciar. Ambas pasadas finalizaron **COMPLETA_CON_INCIDENCIAS**: el éxito del workflow valida ejecución y persistencia, no funcionamiento de todos los portales.

Se comprobaron los hashes de producción intactos en las dos corridas y al finalizar. SQLite pasó `quick_check`; conserva 3.565 versiones/eventos y 222 auditorías (dos consultas reales y la reproducción sin red). Se verificó el manifiesto SHA-256 del estado descargado. El HTML contiene las 3.530 filas, sin recorte.

[Artefacto completo](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40688224634/artifacts/12817161063). Código probado: `e677ded9731bde096ae0efaafa278fdd0a60472e`.

### Auditoría individual — instantánea del 28/10/2026

| Organismo | Portal | Estado estricto | Publicaciones de esta pasada | Incidencia |
|---|---|---|---:|---|
| Municipalidad de Rosario | [Oficial](https://www.rosario.gob.ar/inicio/compras-y-licitaciones) | PARCIAL | 13 | URLError |
| Gobierno de Santa Fe | [Oficial](https://compras.santafe.gob.ar/) | BLOQUEADA | 0 | URLError |
| EPE | [Oficial](https://www.epe.santafe.gov.ar/app2/aperturas) | OPERATIVA | 37 | — |
| ASSA | [Oficial](https://www.aguassantafesinas.com.ar/portal/licitaciones) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| UNR | [Oficial](https://compras.unr.edu.ar/) | BLOQUEADA | 0 | HTTPError 403 |
| Poder Judicial de Santa Fe | [Oficial](https://www.justiciasantafe.gov.ar/index.php/poder-judicial/informacion-general/compras-y-licitaciones/) | BLOQUEADA | 0 | URLError |
| Aeropuerto Internacional Rosario | [Oficial](https://aeropuertorosario.com/institucional/licitaciones/) | PARCIAL | 50 | TIEMPO_FUENTE |
| Municipalidad de Casilda | [Oficial](https://www.casilda.gob.ar/web/licitaciones-casilda/) | OPERATIVA | 68 | — |
| Municipalidad de Carcarañá | [Oficial](https://xn--carcaraa-j3a.gob.ar/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Cañada de Gómez | [Oficial](https://cdg.gob.ar/transparencia/licitaciones-y-concursos/) | BLOQUEADA | 0 | HTTPError 403 |
| Municipalidad de Armstrong | [Oficial](https://armstrong.gov.ar/index.php/transparencia) | OPERATIVA | 7 | — |
| Municipalidad de Las Parejas | [Oficial](https://lasparejas.gov.ar/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Funes | [Oficial](https://funes.gob.ar/) | OPERATIVA | 39 | — |
| Municipalidad de Roldán | [Oficial](https://www.roldan.gov.ar/wp/documents/licitaciones-y-contrataciones/) | PARCIAL | 104 | TIEMPO_FUENTE |
| Municipalidad de Pérez | [Oficial](https://perez.opendata.junar.com/home/) | PENDIENTE | 0 | ValueError |
| Municipalidad de Villa Gobernador Gálvez | [Oficial](https://vggmunicipalidad.gov.ar/licitaciones/) | OPERATIVA | 105 | — |
| Municipalidad de Santo Tomé | [Oficial](https://www.santotome.gob.ar/ciudadania/Informacion_Publica_y_Transparencia) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Santa Fe | [Oficial](https://transparencia.santafeciudad.gov.ar/compras-y-contrataciones/) | BLOQUEADA | 0 | HTTPError 403 |
| Municipalidad de Santa Fe | [Oficial](https://transparencia.santafeciudad.gov.ar/contrataciones-obra/) | BLOQUEADA | 0 | HTTPError 403 |
| Municipalidad de Rafaela | [Oficial](https://www.rafaela.gob.ar/gobiernoabierto/Licitaciones.aspx) | OPERATIVA | 11 | — |
| Municipalidad de Venado Tuerto | [Oficial](https://venadotuerto.gob.ar/licitaciones/) | OPERATIVA | 26 | — |
| Municipalidad de Reconquista | [Oficial](https://reconquista.gob.ar/licitaciones/) | OPERATIVA | 13 | — |
| Gobierno de Entre Ríos | [Oficial](https://portal.entrerios.gov.ar/haciendayfinanzas/contrataciones/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Ministerio de Planeamiento e Infraestructura | [Oficial](https://www.entrerios.gov.ar/minplan/licitaciones) | OPERATIVA | 515 | — |
| CAFESG | [Oficial](https://cafesg.gob.ar/cafesg2/licitaciones/) | OPERATIVA | 68 | — |
| Poder Judicial de Entre Ríos | [Oficial](https://www.jusentrerios.gov.ar/contrataciones/) | OPERATIVA | 51 | — |
| ATER | [Oficial](https://www.ater.gob.ar/ater2/licitaciones.asp) | OPERATIVA | 219 | — |
| Vialidad Entre Ríos | [Oficial](https://www.dpver.gov.ar/category/licitaciones-2026/) | OPERATIVA | 21 | — |
| ENERSA | [Oficial](https://www.enersa.com.ar/area-proveedores/) | BLOQUEADA | 0 | URLError |
| Instituto Becario | [Oficial](https://institutobecario.gov.ar/licitaciones.php) | BLOQUEADA | 0 | URLError |
| Municipalidad de Victoria | [Oficial](https://victoria.gob.ar/web-compras/Invitaciones-Compras/concurso-de-precios/) | BLOQUEADA | 0 | HTTPError 429 |
| Municipalidad de San José | [Oficial](https://sanjose.gob.ar/concursos-licitaciones/) | OPERATIVA | 152 | — |
| Municipalidad de Colón | [Oficial](https://colon.gov.ar/compras-contratos-suministros/licitaciones/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Concepción del Uruguay | [Oficial](https://www.cdeluruguay.gob.ar/index.php/servicios-web/data-gov/licitaciones) | OPERATIVA | 266 | — |
| Municipalidad de Gualeguaychú | [Oficial](https://w3.gualeguaychu.gov.ar/tramites/compras-y-licitaciones/acceso-a-licitaciones-p%C3%BAblicas) | BLOQUEADA | 0 | URLError |
| Municipalidad de Gualeguay | [Oficial](https://municipalidad.gualeguay.gob.ar/modulos/transparencia/licitaciones_publicas.php) | OPERATIVA | 7 | — |
| Municipalidad de Crespo | [Oficial](https://www.crespo.gob.ar/licitaciones-privadas-2026/) | OPERATIVA | 7 | — |
| Municipalidad de Crespo | [Oficial](https://www.crespo.gob.ar/category/licitacion-publica/) | PARCIAL | 175 | DetalleIncompleto, HTTPError 404 |
| Municipalidad de Chajarí | [Oficial](https://chajari.gob.ar/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Federación | [Oficial](https://www.federacion.gob.ar/licitaciones) | PARCIAL | 96 | TIEMPO_FUENTE, ValueError |
| Municipalidad de Nogoyá | [Oficial](https://nuevo.nogoya.gob.ar/compras-licitaciones-y-concursos-nuevo/) | OPERATIVA | 20 | — |
| Municipalidad de La Paz | [Oficial](https://haciendalapaz.gob.ar/compras/) | OPERATIVA | 48 | — |
| Municipalidad de Villaguay | [Oficial](https://villaguay.gob.ar/boletindigital/) | PARCIAL | 238 | HTTPError 404 |
| Municipalidad de Rosario del Tala | [Oficial](https://www.rosariodeltala.gob.ar/?q=licitaciones-publicas) | OPERATIVA | 5 | — |
| Municipalidad de San Nicolás | [Oficial](https://www.sannicolasciudad.gob.ar/areas/economia-y-finanzas/licitacionesyconcursos) | PARCIAL | 26 | DetalleIncompleto |
| Municipalidad de San Pedro | [Oficial](https://sanpedro.net.ar/portal.php) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Pergamino | [Oficial](https://compras.pergamino.gob.ar/) | PENDIENTE | 0 | AccesoRestringido |
| Municipalidad de Arrecifes | [Oficial](https://arrecifes.gob.ar/informacion-publica/licitaciones/) | OPERATIVA | 5 | — |
| Municipalidad de Baradero | [Oficial](https://gobiernoabierto.baradero.gob.ar/precios-y-licitaciones) | OPERATIVA | 128 | — |
| Municipalidad de Rojas | [Oficial](https://transparencia.rojas.gov.ar/index.php?action=17) | OPERATIVA | 10 | — |
| Municipalidad de Rojas | [Oficial](https://transparencia.rojas.gov.ar/index.php?action=24) | SIN_PUBLICACIONES_CONFIRMADO | 0 | — |
| Ente Administrador Puerto Rosario (ENAPRO) | [Oficial](https://enapro.com.ar/category/licitaciones/) | OPERATIVA | 20 | — |
| Municipalidad de Alvear | [Oficial](https://alvear.gob.ar/index.php?anio=2025&pagina=licitaciones) | PARCIAL | 70 | DetalleIncompleto, ValueError |
| Municipalidad de San Lorenzo | [Oficial](https://sanlorenzo.gob.ar/licitaciones/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| IAFAS | [Oficial](https://www.iafas.gov.ar/proveedores/licitaciones/) | PARCIAL | 98 | DetalleIncompleto |
| Universidad Nacional de Entre Ríos (UNER) | [Oficial](https://compras.uner.edu.ar/) | BLOQUEADA | 0 | HTTPError 401 |
| Municipalidad de Colón | [Oficial](https://www.municipalidadcolonpba.gob.ar/licitaciones.php) | PARCIAL | 63 | DetalleIncompleto, HTTPError 404 |
| Boletín Oficial de Santa Fe | [Oficial](https://www.santafe.gov.ar/boletinoficial/) | BLOQUEADA | 0 | URLError |
| Boletín Oficial de Entre Ríos | [Oficial](https://www.entrerios.gov.ar/boletin/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Comuna de General Lagos | [Oficial](https://cglagos.gob.ar/comuna/compras-y-licitaciones) | OPERATIVA | 10 | — |
| Comuna de Arequito | [Oficial](https://comunaarequito.gob.ar/licitaciones/) | OPERATIVA | 10 | — |
| Comuna de Chabás | [Oficial](https://chabas.gob.ar/descargas/92-licitaciones/129-licitaciones-2026/5002-licitacion-publica-01-2026) | OPERATIVA | 3 | — |
| Gobierno de Timbúes | [Oficial](https://www.timbues.gob.ar/index.php?pagina=lista&sec=210) | PARCIAL | 136 | TIEMPO_FUENTE |
| Municipalidad de Sunchales | [Oficial](https://sunchales.gob.ar/gestion/sunchales-impulsa/municipio-transparente/licitaciones-y-contrataciones/) | OPERATIVA | 80 | — |
| Concejo Municipal de Santa Fe | [Oficial](https://www.concejosantafe.gov.ar/concursos-y-licitaciones) | OPERATIVA | 2 | — |
| Municipalidad de Villa Elisa | [Oficial](https://villaelisa.gov.ar/transparencia/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de General Ramírez | [Oficial](https://www.generalramirez.gob.ar/licitaciones-y-concursos/) | OPERATIVA | 88 | — |
| Municipalidad de Lucas González | [Oficial](https://lucasgonzalez.gob.ar/licitaciones-y-concursos/) | OPERATIVA | 2 | — |
| Municipalidad de San Salvador | [Oficial](https://sansalvadorer.gob.ar/) | OPERATIVA | 11 | — |
| Municipalidad de Salto | [Oficial](https://salto.gob.ar/licitaciones/) | PARCIAL | 21 | HTTPError 403 |
| Municipalidad de Junín | [Oficial](https://www.junin.gob.ar/servicio/licitaciones-y-concursos) | PARCIAL | 34 | TIEMPO_FUENTE |
| Municipalidad de Zárate | [Oficial](https://zarate.gob.ar/licitaciones-publicas/) | OPERATIVA | 31 | — |
| Municipalidad de San Andrés de Giles | [Oficial](https://www.sanandresdegiles.gob.ar/?q=licitaciones-publicas) | OPERATIVA | 3 | — |
| Municipalidad de Funes | [Oficial](https://funes.gob.ar/boletin_oficial) | OPERATIVA | 39 | — |

Prioridades restantes: páginas de Rosario y fichas de Aeropuerto Rosario, Roldán, Timbúes y Junín que agotan plazos; adjuntos 404 de Crespo, Villaguay y Colón BA; objetos incompletos de San Nicolás, IAFAS y Alvear; documentos grandes de Federación/Alvear. Compras SF, Poder Judicial SF, Gualeguaychú y Boletín SF agotan lectura; UNR/Cañada de Gómez/Santa Fe capital devuelven 403, UNER 401, Victoria 429 y ENERSA/Instituto Becario presentan error de certificado. No se desactiva TLS ni se eluden restricciones. Los trece pendientes de la tabla necesitan resolver el listado o acceso; no se declaran sin licitaciones.


## Correcciones de cobertura y calidad

**General Ramírez:** fichas con número en h2 y modalidad publicada en el encabezado; objeto, presupuesto, apertura y documentos por ficha. Sigue sólo enlaces publicados a públicas, privadas, concursos y archivos por año. La ficha actual y su copia histórica comparten identidad. Una etiqueta «Adjudicado» vacía no prueba adjudicación; un decreto no se llama pliego. La configuración efectiva del supervisor y la del radar se comprobaron juntas mediante regresión.

**EPE:** se reconoce su numeración propia de diez dígitos únicamente con dominio oficial, modalidad reconocida y objeto dedicado comprobado. Se conserva la protección contra teléfonos/cifras sueltas en otros portales. La identidad no depende de «Hoy», «Mañana» o la URL alternativa. La fecha del listado de aperturas no se usa como publicación. Los pliegos o pagos no recuperados quedan pendientes.

**Falsas novedades de #107:** catorce cambios eran contadores de vistas de Timbúes o descargas de Armstrong. Se excluyen esas etiquetas observadas de la huella semántica, conservando la evidencia original. Otros dos casos pasaban de resumen a detalle y se reportan como datos completados. La repetición local de los datos reales de #107, con esta corrección, produjo cero modificaciones y cinco completamientos; es una reproducción sin red, separada de las dos consultas reales de #116.

## Ejemplos recuperados y contrastables

**Dos fuentes existentes recuperadas como operativas; cero nuevas incorporaciones de configuración.** EPE aporta 37 procedimientos: 19 licitaciones públicas, cinco privadas, once concursos privados y dos compras menores; 32 abiertos y cinco de vigencia desconocida. General Ramírez aporta 88: 87 vencidos y uno de vigencia desconocida. Se conservaron todos.

| Organismo / procedimiento | Objeto resumido | Apertura | Presupuesto publicado | Evidencia |
|---|---|---|---|---|
| EPE — Concurso privado 7040004995 | Candados y portacandados | 02/11/2026; abierta | $24.220.193,69 | [Listado oficial](https://www.epe.santafe.gov.ar/app2/aperturas) |
| EPE — Compra menor 7010004619 | Chapa antideslizante | 03/11/2026; abierta | $8.439.867,81 | [Listado oficial](https://www.epe.santafe.gov.ar/app2/aperturas) |
| General Ramírez — Licitación pública 1/2026 | Broza y piedra para obras | 11/09/2026; vencida | $56.960.000,00 | [Ficha/listado](https://www.generalramirez.gob.ar/licitaciones-y-concursos/licitaciones-publicas/) · [Decreto de llamado](https://www.generalramirez.gob.ar/contenidos/medios/licitaciones-publicas/lic-publica_2026-01-llamado.pdf) |

La fecha de publicación y el pago quedan **desconocidos/no informados** en estos ejemplos. El símbolo $ figura publicado, sin código ISO de moneda comprobado. No se anuncian pliegos de EPE no recuperados ni se presenta el decreto de General Ramírez como pliego. Ese PDF fue accesible y registró SHA-256 `f78500b3158b27ae2e47b874e0e0daed41eeda5457b6a4ac7e8360b95bf46398`, pero no una cláusula de pago comprobada; su lectura/OCR sigue pendiente.


## Descubrimiento

En esta continuación se descubrieron **13 URLs candidatas adicionales**: dos en [descubrimiento #15](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40687832335) y once en [#16](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40688224211). La última tanda inició consultas para **91 URLs**, validó **cero** e incorporó **cero**. Acumulado: **92 URLs candidatas, una aprobada previamente (Funes) y 91 pendientes**, con 159 hallazgos/evidencias repetidas separados de URLs únicas. La tanda #16 registró 21 búsquedas con errores o verificación humana; los resultados de buscadores no acreditan identidad ni publicaciones. La revisión de los 75 pendientes anteriores queda incluida en estas tandas; no se exige al usuario suministrar cada URL.


Los candidatos dudosos conservan evidencia y motivo, sin incorporarse como fuentes confiables. No se eluden autenticación, VPN, TLS, limitaciones de acceso ni verificación humana. No se declara cobertura territorial completa. Persisten municipios/comunas y organismos sectoriales sin fuente validada.

## Consultar y activar de forma controlada

En la ejecución de Actions descargar **radar-controlado**, descomprimirlo y abrir **index.html**; el enlace lleva al informe completo con búsqueda local. Se incluyen catálogo JSON/Markdown, eventos, abiertas, próximas a vencer, auditoría por fuente, SQLite y manifiesto. Los enlaces documentales desconocidos no se inventan y los registros no observados en la última corrida permanecen identificados.

Los artefactos duran 90 días y cada estado contiene todo el historial acumulado. La restauración del artefacto descargado y su integridad se comprobaron localmente. Aún falta probar la continuidad entre dos ejecuciones manuales diarias independientes del workflow y definir respaldos duraderos para pausas de más de 90 días. La prueba doble sí usó el mismo estado entre dos consultas reales.

La programación de las 08:00 Argentina está preparada, pero GitHub sólo ejecuta cron en la rama predeterminada. No se modificó `main` para activar esta rama. Falta autorizar un disparador diario del piloto, completar esa prueba de restauración y definir quién revisa los fallos. Activar producción requiere autorización explícita separada. Ver [puesta en marcha controlada](PUESTA_EN_MARCHA_CONTROLADA.md).
