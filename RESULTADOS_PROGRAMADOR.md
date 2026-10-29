# Piloto diario externo preparado — sin activación

Se publicó el código `bbb42a1c4b1b307626d05245f2e015cc9b1a7f70` exclusivamente en el PR #1, rama `mejora/radar-auditable`. No se instaló un programador, no se creó un PAT ni se modificaron main o archivos de producción.

## Configuración revisable

[Guía completa](PROGRAMADOR_EXTERNO.md), [temporizador](despliegue/systemd/radar-piloto.timer), [servicio](despliegue/systemd/radar-piloto.service), [configuración desactivada](despliegue/piloto.json) y [disparador](tools/programar_piloto.py).

| Control | Implementación / verificación |
|---|---|
| Horario | 08:00 America/Argentina/Buenos_Aires; systemd confirmó próximo disparo a las 11:00 UTC |
| Activación | `habilitado:false`, sin instalación ni enable/start |
| Aislamiento | repositorio, workflow, rama y payload constantes; canal piloto, inicializar=false |
| Permisos externos | PAT fine-grained exclusivo de este repositorio: Actions read/write + Contents read; no creado ni probado con credencial real |
| Secretos | LoadCredential de systemd; archivo root 0600, sin argumentos ni redirecciones con token |
| Simultaneidad | servicio oneshot + flock; comprobar runs recientes; concurrencia por ref en Actions sin cancelar piloto activo |
| Idempotencia | journal atómico sincronizado antes del POST y clave por fecha; reconciliar solicitud incierta, no redisparar automáticamente |
| Fallos | timeouts API, espera 50 minutos, corte servicio 55; fallos/cancelaciones/plazo producen salida no cero |
| Persistencia | restauración íntegra y hash de cadena Git, continuidad, restauración de prueba del nuevo respaldo y push sin force |
| Respaldo diario previo | sigue intacto: 3.691 procedimientos, 3.750 versiones, hash lógico e91854f7e33c86c6390c21fea9d8e6e1214f85248eb8e34966173142024c3c42 |

