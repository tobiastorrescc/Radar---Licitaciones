# Detección efectiva, cobertura y pagos del piloto

Corte de la consulta: **29/10/2026, 22:15 Argentina** (30/10 UTC). Rama `mejora/radar-auditable`, PR #1 abierto. **La ejecución automática del 30/10 a las 08:00 Argentina todavía no ocurrió**: no se presenta esta prueba aislada como su resultado.

## Resultados comprobados

[Consulta real de 77 fuentes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40984204463) y [revisión focalizada de pliegos de abiertas](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40985751189), ambas completadas correctamente. Que Actions finalice correctamente no significa que funcionen todas las fuentes.

| Cobertura estricta | Auditoría anterior, mismas 77 fuentes | Consulta nueva, 77 fuentes |
|---|---:|---:|
| Operativa | 34 | **38** |
| Parcial | 10 | **14** |
| Bloqueada por acceso o problemas técnicos | 23 | **14** |
| Pendiente de extracción/verificación | 9 | **10** |
| Sin publicaciones confirmado | 1 | **1** |

La columna anterior usa el barrido completo #40952155721. La revisión puntual posterior de San Nicolás había elevado el consolidado a 35 operativas y 9 parciales; no se confunde esa revisión con otro barrido completo. El punto de partida diario de 74 fuentes tenía 34 operativas, 14 parciales, 14 bloqueadas, 11 pendientes y una vacía confirmada.

Hay **79 portales inventariados de 73 organismos**: 77 monitoreados y dos todavía no incorporados (Concordia y Ramallo). Esta etapa no agrega URLs al inventario. Recupera conectores y mejora la detección efectiva.

Consulta individual completa: [79 portales, evidencia y causas en JSON](cobertura_por_organismo.json) · [CSV por organismo](cobertura_por_organismo.csv). Incluye estado anterior/actual, publicaciones reconocidas, historial, abiertas observadas, errores y antecedentes. Los recuentos de procedimientos por fuente no deben sumarse como procedimientos únicos globales.

## Por qué las bloqueadas subieron de 14 a 23 y por qué ahora bajaron

Entre la base de 74 y el barrido ampliado, salieron de bloqueadas Reconquista y Colón ER; entraron once fuentes: ocho pantallas de desafío HTTP 200 y tres errores TLS. **14 − 2 + 11 = 23**. Una página HTTP 200 con desafío no es un listado válido. Los sondeos y la nueva extracción prueban que esa condición no fue permanente.

Las once recuperaron acceso, con estos resultados reales:

| Organismo | Estado nuevo | Procedimientos reconocidos en esta consulta |
|---|---|---:|
| Arrecifes | Operativa | 5 |
| Arequito | Operativa | 10 |
| Chabás | Operativa | 3 |
| San Salvador ER | Operativa | 11 |
| Humboldt | Operativa | 2 |
| Victoria | Parcial; HTTP 429 y detalles incompletos | 394 |
| Villaguay | Parcial; adjuntos 404 y tiempo de recorrido | 188 |
| Alvear | Parcial; tamaño documental y tiempo | 64 |
| Timbúes | Parcial; tiempo | 120 |
| Villa Elisa | Parcial; detalles incompletos | 87 |
| Carcarañá | Pendiente; HTML accesible, listado no reconocido | 0 |

Son **884 procedimientos reconocidos en las diez fuentes que vuelven a extraer**, principalmente históricos o ya conocidos; no 884 novedades. Humboldt tiene dos llamados históricos verificables y completa por primera vez el conector en este barrido. Carcarañá no tiene procedimientos confirmados en la línea de base: no se declara recuperada su extracción.

Ahora salieron once de bloqueadas, pero ingresaron Nogoyá (timeout) y Sunchales (DNS): **23 − 11 + 2 = 14**. En esas 14 hay **5 restricciones HTTP 401/403, 5 agotamientos de tiempo, 2 problemas de certificado TLS, 1 HTTP 500 y 1 DNS**. El verificador registra estas causas separadas; no declara permanencia por un único error.

De las 14, EPE, Nogoyá y Sunchales tienen publicaciones anteriores conservadas. En las otras once no hay procedimientos confirmados en el SQLite anterior de referencia. Entre las fuentes agregadas después de las 36 iniciales, UNER y Boletín Oficial SF siguen sin extracción confirmada. El inventario permite distinguirlas de un organismo que sí publicaba y falló temporalmente.

### EPE y Compras Santa Fe

- **EPE**: HTTP 500 en el portal configurado. Se comprobaron también el dominio oficial sin `www` y una ficha pública: fallos TLS/cierre de conexión. Se conservan sus 37 registros anteriores; 27 calculan apertura futura, pero **no fueron confirmados nuevamente**. Un resultado indexado por buscador no se cuenta como recuperación del conector.
- **Compras Santa Fe**: tiempo agotado en el portal y en la alternativa oficial de gestiones de compras; cero publicaciones confirmadas en esta consulta.
- No se deshabilitó TLS ni se sortearon autenticación, desafíos o restricciones. No se cambiaron las URLs operativas por alternativas que tampoco funcionan. Queda pendiente recuperar acceso oficial estable y luego verificar publicaciones.

