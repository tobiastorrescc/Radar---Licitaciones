# Fase 6 — Primer lote territorial: avance real, no cobertura exhaustiva

Corte: 09/11/2026, después de las 16:17 de Argentina. Rama `mejora/radar-auditable`, PR #1. Base `5ebae02`.

**Resultado comercial: cero compras inéditas con recepción vigente comprobada en las 20 localidades exploradas.** No se atribuye ese resultado a falta real de publicaciones: hay navegación y documentación pendientes. La fase conserva avances, pero **no se declara completada**.

## Qué se hizo realmente

1. Antes de cambiar lectores se construyó el inventario territorial y se ejecutó el lote de 20 con los lectores anteriores: [ejecución 42677364803](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42677364803). Intentó las 20 localidades en 119,656 segundos. Hubo navegación más allá de portada en 16.
2. Se corrigieron omisiones comprobadas de navegación e identidad: [ejecución 42679698776](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42679698776). Cinco contrastes dirigidos, 67,927 segundos; la revisión registrada pasó a 18 localidades. No se repitieron las otras 15.
3. Se consultaron desde el catálogo persistente las dos altas y Rosario y se revisaron directamente las rutas institucionales de Totoras y San Gregorio: [ejecución 42681225274](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42681225274). Las 20 localidades tienen exploración más allá de portada, pero ninguna comprobación de raíz o menú equivale a cobertura exhaustiva de sus compras. Los detalles están en [lote01.csv](lote01.csv).

El lote es **16 localidades santafesinas y cuatro entrerrianas**. No se atribuye nueva cobertura bonaerense a esta entrega.

## Fuentes incorporadas y prueba efectiva

Se localizaron 20 sitios institucionales nuevos para el catálogo configurado. **Sólo dos fuentes superaron la validación y quedaron incorporadas** en `inventario/fuentes_auto.json`; las otras no se promocionaron por responder HTTP 200.

| Fuente nueva | URL oficial registrada | Primera exploración | Consulta posterior desde catálogo | Vigentes inéditas |
|---|---|---:|---:|---:|
| Sastre y Ortiz, Santa Fe | https://sastreciudad.gob.ar/intendencia/ | 10 referencias | OPERATIVA, 10 referencias | 0 |
| General Galarza, Entre Ríos | https://galarza.gov.ar/autoridades/ | 1 referencia | OPERATIVA, 1 referencia | 0 |

Estos recuentos son **referencias extraídas**, no necesariamente procedimientos únicos ni compras abiertas. Galarza sólo demostró recuperación de un aviso de 2022; no se afirma cobertura completa ni compras actuales. Sastre incluye avisos de apertura ya realizados. No se publican esas referencias como novedades comerciales.

Las 18 restantes siguen pendientes de incorporación validada: Teodelina, Hughes, San Gregorio, San José de la Esquina, Villa Mugueta, Pilar, Franck, San Jerónimo del Sauce, San Jerónimo Norte, San Guillermo, Totoras, San Javier, Malabrigo, Avellaneda, Cayastá, Valle María, Ubajay y Aldea San Antonio.

## Correcciones motivadas por el barrido

- San Gregorio: seguir los menús «Noticias y Eventos», «Información y Noticias» y «Ordenanzas y Presupuestos». Se comprobaron las rutas reales `pages/actos.php` y `pages/tesoreria.php`; no se encontraron allí convocatorias verificables. Eso deja la cobertura pendiente, no acredita ausencia de compras.
- San José de la Esquina: reconocer la identidad publicada aunque el nombre no sea prefijo del título. Se recuperaron 28 referencias de ordenanzas/documentos, pero el recorrido agotó el plazo y encontró antecedentes antiguos: no se incorporó como fuente operativa completa.
- San Guillermo: contrastar jurisdicción con el Concejo oficial enlazado desde el municipio. Se habilitó navegación hasta pliegos/decretos y se recuperaron 40 referencias. El objeto y las fechas de documentos externos siguen incompletos; fuente parcial, sin alta automática.
- San Jerónimo del Sauce: una página de resultados de búsqueda se había confundido con un procedimiento. Se corrigió el reconocimiento y se retiró **únicamente esa falsa alta Fase 6**. La segunda extracción devuelve cero convocatorias reconocidas y queda pendiente; no se interpreta como «sin novedades».
- Totoras: el primer dominio era el portal de trámites. Se verificó `https://totoras.gob.ar/`, su página institucional y autoridades, y se conservó esa ruta para el siguiente barrido. No se localizó un flujo de compras extraíble; no se incorporó una fuente sin evidencia.
- No se cambiaron los importadores CSV/HTML/PDF ni se añadió OCR. Se reutilizó texto embebido de dos documentos enlazados por San Guillermo, sin repetir procesamiento de imágenes.

