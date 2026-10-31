# Cobertura efectiva: EPE, San José, Victoria y lote Buenos Aires

Trabajo exclusivo sobre `mejora/radar-auditable`, PR #1. Se verificó el avance automático `8f8a4fa`, posterior a `c58aa49`, antes de editar. El piloto del 31/10 había guardado su quinto segmento diario. No se modifica main, producción, programador, correo ni respaldos diarios.

## Resultado individual obligatorio

| Fuente | Prueba real | Procedimientos y calidad | Estado actual |
|---|---|---|---|
| EPE | Índice principal, variante sin www, portal de compras, dos fichas individuales oficiales indexadas, pliegos generales, página institucional histórica y endpoint público de archivo | **0 recuperados actualmente**; **37 anteriores conservados** | **ERROR DE ACCESO, PENDIENTE**. HTTP 500, cierre remoto y fallos TLS/EOF antes de la extracción. Nunca “sin novedades”. |
| San José, Entre Ríos | Índice oficial y seis descargas públicas de sus documentos enlazados en Drive | **152 procedimientos con número, tipo, objeto y enlace**; **492 enlaces documentales preservados** | **Revisada sin procedimientos nuevos**, con documentos agregados. Extracción del índice operativa; seis PDF escaneados comprobados, lectura documental pendiente. |
| Victoria, Entre Ríos | Índice oficial y ampliación de fichas | **397 números reconocidos**, **111 con objeto completo**; **286 fichas pendientes de completar** | **Revisada con resultados parciales**. HTTP 429 al ampliar detalles; no se reintenta ni se elude. |
| Carmen de Areco, Buenos Aires | Portal oficial de transparencia, identidad y jurisdicción, tarjetas y documentos oficiales | **7 procedimientos con objeto, número/año, apertura y pliego** | **Nueva fuente validada e incorporada al monitoreo**. Todos los recuperados están vencidos y se informan como históricos. |

San José y Victoria ya estaban configuradas. No se contabilizan como altas nuevas. Los CSV de [San José](sanjose_procedimientos.csv), [Victoria](victoria_procedimientos.csv), [EPE](epe_procedimientos.csv) y [Carmen de Areco](carmen_areco_procedimientos.csv) conservan sus enlaces y fechas disponibles. Los campos vacíos significan dato no comprobado, no una fecha inventada.

### EPE: diagnóstico y correcciones posibles

