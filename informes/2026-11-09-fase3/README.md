# Fase 3 — recepción verificable y cobertura efectiva

La auditoría parte de `e889b72` y del último respaldo automático `ce79e45` del 8/11. Las consultas se realizaron el **9/11 UTC / noche del 8/11 en Argentina**; este cierre no se presenta como la ejecución diaria del lunes 9/11 a las 08:00.

## Resultado comercial

**7 recepciones vigentes recuperadas de las 119 pendientes; 112 continúan inciertas.** El listado comercial pasa de **19 a 26**. **Cero publicaciones nuevas y vigentes confirmadas** respecto del último respaldo: las siete son recuperaciones, no novedades inéditas.

| Métrica | Antes del enriquecimiento | Después |
|---|---:|---:|
| Fuentes configuradas y consultadas | 93 | 94 |
| Operativas, incluida la confirmada sin publicaciones | 42 | 42 |
| Parciales | 29 | 30 |
| Inaccesibles | 15 | 15 |
| Pendientes de reconocimiento | 7 | 7 |
| Recepciones vigentes comprobadas | 19 | 26 |
| De las 119: recepción comprobada | 0 | 7 |
| De las 119: inciertas | 119 | 112 |
| Publicaciones nuevas y vigentes | — | 0 |

La métrica anterior de fuentes se rectificó desde `antes.json`, guardado antes del alta: una lista compartida incluía Santa Ana también en el resumen antes. Se conserva [el resumen original de Actions](resultado_original_actions.json) y la huella del archivo usado en [resultado.json](resultado.json). La corrección no cambia los 19/26 resultados comerciales ni los controles de deduplicación.

Las recuperaciones son avisos ya conocidos cuya recepción pudo comprobarse, **no publicaciones nuevas del día**. El catálogo conserva todas las observaciones e históricos; el CSV comercial contiene exclusivamente recepción vigente comprobada, sin filtros por rubro, monto, financiación o forma de pago. Las fechas y las condiciones no publicadas siguen pendientes.

## Qué cambió

- Revisión individual de las 119 pendientes, ordenadas por apertura, con identificación inequívoca del procedimiento, descarga oficial de ficha y hasta cuatro documentos por pasada. Los documentos que exceden ese presupuesto quedan pendientes explícitos; no se recorta el número de oportunidades.
- Caché por URL y hash dentro de la auditoría; una descarga compartida de boletín se reutiliza. Las correcciones se verificaron releyendo las capturas existentes sin red y sin OCR.
- El lector diario de Rosario reconoce recepción «hasta el momento de la apertura», además de la fórmula anterior. Regresión real: ficha 38717, Compra Ágil 467/2026. El domicilio de recepción y la apertura aislados siguen sin acreditar cierre.
- Las condiciones de recepción y pago del Boletín de Entre Ríos se extraen **sólo del aviso segmentado por ID editorial**. El PDF colectivo no se vuelve a tratar como pliego individual. Se agregó una regresión que impide heredar la recepción de El Palenque en el llamado judicial publicado en la misma edición.
- Se preservan organismo y jurisdicción cuando la ficha no los repite; un valor vacío no puede crear una oportunidad nueva con organismo desconocido. La segunda pasada comprueba ausencia de eventos duplicados.
- Santa Ana ER: adaptador de avisos intercalados con `<br>`, objeto, apertura y enlaces separados. Extracción nativa de 33 referencias en 1,716 s; seis avisos 2026 con fechas explícitas, todos vencidos. No se descargó su archivo histórico para lograr esa mejora. Nueva fuente **parcial**, no nueva fuente completamente operativa.

## Fuentes críticas y respaldo manual

EPE devolvió HTTP 500. Gestiones SF y el HTML directo del último día hábil del Boletín SF agotaron el tiempo. Tres pruebas complementarias acotadas tardaron 9,228 s en total; no se repitieron indefinidamente ni se desactivó TLS. El barrido completo conserva además sus errores por cada ruta oficial. Ninguna de las tres se declara recuperada ni «sin novedades».

No se obtuvo una URL de exportación CSV comprobada porque la interfaz de Gestiones fue inaccesible. No se inventó endpoint. El archivo de referencia del usuario no está adjunto: no se atribuyen sus 114/99 filas a una extracción real de esta etapa.

El importador reutilizado valida fuente, dominio, hash, fecha y recibo de procedencia. Un archivo manual sin recibo verificable se integra como **pendiente de revalidación**, no como recepción activa automática. Se probó la bandeja existente con la captura EPE anterior: no es una descarga actual ni revalida los 17 controles EPE.

```bash
python tools/importar_oficiales.py --fuente fuente-087 --url 'https://www.santafe.gob.ar/gestionesdecompras/site/index.php' --archivo /ruta/aperturas.csv --capturado-en '2026-11-09T08:00:00-03:00' --bandeja work/entrada-manual
python tools/importar_oficiales.py --bandeja work/entrada-manual --salida work/importados-control
```

La fecha del ejemplo debe sustituirse por la fecha real de obtención, con zona horaria; no se debe reutilizar literalmente para otro archivo. Para el Boletín, usar `fuente-060`, URL exacta de edición oficial y PDF/HTML completo. Para EPE, `fuente-003` y URL oficial correspondiente. Conservar archivo y manifiesto JSON; al aportarlos a `entradas_oficiales/` en esta rama, el importador existente del piloto los compara con el mismo historial. No sobrescribir archivos con otra huella ni editar los respaldos.

## Muestra manual, expansión y limitaciones

