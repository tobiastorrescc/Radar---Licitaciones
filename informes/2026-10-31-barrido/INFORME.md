# Barrido territorial y recuperación efectiva — 31/10/2026

Entrega de una etapa comprobada. **La auditoría exhaustiva de las 20 localidades NO está finalizada.** Hay20 localidades revisadas,16 con procedimientos extraídos y 4 sin cobertura efectiva demostrada. Los accesos fallidos y contenido no útil permanecen pendientes; no se contabilizan como cobertura.

## Resultado comercial comprobado

- **21 oportunidades abiertas nuevas para el radar**:20 del portal provincial entrerriano recuperado y 1 de Obras Públicas UNR. No significa21 publicaciones emitidas hoy.
-45 convocatorias abiertas observadas en las capturas:24 ya catalogadas y21 omitidas anteriormente.26 procedimientos vencidos recuperados se separan de las oportunidades comerciales;66 registros nuevos para la comparación tienen vigencia pendiente.
-1.818 registros en el barrido inicial;2.001 observaciones consolidadas tras correcciones y complementos (incluyen16 candidatos no confirmados). El número de filas no equivale a oportunidades vigentes.
-Muestra de control documentada:32 avisos de la respuesta pública ER másUNR 5/2026. El catálogo previo contenía12 de 33 (36,36%); el conector corregido recupera33 de 33 (100%). **Ese porcentaje sólo describe esta muestra, no las provincias ni los 20 municipios completos.**
-79 fuentes configuradas en el piloto frente a78 anteriores. Se agregó1 ruta UNR y se recuperó1 fuente existente ER. El barrido comprobó39 rutas:15 operativas con publicaciones,8 parciales (incluyen4 tiempos agotados),12 inaccesibles y 4 pendientes. No son los estados de las 79 fuentes completas.

El comparativo usa el catálogo de 4505 vistas únicas de la auditoría anterior41200546592 y el índice persistente de auditorías accesibles. Los12 avisos ER ya conocidos incluyen11 del Poder Judicial y 1 de Vialidad. Se conserva la identidad por organismo, modalidad y procedimiento: compartir número no basta para unificar. Seis filas etiquetadas genéricamente como solicitudes son cotejos expresos en su objeto; se conserva esa evidencia para evitar anunciarlos otra vez.

## Correcciones reutilizables

1. Descubrimiento independiente: registrar avisos válidos sin exigir número, presupuesto, pliego o pago; los avisos sin número requieren una convocatoria y compra concreta, excluyendo normativa y alta de proveedores. Enriquecimiento posterior en `cola_enriquecimiento.json`; no bloquea la incorporación.
2. Portal ER: su HTML es una aplicación vacía para el lector estático. Se siguieron sus scripts oficiales hasta identificar y probar la API pública que utiliza. El adaptador recupera las 32 próximas aperturas con organismo, objeto, procedimiento y fecha. No utiliza autenticación ni evita desafíos de acceso. Archivo, otros endpoints y modalidades todavía requieren revisión.
3. UNR: incorporar Obras Públicas además de Diaguita, que responde403. Recuperar fechas de la ficha oficial y su objeto; el pliego inaccesible no impide registrar el aviso. Se preservan separadas las dosLP3/2026 de objetos distintos, sin inferir que sean el mismo procedimiento.
4. Carcarañá: reconocer “Boletines oficiales” en plural. Se alcanza la sección, pero no ofrece avisos útiles en el HTML observado. Las Parejas: habilitar lectura del documento del índice; el PDF disponible es una plantilla Lorem ipsum y no prueba contrataciones.
5. Armstrong: seguir sección anual de licitaciones y noticias, además del archivo de descargas.7 registros iniciales frente a84 posteriores; siguen pendientes el archivo completo y fechas de algunos avisos. El llamado13/2026 de la pick-up abrió 22/10: no se anuncia como oportunidad vigente.
6. PJER: completar listados antes de fichas y consultar luego según el orden del índice reciente.51 procedimientos conservados; la API provincial confirma11 aperturas futuras ya conocidas. La paginación existía: la omisión principal era la lectura de fechas, no ausencia de paginación.
7. Informe: separar convocatorias recuperadas aún abiertas, vencidas y recuperaciones de vigencia pendiente. Las fechas de creación del CMS se conservan como evidencia, sin convertirlas en fechas de publicación.

## Auditoría de las 20 localidades — estado real

Los contadores incluyen archivo histórico. “Operativa” significa que el conector extrajo procedimientos en la sección revisada, no que se agotaron todas las publicaciones alternativas. Las secciones, errores individuales y última revisión están en[inventario/barrido_estado.json](../../inventario/barrido_estado.json).

