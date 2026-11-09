# Fase 5 — resultado comprobado del 9/11/2026

**Cero compras vigentes inéditas para el radar y cero publicaciones nuevas confirmadas. La meta comercial no se alcanzó. La expansión territorial efectiva sigue pendiente; no se declara completada la Fase 5 por haber implementado sus herramientas.**

Sí se recuperó la comprobación de recepción de un procedimiento conocido de Rosario. El catálogo comercial pasa de **27 a 28 compras con recepción verificada**. La referencia de Fase 4 tenía 28 convocatorias, pero una era la venta de lotes de Ceres: al comparar compras para proveedores, la base correcta es 27. La venta se conserva separada y no se suma al comercial.

## Resultado comercial

- **Rosario, 470/2026:** servicio de limpieza para la Dirección General de Compras y Suministros, Secretaría de Hacienda y Economía. Publicación 4/11; primera detección documentada 6/11. Recepción comprobada hasta **16/11/2026, 10:00 Argentina**, modalidad presencial. Importe publicado 14.630.616,00; moneda y pago pendientes de verificar. [Aviso oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38723) · [Pliego](https://apimgw.rosario.gob.ar/licitaciones-api/v1/licitaciones/38723/documentos/102952).
- Es una **oportunidad conocida recuperada**, no una publicación inédita. Las 28 compras están completas en `comercial_completo.csv`, sin top-N, filtros por rubro o monto.
- María Teresa y Ceres ya estaban informadas en Fase 4 y **no se vuelven a contar como descubrimientos nuevos**. Se añaden dos referencias de auditoría, sin modificar SQLite de producción, respaldos ni su índice histórico original.

Fecha de la muestra: **9/11/2026 10:52:53 Argentina**. Los vencimientos y urgencias del CSV corresponden a esa observación; se deben consultar las condiciones oficiales antes de presentar una oferta. El archivo de Ceres permanece como venta municipal, fuera de las compras a proveedores.

## Antes y después medidos

| Indicador | Fase 4 comparable | Fase 5 |
|---|---:|---:|
| Fuentes configuradas efectivas | 101 | 101 |
| Fuentes configuradas consultadas | 101 | 101 |
| Operativas según resultado del lector | 47 | 46 |
| Parciales | 31 | 32 |
| Inaccesibles | 15 | 16 |
| Pendientes | 8 | 7 |
| Compras con recepción verificada, combinando observación e historial | 27 | 28 |
| Publicaciones nuevas confirmadas en esta etapa | — | 0 |
| Compras vigentes desconocidas para el catálogo anterior | — | 0 |
| Conocidas cuya recepción se recuperó | — | 1 |
| Nuevas fuentes validadas y efectivamente incorporadas al cierre | — | 0 |
| Nuevas localidades con fuente incorporada | — | 0 |
| Control Rosario | 53/53 | 53/53 |
| Aperturas de la cola pendientes de recepción comprobada | 112 | 112 |
| Novedades / eventos en segunda pasada idéntica | — | 0 / 0 |

Los estados son los resultados de cada lector, no una certificación de cobertura integral de todos los avisos de cada organismo. Las filas individuales y los errores están en `fuentes_consultadas.csv`. Hubo 126 rutas de fuentes/candidatas con identidad comprobada revisadas en total, pero sólo 101 están incorporadas: **no se suman las candidatas como fuentes operativas del catálogo**.

La extracción directa con recepción explícita pasó de 23 a 26 registros de captura. Esa métrica no es igual al catálogo comercial, que combina campos históricos ya comprobados. Los procedimientos recuperados del archivo, cambios y datos completados permanecen en auditoría; no se contabilizan como publicaciones nuevas.

## Expansión investigada, sin altas nominales

Se prepararon 45 rutas candidatas con procedencia explícita, derivadas de hosts oficiales ya registrados y búsquedas oficiales observadas. Los dos lotes hicieron **52 validaciones sobre 46 URLs distintas**. Esto incluye resultados de búsqueda que finalmente no correspondían al organismo; quedaron pendientes y no se incorporaron por tener dominio gubernamental.

Se revisaron, entre otras, raíces de Bigand, Pujato, Pavón Arriba, General Lagos, San Martín de las Escobas, Alcorta, Máximo Paz, Chabás, Arequito, Timbúes, Larroque, María Grande, General Ramírez, Ibicuy, Viale, Ramallo, Colón y Baradero. El detalle distingue identidad verificada, resultado del lector y estado del alta. No todas ofrecieron avisos reconocibles ni datos para comprobar vigencia.

Se detectaron y retiraron **tres altas provisionales sin evidencia suficiente** durante las validaciones:

1. Chabás: encabezados y nombres de archivos sin objeto comprobado; se conserva su fuente anterior y la candidata pendiente de lectura documental.
2. Raíz de Colón BA: encabezados de procedimientos, sin objeto ni recepción comprobada en la muestra. Ya se monitorea su boletín. No se presenta esta raíz como alta operativa adicional.
3. Acebal `/acebal/`: el supuesto procedimiento era el artículo histórico «Acebal, nuestro lugar en el mundo». No era una convocatoria. Se conserva el caso de regresión y la candidata en cuarentena, sin borrado de historial.

Las 101 fuentes originales siguen configuradas. La retirada afectó solamente altas provisionales de esta etapa; no se eliminaron lectores ni procedimientos históricos.

## Correcciones implementadas

- **Lector de noticias/decretos reutilizable:** reconoce solicitudes de presupuestos, cotizaciones, concursos privados, compras menores y convocatorias a proveedores. No exige monto, pago ni pliego. Acota la lectura a una ficha editorial y evita concatenar noticias distintas.
- **Navegación de menús:** una sección «Licitaciones» no se procesa como ficha individual. El fallo detenía el recorrido antes de los avisos. Hay una prueba de recorrido portada → sección → convocatoria con recepción explícita.
- **Calidad de validación:** encabezados «Licitación 01-2026.pdf / Descarga / Detalles» y «Segundo llamado» sin objeto no acreditan extracción suficiente. La identidad oficial no basta para declarar una fuente operativa.
- **Texto documental:** se conserva el texto específico de la ficha al procesar sus detalles, en lugar de reemplazarlo por el título.
- **Detección temprana:** ventanas 24, 48, 72 horas y siete días; una fecha sin hora conserva su precisión y no se transforma en una hora inventada. Se admiten convocatorias anteriores todavía vigentes.
- **Informe diario A/B/C/D:** integrado en el generador del piloto, sin cambiar el workflow diario. Separa publicaciones nuevas, primeras detecciones vigentes, conocidas recuperadas y pendientes. Ventas municipales y conocidas vigentes se informan aparte. CSV/JSON sin recorte, con publicación, primera detección, objeto, recepción, presupuesto, pago, modalidad y enlaces.
- **Alertas de plazo:** menos de 24 h, 24–48 h, 48 h–7 días y más de siete días; destaca presentación presencial. Si falta la hora, la urgencia queda pendiente de precisión. No se ocultan cierres próximos.
- **Ventas:** se conservan en el catálogo y archivo separado, pero ya no se suman al informe comercial de suministro. No se aplican filtros por rubro, monto ni pago a las compras.
- **Persistencia:** nuevas semillas y cuarentenas se reutilizan en el descubrimiento periódico existente. Se conservan registros previos, deduplicación y recibos documentales. No se modifica el programador.

No se incorporaron cálculos de rentabilidad, proveedores, servicios pagos ni OCR nuevo.

## Control de regresiones y límites

El primer barrido experimental forzó navegación de noticias sobre fuentes ya operativas y usó 45 s por fuente en lugar del presupuesto anterior de 55 s. Seis fuentes variaron respecto del control. Se realizó una prueba dirigida conservando los lectores probados y el presupuesto anterior:

- General Ramírez: 88 registros, operativa.
- Boletín General Ramírez: un registro, operativa.
- El Trébol, dos rutas: 203 y 155 registros, operativas.
- UNR Obras Públicas: 14 registros conservados; recorrido parcial por límite de 55 s.
- Rafaela: sin extracción actual por timeout de lectura. No se declara sin publicaciones.

La configuración experimental no se aplica indiscriminadamente a las fuentes del piloto: el nuevo lector de noticias es una capacidad optativa de las candidatas. El barrido de prueba vuelve a usar 55 s como presupuesto general. Se conserva el historial cuando una fuente falla; un fallo actual no acredita ausencia de convocatorias ni borra registros anteriores.

No se corrigió ninguna omisión comercial inédita demostrada en esta etapa. Sí se corrigieron el corte de navegación y falsos positivos con regresiones, y se conservó el control 53/53 de Rosario. No se atribuye el resultado cero a falta de publicaciones: **persisten cobertura incompleta, problemas documentales y fuentes inaccesibles**.

## Fuentes críticas y revalidación

- **EPE:** fallos de conexión/TLS en Linux; cero procedimientos actuales recuperados. No se desactivan certificados.
- **Gestiones SF y Boletín SF:** timeouts; las fuentes siguen inaccesibles, con importación oficial CSV/HTML/PDF disponible. El lector web también rechazó el acceso a las ediciones oficiales del 5 y 6 de noviembre. Los avisos de buscadores o agregadores no se aceptaron como sustituto de verificación oficial.
- Se preparó un contraste con curl nativo desde macOS estándar de Actions para repositorio público. **El job quedó en cola sin recibir runner y se canceló antes de consultar fuentes**. No se contabiliza como alternativa probada, recuperación ni error de los portales. El cierre comercial quedó desacoplado de esa dependencia.
- La revalidación secundaria tuvo **60,007 s de presupuesto independiente**, revisó 14 de las 112 aperturas y no obtuvo ninguna recepción vigente comprobada adicional. Un worker que terminó operativo no se confundió con vigencia comercial. Se conservan las 112 en CSV; los resultados parciales y errores de los 14 intentos se entregan por separado.

## Cobertura territorial

`cobertura_territorial.csv` enumera **365 localidades identificadas de Santa Fe, 239 de Entre Ríos y 51 candidatas de Buenos Aires** del padrón existente. Distingue identificación, URL localizada, validación, incorporación y revisión efectiva. Incluye rutas candidatas con identidad comprobada, sin confundirlas con fuentes ya incorporadas.

En esta muestra figuran rutas revisadas para 35 localidades santafesinas, 27 entrerrianas y 13 bonaerenses. **No acredita cobertura exhaustiva**. Las 51 bonaerenses son un inventario preliminar: las distancias viales pendientes están indicadas y no autorizan nuevas altas automáticas fuera del alcance verificado. Cuando el padrón no contiene departamento/partido, se deja pendiente en lugar de inventarlo. Sigue pendiente completar esa asignación territorial y localizar fuentes de numerosas comunas de la lista prioritaria.

## Evidencia reproducible

- [Barrido real de 101 fuentes y primer descubrimiento](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42625654538).
- [Segundo lote y prueba de navegación](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42627183451).
- [Contraste dirigido de seis fuentes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42629154257).
- [Revalidación secundaria; macOS no llegó a ejecutarse](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42628480358). La cancelación afecta exclusivamente a este ensayo aislado, no al piloto.
- [Cierre final nativo y segunda pasada](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42629899171): **correcto**, 503 pruebas Python ejecutadas (una omitida), 28 Node aprobadas, cero novedades y cero eventos repetidos. El artefacto `fase5-comparacion-42629899171` fue descargado y contrastado.

El descubrimiento de las dos rondas consumió 203,08 s y 72,15 s, respectivamente, separado del barrido de las 101 fuentes. El cierre reutilizó capturas, sin red documental ni OCR. La copia aislada reconstruye Fase 4 antes de comparar, por lo que no vuelve a anunciar María Teresa ni Ceres como hallazgos de Fase 5.

Los informes completos A/B/C/D están en el artefacto del cierre. En la próxima corrida del piloto, se generan bajo `descubrimiento/informe.md` y sus CSV/JSON dentro del artefacto de resultados. No se activó correo.

## Entrega y continuidad

- `comercial_completo.csv`: 28 compras vigentes verificadas.
- `nuevas_compras_vigentes.csv` y `nuevas_verificadas.json`: cero, sin rellenar con históricos o conocidas.
- `conocidas_recuperadas.csv`: Rosario 470/2026.
- `ventas_municipales.csv`: separado del comercial.
- `fuentes_consultadas.csv`, `candidatas_consultadas.csv`, `fuentes_nuevas.json`: estados y resultados reales.
- `cobertura_territorial.csv` y resumen: localidades revisadas y pendientes.
- `pendientes_revalidacion_112.csv`, `revalidacion_intentos.csv` y resumen: cola conservada y prueba secundaria.
- `resultado.json`, `control_rosario.json` y `proteccion.json`: métricas, repetición e integridad.

Los CSV del repositorio contienen los datos comerciales y enlaces oficiales; se omiten datos bancarios ajenos al objeto. La evidencia íntegra permanece en los documentos oficiales y las capturas de la auditoría.

**Pendiente prioritario:** recuperar un canal oficial accesible de compras/boletín provincial o importar sus archivos actuales; completar la lectura de adjuntos e índices identificados en comunas; ampliar el inventario con evidencia por localidad, comenzando por las que carecen de fuente. Esta etapa no demuestra un incremento de compras inéditas: ése sigue siendo el criterio de éxito pendiente.

Verificación del árbol GitHub: **78 archivos de producción, respaldos, informes del piloto, despliegue y workflows preexistentes sin cambios**. Main continúa en `c4c44de`. Los cambios del generador de informes y lectores quedan sólo en la rama del PR. No se fusiona ni se activa producción.