Se auditaron las 93 fuentes existentes y 15 rutas candidatas (13 del inventario anterior y Santa Ana/Fighiera). No equivalen a 108 organismos distintos: hay portales complementarios y alias. Una candidata se incorporó como fuente parcial; no hubo altas nuevas plenamente operativas.

El control fijo de Rosario recuperó **53/53 URLs**. Esto acredita descubrimiento en esa muestra, no recepción vigente de las 53. La comparación de las 119 detectó siete omisiones de información de recepción, ahora corregidas; los 112 casos restantes no se anuncian como oportunidades activas.

El porcentaje o conteo de Rosario corresponde exclusivamente a la muestra oficial fija de 53 avisos del 7/11, no a toda la provincia. Las nuevas rutas candidatas fueron consultadas individualmente: UTN Paraná, UADER, Campana, Chacabuco, Ramallo, Capitán Sarmiento/SIBOM, General Arenales, UEP y San Nicolás. Chacabuco aportó antecedentes, sin vigentes verificadas; no se declara nueva cobertura comercial. Fighiera respondió, pero no se extrajeron convocatorias y una sección normativa mostró contenido ajeno al organismo en la consulta manual: queda pendiente de revisión, sin alta confiable.

Las restricciones TLS/timeouts, fuentes con 403, PDF sin texto nativo, tamaño documental y procedimientos ambiguos están registrados por caso. No se resolvieron por inferencia ni OCR adicional. La cobertura territorial sigue incompleta, especialmente comunas pequeñas de Santa Fe y convocatorias bonaerenses cercanas; no se interpreta ausencia de resultados como ausencia de contrataciones.

## Pruebas, continuidad y protección

- [Barrido real de las 93 fuentes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42543122865).
- [Consulta real de las 119 pendientes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42543677143).
- [Fuentes críticas y primeras candidatas](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42543506680): esas dos tareas terminaron correctamente; el primer trabajo de revalidación falló por un esquema de errores y fue corregido y repetido en la ejecución anterior.
- [Santa Ana: lectura mejorada comprobada](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42544649973).
- [Cierre final con segmentación y dos pasadas](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42545489002). Segunda pasada: **0 novedades, 0 eventos**. Artefacto `fase3-cierre-42545489002`, disponible 90 días; evidencia resumida persistida aquí.
- Python: **476 pruebas ejecutadas, 1 omitida opcional**; Node: **28 aprobadas**. No se instaló ni ejecutó OCR nuevo.
- Comparación de árboles GitHub: **69 archivos protegidos sin cambios** respecto de `ce79e45`; `main` permanece en `c4c44de`.

Los 4 lotes de 93 fuentes se ejecutaron con hasta dos jobs simultáneos, cuatro procesos por lote y límites existentes por fuente. La revalidación usa cuatro procesos, 36 segundos por caso y 650 segundos totales; conserva checkpoints. La relectura final de las descargas no consultó los portales. Los tres accesos críticos complementarios sumaron 9,228 segundos. Los cuatro lotes insumieron 240,078; 110,190; 203,300 y 129,020 segundos de consulta; no se suman como tiempo de pared porque se ejecutaron por pares. Los tiempos de las filas de revalidación corresponden a la relectura final sin red (12,797 s en total); los tiempos HTTP originales se conservan dentro de las evidencias de cada caso. No se presentan esos 12,797 s como duración del acceso en vivo.

Se conservó intacto el último commit automático del piloto. El programador y los workflows diarios existentes no se editaron. Los workflows de Fase 3 se ejecutan únicamente por cambios de sus planes en la rama de mejoras; no tienen cron, no escriben respaldos y usan permisos de lectura. No se activa correo ni servicios pagos.

## Archivos

- [Todas las oportunidades comerciales verificadas](informe_comercial.csv), [versión legible](informe_comercial.md).
- [Revisión de los 119 casos](revalidacion_119.csv), [resueltos](119_resueltas.csv), [inciertos](119_pendientes.csv).
- [Recepciones vigentes recuperadas](recuperadas-vigentes.json), [publicaciones nuevas y vigentes](nuevas-vigentes.json).
- [Auditoría de fuentes](fuentes_consultadas.csv), [contraste manual](contraste_manual.json).
- [Métricas](resultado.json), [segunda pasada e integridad](continuidad.json), [rutas críticas](rutas_criticas.json), [importaciones](importaciones_oficiales.json).

Prioridad siguiente: resolver las incertidumbres mediante documentos actuales accesibles o archivos oficiales aportados; corregir las fuentes con omisiones reales de recepción y ampliar comunas/municipios con evidencia. No se considera alcanzada la meta diaria por contar recuperaciones o antecedentes.

### Recepciones recuperadas: ejemplos

| Organismo / procedimiento | Objeto | Cierre comprobado (Argentina) | Pago |
|---|---|---|---|
| [Rosario 467/2026](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38717) | Servicio de impresiones para Igualdad, Género y DDHH | 10/11/2026 09:00 | Pendiente de verificar |
| [Rosario 469/2026](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38721) | Accesorios para pintura para Obras Públicas / Arquitectura | 11/11/2026 11:00 | Pendiente de verificar |
| [El Palenque 8/2026](https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Noviembre/06-11-26.pdf) | Inmueble urbano para sala de velatorios | 20/11/2026 10:59 | Pendiente de verificar |

Las siete recuperadas mantienen pago pendiente. Entre las 26 comerciales, el Cotejo 2539 de Viale conserva pago contado documentado; ya era conocido y no se atribuye como hallazgo nuevo.
