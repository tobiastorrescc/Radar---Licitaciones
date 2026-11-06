# Recuperación efectiva — resultado y bloqueos

Evidencia del **5/11/2026 a las 23:27:28 de Argentina (6/11 UTC)**. Base solicitada: `546dbf9`. Trabajo exclusivo en `mejora/radar-auditable`, PR #1 abierto, sin merge.

**Las tres fuentes críticas siguen inaccesibles. Cero fuentes recuperadas en vivo y cero oportunidades adicionales atribuibles a su reparación.** El barrido ampliado sí encontró una publicación nueva con recepción vigente comprobada en Rosario. No se presenta como resultado de recuperar EPE, Gestiones o Boletín.

## Resultados comerciales comprobados

- **9 fuentes consultadas y finalizadas**: 2 operativas, 2 parciales y 5 inaccesibles. Ninguna inaccesible se informa como «sin novedades».
- **325 procedimientos** y un candidato: 288 procedimientos directos + 37 antecedentes EPE ya conocidos. Los antecedentes no son publicaciones nuevas.
- 81 aperturas documentales futuras: 65 de Rosario y las mismas 16 del lote anterior (ASSA 3, Aeropuerto 5, PJER 8). **Una apertura futura no acredita por sí sola recepción vigente.**
- **6 convocatorias con presentación vigente comprobada**: Rosario 3 y ASSA 3. De ellas, una es publicación nueva respecto del respaldo diario; cinco ya conocidas. No se recortó el listado por presupuesto, rubro, pago ni cantidad.
- 110 procedimientos pendientes de presentación/revalidación y 209 vencidos documentales, separados del informe comercial. No se borran: el [catálogo observado](catalogo_observado.csv) conserva todos los registros, y el [CSV de pendientes](pendientes_presentacion.csv) detalla los motivos. Una prórroga no comprobada no se inventa.
- Dos publicaciones nuevas con fecha comprobada contra la copia del respaldo: Compra Ágil 128/2026 y Licitación Privada 26/2026, Rosario. **Sólo la primera** tiene recepción vigente comprobada; la segunda permanece pendiente y no se publica como cotizable.

### Publicación nueva cotizable

**Municipalidad de Rosario — Compra Ágil 128/2026**. Servicio de impresión, rotulación y colocación de vinilo y PVC espumado para el Centro Cultural «Roberto Fontanarrosa».

- Publicación: 5/11/2026.
- Apertura y cierre de recepción: **10/11/2026 a las 10:00, Argentina**.
- El aviso expresa: «Lunes a viernes (hábiles administrativos) de 08:00 a 14:00, **hasta el día y hora de apertura de sobres**».
- Presentación presencial: Oficina de Compras (SCyE), Aristóbulo del Valle 2734.
- Presupuesto publicado: **$5.800.000,00**; el sitio no explicita código ISO de moneda. Pago: **Pendiente de verificar**.
- [Publicación oficial y acceso al pliego](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38736).
- HTML oficial capturado: SHA-256 `d40bc03cbf9c4fdd4e44d67242c0b87a81687252aeeb68908ee59a49a49ae58f`.

[CSV de la nueva vigente](nuevas_vigentes.csv) · [Informe completo de seis vigentes](informe_comercial.md) · [CSV comercial completo](informe_comercial.csv). Se trata de detección por el lector existente de Rosario, no de una omisión demostrada del código anterior ni de una mejora porcentual global.

## Estado individual y comparación equivalente

