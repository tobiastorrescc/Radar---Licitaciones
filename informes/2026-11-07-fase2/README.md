# Fase 2 — cobertura real, omisiones y saldo comercial

Auditoría del **7/11/2026**, a partir de `97311de` y del respaldo automático `76ebec5`. Evidencia consolidada hasta **08:51:06, Argentina**. PR #1, rama `mejora/radar-auditable`.

**Resultado principal:** el barrido recuperó los 22 avisos que faltaban en una muestra oficial de Rosario y se incorporaron cinco fuentes con extracción comprobada. **No se recuperaron las tres fuentes críticas y no hubo publicaciones nuevas con recepción vigente comprobada adicionales al respaldo actual.** La meta comercial no se considera alcanzada.

El informe ofrece **19 convocatorias con recepción vigente comprobada**, sin recortes por rubro, monto, financiación, pago o modalidad. Son oportunidades disponibles en la muestra, no 19 publicaciones nuevas de esta etapa. La expansión de fuentes aporta vigilancia futura, pero sus antecedentes no se presentan como éxito comercial.

## Comparación antes / después

La línea de base de esta etapa consultó el catálogo efectivo completo de 88 fuentes. No se compara artificialmente esa cobertura con el lote de nueve de la entrega anterior.

| Métrica | Antes | Después |
|---|---:|---:|
| Fuentes efectivas configuradas | 88 | 93 |
| Fuentes del catálogo realmente consultadas | 88 | 93 |
| Operativas, incluida una sin publicaciones confirmada | 40 | 43 |
| Parciales, incluidos plazos agotados con resultados | 25 | 27 |
| Inaccesibles, incluidos plazos agotados sin resultados | 16 | 16 |
| Pendientes de reconocimiento | 7 | 7 |
| Convocatorias con recepción vigente comprobada | 18 | 19 |
| Publicaciones nuevas confirmadas respecto del respaldo inicial | 4 | 5 |
| Publicaciones nuevas confirmadas respecto del respaldo actual del piloto | — | 0 |
| Publicaciones nuevas **y cotizables** comprobadas | 0 | 0 |
| Omisiones en la muestra oficial de 53 avisos de Rosario | 22 | 0 |
| Omisiones recuperadas en esa muestra | — | 22 |

**101 fuentes/candidatas distintas fueron consultadas**, incluidas las ocho candidatas que no se incorporaron. Son 93 fuentes monitoreadas, no 101 fuentes operativas. Las cifras técnicas originales y la distinción entre parcial e inaccesible están en [fuentes_101_auditadas.csv](fuentes_101_auditadas.csv).

Las cinco publicaciones con fecha comprobada corresponden al 6/11 y ya figuran en el respaldo del piloto del 7/11. Su recepción de ofertas no quedó comprobada: no se anuncian como nuevas cotizables ni como cinco publicaciones del sábado. La diferencia de cuatro a cinco incluye completar fecha/identificación de un aviso ya detectado de forma incompleta; no equivale a descubrir una URL inédita.

## Rosario: omisión reproducida y recuperación efectiva

El portal oficial exponía **53 próximas aperturas**. El primer barrido desde Actions recuperó 31: falló una página de compras ágiles y no se obtuvo la continuación del listado. Un reintento diferido acotado llevó a 51; persistió el fallo en la última página.

Se consultó el formulario oficial `/inicio/compras-licitaciones`, se comprobó su redirección después de una búsqueda pública de noviembre y se incorporó una consulta mensual complementaria mediante los parámetros **realmente observados** `mesApertura[0]`, `anioApertura[0]` y los enlaces de categoría `verTipo`. La ruta principal de próximas aperturas permanece. Se consultan el mes actual y el siguiente; no se excluyen las aperturas posteriores que aparecen en la ruta principal.

