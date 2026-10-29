# Recuperación y calidad del radar — 29/10/2026

El PR #1 permanece abierto. `main` y el historial diario no cambiaron en esta etapa. Se trabajó y auditó exclusivamente en `mejora/radar-auditable`, con copias independientes del respaldo.

El inventario fijo contiene 73 organismos y 79 portales; 77 están incorporados al monitoreo. Las candidatas pendientes se contabilizan aparte.

La auditoría completa consultó y finalizó las 77 fuentes configuradas a las 17:51, hora argentina. El consolidado incorpora las reverificaciones posteriores de San Nicolás y Chajarí. No se declara cobertura territorial completa ni se equipara primera detección con publicación reciente.

| Estado | Antes: 74 | Última observación: 77 |
|---|---:|---:|
| Operativas con publicaciones reales | 34 | 35 |
| Parciales | 14 | 9 |
| Bloqueadas | 14 | 23 |
| Pendientes | 11 | 9 |
| Sin publicaciones, confirmado expresamente | 1 | 1 |

La recuperación de conectores no equivale a una mejora general de disponibilidad: durante la última corrida aumentaron los desafíos HTTP 200 y los fallos TLS. Se conservan y reportan los datos anteriores. Ningún bloqueo se convirtió en un supuesto portal vacío.

## Recuperaciones efectivas y nuevas fuentes

| Organismo / sección | Resultado real | Alcance / límite |
|---|---|---|
| ASSA | API pública recuperada: 4 procedimientos, paginación y fichas | No usar la fecha sugerida como publicación comprobada. Localidad del procedimiento desconocida cuando `localidades=[]`; no confundir sede u oficina de apertura con lugar de prestación. |
| Reconquista, licitaciones | 13 procedimientos; fuente nuevamente operativa | Se mantienen adjuntos y condiciones verificadas. |
| Reconquista, concursos de precios — nueva | 14 procedimientos; operativa | Incluye procedimientos históricos; no se cuentan como publicaciones nuevas del día. |
| Reconquista, concursos de ofertas — nueva | 3 procedimientos; operativa | Incluye concesiones: nunca se presume que un canon sea un cobro del proveedor. |
| Chajarí | API pública POST recuperada: 699 procedimientos, abiertas, en evaluación y adjudicadas; archivo paginado | No se registran oferentes ni ofertas; no se recopilan sus datos de contacto. |
| Gualeguay | 6 procedimientos; recuperada la página grande con límite explícito de 32 MB | El resto conserva el máximo de 12 MB; exceder un límite se informa como incidencia. |
| San Nicolás | 20 procedimientos reales en 9 documentos; operativa tras regresión | 6 enlaces colectivos se relacionan con los procedimientos del PDF. Archivo observado 2018–2019: no acredita cobertura de convocatorias de 2026. |
| Humboldt — nueva | Dos convocatorias históricas comprobadas en una captura oficial | La última consulta encontró desafío de acceso: se cuenta bloqueada, no operativa. |

**Fuentes nuevas configuradas: 3; operativas: 2; parciales: 0; bloqueadas: 1; pendientes de extracción: 0.** Las pendientes de descubrimiento se cuentan aparte.

## Procedimientos y calidad de datos

- Historial aislado: 3.697 → 4.426 registros; catálogo comercial único: 4.408. Los 18 duplicados legados se unifican en la vista, sin borrar ninguna fila ni versión. Se conserva la relación entre IDs y URLs originales.
- 0 publicaciones nuevas con fecha de publicación comprobada; 8 detecciones sin fecha suficiente; 720 incorporaciones de línea de base y 1 recuperación histórica por año de procedimiento. No presentar las 729 incorporaciones como novedades publicadas hoy.
- 12 modificaciones y 95 registros con datos completados en la corrida. Las mejoras de representación sin diferencias semánticas no generan novedades.
- Conservados los 3.697 IDs previos y las 3.758 versiones previas; 4.594 versiones en la copia ampliada. Cero registros anteriores repetidos como nuevos.
- 51 oportunidades abiertas según la última fecha conocida: 23 observadas en esta corrida. 20 próximas a vencer: 9 observadas en esta corrida. Las restantes requieren reconfirmar su fuente.
- Separación entre publicación, apertura y límite de presentación. Un límite de presentación ya vencido prevalece sobre una apertura futura. Si falta hora en un cierre de hoy, no se asegura que la convocatoria siga abierta.
- Detección de presentación online, por correo electrónico o presencial sólo con contexto expreso. Las remisiones ambiguas siguen desconocidas.
- XLS/XLSX se leen como datos y fechas, sin ejecutar fórmulas ni macros; se acotan tamaños y celdas. Los XLS enlazados erróneamente por Villaguay siguen pendientes y no se inventan destinos alternativos.

