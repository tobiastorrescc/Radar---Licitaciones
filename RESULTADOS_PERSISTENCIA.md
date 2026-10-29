# Resultados: persistencia duradera y piloto diario

Código auditado: `0ea4ce8b935d85eb7f599e2b86924c1b587f0054`. PR #1 abierto en `mejora/radar-auditable`, sin merge ni cambios al historial de producción. No se activa producción ni un cron de la rama.

## Pruebas y ejecución independiente

**249 pruebas aprobadas en GitHub Actions, sin omisiones.** [Orquestador #129](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40743856747) completado correctamente. Invocó el mismo punto de entrada `workflow_dispatch` que usa el piloto, en dos runners independientes.

| Estado | Procedimientos | Versiones conservadas |
|---|---:|---:|
| Semilla auditada #116 | 3.530 | 3.565 |
| Consulta independiente #130 | 3.584 | 3.637 |
| Consulta independiente #131 | 3.691 | 3.750 |

[#130](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40743984529) verificó procedencia e integridad de la semilla, consultó las 74 fuentes, conservó sus registros/versiones y publicó un primer segmento de respaldo en Git. [#131](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40745969935) hizo un nuevo checkout, restauró la cadena desde Git y volvió a consultar las 74 fuentes: **cero identidades anteriores repetidas como nuevas, cero procedimientos perdidos y cero versiones anteriores alteradas**. En la segunda se conservaron 160 procedimientos no recuperados en esa consulta.

La segunda registró 3.418 sin cambios, 107 recuperaciones de línea de base separadas y seis cambios de contenido recuperado. No confirmó publicaciones recién emitidas. Los cambios observados pueden completar o variar la extracción de documentos; no prueban por sí solos una edición del organismo. La primera tuvo una detección sin fecha de publicación comprobable, conservada en el historial. No se presenta el archivo histórico como miles de novedades diarias.

La prueba anterior [#119](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40737559091) creó una línea de base aislada de 3.302 procedimientos con cero alertas; [#120](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40738960873) la restauró y terminó con 3.417, también sin repetir identidades como nuevas. Las bases de validación están identificadas por revisión y separadas del piloto diario.

## Respaldo duradero preparado

`piloto_respaldo/diario/` se prepara con los mismos blobs de la cadena final validada: base de 3.446.248 bytes e incremento de 1.693.991 bytes, más el índice. La copia no cambia contenido ni hashes. Quedan 3.691 procedimientos, 3.750 versiones/eventos y 370 auditorías. Las cinco corridas incluyen tres heredadas de #116, una de ellas una reproducción sin red, y las dos consultas reales nuevas.

El hash lógico del estado descargado coincide con el índice de Git: `e91854f7e33c86c6390c21fea9d8e6e1214f85248eb8e34966173142024c3c42`. SQLite pasó `quick_check`. Los hashes de los archivos de producción permanecieron intactos en ambas ejecuciones.

Los segmentos están versionados en Git y **no caducan con los artefactos de Actions**. Cada uno enlaza el hash del anterior y contiene el incremento; antes de publicar se restaura toda la cadena y se compara el contenido exacto. Faltantes, corrupción o pérdida de historia detienen el proceso sin reinicialización silenciosa. El canal diario existente nunca se sobrescribe al preparar una validación. Conservar el repositorio y su rama; una copia externa del repositorio añade protección ante pérdida del proveedor. Se respaldan datos, referencias, hashes y evidencias textuales; no se declara un archivo eterno de todos los PDF originales.

## Salud de las fuentes — última consulta #131

| Estado estricto | Fuentes |
|---|---:|
| Operativas con procedimientos y objeto | 34 |
| Parciales | 14 |
| Bloqueadas | 13 |
| Pendientes | 12 |
| Sin publicaciones confirmado | 1 |
| Total consultadas/finalizadas | 74 |

Ambas corridas terminaron **COMPLETA_CON_INCIDENCIAS**. La última tuvo 23 fuentes con errores de red y 18 con extracción; tres tuvieron ambas categorías. Hubo once con algún timeout, cero errores internos y cero sin iniciar. No sumar las categorías solapadas. Durante la primera hubo varios HTTP 200 con una página «One moment, please» de verificación: no cuentan como fuentes operativas ni como ausencia de licitaciones. La variación entre pasadas queda en sus auditorías, sin eludir desafíos, TLS, autenticación ni bloqueos.

El catálogo final contiene 52 abiertas y 22 próximas a vencer según los últimos datos conocidos. Hay **92 pagos verificados y 3.599 pendientes**. Los registros no observados hoy siguen identificados: una fuente fallida requiere nueva comprobación antes de tratar sus datos como actuales.

## Recuperación efectiva y límites

**Villa Elisa pasó de no extraer procedimientos a recuperar 87**: 52 concursos de precios, 23 privadas y doce públicas, incluyendo segundos llamados. Hay 71 con objeto y dieciséis sin concepto suficiente: por ello permanece **PARCIAL**, no se presenta como fuente completa. Se corrigió la grilla real por columnas, números sin modalidad en la celda y asignación de documentos a cada fila. La portada se usa para seguir el PDF publicado de un llamado, no como objeto de compra. Los fixtures de la primera captura real revelaron y permitieron corregir la mezcla de etiquetas y navegación.

Los archivos anuales se recorren por año reciente primero, manteniendo todos los anteriores en la cola y en el historial. Villaguay recuperó 238 publicaciones en la última consulta frente a 172 en la primera prueba de esta etapa. Sigue parcial por enlaces PDF/XLS 404; llegar primero a 2026 no convierte enlaces rotos en fuentes funcionales. Crespo conserva 175, con cuatro adjuntos antiguos 404 y un objeto incompleto.

EPE respondió HTTP 500 en estas consultas. Sus 37 procedimientos previamente comprobados permanecen en el historial, con fecha de última observación: no se declaran verificados de nuevo. Persisten 403 en UNR, Cañada de Gómez, Santa Fe capital y Salto; UNER 401; fallos de certificado en ENERSA/Instituto Becario; timeouts en Compras SF, Poder Judicial SF, Gualeguaychú y Boletín SF. No se desactiva TLS ni se eluden restricciones.

## Ejemplos recuperados en Villa Elisa

| Procedimiento | Objeto resumido | Información comprobable | Fuente/documento |
|---|---|---|---|
| Licitación pública 4/2026 | Vehículo para pasajeros; segundo llamado | Segundo llamado extraído del PDF; fechas, presupuesto y pago pendientes de comprobación | [Oficial/documento](https://villaelisa.gov.ar/wp-content/uploads/2026/10/2026_004-_Licitacion-UTILITARIO-5-PERSONAS-2do-llamado-con-marcadeagua.pdf) |
| Concurso de precios 1/2026 | Hormigón elaborado H21 | Pago posterior a cinco días hábiles, condicionado al convenio, garantía y factura; ver cláusula completa | [Oficial/documento](https://villaelisa.gov.ar/descargas/transparencia/licitaciones%20y%20concursos/2026/concursos%20de%20precios/001-26/2026_001%20CONCURSO%2060%20M3%20HORMIGON%20ELABORADO%20H21%20-%20Veredas%20Escenario.pdf) |

Las fechas de apertura/publicación y presupuestos no extraídos permanecen desconocidos. No se afirman abiertas estas convocatorias ni se inventa un plazo de pago para el segundo llamado. Los dieciséis conceptos incompletos y la extracción de fechas/estados desde sus documentos son trabajo pendiente.

## Candidatas y cobertura pendiente

Se consultaron las **91 URLs originales** en [descubrimiento #17](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40737464889). Causas: 50 sin identidad/jurisdicción suficiente, 25 errores de red (timeout, TLS o HTTP), ocho redirecciones a contrastar, seis sin extracción completa y dos PDF aislados sin identidad HTML. Cero promociones.

Tras las búsquedas siguientes, [#20](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40743856677) acumula **105 URLs candidatas**, una validada previamente —Funes— y **104 pendientes**; consultó cien en su última tanda, validó cero e incorporó cero. Cuatro no fueron consultadas en esa última tanda; no se afirma haber validado todas las acumuladas. Se mantienen las 74 fuentes configuradas y no se declara cobertura territorial completa. Prioridades: accesos alternativos públicos autorizados, Chajarí/Ramallo y boletines con identidad comprobada pero sin extracción, completar Villa Elisa y los objetos/adjuntos de parciales.

## Consultar y ejecutar el piloto

Descargar [radar-controlado de #131](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40745969935/artifacts/12842955107), descomprimir y abrir `index.html`. Las 3.691 filas están presentes. Incluye todas las oportunidades detectadas, historial, novedades/cambios de la corrida, abiertas, próximas a vencer, enlaces oficiales y a documentos identificados, pago y respaldo, JSON/Markdown y auditoría por fuente. Sin filtros por rubro, monto, modalidad o financiación ni límite comercial de cantidad. Se priorizan contado/contra entrega comprobados y llamados especiales; no se calculan costos ni rentabilidad.

Con el estado diario preparado, el punto de entrada probado es:

```sh
gh workflow run radar-diario.yml --ref mejora/radar-auditable -f modo=controlado -f canal=piloto
```

El disparador API quedó validado mediante ejecuciones reales independientes. **La periodicidad diaria aún no está instalada en esta rama:** GitHub sólo ejecuta cron desde la rama predeterminada. Para las 08:00 Argentina sin modificar `main` hace falta conectar un programador externo a este disparador. No se activa un cron ni producción en esta etapa. La producción requiere su autorización separada; este PR no se fusiona.

## Auditoría individual de #131

| Organismo | Portal | Estado | Publicaciones | Incidencia |
|---|---|---|---:|---|
| Municipalidad de Rosario | [Oficial](https://www.rosario.gob.ar/inicio/compras-y-licitaciones) | PARCIAL | 14 | URLError |
| Gobierno de Santa Fe | [Oficial](https://compras.santafe.gob.ar/) | BLOQUEADA | 0 | URLError |
| EPE | [Oficial](https://www.epe.santafe.gov.ar/app2/aperturas) | BLOQUEADA | 0 | HTTPError 500 |
| ASSA | [Oficial](https://www.aguassantafesinas.com.ar/portal/licitaciones) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| UNR | [Oficial](https://compras.unr.edu.ar/) | BLOQUEADA | 0 | HTTPError 403 |
| Poder Judicial de Santa Fe | [Oficial](https://www.justiciasantafe.gov.ar/index.php/poder-judicial/informacion-general/compras-y-licitaciones/) | BLOQUEADA | 0 | URLError |
| Aeropuerto Internacional Rosario | [Oficial](https://aeropuertorosario.com/institucional/licitaciones/) | PARCIAL | 37 | TIEMPO_FUENTE |
| Municipalidad de Casilda | [Oficial](https://www.casilda.gob.ar/web/licitaciones-casilda/) | OPERATIVA | 68 | — |
| Municipalidad de Carcarañá | [Oficial](https://xn--carcaraa-j3a.gob.ar/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Cañada de Gómez | [Oficial](https://cdg.gob.ar/transparencia/licitaciones-y-concursos/) | BLOQUEADA | 0 | HTTPError 403 |
| Municipalidad de Armstrong | [Oficial](https://armstrong.gov.ar/index.php/transparencia) | OPERATIVA | 7 | — |
| Municipalidad de Las Parejas | [Oficial](https://lasparejas.gov.ar/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Funes | [Oficial](https://funes.gob.ar/) | OPERATIVA | 39 | — |
| Municipalidad de Roldán | [Oficial](https://www.roldan.gov.ar/wp/documents/licitaciones-y-contrataciones/) | PARCIAL | 86 | TIEMPO_FUENTE |
| Municipalidad de Pérez | [Oficial](https://perez.opendata.junar.com/home/) | PENDIENTE | 0 | ValueError |
| Municipalidad de Villa Gobernador Gálvez | [Oficial](https://vggmunicipalidad.gov.ar/licitaciones/) | OPERATIVA | 106 | — |
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
| Municipalidad de Victoria | [Oficial](https://victoria.gob.ar/web-compras/Invitaciones-Compras/concurso-de-precios/) | PARCIAL | 397 | DetalleIncompleto, HTTPError 429 |
| Municipalidad de San José | [Oficial](https://sanjose.gob.ar/concursos-licitaciones/) | OPERATIVA | 152 | — |
| Municipalidad de Colón | [Oficial](https://colon.gov.ar/compras-contratos-suministros/licitaciones/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Concepción del Uruguay | [Oficial](https://www.cdeluruguay.gob.ar/index.php/servicios-web/data-gov/licitaciones) | OPERATIVA | 266 | — |
| Municipalidad de Gualeguaychú | [Oficial](https://w3.gualeguaychu.gov.ar/tramites/compras-y-licitaciones/acceso-a-licitaciones-p%C3%BAblicas) | BLOQUEADA | 0 | URLError |
| Municipalidad de Gualeguay | [Oficial](https://municipalidad.gualeguay.gob.ar/modulos/transparencia/licitaciones_publicas.php) | OPERATIVA | 7 | — |
| Municipalidad de Crespo | [Oficial](https://www.crespo.gob.ar/licitaciones-privadas-2026/) | OPERATIVA | 7 | — |
| Municipalidad de Crespo | [Oficial](https://www.crespo.gob.ar/category/licitacion-publica/) | PARCIAL | 175 | DetalleIncompleto, HTTPError 404 |
| Municipalidad de Chajarí | [Oficial](https://chajari.gob.ar/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Municipalidad de Federación | [Oficial](https://www.federacion.gob.ar/licitaciones) | PARCIAL | 114 | TIEMPO_FUENTE, ValueError |
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
| Municipalidad de Alvear | [Oficial](https://alvear.gob.ar/index.php?anio=2025&pagina=licitaciones) | PARCIAL | 61 | TIEMPO_FUENTE |
| Municipalidad de San Lorenzo | [Oficial](https://sanlorenzo.gob.ar/licitaciones/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| IAFAS | [Oficial](https://www.iafas.gov.ar/proveedores/licitaciones/) | PARCIAL | 98 | DetalleIncompleto |
| Universidad Nacional de Entre Ríos (UNER) | [Oficial](https://compras.uner.edu.ar/) | BLOQUEADA | 0 | HTTPError 401 |
| Municipalidad de Colón | [Oficial](https://www.municipalidadcolonpba.gob.ar/licitaciones.php) | PARCIAL | 63 | DetalleIncompleto, HTTPError 404 |
| Boletín Oficial de Santa Fe | [Oficial](https://www.santafe.gov.ar/boletinoficial/) | BLOQUEADA | 0 | URLError |
| Boletín Oficial de Entre Ríos | [Oficial](https://www.entrerios.gov.ar/boletin/) | PENDIENTE | 0 | SinPublicacionesDetectadas |
| Comuna de General Lagos | [Oficial](https://cglagos.gob.ar/comuna/compras-y-licitaciones) | OPERATIVA | 10 | — |
| Comuna de Arequito | [Oficial](https://comunaarequito.gob.ar/licitaciones/) | OPERATIVA | 10 | — |
| Comuna de Chabás | [Oficial](https://chabas.gob.ar/descargas/92-licitaciones/129-licitaciones-2026/5002-licitacion-publica-01-2026) | OPERATIVA | 3 | — |
| Gobierno de Timbúes | [Oficial](https://www.timbues.gob.ar/index.php?pagina=lista&sec=210) | PARCIAL | 134 | TIEMPO_FUENTE |
| Municipalidad de Sunchales | [Oficial](https://sunchales.gob.ar/gestion/sunchales-impulsa/municipio-transparente/licitaciones-y-contrataciones/) | OPERATIVA | 80 | — |
| Concejo Municipal de Santa Fe | [Oficial](https://www.concejosantafe.gov.ar/concursos-y-licitaciones) | OPERATIVA | 2 | — |
| Municipalidad de Villa Elisa | [Oficial](https://villaelisa.gov.ar/transparencia/) | PARCIAL | 87 | DetalleIncompleto |
| Municipalidad de General Ramírez | [Oficial](https://www.generalramirez.gob.ar/licitaciones-y-concursos/) | OPERATIVA | 88 | — |
| Municipalidad de Lucas González | [Oficial](https://lucasgonzalez.gob.ar/licitaciones-y-concursos/) | OPERATIVA | 2 | — |
| Municipalidad de San Salvador | [Oficial](https://sansalvadorer.gob.ar/) | OPERATIVA | 11 | — |
| Municipalidad de Salto | [Oficial](https://salto.gob.ar/licitaciones/) | BLOQUEADA | 0 | HTTPError 403 |
| Municipalidad de Junín | [Oficial](https://www.junin.gob.ar/servicio/licitaciones-y-concursos) | PARCIAL | 29 | TIEMPO_FUENTE |
| Municipalidad de Zárate | [Oficial](https://zarate.gob.ar/licitaciones-publicas/) | OPERATIVA | 31 | — |
| Municipalidad de San Andrés de Giles | [Oficial](https://www.sanandresdegiles.gob.ar/?q=licitaciones-publicas) | OPERATIVA | 3 | — |
| Municipalidad de Funes | [Oficial](https://funes.gob.ar/boletin_oficial) | OPERATIVA | 39 | — |