## Fechas y nuevas detecciones

Se corrigió el reconocimiento de fechas para que **«Publicada para Apertura» sea un estado**, y no consuma ni desplace la fecha rotulada de apertura. Los campos vacíos no toman la fecha del campo siguiente. También se reconoce publicación rotulada en columnas de tablas y `Fecha Publicación` sin «de».

Sobre la misma evidencia de la auditoría anterior, **20 procedimientos recuperan apertura futura comprobable: las abiertas calculadas pasan de 51 a 71 sin descargar publicaciones nuevas** (18 Rosario, una Vialidad ER y una Ministerio de Planeamiento ER). Esta mejora de clasificación no se anuncia como una novedad comercial.

Se investigaron las [ocho detecciones sin fecha suficiente](auditoria_fechas.json): una era un contenedor incorrecto de múltiples tarjetas; se conserva como candidato, separado de las fichas genuinas. Las otras siete no permiten comprobar fecha de publicación. En Rosario los detalles agotan el tiempo; el listado muestra apertura, no publicación. El HTML oficial de Planeamiento tampoco contiene publicación comprobable; la fecha del decreto o del directorio PDF de Casilda no se usa como publicación.

Rosario ahora recorre primero los listados paginados y luego los detalles; recuperó **76 fichas genuinas**, frente a 16 publicaciones del extractor anterior en el último barrido. Queda parcial porque no logra descargar todos los detalles y pliegos. Se eliminó el parámetro de sesión `sid` de las URLs de sus fichas para evitar consultas repetidas al mismo documento.

Comparación real contra el **respaldo diario restaurado** de 3.697 filas:

| Clasificación | Cantidad |
|---|---:|
| Publicaciones nuevas con fecha comprobada | **0** |
| Detecciones sin fecha suficiente | **65** |
| Recuperaciones históricas/de línea de base | **724** |
| Modificaciones | **36** |
| Datos completados | **208** |
| Sin cambios | **3.126** |

Las 65 detecciones se reportan completas y separadas; no se descartan ni se inventa que fueron publicadas hoy. De ellas, 63 pertenecen a Rosario y dos a otras fuentes. El informe íntegro de Actions incluye cada evento, modificaciones y recuperaciones, sin límite ni filtros comerciales. Esta comparación usa la base diaria de 3.697; la auditoría ampliada anterior de 4.426 sigue archivada por separado y no se impuso sobre el piloto diario.

El nuevo catálogo aislado contiene **4.486 filas históricas, 4.790 versiones, 4.468 identidades de vista y 4.467 procedimientos**; una fila heredada es el contenedor inválido conservado. Los 3.697 IDs y las 3.758 versiones de la base diaria se conservaron, con cero repetidas como nuevas según el control de continuidad.

## Abiertas y pagos

Hay **129 abiertas calculadas**, de las cuales **102 fueron observadas en esta consulta** y 27 corresponden al historial EPE sin revalidación de acceso. **79** entran en la ventana de proximidad del radar; cuando no existe fecha límite de presentación se usa la apertura como referencia, debidamente identificada.

El análisis general reúne **96 pagos verificados**. La revisión focalizada agrega el de Chajarí: **97 oportunidades con evidencia verificada en conjunto**, sin insertar resultados de esta prueba en el historial diario. Entre las abiertas, **3 verificadas y 126 pendientes**; [lista completa de 129 abiertas y pagos](abiertas_y_pagos.md), [evidencias de las tres verificadas](pagos_verificados_abiertas.json) y [métricas y hashes de SQLite](pagos_abiertas_resultado.json).