|Localidad|Publicaciones extraídas|Abiertas observadas|Estado de la captura|Limitación|
|---|---:|---:|---|---|
|[Ramayón](https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026%2F2026-09-18licitaciones.html)|0|0|BLOQUEADA|Sitio propio no localizado. Avisos oficiales01/2026 y02/2026 en boletín18/09; acceso automático agota tiempo.01/2026 está vencida: apertura08/10.|
|[Casilda](https://www.casilda.gob.ar/web/licitaciones-casilda/)|69|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Carcarañá](https://xn--carcaraa-j3a.gob.ar/)|0|0|PENDIENTE|Se alcanzó boletines; el HTML publicado no contiene avisos ni enlaces documentales útiles. Pendiente contenido alternativo.|
|[Cañada de Gómez](https://cdg.gob.ar/transparencia/licitaciones-y-concursos/)|0|0|BLOQUEADA|HTTP403 en Actions; la lectura web permite ver índice. No se elude acceso.|
|[Armstrong](https://armstrong.gov.ar/index.php/transparencia)|84|0|TIEMPO_FUENTE|Índice antiguo de descargas omitía blog y categorías anuales.84 registros; recorrido histórico aún alcanza límite.|
|[Las Parejas](https://lasparejas.gov.ar/)|0|0|PENDIENTE|El único PDF enlazado como boletín Octubre-Diciembre contiene Lorem ipsum. No es evidencia de compras ni ausencia de convocatorias.|
|[Alvear](https://alvear.gob.ar/index.php?anio=2025&pagina=licitaciones)|64|0|PARCIAL|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Chajarí](https://chajari.gob.ar/)|699|1|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[La Paz](https://haciendalapaz.gob.ar/compras/)|50|2|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Victoria](https://victoria.gob.ar/web-compras/Invitaciones-Compras/concurso-de-precios/)|397|0|PARCIAL|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[General Lagos](https://cglagos.gob.ar/comuna/compras-y-licitaciones)|10|0|PARCIAL|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Arequito](https://comunaarequito.gob.ar/licitaciones/)|10|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Chabás](https://chabas.gob.ar/descargas/92-licitaciones/129-licitaciones-2026/5002-licitacion-publica-01-2026)|3|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Timbúes](https://www.timbues.gob.ar/index.php?pagina=lista&sec=210)|123|0|TIEMPO_FUENTE|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Humboldt](https://www.humboldt.gob.ar/)|2|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Villa Elisa](https://villaelisa.gov.ar/transparencia/)|87|0|PARCIAL|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[General Ramírez](https://www.generalramirez.gob.ar/licitaciones-y-concursos/)|88|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[Lucas González](https://lucasgonzalez.gob.ar/licitaciones-y-concursos/)|2|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[San Salvador](https://sansalvadorer.gob.ar/)|10|1|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|
|[San José](https://sanjose.gob.ar/concursos-licitaciones/)|152|0|OPERATIVA|La extracción actual no demuestra cobertura exhaustiva de boletines, modalidades ni archivo; continuar contraste.|

No se comprobó ninguna oportunidad municipal vigente inédita en esta muestra inicial. El aumento comercial efectivo vino de organismos provinciales y UNR. Ramayón y los otros municipios pendientes siguen siendo prioridad: la recuperación de compras pequeñas aún es insuficiente.

## Organismos importantes y portales provinciales

|Organismo|Resultado real|Pendiente|
|---|---|---|
|EPE|Índices con EOF TLS; compras y documento cierran conexión; ficha oficial 19015 devuelve HTTP500.|ERROR DE ACCESO. La búsqueda indexada muestra convocatorias; no equivale a recuperación automática ni a vigencia actual confirmada. No se informa sin novedades.|
|ASSA|API pública operativa:3 procedimientos vigentes1729,1728,1277.|Continuar control contra todas las secciones; no hubo una nueva convocatoria omitida confirmada aquí.|
|Poder Judicial ER|51 procedimientos reconocidos,11 aperturas futuras corroboradas mediante la API provincial.|La lectura de todas las fichas sigue excediendo65 s. Se guardan resultados parciales, no se pierde el listado.|
|Aeropuerto Rosario|49 publicaciones reconocidas,5 convocatorias abiertas observadas.|Recorrido aún agota tiempo; conservar cola y revisar modalidades restantes. Las 5 ya eran conocidas.|
|Poder Judicial SF|Timeout en sitio y boletín complementario.|Inaccesible desde Actions; no se declara cubierto.|
|UNR|Obras Públicas14 procedimientos, 1 vigente inédita; Noticias13 avisos contrastados.|Diaguita 403; faltan las restantes unidades de compra y acceso a pliegos.|
|Hospitales/Salud ER|6 nuevas convocatorias: lámpara de hendidura, camas, coagulómetro/electrolitos, ecógrafo, sillones odontológicos y lavadora de instrumental.|Recuperadas a través de Salud provincial; no equivale a auditar todos los portales propios de hospitales.|
|Hospitales/SAMCo SF|Boletines15/10 y19/10 y gestión139389 intentados;timeout.|No cubiertos. Hospital Alassia, Centenario y SAMCo Arroyo Seco conservan referencias para siguiente revisión.|
|Compras SF y Boletín SF|Timeout, incluso en variante oficial .gob.ar.|No se pudo agotar compras menores/directas ni recuperar Ramayón automáticamente.|
|Provincia ER|32 próximas aperturas reales recuperadas en1,22 s porAPI oficial.|No se declara cubierto el archivo completo, compras directas o todas las modalidades. API UEP devuelve64 registros históricos: pendiente adaptador, no incorporada.|

## Todas las21 vigentes recuperadas

[JSON íntegro](vigentes_recuperadas.json) · [CSV íntegro](vigentes_recuperadas.csv) · [Las45 abiertas observadas](vigentes_observadas.csv). Sin top ni filtros. Los enlaces ER apuntan al JSON oficial que publica los avisos; las fichas individuales y pliegos se incorporarán cuando sus rutas se comprueben. Presupuestos y pagos desconocidos no bloquean el descubrimiento.

|Organismo|Procedimiento|Objeto completo publicado|Apertura|Presupuesto|Evidencia oficial|
|---|---|---|---|---|---|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 238/2026|COMPRA DE LIBROS|2026-11-02 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 231/2026|reparacion de vehiculo oficial ford 100|2026-11-02 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 235/2026|COMPRA DE MATERIALES PARA CONFECCION DE SILLAS|2026-11-02 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|DIR. GRAL. DE CONTRATACIONES DEL ESTADO - MIN. DE ECONOMIA Y SERVICIOS PUBLICOS - PODER EJECUTIVO|licitacion privada 16/2026|Contratar el alquiler de treinta (30) equipos fotocopiadores, con suministro de insumos (tóner, repuestos, materiales y accesorios, excepto papel) con mantenimiento y servicio técnico de los mismos|2026-11-02 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 242/2026|COMPRA DE ARTICULOS DE LIBRERIA|2026-11-03 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 239/2026|compra de materiales electricos|2026-11-03 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 236/2026|COMPRA DE ABERTURA PARA ESC 37 AMBROSETTI GUALGUAY|2026-11-03 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|UNR|licitacion publica 5/2026|Obra Pública “Aulas 2° Piso Nido 1 – Etapa II – Escuela Preuniversitaria de Ciencias Sociales y Humanísticas”|2026-11-04 |2173527434.36 (moneda no explicitada)|[Publicación](https://unr.edu.ar/convocatoria-licitacion-publica-n-5-2026-aulas-2-piso-escuela-preuniversitaria-de-ciencias-sociales-y-humanisticas/)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 246/2026|COMPRA DE CORREA POLI V PARA CACTUS CITROEN|2026-11-05 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 245/2026|compra de componentes informaticos|2026-11-05 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|MIN. SALUD - PODER EJECUTIVO|licitacion publica 20/2026|Adquirir Quince (15) Sillones Odontológicos Completos solicitados por la Dirección de Odontología.-|2026-11-05 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 247/2026|REPARACION DE PUERTA DE INGRESO CGE|2026-11-06 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|Vialidad Entre Ríos|licitacion privada 33/2026|ADQUISICION DE REPUESTOS PARA MOTONIVELADORA NEW HOLLAND EQ. M-33|2026-11-06 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|CONSEJO GRAL. EDUCACION - MIN. GOBIERNO Y TRABAJO - PODER EJECUTIVO|solicitud de cotizacion 240/2026|servicio completo con mano de obra sprinter AF952RN|2026-11-09 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|DIR. GRAL. DE CONTRATACIONES DEL ESTADO - MIN. DE ECONOMIA Y SERVICIOS PUBLICOS - PODER EJECUTIVO|licitacion privada 17/2026|Adquirir elementos ortopédicos (bastones, sillas de ruedas, sillas posturales, sillas de ducha y bipedestadores).-|2026-11-11 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|MIN. SALUD - PODER EJECUTIVO|licitacion publica 21/2026|Adquirir Una (01) Lavadora Termodesinfectadora de Instrumental Quirúrgico.-|2026-11-11 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|MIN. SALUD - PODER EJECUTIVO|licitacion privada 22/2026|Adquirir Un (01) Ecógrafo básico.-|2026-11-13 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|MIN. SALUD - PODER EJECUTIVO|licitacion privada 23/2026|Adquirir Un (01) Analizador de Coágulos (Coagulómetro) y Un (01) Analizador Ión Selectivo (Electrolitos).-|2026-11-16 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|MIN. SALUD - PODER EJECUTIVO|licitacion privada 24/2026|Adquirir Diecisiete (17) Camas de Internación, colchones y almohadas.-|2026-11-18 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|DIR. GRAL. DE CONTRATACIONES DEL ESTADO - MIN. DE ECONOMIA Y SERVICIOS PUBLICOS - PODER EJECUTIVO|licitacion publica 13/2026|Adquirir 2.253 colchones de una plaza.|2026-11-19 09:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|
|MIN. SALUD - PODER EJECUTIVO|licitacion privada 25/2026|Adquirir Una (01) Lámpara de Hendidura.-|2026-11-24 10:00|No publicado/comprobado|[Publicación](https://portal.entrerios.gov.ar/api/public/consulta/contrataciones/licitaciones)|

La fecha de apertura es referencial cuando no se publica una fecha límite separada; no se garantiza posibilidad de presentar ofertas hasta ese instante. UNR 5/2026 sí informa presentación 04/11/2026 a 12:00 y el mismo horario de apertura. Publicación02/10; presupuesto2.173.527.434,36. No es una publicación nueva del 31/10. Para las 32 filas ER, la fecha de publicación queda pendiente:created_at no prueba cuándo se hizo público el aviso.

## Prueba controlada, historial y funcionamiento diario

[Barrido inicial41210359641](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41210359641), [correcciones39 rutas41211320771](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41211320771), [regresión41211936296](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41211936296), [API pública y fichas41212482113](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41212482113), [piloto comparativo41212723753](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41212723753). Los artefactos conservan capturas con URL, hash y errores por fuente.

El piloto restauró una copia independiente del respaldo diario y produjo un informe íntegro. Primera pasada:2.001 observaciones,16 candidatos sin confirmar,1.985 procedimientos comparados contra el respaldo,10 modificaciones,181 datos completados,36 primeras detecciones sin fecha,93 recuperaciones bajo las categorías del motor y 0 publicaciones nuevas del día con fecha comprobada. Esas categorías de eventos no sustituyen el contraste contra todas las auditorías:21 convocatorias están abiertas y eran inéditas para el catálogo accesible.

Segunda pasada sobre la misma captura: **0 novedades,0 eventos y1.985 SIN_CAMBIOS**. Persisten4.640 filas históricas; la vista unificada contiene4.621. Se conservan19 unificaciones previas, sin borrar registros. Producción y respaldo diario:hashes intactos.0  OCR nuevo y 0 consultas externas adicionales en el contraste.

El catálogo aislado calcula154 abiertas y 99 próximas, pero sólo45 abiertas se observaron en este barrido. Las demás se conservan por historial y requieren revalidación. No se anuncia vigencia comprobada de las 154.

No se cambió main, el programador diario ni el respaldo del piloto. No se activó correo ni servicios pagos. Los cambios están en la rama del PR #1; permanece sin fusionar. La etapa A reduce trabajo documental síncrono, conserva evidencias de pago anteriores y deja la cola de enriquecimiento separada.

## Continuidad prioritaria

1. Ramayón y otras comunas pequeñas: recuperar acceso al boletín oficial y localizar páginas propias sin inventarlas; ampliar muestra de oportunidades municipales vigentes.
2. EPE y Compras SF: continuar diagnóstico de HTTP500/EOF/timeout sobre rutas oficiales documentadas, sin eludir controles.
3. PortalER: incorporar archivo/buscador y modalidades restantes, validar rutas individuales y documentos; aprovecharAPI UEP ya localizada sin contar sus64 históricos como vigentes.
4. Carcarañá y Las Parejas: hallar avisos reales alternativos; el índice vacío o una plantilla no valida el conector.
5. Completar revisión de decretos/boletines en las 20 localidades y organismos sanitarios. La expansión masiva sigue detrás de este cierre territorial pendiente.

Pendientes persistentes:[inventario/pendientes_barrido20.json](../../inventario/pendientes_barrido20.json). Métricas descargables:[metricas.json](metricas.json).