GitHub aprobó **265 pruebas sin omisiones** en [#133](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40789691635), job 123171526621. Incluyen once pruebas del disparador externo y cinco de acceso/codificación, además de la suite de conectores, incremental, pagos y respaldos. El dry-run en Actions confirmó configuración desactivada y calendario. Localmente: 264 aprobadas y una omitida por sockets; esa misma prueba HTTP sí pasó en Actions.

No se afirma que el servicio esté instalado o que un PAT externo tenga permisos comprobados: el entorno no tiene servidor de destino ni esa credencial. La instalación y primera ejecución supervisada del servicio requieren la autorización posterior. Los ensayos reales siguientes usan workflow_dispatch desde el controlador existente, con runners independientes y canal de validación; no activan periodicidad.

## Recuperación de fuentes

Villaguay publicaba una respuesta con header/meta UTF-8, secuencias UTF-8 válidas en los href de PDF y bytes Latin-1 en otro texto. La decodificación anterior sustituía toda la página por CP1252 y convertía los enlaces a `%C3%83%C2%BA`. Se conserva ahora cada secuencia válida y se interpretan sólo los bytes inválidos de forma local. No se generan rutas por conjetura. El fixture hexadecimal contiene fragmentos de los bytes originales de #131, con URL, hash y procedencia.

Sobre las capturas anteriores se recupera la dirección exacta de cuatro enlaces en cuatro páginas. Esto prueba el defecto de codificación; sólo la nueva consulta real determina si cada documento está accesible. Los desafíos HTTP 200 con firmas concretas de verificación humana pasan a `ACCESO/AccesoRestringido`, sin parsearlos como licitaciones ni como listados vacíos. Las publicaciones recuperadas antes de un bloqueo se conservan como parciales. No se eluden restricciones ni se desactiva TLS.

En Crespo, la fila 34/2018 de la página 2016 tiene objeto, fecha, presupuesto y proveedor vacíos en la captura: sigue incompleta, sin datos inventados. Sus enlaces históricos 404 no se sustituyen por rutas supuestas.

## Descubrimiento periódico conservado

[#21](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40789691634) finalizó correctamente: 100 URLs consultadas, cero URLs únicas nuevas, cero validadas/incorporadas, seis nuevos hallazgos de evidencia. Se conservan 105 candidatas acumuladas, una incorporación previa y **104 pendientes**; cuatro no consultadas en esta tanda. Hubo 21 búsquedas con verificación humana, sin evasión. No se declara cobertura completa.

## Servicio externo, costo y autorización posterior

Requiere un servidor Linux disponible a las 08:00. Un equipo/NAS/VPS existente puede ejecutar systemd sin nueva suscripción; si hay que contratar un VPS o almacenamiento externo, tendrá el costo de ese proveedor. systemd/script y la llamada API no añaden una tarifa por despacho. Las condiciones y cuotas de runners/artefactos de GitHub deben verificarse al activar; no se garantiza costo total cero ni se contrató un servicio.

Antes de activar: elegir servidor y responsable, instalar archivos sin habilitar, provisionar PAT limitado, verificar unidades/permisos/TLS, configurar alerta de fallo o ausencia diaria y copia externa del repositorio. Luego, con autorización, habilitar y realizar primera prueba supervisada del servicio. El respaldo Git duradero y los artefactos de 90 días ya existen; no se instaló respaldo en otro proveedor. Producción mantiene autorización separada.

Se conservan todas las oportunidades y novedades, con pagos comprobados o no informados, desiertas, segundos llamados y reaperturas. Sin filtros por rubro/monto y sin cálculo de rentabilidad.

## Límite detectado en los PDF de Villaguay

La primera auditoría #134 dejó de registrar 404 para los PDF públicos afectados por la codificación; permanecieron seis XLS 404 y se alcanzó el límite de 60 segundos, con 208 publicaciones parciales. Esto no convierte la fuente en operativa. El [PDF oficial de públicas 2026](http://villaguay.gob.ar/boletindigital/documentos/Licitaciones/2026/Lic.P%C3%BAblicas-2026.pdf) contiene una tabla con números desnudos y año/modalidad en el encabezado final, que el extractor documental actual no convierte aún en procedimientos. No se afirma haber recuperado esas cinco filas en el radar ni haber descubierto oportunidades nuevas de ese PDF. Próximo paso: extractor de tabla con contexto documental, separación de presupuesto/adjudicación y condiciones por fila, con fechas y moneda comprobadas. No atribuir a todas las filas la primera condición de pago ni anunciar adjudicaciones históricas como convocatorias abiertas.

La segunda consulta independiente conservó los registros anteriores aunque las fuentes con incidencias no devolvieran todas sus páginas. El estado diario de 3.691 permanece separado del ensayo, que parte de la semilla #116; no se reemplaza con un conjunto menor.

## Dos auditorías reales e independientes completadas

[Orquestador #133](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40789691635) terminó **success**. Las dos ejecuciones usaron runners distintos y workflow_dispatch; el job de producción quedó omitido en ambas.

| Ejecución | Base previa | Historial final | Versiones finales | Repetidas como nuevas |
|---|---:|---:|---:|---:|
| [#134](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40789756701) | 3.530 | 3.672 | 3.731 | 0 |
| [#135](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40790655545) | 3.672 | 3.689 | 3.749 | 0 |

No se perdió ningún procedimiento ni se alteraron versiones anteriores. La segunda restauró el respaldo de Git (`RESTAURADO True`), verificó continuidad, exportó el segundo segmento y lo persistió en esta rama. Cada exportación ensaya restauración completa antes del push. SQLite descargado pasó quick_check y su hash lógico coincide con el índice final: `6f308735516daca2648ef17f932607200238a0230dc01833f7309451d36f282d`. Las huellas de producción quedaron idénticas antes/después en ambas auditorías.

**Este canal de validación parte de la semilla #116**, no del diario preparado de 3.691: son conjuntos independientes. El directorio `piloto_respaldo/diario/` permanece con su cadena y hash anteriores; no se sobrescribió con las 3.689 filas del ensayo ni se perdieron dos registros diarios. Las nuevas observaciones quedan duraderas en `piloto_respaldo/validaciones/bbb42a1c4b1b307626d05245f2e015cc9b1a7f70/`.

En #134 hubo 141 recuperaciones históricas de línea de base, 23 cambios del contenido recuperado, un dato completado y una primera detección sin fecha de publicación verificable. No se afirman 166 licitaciones recién publicadas. En #135: 3.494 sin cambios, 17 recuperaciones de línea de base y un dato completado; **cero nuevas publicaciones confirmadas**. Los cambios de extracción no prueban una modificación editorial del organismo.

## Salud observada en la segunda consulta

Se consultaron y finalizaron las **74 fuentes**; cero sin iniciar y cero errores internos. Consulta de fuentes: 284 segundos, más análisis documental acotado y persistencia.

| Estado estricto | Cantidad |
|---|---:|
| Operativas con procedimientos y objetos | 33 |
| Parciales | 15 |
| Bloqueadas | 13 |
| Pendientes | 12 |
| Sin publicaciones confirmado | 1 |

Hubo 24 fuentes con error de red, 19 con extracción y cuatro con ambas; una con incidencia de acceso. Trece tuvieron algún timeout. Las categorías se superponen; no sumarlas como fuentes diferentes. Una ejecución success conserva la auditoría aun cuando la cobertura global sea **COMPLETA_CON_INCIDENCIAS**.

- **Villaguay:** 238 publicaciones, 54,8 segundos, seis XLS 404; sin los anteriores 404 de los PDF corregidos. Sigue parcial, con el extractor de tabla 2026 pendiente. En la primera consulta, 208 antes del corte de 60 segundos; la segunda restauró el historial y no borró lo no observado.
- **Crespo pública:** 175 publicaciones, cuatro PDF históricos 404 y una fila sin objeto en el original.
- **Villa Elisa:** 87 publicaciones, 16 sin detalle completo. No se convierten celdas vacías en objetos inventados.
- **EPE:** HTTP 500 en ambas consultas; cero recuperación actual. Se conservan sus datos anteriores con última observación, sin anunciarlos verificados hoy.

Las trece bloqueadas de #135:

| Fuente | Incidencia |
|---|---|
| [Gobierno de Santa Fe](https://compras.santafe.gob.ar/) | Timeout |
| [EPE](https://www.epe.santafe.gov.ar/app2/aperturas) | HTTP 500 |
| [UNR](https://compras.unr.edu.ar/) | HTTP 403 |
| [Poder Judicial de Santa Fe](https://www.justiciasantafe.gov.ar/index.php/poder-judicial/informacion-general/compras-y-licitaciones/) | Timeout |
| [Municipalidad de Cañada de Gómez](https://cdg.gob.ar/transparencia/licitaciones-y-concursos/) | HTTP 403 |
| [Municipalidad de Santa Fe](https://transparencia.santafeciudad.gov.ar/compras-y-contrataciones/) | HTTP 403 |
| [Municipalidad de Santa Fe](https://transparencia.santafeciudad.gov.ar/contrataciones-obra/) | HTTP 403 |
| [ENERSA](https://www.enersa.com.ar/area-proveedores/) | <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)> |
| [Instituto Becario](https://institutobecario.gov.ar/licitaciones.php) | <urlopen error [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1016)> |
| [Municipalidad de Gualeguaychú](https://w3.gualeguaychu.gov.ar/tramites/compras-y-licitaciones/acceso-a-licitaciones-p%C3%BAblicas) | Timeout |
| [Universidad Nacional de Entre Ríos (UNER)](https://compras.uner.edu.ar/) | HTTP 401 |
| [Boletín Oficial de Santa Fe](https://www.santafe.gov.ar/boletinoficial/) | Timeout |
| [Municipalidad de Zárate](https://zarate.gob.ar/licitaciones-publicas/) | Timeout |

## Reporte íntegro y pagos

[Artefacto completo #135](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40790655545/artifacts/12861517881): descargar `radar-controlado` y abrir `index.html`. Incluye las **3.689 oportunidades conservadas**, todas las detecciones/cambios, auditoría individual, JSON/Markdown, 52 abiertas y 22 próximas a vencer **según los últimos datos conocidos**; 177 no observadas en esta consulta permanecen explícitamente señaladas.

Se conservaron **100 condiciones de pago verificadas y 3.589 pendientes**, frente a 92 verificadas en #131; no es un conteo de publicaciones nuevas. Ejemplo: Villa Elisa, concurso **28/2026**, 8.000 litros de gasoil: [documento de respaldo](https://villaelisa.gov.ar/descargas/transparencia/licitaciones%20y%20concursos/2026/concursos%20de%20precios/028-26/2026_028%20Concurso%208000%20LTS%20GAS%20OIL%20-%20Dec%20389.pdf), clasificado cinco días hábiles desde presentación de factura; apertura y vigencia desconocidas. No se anuncia como pago contado ni como convocatoria abierta.

La ordenación conserva prioridad a contado/contra entrega comprobados y llamados especiales, manteniendo todos los demás registros visibles. No se filtra por monto, rubro, modalidad o financiación; no se calculan costos, proveedores ni rentabilidad.