## Pago y documentos

El catálogo deduplicado contiene **100 condiciones de pago verificadas documentalmente y 4.308 pendientes**. Son evidencias del catálogo, no una afirmación de que los 100 documentos se hayan revalidado por HTTP hoy. La reclasificación reutiliza citas y hashes guardados; no descarga de nuevo un pliego sólo porque cambió el analizador.

Clasificaciones: 4 contra entrega; 38 a 5 días; 3 a 10 días; 2 a 15 días; 18 a 30 días; 9 con otros plazos; 9 mixtas; 9 con opciones publicadas; 5 contra presentación de factura; 2 con pagos parciales; 1 contra factura conformada. No hubo contado puro comprobado bajo la interpretación conservadora de sus definiciones.

Se distinguen entrega, factura presentada, factura recibida/conformada, recepción conforme y aprobación administrativa. Se reconocen anticipos y pagos parciales explícitos, sin convertir instrucciones genéricas para que el oferente proponga condiciones en una condición seleccionada. No se supone que la palabra contado anule un plazo definido en el propio pliego.

El pliego y decreto de Chajarí 19/2026 se descargó realmente mediante el endpoint público de lectura: PDF de 5.845.179 bytes, SHA-256 `2b0bd43c642b8ecc8691d43b781a8391d70582baebb5e2b06b309df1e5c5304f`. La descarga posterior con plazo de 45 segundos pasó. Requiere OCR: el pago queda **Pago no informado**, sin inferencias. Estas descargas grandes se serializan por portal y se cachean. El endpoint de inscripción de oferentes se rechaza expresamente.

[Las 100 condiciones, citas y enlaces](pagos_verificados.json) · [Prueba del procedimiento y pliego de Chajarí](ejemplo_chajari.json).

## Ejemplos verificables