La nueva ruta registró **los 53/53 avisos de la muestra**, incluidos los 22 ausentes del primer control. También recuperó registros recientes ya cerrados de noviembre: se conservaron como antecedentes, no como oportunidades activas. La fuente **sigue parcial** porque hubo fallos de fichas y se alcanzó su plazo de 240 s; descubrir todos los avisos de esta muestra no acredita tener todos sus campos ni cobertura global.

- [Control de los 53 avisos, campos y URLs](control_rosario_53.csv).
- [Los 22 avisos recuperados, con motivo de omisión](omisiones_rosario_recuperadas.csv).
- [Comparación de conjuntos](rosario.json).
- [Publicaciones del 6/11 con información documental, sin presumir recepción vigente](publicaciones_6nov_sin_recepcion_comprobada.csv). Este archivo contiene también registros ya conocidos; no todas sus filas son nuevas.

Ejemplos de avisos recuperados en el recorrido, todavía sin recepción comprobada:

- [Artículos de limpieza para la Dirección General de Defunciones — ficha 38741](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38741).
- [Servicio de limpieza para la Dirección General de Compras y Suministro — ficha 38723](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38723).

La Compra Ágil **128/2026** sigue como control conocido. Su nueva observación no se atribuye a una capacidad de descubrimiento inédita: el lector ya la detectaba. La mejora es resistir la omisión intermitente de páginas, no volver a contar esa contratación como nueva.

## Fuentes nuevas incorporadas

