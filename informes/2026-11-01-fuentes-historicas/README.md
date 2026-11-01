# Recuperación de fuentes históricas — 1 de noviembre de 2026

Trabajo exclusivo en `mejora/radar-auditable`, PR #1. No se modificaron main, producción, el programador ni los respaldos. No se activaron servicios, correo, OCR adicional ni análisis de rentabilidad.

## Inventario reproducible

Se recorrieron los 207 commits alcanzables del checkout completo en GitHub Actions y 809 blobs de texto (65.156.268 bytes), incluidos scripts, fuentes, informes, auditorías e índices comprimidos. Se recuperaron **8.870 referencias de dominios oficiales/conocidos**: 4.689 documentos, 1.433 portales/secciones, 507 avisos/boletines internos, 1.458 enlaces asociados a procedimientos y 783 referencias institucionales. No son 8.870 fuentes operativas. Hay 121 nombres de organismos asociados en los archivos históricos; esa asociación no constituye validación territorial ni institucional.

No hubo archivos excluidos por tamaño. Un blob histórico intermedio del índice comprimido (`30730e1c45c8d854b7cf2ac4f10cdb5e9e002dd9`) está corrupto y se registra como ilegible; las versiones posteriores legibles sí se procesaron. No se recuperan conversaciones fuera de Git ni commits borrados/inaccesibles.

- [Inventario completo CSV comprimido](inventario_completo.csv.gz): URL, organismo/localidad/provincia cuando constan, tipo, estado previo, extracción actual, publicaciones y cantidades observadas.
- [Evidencias completas JSON comprimido](inventario_evidencias.json.gz): commit, blob y archivo de procedencia por URL; apertura con `gzip -dc`.
- [14 referencias solicitadas y pruebas individuales](referencias_verificadas.csv).
- [672 procedimientos comprobados, sin recortes](publicaciones_comprobadas.csv.gz).
- [Nuevas abiertas y vigencias pendientes](nuevas_y_pendientes.csv): vacío en esta muestra, no significa ausencia de novedades en todo el territorio.
- [Resumen verificable](resumen.json).

Se incorporan **23 rutas estables históricas a la cola persistente** `inventario/candidatas_historia.json`, consumida por el descubrimiento periódico existente. Son candidatas pendientes, no altas confiables. Se excluyen fichas individuales, documentos, rutas con números, duplicados de protocolo/barra y fuentes ya incorporadas. El resto permanece inventariado para contraste: no se fabricaron portales ni se promovieron cientos de URLs sin validación. Las validaciones siguen exigiendo organismo, jurisdicción y procedimientos con objeto.

## Resultado de las referencias solicitadas

| Referencia | Extracción nativa actual | Procedimientos | Abiertas calculadas |
|---|---|---:|---:|
| Boletín Oficial Santa Fe | Error de acceso: timeout, incluida ruta histórica Ramayón | 0 | 0 |
| Compras Santa Fe `.gov.ar` | Error de acceso: timeout | 0 | 0 |
| Gestiones de Compras Santa Fe | Error de acceso: timeout | 0 | 0 |
| EPE aperturas | Error de acceso: TLS/EOF | 0 | 0 |
| EPE compras | Error de acceso: TLS/EOF | 0 | 0 |
| Rosario | Parcial: límite de tiempo, captura conservada | 58 | 58 |
| Compras UNR | Error de acceso: HTTP 403; no confundir con otras secciones UNR operativas | 0 | 0 |
| Aeropuerto Rosario | Parcial: límite de tiempo | 49 | 5 |
| Minplan Entre Ríos | Operativa en la muestra | 486 | 2 |
| San José | Error de acceso: timeout | 0 | 0 |
| SIBOM raíz provincial | Accesible; extracción territorial pendiente. No alta global bonaerense | — | — |
| Zárate | Operativa en la muestra | 31 | 0 |
| Salto | Operativa en la muestra | 21 | 0 |
| Arrecifes | Operativa: seis DOCX leídos, sin OCR | 6 | 0 |

En las 14 referencias: **4 operativas, 2 parciales, 7 con error de acceso y 1 pendiente de extracción territorial**. Acceso HTTP exitoso por sí solo no valida una fuente. Las cantidades pertenecen a capturas del 1/11; no son todas publicaciones nuevas ni cobertura exhaustiva de sus organismos.

Control adicional: **Ramallo**, índice municipal y SIBOM ciudad 102: 21 procedimientos históricos reales, recorrido parcial por límite de tiempo y timeout de un boletín. Existía conector, pero `incorporada:false` impedía monitorearlo. Se habilita como **PARCIAL**, conservando sus incidencias y sin afirmar convocatorias abiertas. Se pasa de **80 fuentes configuradas activas + 2 auto = 82**, a **81 + 2 = 83**; las 82 entradas del inventario configurado no eran todas activas. Concordia continúa pendiente, sin habilitación ficticia.

## Omisión corregida y ejemplo verificable

En Arrecifes el índice reconocía cinco avisos. La lectura de todos los documentos publicados descubre un sexto y evita que presupuesto/pliego sean requisitos para registrar un aviso. El lector DOCX introducía espacios entre fragmentos de Word (`202` + `6`, `1` + `1:00`); se corrige la concatenación y se conserva el espaciado real. La caché invalida sólo el texto DOCX afectado y reutiliza bytes; no invalida PDF ni OCR previo. También se reconocen fechas rotuladas DÍA/MES/AÑO/HORA.