## Comparación independiente documentada

[control_manual.json](control_manual.json) contiene cinco avisos contrastados fuera del proceso Python, con enlaces oficiales y fechas. El agente detecta número/enlace en 5/5, pero sólo 4/5 tienen objeto y fechas suficientes en su extracción. Es una **muestra pequeña de avisos cerrados**, no un porcentaje territorial ni prueba de compras nuevas.

| Organismo | Procedimiento y objeto | Fecha oficial | Resultado |
|---|---|---|---|
| Sastre y Ortiz | LP 5/2026, 826 m³ de hormigón H-25 | Apertura 18/10/2026 | Detectado; vencido |
| Sastre y Ortiz | LP 6/2026, hidroelevador sobre tráiler | Apertura 21/10/2026 | Detectado; vencido |
| Malabrigo | LP 3/2026, materiales para viviendas de la tercera edad | Recepción 16/10/2026 13:00; apertura 19/10 | Detectado; vencido |
| Franck | Ordenanza/LP 2240/2026, tribunas de hormigón | Recepción 11/05/2026 10:30; apertura 11:00 | Detectado; vencido |
| San Guillermo | CPP 3/2026, moldes para pavimento y regla vibradora | Recepción 05/11/2026 10:00; apertura 10:30 | Enlace/número detectados; objeto/fechas requieren documento externo |