| Fuente | Antes (`546dbf9`) | Ahora | Procedimientos directos | Apertura futura documental | Recepción vigente comprobada | Obstáculo actual |
|---|---|---|---:|---:|---:|---|
| EPE | Inaccesible | Inaccesible | 0 | 0 | 0 | TLS: EOF durante handshake; no se desactiva validación |
| Gestiones SF | Inaccesible | Inaccesible | 0 | 0 | 0 | Timeout HTTP y Chrome antes de cargar el DOM; exportación sin URL comprobada |
| Boletín SF | Inaccesible | Inaccesible | 0 | 0 | 0 | Timeout en secciones diarias y alternativas oficiales |
| Cañada de Gómez | Inaccesible | Inaccesible | 0 | 0 | 0 | HTTP 403; nomencladores sigue omitido |
| Compras UNR | Inaccesible | Inaccesible | 0 | 0 | 0 | HTTP 403 |
| ASSA | Operativa | Operativa | 3 | 3 | 3 | Sin incidencias en este lote |
| Aeropuerto Rosario | Parcial | Parcial | 162 | 5 | 0 | Se conservan resultados al alcanzar 120 s; recepción pendiente |
| Poder Judicial ER | Operativa | Operativa | 58 | 8 | 0 | Extracción completa del recorrido configurado; recepción pendiente |
| Rosario | Fuera del lote anterior de ocho | Parcial | 65 | 65 | 3 | Timeouts de páginas/fichas y recorrido incompleto declarado |

La muestra común de ocho mantiene **2 operativas, 1 parcial, 5 inaccesibles y 16 aperturas futuras documentales**. No hubo pérdida de esos procedimientos. El cambio de etiqueta comercial de 16 a 3 en esa muestra aplica la exigencia de verificar recepción; las otras 13 siguen visibles como pendientes, sin eliminar evidencia ni historial. Rosario ya estaba configurada: **cero fuentes nuevas incorporadas**.

Detalle de tiempos, URLs y errores: [fuentes.csv](fuentes.csv) y [fuentes.json](fuentes.json). Barrido de red: **208,216 s**; importación: **0,262 s**; total de esas etapas **208,478 s**. No es comparable con los 123,414 s del lote anterior de ocho sin aclarar que se añadió Rosario al control.

## Cambios implementados

1. **Gestiones**: navegador estándar aislado en Actions, con presupuesto total y por navegación, inspección de formularios y respuestas públicas, exportación sólo desde enlace/botón realmente observado, capturas importables y recorrido de páginas. No se eluden restricciones ni se inventa el endpoint CSV. El recorrido HTML detecta páginas repetidas y diferencia un total publicado mayor al recuperado. Pruebas de siete páginas, 75 filas CSV y conteo incompleto, sin truncamiento a las primeras filas.
2. **Boletín**: corrección de encabezados `MUNICIPIO DE` y consorcios; el aviso real histórico de Bigand 3/2026 ya no se atribuye al organismo anterior. Convocatorias sin número se conservan por huella del aviso, también en importación; fechas nuevas expresas en prórrogas prevalecen sobre la apertura anterior sin inventar otro llamado. Se conserva el lector de sección completa HTML/PDF, sus encabezados repetidos, procedencia y bandeja de archivos. **Sin descarga real actual, no se certifica cobertura de ninguna edición de esta etapa.**
3. **EPE**: control persistente de los 17 antecedentes, contrastados contra una única consulta compartida. Resultado individual: **17 pendientes, 0 vigentes verificadas y 0 vencidas dentro de estos 17** a la hora de la evidencia. Los otros 20 antecedentes del archivo se conservan; no se reemplaza su última observación oficial del 28/10 por la fecha de importación.
4. **Control manual**: herramienta reutilizable para CSV/JSON con grupos automático, manual y ambos, CSV íntegro de omisiones, fechas de revisión y causa probable. Un organismo ajeno al lote no se etiqueta como omisión comprobada del extractor consultado.
5. **Alertas**: estados separados para revisión correcta sin novedades, parcial, inaccesible y recuperación documental con procedencia comprobable. Antes de comparar contra historial, no se afirma «sin novedades». Un archivo antiguo no convierte el acceso fallido en operativo.
6. **Informe comercial y entrega preparada**: exigen recepción vigente comprobada y observación actual; apertura y publicación son independientes. Vencidos e inciertos permanecen en auditoría. El CSV, el catálogo y el historial siguen completos. No se activa correo ni se agrega análisis comercial u OCR.