| Organismo | Procedimiento / objeto | Fecha comprobada | Monto / pago | Enlace |
|---|---|---|---|---|
| Chajarí | Licitación pública 19/2026 — repuestos para retroexcavadoras | Apertura 19/11/2026, 10:00 Argentina | 59.500.000, moneda no explicitada; pago no informado, requiere OCR | [Procedimiento y descarga del pliego](https://licitaciones.chajari.gob.ar/licitaciones?state=para_apertura?id=710) |
| ASSA | Publicación 1729 — cajas y bases para conexiones domiciliarias | Apertura y límite 16/11/2026, 10:00 Argentina; publicación desconocida | Presupuesto y pago desconocidos | [Ficha pública oficial](https://www.aguassantafesinas.com.ar/api/v1/publico/pliego/e5f2051e251a46adbc356bc8a342145b) |
| Reconquista — nueva sección | Concurso de precios 1/2026 — sistema de gestión web operativa y reclamos | Fecha no comprobada en el listado; recuperación de línea de base | Sin monto inventado | [Listado oficial](https://reconquista.gob.ar/concurso-de-precios/) |
| Reconquista — nueva sección | Concurso de ofertas 3/2026 — concesión de local del complejo Pucará | Fecha no comprobada en el listado; recuperación de línea de base | Sin condición de pago supuesta | [Listado oficial](https://reconquista.gob.ar/concurso-de-ofertas/) |

## Descubrimiento y deuda territorial

Dos lotes revisaron 111 URLs únicas, incluyendo el conjunto previo. El proceso descubrió 3 URLs adicionales, validó 0 fuentes nuevas y promovió 0 automáticamente: no se rebajaron los controles para mejorar el contador. Su inventario quedó con 112 URLs, una fuente validada previamente y 111 pendientes. Se conservaron además 4 contrastes del agente —UTN Paraná, UADER y los nuevos índices de Ramallo/SIBOM—, tres URLs adicionales únicas a la cola.

El descubrimiento periódico se conecta ahora al trabajador diario después del respaldo: cada tres días, hasta 180 segundos, 12 búsquedas y 36 candidatos, rotando el padrón. Los límites acotan solicitudes, no las oportunidades informadas. Un cron ubicado sólo en la rama no era suficiente para ejecutarlo. Los candidatos dudosos conservan evidencia y motivo.

Padrón existente: 365 gobiernos locales de Santa Fe, 239 de Entre Ríos y 51 bonaerenses en el radio geodésico aproximado de 280 km. No certifica distancias viales ni exhaustividad administrativa vigente. En la última observación hay portal municipal/comunal operativo para 9 de Santa Fe, 10 de Entre Ríos y 5 bonaerenses.

[Padrón completo y localidades sin cobertura operativa](cobertura_territorial.csv). Falta una gran parte del territorio, incluidos organismos sectoriales. No se declara cobertura completa por tener el padrón.

## Fuentes con incidencias, una por una

| Organismo | Estado | Causa observada | Portal |
|---|---|---|---|
| Municipalidad de Rosario | PARCIAL | RED: <urlopen error timed out> | [Portal](https://www.rosario.gob.ar/inicio/compras-y-licitaciones) |
| Gobierno de Santa Fe | BLOQUEADA | RED: <urlopen error timed out> | [Portal](https://compras.santafe.gob.ar/) |
| EPE | BLOQUEADA | RED: HTTP Error 500: Internal Server Error | [Portal](https://www.epe.santafe.gov.ar/app2/aperturas) |
| UNR | BLOQUEADA | RED: HTTP Error 403: Forbidden | [Portal](https://compras.unr.edu.ar/) |
| Poder Judicial de Santa Fe | BLOQUEADA | RED: <urlopen error timed out> | [Portal](https://www.justiciasantafe.gov.ar/index.php/poder-judicial/informacion-general/compras-y-licitaciones/) |
| Aeropuerto Internacional Rosario | PARCIAL | RED: Plazo agotado; se conserva lo extraído | [Portal](https://aeropuertorosario.com/institucional/licitaciones/) |
| Municipalidad de Carcarañá | BLOQUEADA | RED: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1016)> | [Portal](https://xn--carcaraa-j3a.gob.ar/) |
| Municipalidad de Cañada de Gómez | BLOQUEADA | RED: HTTP Error 403: Forbidden | [Portal](https://cdg.gob.ar/transparencia/licitaciones-y-concursos/) |
| Municipalidad de Las Parejas | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://lasparejas.gov.ar/) |
| Municipalidad de Roldán | PARCIAL | RED: Plazo agotado; se conserva lo extraído | [Portal](https://www.roldan.gov.ar/wp/documents/licitaciones-y-contrataciones/) |
| Municipalidad de Pérez | PENDIENTE | EXTRACCION: Redirección fuera de dominios oficiales declarados | [Portal](https://perez.opendata.junar.com/home/) |
| Municipalidad de Santo Tomé | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://www.santotome.gob.ar/ciudadania/Informacion_Publica_y_Transparencia) |
| Municipalidad de Santa Fe | BLOQUEADA | RED: HTTP Error 403: Forbidden | [Portal](https://transparencia.santafeciudad.gov.ar/compras-y-contrataciones/) |
| Municipalidad de Santa Fe | BLOQUEADA | RED: HTTP Error 403: Forbidden | [Portal](https://transparencia.santafeciudad.gov.ar/contrataciones-obra/) |
| Gobierno de Entre Ríos | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://portal.entrerios.gov.ar/haciendayfinanzas/contrataciones/) |
| ENERSA | BLOQUEADA | RED: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)> | [Portal](https://www.enersa.com.ar/area-proveedores/) |
| Instituto Becario | BLOQUEADA | RED: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)> | [Portal](https://institutobecario.gov.ar/licitaciones.php) |
| Municipalidad de Victoria | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://victoria.gob.ar/web-compras/Invitaciones-Compras/concurso-de-precios/) |
| Municipalidad de Colón | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://colon.gov.ar/compras-contratos-suministros/licitaciones/) |
| Municipalidad de Gualeguaychú | BLOQUEADA | RED: <urlopen error timed out> | [Portal](https://w3.gualeguaychu.gov.ar/tramites/compras-y-licitaciones/acceso-a-licitaciones-p%C3%BAblicas) |
| Municipalidad de Crespo | PARCIAL | EXTRACCION: Publicaciones identificadas sin objeto completo; RED: HTTP Error 404: Not Found | [Portal](https://www.crespo.gob.ar/category/licitacion-publica/) |
| Municipalidad de Federación | PARCIAL | EXTRACCION: Plazo agotado; se conserva lo extraído; EXTRACCION: Respuesta supera 12000000 bytes; recorrido parcial | [Portal](https://www.federacion.gob.ar/licitaciones) |
| Municipalidad de Villaguay | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://villaguay.gob.ar/boletindigital/) |
| Municipalidad de San Pedro | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://sanpedro.net.ar/portal.php) |
| Municipalidad de Pergamino | PENDIENTE | ACCESO: El portal requiere autenticación o red privada; no se elude | [Portal](https://compras.pergamino.gob.ar/) |
| Municipalidad de Arrecifes | BLOQUEADA | RED: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1016)> | [Portal](https://arrecifes.gob.ar/informacion-publica/licitaciones/) |
| Municipalidad de Alvear | BLOQUEADA | RED: <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: self-signed certificate (_ssl.c:1016)> | [Portal](https://alvear.gob.ar/index.php?anio=2025&pagina=licitaciones) |
| Municipalidad de San Lorenzo | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://sanlorenzo.gob.ar/licitaciones/) |
| IAFAS | PARCIAL | EXTRACCION: Publicaciones identificadas sin objeto completo | [Portal](https://www.iafas.gov.ar/proveedores/licitaciones/) |
| Universidad Nacional de Entre Ríos (UNER) | BLOQUEADA | RED: HTTP Error 401: Unauthorized | [Portal](https://compras.uner.edu.ar/) |
| Municipalidad de Colón | PARCIAL | EXTRACCION: Publicaciones identificadas sin objeto completo; RED: HTTP Error 404: Not Found | [Portal](https://www.municipalidadcolonpba.gob.ar/licitaciones.php) |
| Boletín Oficial de Santa Fe | BLOQUEADA | RED: <urlopen error timed out> | [Portal](https://www.santafe.gov.ar/boletinoficial/) |
| Boletín Oficial de Entre Ríos | PENDIENTE | EXTRACCION: Listado no reconocido; no se declara vacío | [Portal](https://www.entrerios.gov.ar/boletin/) |
| Comuna de Arequito | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://comunaarequito.gob.ar/licitaciones/) |
| Comuna de Chabás | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://chabas.gob.ar/descargas/92-licitaciones/129-licitaciones-2026/5002-licitacion-publica-01-2026) |
| Gobierno de Timbúes | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://www.timbues.gob.ar/index.php?pagina=lista&sec=210) |
| Municipalidad de Villa Elisa | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://villaelisa.gov.ar/transparencia/) |
| Municipalidad de San Salvador | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://sansalvadorer.gob.ar/) |
| Municipalidad de Salto | PARCIAL | RED: HTTP Error 403: Forbidden | [Portal](https://salto.gob.ar/licitaciones/) |
| Municipalidad de Junín | PARCIAL | RED: Plazo agotado; se conserva lo extraído | [Portal](https://www.junin.gob.ar/servicio/licitaciones-y-concursos) |
| Comuna de Humboldt | BLOQUEADA | ACCESO: Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo | [Portal](https://www.humboldt.gob.ar/) |

[Auditoría estructurada de las 77 fuentes](fuentes.json) · [CSV de fuentes](fuentes.csv).

Próximo lote: EPE (HTTP 500) y Compras Santa Fe/Poder Judicial/Boletín (tiempos de espera); verificar certificados de ENERSA, Instituto Becario y otros portales con TLS inválido por vías oficiales; resolver acceso público de UNR/UNER y Santa Fe capital sin eludir 401/403; recuperar documentos de Federación y enlaces XLS de Villaguay; completar los objetos faltantes en Villa Elisa e IAFAS; mejorar el recorrido restante de Aeropuerto Rosario y Roldán. Concordia, Ramallo, hospitales/SAMCo y universidades requieren todavía conectores propios comprobados.

## Informe diario y puesta en marcha

El orden comercial es: desiertas/segundos llamados/reaperturas; contado/contra entrega o plazo corto comprobado; presupuesto agrupado por moneda sin conversión; límite de presentación o apertura referencial. No se calcula rentabilidad ni se buscan proveedores. Se conservan todas las filas, incluidas las de pago largo o desconocido. Las pruebas incluyen 105 oportunidades sin truncamiento.

El trabajador prepara Markdown, JSON, CSV seguro para planillas y un `.eml` con adjuntos. Tras el siguiente escaneo diario exitoso publicará [el último informe íntegro](https://github.com/tobiastorrescc/Radar---Licitaciones/blob/mejora/radar-auditable/piloto_reportes/ultimo/informe.md) en esta rama. Hasta entonces están los artefactos de auditoría. Los commits conservan informes anteriores. El `.eml` no se envía.

[Alternativas gratuitas y permisos para el correo](../../ENTREGA_DIARIA.md): GitHub para consulta y alertas; cuenta Gmail existente con autorización y método de acceso permitido, o proveedor transaccional gratuito sujeto a sus requisitos. No se configuraron destinatarios ni credenciales ni se activó ningún envío.

El programador de `main` conserva `dfca1a52c5371929ce6c07741a88fd209a7da852`: 08:00 Argentina y supervisión 09:30, sin reactivar el cron antiguo. Hoy los eventos programados terminaron correctamente a las 08:32 y 10:35, con retrasos de GitHub respecto al horario solicitado y sin otro escaneo del día. Los cambios del trabajador se probaron aisladamente; el primer escaneo diario con esta ampliación queda para el próximo disparo.

El respaldo diario conserva 6 corridas, 3.697 procedimientos y 3.758 versiones, con hash lógico `af90259db6892b9d7821b4d3a03acfc5ecefb6cc9e1ea5599eaa825684ef5815`. La auditoría ampliada se archivó y restauró desde [`piloto_respaldo/auditorias/2026-10-29`](../../piloto_respaldo/auditorias/2026-10-29), independiente del diario. Los artefactos adicionales se conservan 90 días; la cadena Git no depende de su expiración.

## Validaciones realizadas

- 313 pruebas nativas en GitHub Actions: 285 Python + 28 JavaScript, sin omisiones ni fallos. La única omisión local por sockets restringidos se ejecutó y pasó en el runner nativo.
- [Auditoría completa de 77 fuentes y respaldo/continuidad](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40952155721).
- [Regresión real de San Nicolás](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40952782930).
- [Chajarí: procedimiento y PDF público comprobados con límites corregidos](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40955443854).
- [Reclasificación nativa de citas reales y archivo Git restaurado](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40954765037).
- [Suite de regresión del trabajador](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40955444116).
- [Disparo horario de hoy](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40866101791) y [supervisión horaria](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40883379312).

[Métricas reproducibles](resultado.json) · [Continuidad sin pérdida ni falsas novedades](continuidad.json) · [Reclasificación de citas](reproceso_resultado.json).
