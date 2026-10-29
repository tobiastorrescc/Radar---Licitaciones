# Revisión de las abiertas de Actions #54

Se recuperaron del artefacto #54 los 11 registros ABIERTA originales en Actions #57. Se guardan sin modificación en `tests/fixtures/reales/abiertas54.json`. Las capturas HTML oficiales, fecha/run y hash del documento original están documentadas en `tests/fixtures/reales/revision57-proveniencia.json`. No se cambia el historial de producción.

## Causas comprobadas

- El regex de códigos consumía texto de plantilla como «Licitaciones … Estado». También trataba espacios alrededor de guiones como identificadores distintos. La plantilla general y sus archivos podían generar registros adicionales del mismo llamado.
- El Aeropuerto publica número/objeto/apertura en una tabla horizontal y presupuesto en otro párrafo. Antes se tomaba el texto de la tabla o de la lista de descargas, sin ese presupuesto. Los nombres de anexos llegaban a ocupar el campo objeto.
- Al unir variantes se elegía el título más largo, perdiendo datos de una ficha más breve pero mejor estructurada.
- Los códigos cortos y largos requieren evidencia de equivalencia. Dos series administrativas distintas (por ejemplo OF-LEGALES y COM-CON) pueden usar el mismo tipo/número anual: sus sufijos oficiales se conservan. No se fusionan sólo por el contador numérico.

## Corrección

El lector del Aeropuerto interpreta la tabla de campos oficiales, el párrafo de presupuesto y los enlaces reales de descargas. No genera una convocatoria por cada nombre de archivo. Mantiene el objeto de compra separado de la navegación y de la lista de adjuntos.

La identidad usa organismo, código/número normalizado y convocatoria. La compra directa 52/2026 recuperada en #61 mostró otro formato: «Contratación Directa Nº 52/2026» y «52/2026». Se normalizan también los rótulos incluidos en el campo número, con fixture real y regresiones para distintos tipos de procedimiento. Las variantes tipográficas y los espacios de guiones se normalizan. Las abreviaturas se resuelven mediante el código completo observado en la tabla, URL de ficha o adjuntos inequívocos. Cada fusión conserva las URLs y adjuntos. Un segundo llamado es una convocatoria distinta; «desierta» y «adjudicada» son situaciones, no otro número de llamado.

Los 11 registros originales se reducen a **9 identidades** al eliminar dos duplicados del Aeropuerto. Esto no afirma que el portal tenga solamente nueve convocatorias abiertas: la nueva consulta puede recuperar otras. El reporte `revision_11_abiertas54.json` muestra, fila por fila, la identidad corregida, duplicada de qué fila, estado y presupuesto recuperados en la nueva corrida.

Las páginas de listados pueden contener varias convocatorias reales (por ejemplo los datos JSON de Concepción del Uruguay). Se exige identificar cada procedimiento individual. Una página general sin esa identidad no se clasifica ABIERTA por contener una fecha futura ajena. Sus candidatos se mantienen en el artefacto y no se presentan como oportunidades comerciales.

## Presupuestos oficiales comprobados en las capturas #57

| Aeropuerto Rosario | Presupuesto publicado | Apertura |
|---|---:|---|
| LPR-2026-00000002, jardinería | $36.000.000 | 28/10/2026 11:00 |
| CPRV-2026-00000001, líquidos azules | $10.000.000 | 30/10/2026 11:00 |
| LPU-2026-00000001, serie OF-LEGALES, volquetes | $31.200.000 | 30/10/2026 11:00 |
| LPU-2026-00000002, serie OF-LEGALES, tándems | $61.806.395,30 | 02/11/2026 11:00 |
| LPR-2026-00000001, control documentario | $13.200.000 | 29/10/2026 11:00 |

La moneda permanece desconocida cuando el texto usa sólo `$`. No se usa el costo del pliego como presupuesto.

## Vigencia y reportes

Apertura y publicación se extraen de sus etiquetas independientes. Nunca se usa primera detección, año del procedimiento o apertura como fecha de publicación. Se conserva la hora publicada de apertura y se compara en hora de Argentina. La vigencia de los reportes se recalcula al finalizar la comprobación de enlaces, para no mantener abierta una convocatoria que venció durante la consulta. El día de apertura sin hora comprobada queda desconocido. Una situación de cierre explícita prevalece sobre una fecha futura; el encabezado vacío «Proveedor adjudicado» y una condición futura «será adjudicada» no prueban adjudicación.

Se agregan `oportunidades_abiertas.json/.md` y `oportunidades_proximas_a_vencer.json/.md`. La segunda vista incluye las abiertas que vencen dentro de siete días calendario, inclusive. Incluyen todas las abiertas observadas, incluso si ya se encontraban en el historial. El reporte íntegro de primeras detecciones sigue incluyendo las vencidas y desconocidas; ninguna vista borra registros anteriores ni filtra por monto, rubro o financiación.

## Comprobación de enlaces

Los adjuntos de todas las abiertas se comprueban en procesos aislados (4 concurrentes, hasta 15 s por enlace, 180 s globales). Los que no terminan conservan un estado pendiente explícito. No hay límite de cantidad: se registran también los que no pudieron iniciarse dentro del plazo.

Se usa GET con validación TLS y se comprueba firma PDF/ZIP-DOCX: una respuesta HTML con HTTP 200 no valida el documento. Se registra URL final, fecha, bytes y SHA256. La identificación del pliego se fundamenta en la etiqueta oficial o en un encabezado explícito de pliego y procedimiento compatible. La auditoría real #59 detectó resoluciones RESCONJ que mencionaban el pliego: se agregaron regresiones para conservarlas como resoluciones y evitar que reemplacen al pliego técnico. Una mera mención de la palabra pliego no valida el tipo de documento. Se distingue documento accesible de lectura pendiente/OCR, error, redirección a otro dominio y pliego no identificado. No se comprueban indiscriminadamente los pliegos de todo el archivo histórico; el alcance es el conjunto de abiertas de la corrida. Sus presupuestos sólo se completan desde un documento cuando la pertenencia al procedimiento es inequívoca.

## Preservación y pruebas

La deduplicación persistente compara con un índice derivado de las entradas antiguas, sin borrarlas ni reescribirlas. Las versiones enriquecidas quedan en los reportes actuales y en el artefacto. El workflow diario conserva su horario y el job de producción sigue deshabilitado en el PR.

Las regresiones incluyen las cinco fichas reales, las 11 abiertas originales, variantes de códigos/URLs/convocatorias, series distintas que no se deben fusionar, plantilla general, presupuesto omitido, distinción de fechas, hora de cierre, HTTP 200 con HTML y persistencia de más de 1.400 abiertas sin límite.