| Fuente | Estado comprobado | Publicaciones extraídas | Vigentes comprobadas | Método |
|---|---|---:|---:|---|
| [San Justo, Santa Fe](https://sanjusto.gov.ar/) | Operativa | 3 | 0 | Noticias y fichas oficiales |
| [Suardi](https://www.suardiciudad.ar/) | Parcial | 8 | 0 | Noticias y enlaces de procedimientos; faltan detalles |
| [Colonia Avellaneda](https://coloniaavellaneda.gob.ar/web/informacion-publica/) | Operativa | 9 | 0 | Secciones por procedimiento y documentos |
| [Vialidad ER, portal de contrataciones](https://aplicaciones.vialidadentrerios.gob.ar/contrataciones-licitaciones) | Operativa | 517 | 0 | Tarjetas estructuradas y las 26 páginas publicadas |
| [Ministerio Público bonaerense](https://www.mpba.gov.ar/licitaciones) | Parcial | 95 | 0 | Formulario público por departamentos y localidades dentro del alcance; tarjetas y documentos |

Vialidad es un **portal complementario** de un organismo que ya estaba configurado; se conserva el lector anterior de `dpver.gov.ar`. No se cuentan cinco municipios nuevos ni cinco organismos distintos. El lector nuevo conserva modalidades publicadas sin una lista restrictiva: el primer prototipo omitía variantes y sólo recuperaba 433 tarjetas. Ahora alcanza las 517 del contador oficial, con número cuando consta y huella de aviso cuando falta. Se corrigió además una fila sin fecha que interrumpía la página.

En MPBA se corrigió un campo de ámbito nulo que impedía registrar tarjetas y persistirlas. No se atribuye una contratación a una localidad por una mera coincidencia de nombre de calle. Su plazo de 90 s dejó resultados parciales; las 95 convocatorias recuperadas están vencidas. Ninguna se suma como oportunidad comercial nueva.

## Fuentes críticas: no recuperadas

| Fuente | Comprobación | Estado |
|---|---|---|
| [EPE](https://epe.santafe.gov.ar/app2/aperturas) | Lector habitual: TLS/EOF. TLS 1.2 validado: respuesta vacía o HTTP 500; una respuesta contiene **“Web Page Blocked”**. HTTP público: conexión reiniciada. | Inaccesible; no se eludió el bloqueo |
| [Gestiones Santa Fe](https://www.santafe.gob.ar/gestionesdecompras/site/index.php) | Persisten timeouts en dominios oficiales y TLS 1.2. La prueba Chrome anterior tampoco cargó el portal. | Inaccesible; endpoint CSV todavía no comprobado |
| [Boletín Santa Fe](https://www.santafe.gov.ar/boletinoficial/) | Fallaron sección diaria directa, dominio alternativo y PDF oficial del 6/11. | Inaccesible; ninguna edición actual se considera cubierta |

[Resultados de transporte y tiempos](transporte_criticas.json). No se desactivó validación de certificados. Las capturas HTTP 500 no se interpretaron como ausencia de licitaciones.

Los **17 EPE** archivados se revisaron individualmente: **0 vigentes verificadas, 14 pendientes y 3 con apertura documental superada**, sin prórroga actual comprobada. Esas tres no son cierres revalidados en vivo. Ninguna de las 17 se publica como cotizable. [Detalle individual](epe_17.csv).

La importación oficial existente se conserva y alimenta el mismo catálogo. Para un CSV descargado por el usuario:

```sh
python tools/importar_oficiales.py --fuente fuente-087 --url 'https://www.santafe.gob.ar/gestionesdecompras/site/index.php' --archivo /ruta/aperturas.csv --bandeja entradas_oficiales
python tools/importar_oficiales.py --bandeja entradas_oficiales --salida work/importados-control
```

El archivo y su JSON se conservan juntos en la bandeja. Se valida hash, dominio y procedencia; no se inventa la fecha de captura. Sin recibo comprobable, la vigencia queda pendiente. Boletín admite HTML o PDF con texto mediante el mismo importador. [Operación y límites del importador](../2026-11-06-recuperacion-efectiva/OPERACION.md). El CSV manual `Para_apertura_al_05112026.csv` no estaba disponible: sus cifras no se contabilizaron como extracción de esta fase.

## Informe comercial y revisión manual

- [Las 19 convocatorias con recepción vigente comprobada](informe_comercial.md).
- [CSV comercial íntegro](informe_comercial.csv), con organismo, provincia/localidad, número, objeto disponible, publicación comprobada, apertura, cierre, presupuesto, pago, presentación y enlaces.
- [119 procedimientos con apertura futura, pero recepción aún pendiente](presentacion_pendiente_actual.csv).

Los demás registros inciertos se conservan íntegros en `comercial/presentacion_pendiente.json` del artefacto de cierre: **2.156**, incluidos antecedentes. No se muestran como abiertos. En Venado Tuerto 27/2026 se recuperó el rótulo del pliego y su recepción, pero falta completar el objeto concreto; no se presenta como ficha documental completa.

Ejemplos cotizables ya conocidos o detectados por las fuentes existentes, **no atribuidos a la recuperación de EPE/Gestiones/Boletín**:

- [ASSA 1730 — adquisición de piezas de racorería](https://www.aguassantafesinas.com.ar/api/v1/publico/pliego/eca265b00de6496bb7f992e8dc0b4788): recepción hasta **24/11/2026, 10:00**. Publicación y pago pendientes.
- [ASSA 1277 — reparación y mantenimiento de electrobomba de 125 HP, Esperanza](https://www.aguassantafesinas.com.ar/api/v1/publico/pliego/5e038b0268194c08997676c0300ef5b0): recepción hasta **10/11/2026, 09:59**.
- [Rosario, Compra Ágil 128/2026 — impresión y rotulación para el Centro Cultural Roberto Fontanarrosa](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38736): recepción hasta **10/11/2026, 10:00**. Control conocido, presupuesto publicado $5.800.000; pago pendiente.

Las horas son de Argentina. El informe mantiene prioridad de llamados especiales, pagos comprobados, presupuesto y vencimiento; no estima rentabilidad. Incluye una sección fija con enlaces de fuentes que requieren revisión manual.

## Pendientes y cobertura territorial

Ocho candidatas no se incorporaron. [Candidatas y evidencia](candidatas_pendientes.csv). Se añadieron seis portales institucionales pendientes a la entrada del descubridor periódico existente, sin sustituir su estado: Bigand, Baigorria, Pujato, Fray Luis Beltrán, María Grande y San Benito. Los decretos de Pergamino y el portal secundario de Ramallo requieren comprobar convocatorias y/o procedencia institucional; no se promovieron por contener números de licitación.

- Pujato: corregida una trampa de navegación del calendario, que multiplicaba combinaciones de meses en páginas de noticias. Tiempo 55 → 18,6 s; **cero convocatorias extraídas**, sigue pendiente.
- Fray Luis Beltrán: redirección oficial `.gov.ar` → `.gob.ar` comprobada; no se extrajeron llamados y hay enlaces rotos. No se considera cubierta.
- Baigorria: la sección Compras ofrece contactos, no avisos extraídos; no se infiere que no existan compras.
- María Grande: documentos en carpeta pública incrustada de Drive y recorrido incompleto; sin evidencia suficiente para alta confiable.
- Cañada de Gómez y Compras UNR siguen con HTTP 403. Santa Fe capital y otros organismos conservan sus errores en el inventario individual.
- Ramayón, Fidela, Lehmann, Oliveros y otras comunas no tienen cobertura efectiva comprobada por el Boletín SF mientras éste permanezca inaccesible. No se declara cobertura exhaustiva de Santa Fe, Entre Ríos ni Buenos Aires cercana.

[Municipios prioritarios y estado de sus fuentes directas](municipios_objetivo.csv). La existencia de una URL no certifica revisión de todas las secciones ni cobertura permanente. Próximas prioridades: una captura oficial actual de Gestiones/Boletín, recepción de los avisos de Rosario todavía incompletos y portales propios de comunas sin fuente validada.

## Pruebas, conservación y reproducción

- [Barrido inicial de las 88 fuentes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42367128746).
- [Trece candidatas y primer reintento de Rosario](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42367624095).
- [Ruta mensual oficial: los 53 avisos del control](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42368523333).
- [Calendario, redirección y formularios públicos](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42369430468).
- [Validación final de DPV y MPBA](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42369784799).
- [Cierre real contra las dos copias de respaldo](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42370437224): **cero novedades y cero eventos en ambas segundas pasadas**, sin red ni OCR. No son dos nuevos barridos de portales: se repiten capturas para comprobar deduplicación.
- [CI de código y catálogo](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42370437240): **463 pruebas Python y 28 Node aprobadas** en Actions. Se corrigieron la desincronización inicial de `fuentes.txt`/`fuentes.json` y el campo nulo de persistencia detectados por las validaciones; no se descartaron los fallos.
- [Piloto diario del 7/11](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42368222744): **success**. Conservado su respaldo automático `ca444e0`; los cambios se aplicaron por encima de ese commit.

Los artefactos nativos contienen las capturas y checkpoints completos (90 días de retención). Este directorio conserva métricas, CSV y referencias de forma versionada. `cierre-inicial.json` y `cierre-actual.json` documentan las comprobaciones de integridad. El informe no suma 594 recuperaciones de línea de base como publicaciones nuevas.

**Main, producción, respaldos y programador no fueron modificados por estos cambios.** PR abierto, sin merge. Sin servicios pagos, nuevos procesos OCR, correo activado ni cálculos de rentabilidad. La cobertura y el saldo de nuevas publicaciones cotizables siguen necesitando mejoras; no se atribuye el resultado a falta de volumen regional cuando hubo fuentes inaccesibles.

Comprobación adicional de Buenos Aires: [Rojas, ruta de compras 2026](rojas_2026.json), [run real](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42372161366). La tabla devolvió 1.800 referencias administrativas sin apertura/cierre comprobables; no se las sumó al catálogo de convocatorias ni a las novedades.

Falta comprobar la próxima corrida diaria con las 93 fuentes. Se mantuvieron su presupuesto de ejecución y el programador. El saldo de cero publicaciones nuevas cotizables no demuestra ausencia de publicaciones en la región: persisten fuentes inaccesibles y localidades sin auditoría.