La preparación y límites de la importación se explican en [OPERACION.md](OPERACION.md). Un CSV o HTML aportado sin recibo de descarga comprobable se procesa, pero su vigencia queda pendiente. La referencia manual a `Para_apertura_al_05112026.csv` (114 filas/99 aperturas futuras) no se utilizó como archivo ni como resultado: no está disponible entre los archivos del repositorio.

## Control manual y omisiones

22 controles documentados: nueve coinciden con el radar, trece no aparecen en esta captura. De esos trece, once corresponden a fuentes fuera del lote, y dos a fuentes consultadas pero inaccesibles: Cañada de Gómez y Ramayón/Boletín. Los dos controles son del 31/10: Ramayón está vencido; la vigencia actual de Cañada no se revalidó. **No se anuncia cero omisiones globales ni una auditoría manual nueva de toda la región.**

Los **nueve controles recientes de Rosario fueron detectados (9/9)**. Esto sólo mide esa muestra, no todas las publicaciones de Rosario ni las tres provincias. Ninguna omisión comercial pendiente de Cañada se resolvió mediante una carga manual simulada.

[Comparación íntegra y causas](comparacion_manual.json) · [CSV de los trece controles sin coincidencia](omisiones.csv) · [Revalidación individual de 17 EPE](epe_revalidacion.csv).

## Validación reproducible y conservación

- [Barrido real de nueve fuentes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42150027629), revisión `64f1471`; se inspeccionaron registros y documentos, no sólo la conclusión del job.
- [Prueba real Chrome de Gestiones](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42146915391): tres rutas oficiales, **69,084 s**, cero respuestas procesables. [Evidencia del fallo](navegador_gestiones.json). Workflow verde significa auditoría guardada, **no fuente recuperada**.
- [Repetición contra copia del respaldo](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42150975408): primera pasada 124 recuperaciones de línea de base, 46 datos completados, 41 modificaciones, dos primeras detecciones sin fecha y dos publicaciones nuevas confirmadas. No se suman esas categorías como nuevas comerciales. **Segunda pasada: cero novedades y cero eventos**. Las 52 fichas de Rosario se releyeron de capturas, sin red ni OCR.
- [CI de código](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42150975535): **457 pruebas Python aprobadas y 28 Node aprobadas**, sin omisiones en Actions. Localmente una prueba opcional de una dependencia está omitida.
- La repetición mantiene 6.048 registros persistentes; 6.029 identidades en vista agrupada. Las 19 agrupaciones son una vista conservada, no borrados del historial. Producción y respaldos intactos por comprobación del propio replay. [Resultado integral de repetición](repeticion_integral.json). Los 110 pendientes corresponden a la muestra; el catálogo completo aislado contiene 3.043 pendientes de presentación/revalidación y no se anuncia como revisado hoy.
- Comparación de árboles desde `546dbf9`: **34 archivos protegidos sin cambios**, incluidos producción, respaldo diario y workflows del programador/piloto. `main` permanece en `c4c44de`. No se activó ningún envío ni servicio pago.

## Qué falta

La prioridad sigue siendo **obtener contenido actual oficial de Gestiones y Boletín y revalidar EPE**. El navegador no resolvió el acceso desde GitHub. Se necesita una descarga oficial accesible o un archivo oficial nuevo que permita contrastar avisos concretos; la bandeja está preparada y probada. Persisten los 403 de Cañada/UNR y el timeout parcial del Aeropuerto. No se garantiza un mínimo diario de oportunidades ni se atribuye el saldo a bajo volumen real mientras estas fuentes no pudieron revisarse.

Las evidencias completas HTML/PDF y checkpoints quedan en los artefactos de Actions (retención de 90 días); los CSV, resultados y huellas de este directorio quedan versionados en Git.
