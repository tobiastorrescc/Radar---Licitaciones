# Informe comercial: cobro rápido y revisión de 116 oportunidades

Informe cerrado el **31/10/2026**, con evidencia de portales y documentos capturada el **30/10**. No representa una reconsulta de las 116 el día 31. Se continúa PR #1, sin merge ni cambios en main, historial de producción, programador o respaldos.

## Qué estaba guardado y qué se completó al retomar

GitHub conservaba el commit **d778963fb2c99055c5cdc0fc82097fd43b76217b**. La [auditoría final 41136973306](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41136973306) y las [pruebas 41136973281](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41136973281) terminaron correctamente. No se volvieron a ejecutar esas consultas ni OCR al retomar.

Faltaba publicar este informe y completar la transcripción comercial de La Paz 39/2026. Se reutilizaron el PDF, el OCR por hash y la inspección visual ya realizada de las páginas 1, 3 y 4. Se incorporó la tabla de nueve renglones, el requisito minero específico de la broza y el plazo de entrega separado del plazo de pago. La anotación solo se aplica al mismo SHA-256, no a futuros documentos distintos.

## Resultado medido

| Indicador sobre la misma cohorte | Antes | Después |
|---|---:|---:|
| Oportunidades conservadas | 116 | **116** |
| Pago verificado | 7 (6,03 %) | **9 (7,76 %)** |
| Pago pendiente | 109 | **107** |
| Pasan de desconocido a verificado | — | **2** |
| Pago rápido documentado | 1 | **2** |
| Primeras detecciones de Rosario con fecha de publicación comprobada | 0 de 9 | **9 de 9** |

Los dos pagos nuevos son La Paz 39/2026 (diez días hábiles desde entrega y factura) y La Paz 40/2026 (opciones de calendario para servicios). **El 40/2026 no tiene garantizado un cobro a diez días y queda fuera del listado rápido.** Se corrigió una extracción que cortaba el artículo antes de su continuación sobre servicios; la regresión utiliza el OCR real de esa página.

Hay **63 fichas observadas en las capturas del 30/10 y 53 conservadas sin reobservación de su publicación**. Una apertura futura calculada no prueba por sí sola ausencia de suspensión o prórroga posterior. La descarga de un pliego tampoco equivale a confirmar el estado de la convocatoria.

Se conservaron todas las 116 oportunidades, sin límites por cantidad, monto o rubro. [Estado individual de las 116](estado_116.csv) · [Fichas completas](TODAS_LAS_OPORTUNIDADES.md) · [Métricas y procedencia](metricas.json).

## Listado completo de cobro rápido

El orden siguiente usa **condición contractual publicada**, seguida de fecha límite. **No se puede ordenar honestamente por tiempo efectivo de acreditación**: no está comprobado en ninguno de los dos casos. Tampoco se conoce cuándo el proveedor desembolsaría el capital. No se estima rentabilidad.