El fallo ocurre antes de procesar HTML: el adaptador no recibe una página utilizable. Las búsquedas muestran páginas oficiales **indexadas días antes**, mientras que abrir el índice en el momento de la revisión también devolvió HTTP 500. Una referencia del buscador no acredita funcionamiento actual ni cobertura completa. Por ejemplo, la [ficha oficial 19377](https://epe.santafe.gov.ar/app2/apertura/19377), indexada, corresponde a la Pública 7060002884 de mantenimiento de líneas en Rosario, con apertura 24/09/2026; no se usa como una convocatoria nueva o vigente.

Se añadieron **un reintento máximo** para HTTP 500/502/503/504 y cierres remotos, con conexión de cuatro segundos, lectura de seis y supervisión global por fuente. Se conserva la auditoría de intentos. No se reintentan 401/403/429 ni se deshabilita TLS. Las dos variantes oficiales del índice permanecen configuradas; las rutas de investigación fallidas no se presentan como fuentes operativas. Un HTTP 200 sin procedimientos reconocidos tampoco se considera un listado vacío confirmado.

[Auditoría EPE](epe_auditoria.json). Alternativa registrada: volver a comprobar índices y fichas públicas cuando el servicio entregue una respuesta válida y contrastar con el boletín provincial; las páginas indexadas sirven como pistas, no sustituyen la verificación del portal. No se inventó un endpoint de API de listados ni se enumeraron identificadores de documentos.

### San José: publicaciones y documentos reales

- **Pública 4/2026:** concesión de cafetería en Balneario Camping Municipal. [Publicación municipal](https://sanjose.gob.ar/concursos-licitaciones/) · [Pliego enlazado oficialmente](https://drive.google.com/file/d/1ZloFmq9xo9-KUZR7mpP0W1bTNQwOiUvH/view?usp=drive_link).
- **Privada 4/2026:** alquiler de dos tractores con pasteras y una motoguadaña. [Pliego enlazado oficialmente](https://drive.google.com/file/d/1Q7mbBKyju2lH0qteI75LuJiOFi6b1q-v/view?usp=drive_link).

Ambas conservan identidad separada: compartir número y año no basta para unificarlas. El índice no publica una fecha de apertura comprobable en esas fichas. Los enlaces a decretos, adjudicaciones, circulares y segundos llamados se preservan sin asumir la fecha o vigencia del procedimiento por el nombre del documento.

Se recuperó la descarga siguiendo **el endpoint público realmente publicado por el visor de Drive**, comprobando que corresponde al mismo archivo. No se usó autenticación ni se aceptaron confirmaciones para eludir restricciones. Los seis archivos ensayados son PDF escaneados; quedaron con `lectura_pendiente`, sin declarar pago no publicado. Se reutiliza la caché por URL/hash. [Auditoría San José](sanjose_auditoria.json).

### Victoria: alcance real y pendiente

El índice devuelve concursos y enlaces a licitaciones. Ejemplos recuperados con objeto:

- [Concurso 116/2023: tambores de aceite](https://victoria.gob.ar/web-compras/Oficina-de-Compras/concurso-de-precios-no-116-23-tambores-de-aceite-of-corralon-planeamiento/).
- [Concurso 70/2023: 12.000 litros de gasoil para unidades de TUM](https://victoria.gob.ar/web-compras/Oficina-de-Compras/concurso-de-precios-no-070-23-12-000-litros-de-gasoil-tipo-diesel-500-para-abastecer-a-las-unidades-de-tum-sec-gobierno/).

Son recuperaciones históricas; sus fechas de publicación/apertura no se verificaron. Los concursos actuales como [95/2026](https://victoria.gob.ar/web-compras/Oficina-de-Compras/concurso-de-precios-no-095-26/) siguen sin objeto completo mientras no se pueda consultar su ficha. **No se declara que los 397 números sean 397 oportunidades comerciales completas.**

Se corrigieron tres números que absorbían “12.000 litros” como parte del identificador: 70, 37 y 15/2023. También se priorizan listados y se evita tratar una suscripción `/feed/` como ficha HTML; esta última corrección tiene regresión local y no implica haber superado el HTTP 429. Ante el límite se detiene la fuente y se conservan resultados parciales. Alternativa para próxima iteración: reconsulta posterior respetando el límite y extracción del objeto y documentos de fichas aún pendientes. [Auditoría Victoria](victoria_auditoria.json).

## Incorporación efectiva de Buenos Aires

Se investigaron individualmente **ocho nuevas URLs candidatas**, correspondientes a Campana, tres secciones de Chacabuco, Carmen de Areco, General Arenales, SIBOM de Capitán Sarmiento y la portada actual de Ramallo. La búsqueda se contrastó con las páginas; no se considera revisión completa de un municipio.

**Carmen de Areco pasó la validación real y se incorporó antes de la corrida controlada.** Ejemplos:

| Procedimiento | Objeto | Apertura publicada | Enlace oficial |
|---|---|---|---|
| Privada 6/2026 | 250 m³ de conchilla de granulometría fina | 22/09/2026 | [Pliego](https://carmendeareco.gob.ar/wp-content/uploads/2026/08/pliego-licitacion-privada-6-adq-de-conchilla.pdf) |
| Privada 7/2026 | Construcción de red de agua en Chacra 84 | 16/10/2026 | [Pliego](https://carmendeareco.gob.ar/wp-content/uploads/2026/09/Pliego-licitacion-privada-n-7-construccion-de-red-de-agua-en-chacra-84.pdf) |

El año se toma del campo municipal de cada tarjeta, no de la fecha actual. Apertura y actualización del archivo no se confunden con publicación. Los documentos generales sin número de contratación no se convierten en oportunidades.

Las otras siete URLs quedaron pendientes:

- **Campana:** página oficial real, pero el contraste automático no completó identidad/jurisdicción. Además se corrigió un falso objeto que incluía instrucciones para dar de alta proveedores. Falta extraer el objeto del documento de la contratación; no se validó por responder HTTP.
- **Chacabuco, tres rutas:** páginas públicas verificadas, con licitaciones y una sección privada; falta contraste documental suficiente de jurisdicción y extracción completa. Próxima alternativa: directorio provincial y documentos enlazados, sin confundir Parque Chacabuco de CABA con el municipio bonaerense.
- **General Arenales:** timeout de acceso; no se afirma que no publique.
- **Capitán Sarmiento, SIBOM:** municipio correcto e índice accesible; falta conector que recorra boletines y contenidos para identificar contrataciones. El índice solo no se valida.
- **Ramallo:** portada actual accesible, sin procedimientos reconocidos. Publica un enlace a `https://ramallo.gob.ar/boletines`, registrado como alternativa de investigación; falta extraer sus convocatorias.

La cola persistente queda en **123 URLs únicas: dos validadas acumuladas —Funes y Carmen de Areco— y 121 pendientes**. Las dos validadas son del registro de descubrimiento, no el total de fuentes operativas. Se conservan estados, errores, evidencia y revisiones entre ejecuciones. El buscador automático encontró una verificación humana: no se eludió; las ocho semillas de esta etapa se encontraron mediante investigación específica del agente. [Detalle de candidatas](candidatas_buenos_aires.json).

San Nicolás, Zárate, Pergamino, San Pedro, Salto, Baradero, Arrecifes, Colón y Rojas siguen dentro del monitoreo y del [informe individual por organismo](cobertura_por_organismo.csv). Continúan pendientes de completar municipios, comunas y organismos de Santa Fe y Entre Ríos. No se declara cobertura territorial exhaustiva. La selección bonaerense sigue los municipios solicitados; no se inventó una medición exacta por ruta para cada localidad.

## Corrida real, informe y deduplicación

La [corrida controlada 41199939113](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41199939113) restauró una **copia** del respaldo diario del 31/10, consultó las **78 fuentes** y terminó **completa con incidencias**. Se revisó el informe producido; no se tomó el verde de Actions como prueba de cobertura.

| Cobertura | Diario anterior del 31/10 | Corrida controlada |
|---|---:|---:|
| Operativas | 40 | **42** |
| Parciales | 14 | **13** |
| Inaccesibles / bloqueadas | 12 | **12** |
| Pendientes | 10 | **10** |
| Sin publicaciones confirmado | 1 | **1** |
| Configuradas | 77 | **78** |

Una de las altas operativas es Carmen; las variaciones de accesibilidad de las demás no se atribuyen todas al código. Los cuatro estados de revisión complementarios son **18 revisadas con resultados, 38 revisadas sin novedades materiales, 14 con error de acceso y ocho pendientes**. Estos estados distinguen resultado diario y acceso; no equivalen uno a uno a la cobertura del conector. Por ejemplo, una fuente con timeout y sin resultados puede figurar como pendiente en cobertura y como error de acceso en revisión. Los errores conservan causas temporales y no se califican todos como bloqueos permanentes.

Resultados de la captura, fecha de evidencia **31/10/2026 09:16 Argentina**:

- **0 publicaciones nuevas con fecha comprobada**.
- **1 primera detección sin fecha comprobada:** Gualeguay, Pública 12/2026, 1.000 toneladas de ripio arcilloso y 1.000 de ripio arenoso. El nombre del archivo incluye una fecha no rotulada como publicación: no se usa para afirmar antigüedad o novedad. [Fuente oficial](https://municipalidad.gualeguay.gob.ar/modulos/transparencia/licitaciones_publicas.php).
- **12 recuperaciones históricas/de línea de base**.
- **3 cambios materiales:** Villa Elisa 13/2026, Funes 5/2026 y San Salvador 3/2026.
- **200 datos completados**; no son 200 licitaciones nuevas.
- **216 registros informados**, sin recorte a un top. [Informe íntegro](INFORME_RADAR_INTEGRO.md) · [CSV completo de eventos](eventos_sin_recorte.csv).

Se revisa una ventana conservadora de **72 horas por fecha publicada** y **60 días próximos por vencimiento**, sin ocultar lo que quede fuera: hay una publicación con fecha dentro de la primera ventana y 119 convocatorias calculadas dentro de la segunda. Con fecha sin hora se incluye el día inicial completo para no perder avisos. Las detecciones sin fecha siguen visibles en su sección.

La base diaria de partida tenía **4.511 registros**. La copia controlada terminó en **4.524**, con **4.505 procedimientos únicos en la vista consolidada**; los 19 registros unificados no se borran del historial. Se añadió un índice derivado con **4.521 identidades de cuatro auditorías previas accesibles**, con procedencia y huellas de las bases, para evitar presentar como inédita una publicación ya capturada en otra auditoría.

El [contraste final 41200546592](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41200546592) reprodujo la captura contra el respaldo y ese índice, **sin nuevas consultas ni OCR**. La segunda aplicación produjo **4.249 registros sin cambios y cero novedades, modificaciones o datos completados adicionales**. Se comprobaron invariantes del informe y hashes de producción y respaldos. [Prueba completa](prueba_deduplicacion.json) · [Métricas](metricas.json).

## Pago y prioridad comercial

Quedan **121 oportunidades calculadas como abiertas**, **78 próximas a vencer**, y 256 registros del catálogo no fueron observados en la captura actual: su conservación no confirma vigencia. Hay **11 abiertas con condiciones de pago verificadas** —algunas mixtas o sin plazo firme— y **110 pendientes**. Se mantienen los dos casos rápidos documentados: **Chajarí 19/2026, contado contra entrega**, y **La Paz 39/2026, diez días hábiles desde entrega y factura**. [Listado separado de cobro rápido](COBRO_RAPIDO.md) · [Todas las abiertas](ABIERTAS.md) · [Próximas a vencer](PROXIMAS_A_VENCER.md).

Se conservan plazos, hitos, anticipos y parciales cuando hay cláusula documental. Desiertas, segundos llamados y reaperturas mantienen sus marcas. No se supone acreditación inmediata ni se calcula rentabilidad. Las oportunidades de 60–90 días o pago desconocido siguen en el catálogo y la cola documental. Ninguna publicación nueva se elimina por monto, rubro o financiación.

## Pruebas, preservación y pendientes

Las pruebas cubren reintentos limitados, HTTP 429, HTTP 200 sin procedimientos, enlaces públicos de Drive sin autenticación, tarjetas reales de Carmen con año explícito, números de Victoria, error de acceso frente a sin novedades e identidades de auditorías previas. La corrida y el replay reales quedaron auditados; el commit final vuelve a ejecutar las regresiones en Actions.

La incorporación de Carmen queda persistida en `inventario/fuentes_auto.json`, y la cola en `inventario/descubrimiento_estado.json`. EPE queda configurada como **PENDIENTE + ERROR_DE_ACCESO**, San José operativa en extracción del índice y Victoria parcial. Los respaldos diarios y la auditoría antigua no se sobrescriben. El PR #1 permanece abierto; no se fusiona ni se activa correo.

Pendiente prioritario: acceso real a EPE; detalles y documentos de Victoria tras respetar el HTTP 429; lectura selectiva de PDF escaneados recientes de San José; contraste de jurisdicción y conectores de las siete candidatas bonaerenses no validadas; ampliación de municipios y comunas aún sin consulta efectiva. No se da por reparado un portal cuyo servidor sigue impidiendo recuperar procedimientos.