| Organismo / procedimiento | Apertura | Pago comprobado | Respaldo |
|---|---|---|---|
| Chajarí, pública 19/2026; repuestos de retroexcavadoras | 19/11/2026 10:00 | **Contado contra entrega** | [Ficha oficial](https://licitaciones.chajari.gob.ar/licitaciones?state=para_apertura?id=710), pliego páginas 4 y 6 |
| Crespo, pública 6/2026; caños PVC cloacal | 17/11/2026 | 20 días hábiles desde presentación de factura | [Pliego oficial](https://www.crespo.gob.ar/wp-content/uploads/2026/10/LICITACION-PUBLICA-No-06-26-Pliego.pdf) |
| Aeropuerto Rosario, directa 52/2026; herramientas de reparación de pavimento | 03/11/2026 | 30 días después de conformidad de recepción | [Documento oficial](https://aeropuertorosario.com/wp-content/uploads/2026/10/DOC-2026-00012875-APPSF-ODAeroRos.pdf) |

El presupuesto de Chajarí es 59.500.000 según pliego; la ficha guardada no identifica moneda de forma separada y no se completa por suposición. Su descarga es dinámica: botón de pliego en la ficha; petición pública de lectura `POST https://licitaciones.chajari.gob.ar/return_file` con `{"atta_id":"6397","file_name":"pliego_y_decreto","licitacion_id":710}`. SHA256 PDF: `2b0bd43c642b8ecc8691d43b781a8391d70582baebb5e2b06b309df1e5c5304f`. No se inventa un enlace PDF estático.

La revisión focalizada lee sólo abiertas pendientes. El cupo diario es **hasta tres documentos que realmente requieran OCR y cuatro páginas nuevas por documento**, dentro del plazo total y con procesos aislados. La revisión explícita de Chajarí completó sus nueve páginas; la auditoría posterior reutilizó las nueve sin OCR adicional ni nueva descarga. En esa última revisión se procesaron nueve páginas nuevas de otros tres documentos, conservando los parciales. Los PDF nativos no consumen cupo OCR y los OCR completos cacheados se reutilizan incluso sin cupo nuevo. Una cláusula hallada en un OCR parcial queda pendiente hasta completar la lectura, para no ignorar condiciones contradictorias.

Las 126 abiertas pendientes se explican así: **109 sin documento identificado, 4 requieren completar lectura/OCR, 5 tienen condiciones contradictorias, 6 documentos no comprobados y 2 sin cláusula comprobable**. La principal mejora siguiente debe ser conseguir detalles/pliegos de Rosario (76) y EPE (27); no escanear indiscriminadamente el archivo histórico.

## Las 18 unificaciones

[Auditoría individual con todos los IDs y variantes](auditoria_duplicados.json): 18 filas adicionales en 16 grupos. **12 unificaciones no presentan conflicto detectado; seis, en cuatro grupos de Federación (18/2023, 8/2026, 1/2024, 10/2024), requieren revisión** por fechas diferentes o un «nuevo llamado» presente sólo en parte de la evidencia. No se declara que esas seis estén definitivamente resueltas. Las variantes quedan expuestas en JSON y desplegables del informe HTML, sin borrar ninguna fila o versión.

Además se corrigió un riesgo confirmado que no debe tratarse como duplicado: **dos fichas de Rosario comparten Compra Ágil 48/2026**, pero una compra repuestos para Tránsito (ficha 38640) y otra mantiene ascensores de la Ex Aduana (38628). Ahora conservan identidades distintas por ficha oficial. La migración reutiliza un ID anterior sólo cuando coincide literalmente la tarjeta, con prueba de regresión de conservación del historial.

## Ejecución automática y seguridad

El programador de `main` no se modificó, ni se reactivó el cron legado, ni se despachó un piloto diario adicional. `main` conserva `dfca1a52c5371929ce6c07741a88fd209a7da852`. La rama del PR incorpora comparación de sólo lectura antes/después de cada consulta, con cobertura por organismo, separación de eventos y comprobación de pérdidas. Una consulta fallida/incompleta no se presenta como ausencia de novedades.

En la siguiente ejecución diaria y después de restaurar el respaldo, se capturará automáticamente la base anterior. Al terminar se publicarán `auditoria_diaria.md` y `auditoria_diaria.json` junto al informe en **`piloto_reportes/ultimo/`**, y en el artefacto `radar-controlado`. El cierre y la supervisión existentes mantienen sus alertas. **Queda pendiente observar la ejecución del 30/10 a las 08:00 y su supervisión de las 09:30**; GitHub puede demorar los horarios. La lógica ya se validó con una corrida real aislada y un replay contra los estados reales anteriores.

No se modificó `piloto_respaldo/diario`, ni el archivo de auditoría previa, ni los archivos de producción. La revisión focalizada conserva idéntico SHA256 del SQLite antes y después. No hay correo activado, filtros por rubro/monto/modalidad/financiación, límites de cantidad de oportunidades ni cálculos de rentabilidad.

## Validación y pendientes

[CI de la implementación](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40985751112): **303 pruebas Python y 28 JavaScript, todas aprobadas**, sin omisiones de Python en Actions. Se probaron fechas y estados, separación de fichas con igual número, migración de IDs, conservación de variantes, clasificación de errores, OCR parcial, reanudación y reutilización sin repetición, límites y comparación incremental.

Próximos pasos concretos: recuperar acceso oficial de EPE y Compras SF; resolver detalles de Rosario; revisar las cuatro agrupaciones de Federación; completar OCR selectivo de IAFAS y Concepción del Uruguay y los pliegos que exceden tamaño; reparar Carcarañá, las diez pendientes y las catorce parciales; observar la próxima corrida programada con su comparación automática. No se declara cobertura territorial completa ni se fusiona el PR.