| Orden contractual | Organismo / procedimiento | Objeto | Presupuesto publicado | Pago | Fecha / presentación | Vigencia y evidencia |
|---|---|---|---:|---|---|---|
| 1 | Municipalidad de Chajarí — Pública 19/2026 | Repuestos originales para trenes de rodaje de New Holland E215C EVO y Komatsu PC200; 13 renglones | $59.500.000 | **Contado contra entrega**; acreditación bancaria inmediata no comprobada | Apertura **19/11/2026 10:00**. Oferta online y nota de contraseña en sobre hasta **09:30**; no se inventa otro límite de carga digital | API oficial consultada 30/10 19:16:46 Argentina: estado **para_apertura**. [Ficha, cantidades y pliego](CHAJARI_19_2026.md) |
| 2 | Municipalidad de La Paz — Concurso 39/2026, Decreto 563/26 | Materiales para cordón cuneta en calle Torres Vilches entre Chañar y C. D. Vila; nueve renglones | $34.995.000 | **10 días hábiles desde entrega del bien y presentación de factura**, con recepción de materiales asentada | **04/11/2026 09:00**, hasta apertura del primer sobre; **presencial**, Mesa de Entradas, sobre cerrado | Pliego comprobado; vigencia de la publicación **pendiente de reconfirmar**, conservada por evidencia previa. [Ficha completa](LA_PAZ_39_2026.md) · [PDF oficial](https://haciendalapaz.gob.ar/archivos/20261030074127-f_pliego.pdf) |

No se encontraron anticipos ni otros pagos numéricos de hasta quince días verificables en esta cohorte. Esto no implica que las 107 pendientes carezcan de condiciones favorables. [Listado separado y fichas de cobro rápido](COBRO_RAPIDO.md) · [Datos estructurados](rapidas.json).

### La Paz 39/2026: cláusula y cantidades

**Artículo 9º, página 4:** “La Municipalidad de La Paz abonará el importe correspondiente al presente Concurso, dentro de los 10 (diez) días hábiles posteriores a la fecha de entrega del bien adjudicado y presentación de la factura.” Exige asentar la recepción total en la factura; los materiales quedan sujetos a revisión. Contempla pagos parciales por certificaciones parciales y retenciones por deudas con el Municipio. No se interpreta como diez días desde adjudicación.

**Entrega, artículo 8º, página 3:** dentro de **30 días hábiles desde notificación de adjudicación**, en la ciudad de La Paz y lugar que determine el Municipio; flete y acarreo a cargo del adjudicatario. El vencimiento de pago comienza después de entrega y factura. No se suman estos plazos para inventar una fecha de acreditación.

| Ítem | Descripción comprobada visualmente, página 1 | Cantidad |
|---:|---|---:|
| 1 | Broza de 1ª calidad | 40 m³ |
| 2 | Hormigón H21 con macrofibras de PVC, dosificación 1,5 kg/m³ | 115 m³ |
| 3 | Hierro liso Ø16 mm × 12 m | 16 unidades |
| 4 | Caño negro K4 para pasadores Ø3/4 pulgada | 15 m |
| 5 | Hierro nervado ADN 420 Ø6 mm × 12 m | 70 unidades |
| 6 | Plancha de telgopor 1 m × 1 m × 1 cm | 25 unidades |
| 7 | Tabla para encofrado 4 pulgadas × 1 pulgada × 4 m | 20 unidades |
| 8 | Estacas 1 pulgada × 1 pulgada × 0,50 m | 100 unidades |
| 9 | Alambre de atar Nº 16 | 5 kg |

Requiere pliego y anexos firmados, cotización por escrito con precios unitarios y total con IVA, documentación societaria y representación cuando corresponda y declaración de domicilio electrónico. Para cotizar broza: registro provincial de actividades mineras, número de productor minero vigente y habilitación de comercialización. Mantenimiento de oferta: veinte días hábiles, con renovación prevista. El pliego permite variar adquisiciones en ±30 %. No se introduce una garantía monetaria no comprobada.

### Chajarí 19/2026: los trece renglones

| Equipo | Renglón | Descripción | Cantidad |
|---|---:|---|---:|
| New Holland E215C EVO | 1 | Cadena | 2 |
| New Holland E215C EVO | 2 | Rueda guía completa | 2 |
| New Holland E215C EVO | 3 | Rueda dentada / rueda 21Z | 2 |
| New Holland E215C EVO | 4 | Rodillo inferior | 16 |
| New Holland E215C EVO | 5 | Rodillo superior | 4 |
| New Holland E215C EVO | 6 | Tornillos para zapatas | 400 |
| New Holland E215C EVO | 7 | Tuercas para zapatas | 400 |
| Komatsu PC200 | 1 | Rueda guía | 2 |
| Komatsu PC200 | 2 | Rodillo inferior | 18 |
| Komatsu PC200 | 3 | Rodillo superior | 4 |
| Komatsu PC200 | 4 | Rueda dentada | 2 |
| Komatsu PC200 | 5 | Bulones con tuercas | 400 |
| Komatsu PC200 | 6 | Cadena de 51 eslabones | 2 |

Repuestos **nuevos, sin uso y originales**. Entrega en corralón municipal; el oferente debe indicar su plazo, sin un número de días impuesto en la cláusula examinada. Recibo de compra del pliego, garantía de oferta del 1 % (**$595.000**), presupuesto firmado y sellado, personería cuando corresponda y constancia de CUIT. Presentación online y nota de contraseña presencial en sobre. “Contado contra entrega” consta en página 4, artículo 12, y página 6. [Ficha y acceso oficial al pliego](CHAJARI_19_2026.md). No se inventa una URL estática para el documento servido mediante `return_file`.

## Las nueve primeras detecciones de Rosario

Las nueve tienen publicación oficial **30/10/2026**, recuperada de un campo rotulado “Fecha de publicación”, independiente de apertura y última actualización. Sus números de contratación son **64, 125, 471, 470, 469, 468, 110, 210 y 462/2026**. Los valores anteriores correspondían a expedientes. [Tabla con objetos, expedientes, fechas y enlaces oficiales](ROSARIO_NUEVE.md) · [Evidencias estructuradas](ROSARIO_NUEVE.json).

No se reescribe su primera detección ni se generan nuevas alertas por completar la fecha. La lectura de detalle implementada para esta revisión reconoce la ficha Drupal y sus enlaces documentales de API sin extensión PDF. Su incorporación a la ruta incremental diaria requiere revisar primero la migración de identidades: en esta etapa el piloto continúa intacto.

## Alcance real y pendientes

La revisión completa de la cohorte significa que sus 116 fichas permanecen registradas y con estado de investigación; **no que se hayan podido leer pliegos de las 116**. La primera pasada consultó 90 URLs oficiales únicas. La revisión ampliada registró 122 enlaces documentales: 34 accesibles, 87 errores y uno que no era documento; 85 errores correspondían a timeout del handshake TLS de los documentos de Rosario. Los errores permanecen visibles y no se eluden. En la pasada siguiente se evitó volver a intentar inmediatamente esos 85 enlaces fallidos.

La fase selectiva procesó solo **dos páginas nuevas de dos documentos escaneados**, CAFESG y Ministerio de Planeamiento; el OCR anterior se reutilizó. La última pasada usó **cero OCR nuevo** y al retomar el 31/10 tampoco se descargó ni procesó nuevamente documento alguno. Permanecen pendientes pliegos grandes de Concepción del Uruguay y documentos de Rosario inaccesibles por TLS, entre otros. No se califican esos casos como “pago no publicado”.

Falta reconfirmar la publicación de La Paz 39/2026 antes de ofertar, documentar pagos en las 107 pendientes y trasladar las correcciones de números de Rosario al escaneo incremental con compatibilidad de identidades e historial. El orden efectivo de recuperación del capital seguirá pendiente mientras no exista evidencia suficiente de desembolso y acreditación. Se conserva todo el catálogo y no se calcula rentabilidad.

Las pruebas automáticas del código anterior a la interrupción aprobaron; el commit de cierre agrega una regresión para la tabla de La Paz por hash y página. Se publican los resultados dentro del mismo PR #1. No se modifica el correo ni se activa envío.