[Arrecifes, llamado público 3, explotación de servicios del balneario municipal](https://arrecifes.gob.ar/wp-content/uploads/2026/09/NOTA-LLAMADO-A-LICITACION-PUBLICA-3-2026-1-1.docx), apertura **5/10/2026 11:00**: histórico vencido, no oportunidad comercial nueva. No se fusiona con el llamado 3 del documento de 2024. Otro ejemplo: [repavimentación de Tucumán y Gerardo Risso](https://arrecifes.gob.ar/wp-content/uploads/2026/07/LICITACION-PUBLICA-1-2026-REPAVIMENTACION.docx), presupuesto documental **$238.329.000**, apertura **3/8/2026 11:00**, también vencido. La numeración anual rotulada `Nº:` requiere mejora adicional; no se infiere del año de apertura ni del nombre del archivo.

Comparación sobre los **672 procedimientos efectivamente comprobados** frente al catálogo anterior de 5.460 vistas: **65 abiertas ya conocidas, 606 conocidas no abiertas y 1 histórico antes omitido**. **Cero abiertas inéditas recuperadas y cero publicaciones nuevas con fecha comprobada en esta muestra**. No se presenta este resultado como cobertura global ni como cumplimiento de la meta de 20 nuevas diarias.

## Caso Ramayón

Se localizó el [aviso oficial del Boletín, edición 18/9/2026](https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-09-18licitaciones.html): Comuna de Ramayón, licitación pública 01/2026, tractor 0 km 4x4 Perkins 90/95 HP, presupuesto $50.000.000, pago contado, presentación hasta 6/10/2026 10:30 y apertura 8/10/2026 10:30. Está vencido.

La regresión recorre índice → sección → aviso, sin exigir PDF ni presupuesto, y no mezcla el aviso vecino. **La fixture es una transcripción de la consulta web, no una captura HTTP nativa**. La ruta HTML, la variante publicada PDF y el índice continúan agotando tiempo desde Actions. Por tanto, se demuestra reconocimiento controlado, pero **no se declara recuperado el acceso automático de Ramayón/Boletín**.

## Pruebas, persistencia y siguientes prioridades

402 pruebas nativas aprobadas; localmente 401 aprobadas y 1 omitida por dependencia opcional. [Pruebas nativas aprobadas](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41271437364). [Piloto comparativo aprobado](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41271437311): 52 fuentes mediante capturas reutilizadas, dos pasadas; segunda pasada con **2.598 sin cambios, cero eventos y cero novedades**, producción y respaldo intactos, cero consultas adicionales y cero OCR. Se inspeccionó el reporte diario completo, no sólo la conclusión del workflow. El reporte conserva las incidencias de las capturas. La primera pasada registró 28 primeras detecciones sin fecha, 21 recuperaciones de línea de base, 10 completados y 49 cambios; **cero nuevas con fecha comprobada**. No equivalen a 87 publicaciones nuevas. El contraste ampliado detectó además una diferencia de nombre `MUNICIPALIDAD DE SEGUÍ-` frente a `Municipalidad de Seguí`: es el mismo 09/2026, no una abierta inédita. Se elimina el separador final únicamente en la identidad, con regresión para conservar organismos/provincias diferentes. La reproducción ampliada incluye capturas antiguas: una falsa lectura de «calle Pública Nº26» sigue documentada en ese material previo, no se cuenta como convocatoria real ni como nueva. La extracción documental actual ya exige una cabecera de procedimiento. Una primera prueba comparativa detectó un conflicto SQLite al converger evidencias de varias capturas al mismo registro histórico. Se corrigió consolidando sus evidencias antes de persistir un único evento, sin borrar registros ni versiones; regresión específica conserva ambos anexos. La comparación también evita llamar hallazgo histórico a un documento cuyo texto/identidad mejoró pero cuya URL, organismo y número literal ya existían.

Prioridades pendientes: recuperar acceso nativo a Boletín/Compras/EPE/San José/Compras UNR; validar las 23 rutas mediante la cola y comprobar nuevas publicaciones; continuar el padrón territorial (655 localidades inventariadas, no todas auditadas); resolver límites de navegación de Rosario, Aeropuerto y Ramallo; mejorar la numeración anual rotulada en DOCX sin inferencias. El inventario no equivale a cobertura completa ni garantiza 20 publicaciones diarias cuando el volumen real sea menor.

## Reproducción

```bash
python -m unittest discover -s tests
# Checkout completo, sin OCR ni red:
python tools/inventariar_historial.py --salida work/historial-fuentes
# Prueba HTTP nativa y acotada: plan/manifiesto versionados en la rama.
# Las capturas y el CSV completo quedan en los artefactos de Actions.
gzip -dc informes/2026-11-01-fuentes-historicas/inventario_completo.csv.gz > /tmp/inventario_fuentes.csv
```

Validación final: [dos pasadas y huellas](validacion_dos_pasadas.json), [clasificación incremental](resumen_pasadas.json). El contraste ampliado reutilizó 52 capturas de distintas fechas; encontró 94 abiertas ya conocidas y **ninguna abierta inédita**, dos recuperaciones históricas y un registro dudoso procedente de una extracción antigua (calle Pública Nº26). Ese registro no acredita una oportunidad. Las cifras de cobertura estricta del contraste son 17 operativas, 15 parciales, 16 bloqueadas y 4 pendientes, únicamente sobre esas capturas; no representan un escaneo simultáneo de las 83 fuentes diarias. El informe diario derivado conserva 171 abiertas calculadas, de las cuales 100 fueron observadas en las capturas y 71 sólo por historial; no se presentan todas como vigentes revalidadas hoy.

[Artefacto nativo con CSV sin comprimir e informes completos](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41271437311/artifacts/13069107656). El CSV de 672 publicaciones corresponde a las referencias probadas; el informe comparativo ampliado incluye además capturas anteriores y no debe sumarse como publicaciones nuevas.