El pliego de San Guillermo se contrastó mediante la conexión de [Google Drive](https://drive.google.com/file/d/1urldu4Akl8axyfFpGE_MuwQubLYFHOCn/view), enlazada por la [página municipal](https://sanguillermo.gob.ar/pliegos-y-licitaciones/). Esto **no demuestra descarga anónima desde Actions**; permanece parcial. No se contabiliza como oportunidad vigente.

Las lecturas web de los 20 sitios y sus limitaciones se conservan en `inventario/fase6_control_web.json`. Algunas secciones no pudieron contrastarse independientemente o devolvieron referencias ambiguas: no se cuentan como comprobación exhaustiva.

## Resultados antes y después

| Indicador | Referencia Fase 5 | Resultado de esta muestra |
|---|---:|---|
| Fuentes configuradas | 101 | **103** |
| Fuentes operativas | 46 | Dos altas operativas comprobadas; las 101 anteriores no se reauditaron globalmente |
| Fuentes parciales / inaccesibles / pendientes | 32 / 16 / 7 | No hay nuevo censo global comparable |
| Localidades nuevas exploradas | 0 | **20**, con limitaciones de cobertura |
| Fuentes nuevas incorporadas y reconsultadas | 0 | **2** |
| Compras verificadas del catálogo global | 28 | No se revalidó el conjunto; **0 adicionales del lote** |
| Publicaciones recientes nuevas confirmadas del lote | 0 | **0** |
| Compras vigentes desconocidas del lote | 0 | **0** |
| Aperturas previas pendientes | 112 | Se conserva la cola, sin reasignar como novedades |

Las dos exploraciones territoriales capturaron 143 referencias: 31 tienen vigencia vencida y 112 no cuentan con fecha suficiente en la extracción. Incluyen anexos, adjudicaciones y dos encabezados rechazados. No son 143 oportunidades comerciales. Se excluyeron esos dos encabezados de la cola publicada y se conservaron como evidencia en [referencias_rechazadas.json](referencias_rechazadas.json).

El cierre consultó tres fuentes configuradas: las dos altas fueron OPERATIVAS; Rosario fue parcial por tiempo/red. En esa consulta se comprobaron **seis compras vigentes de Rosario**, todas de una fuente ya conocida. Se publican completas en [comercial_muestra_actual.csv](comercial_muestra_actual.csv); no se atribuyen como descubrimientos inéditos del lote. [publicaciones_nuevas_vigentes.csv](publicaciones_nuevas_vigentes.csv) queda correctamente sin filas. [pendientes_muestra.csv](pendientes_muestra.csv) conserva las 155 referencias pendientes de la muestra ampliada, con resumen y enlace; no se confunde con la cola previa de 112 aperturas.

## Incidencia pendiente: control Rosario

La consulta real alcanzó **52/53** avisos del control fechado el 7/11 y 64 referencias totales antes del límite de 240 segundos. Falta la ficha `38659` (extintores Hospital Carrasco), cuya apertura de referencia era el 09/11 a las 11:00, anterior al barrido. No se confirmó si desapareció del listado por cierre o si hubo omisión; su consulta independiente tampoco pudo completarse. **No se afirma 53/53 ni se declara regresión descartada.**

La ejecución de cierre terminó en **failure**, precisamente porque mantiene el control estricto de 53. Los resultados parciales y los CSV se guardaron. La integridad y la segunda pasada sí fueron correctas. No se relajó el control para obtener una ejecución verde. Hay que revalidar el caso con un listado oficial accesible o la ficha, comparar las capturas y resolverlo antes de aceptar el cierre de fase.

## Inventario, lotes y faltantes

[cobertura_territorial.csv](cobertura_territorial.csv) contiene **655 localidades identificadas**: 365 Santa Fe, 239 Entre Ríos y 51 Buenos Aires del padrón existente. **No son 655 localidades auditadas.** El departamento oficial sigue pendiente donde el padrón no lo publica; el lote aporta un departamento propuesto, separado del dato oficial. Buenos Aires conserva preselección geodésica; falta contrastar distancia vial antes de nuevas altas.

- 34 localidades tenían extracción operativa en la referencia; dos nuevas tienen extracción histórica comprobada.
- [localidades_pendientes.csv](localidades_pendientes.csv) enumera las 619 restantes sin ese nivel de extracción comprobado, incluidas parciales e inaccesibles. También continúan las limitaciones territoriales/departamentales descritas.
- **Lotes exhaustivos completados: 0.** Lote 01 explorado en sus 20 localidades, con revisión y comparación todavía parciales. No se inició otro lote para evitar presentar como terminado el primero.
- Próximo trabajo: cerrar Hughes/Siglo Servicios, documentos externos de San Guillermo, ruta de compras de Totoras, límites de Franck/Malabrigo/Valle María y navegación actual de San José. Después seleccionar el siguiente lote de 20 localidades sin cobertura operativa comprobada; el CSV es la cola persistente.

## Bloqueos y prioridades

Hughes delega concursos en un formulario público de Siglo Servicios: se comprobó el enlace oficial y descargó su HTML; el listado no devolvió convocatorias verificadas con la consulta inicial. Falta estudiar sus filtros publicados. No se automatizó un endpoint supuesto.

Franck, Malabrigo, Valle María, Avellaneda, San José de la Esquina y San Guillermo alcanzaron límites: conservan capturas parciales y no se contabilizan como altas completas. Pilar publica documentos en un subdominio CMS; requiere contraste del contenido. Aldea San Antonio tiene limitaciones de acceso/lectura independiente. Las demás fuentes sin procedimientos reconocidos permanecen pendientes, no «sin compras».

EPE, Gestiones y Boletín se mantienen separadas de este lote. Última evidencia Fase 5: EPE con fallo TLS, Gestiones con timeout y Boletín con timeout en ediciones directas. No se repitieron indefinidamente los mismos intentos ni se declararon recuperadas. Los importadores oficiales siguen disponibles; no hubo nuevos archivos oficiales aportados para esas tres fuentes en esta fase.

## Pruebas, persistencia y conservación

- **506 pruebas Python: OK, una omitida; 28 Node: OK**, localmente y en Actions.
- Segunda pasada incremental en una copia restaurada del respaldo: **cero novedades y cero eventos**. Historial de la copia: 6.771 registros iniciales; 6.914 después. Las nuevas detecciones de esa copia incluyen históricos y fechas desconocidas, no publicaciones comerciales nuevas.
- El cierre falla únicamente su exigencia de Rosario 53/53; no se oculta esa incidencia.
- Se compararon por SHA los **83 archivos protegidos presentes en la base** (incluyen los 78 requeridos): **cero cambios**. [proteccion.json](proteccion.json). Main sigue en `c4c44de36b8064bf84db4fa1071004e0f8c45ad8`.
- Producción, respaldos, despliegue y workflows preexistentes intactos. Sólo se añadieron workflows de prueba de rama, sin cron. El workflow existente del programador pasó su CI en [42681225169](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42681225169); no se modificó ni se despachó producción para esta prueba.
- Evidencias completas de HTML y checkpoints en artefactos de las tres ejecuciones, retención 90 días; hechos, CSV, inventario y resultados resumidos persistidos en el PR. No se publican pliegos completos ni credenciales.

La incorporación técnica de dos fuentes es verificable. **La mejora comercial buscada todavía no se consiguió en este lote.** El avance queda conservado sin presentar antecedentes como descubrimientos cotizables.
