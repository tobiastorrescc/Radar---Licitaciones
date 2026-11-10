# Fase 7 — Rosario, dos niveles de descubrimiento y barrido territorial

Base: `98bfebd`. Rama `mejora/radar-auditable`, PR #1. Corte comercial: **09/11/2026 22:39 Argentina**; último contraste de Rosario 22:43. Los informes se publican el 10/11 UTC. No se afirma vigencia posterior al corte sin nueva consulta.

**Resultados: dos fuentes nuevas con extracción HTML comprobada, dos oportunidades conocidas con recepción revalidada documentalmente, cero compras inéditas vigentes.** Se ejecutó la exploración rápida sobre 51 sitios; 46 devolvieron HTML. Hay avances verificables, pero no se declara cobertura territorial exhaustiva ni Rosario libre de incidencias.

## 1. Rosario: aviso faltante y evidencia real

La referencia omitida era la [ficha 38659](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38659): **Compra Ágil 63/2026**, expediente **40631/2026**, extintores para el Hospital Carrasco. El listado de referencia exponía el expediente como `40631/2026`; la ficha publica el número de contratación `63/2026`.

La ficha oficial se recuperó realmente desde Actions y muestra **“Abierta en Evaluación”**, apertura **09/11/2026 11:00**, publicación **29/10/2026** y presupuesto **$1.335.000**. Dejó de aparecer en el listado de próximas aperturas. Esto documenta un cambio de estado de la fuente; no corresponde reconstruir el aviso ni presentarlo como compra vigente.

El lector anterior agotaba 240,015 segundos mezclando listados, fichas y documentos. Ahora, en modo de descubrimiento, se registran primero los avisos y se conserva una cola de fichas pendientes de enriquecimiento. El modo de lectura completa sigue disponible. El tiempo por fuente explícito de 240 segundos explicaba por qué un parámetro general menor no tenía efecto; no se aumentó el timeout global.

| Ejecución real | Referencias del control | Tiempo | Alcance y limitación |
|---|---:|---:|---|
| [42731776470](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42731776470) | 53/53 | 22,741 s | 52 por listados y la ficha faltante por contraste; tres fallas de paginación |
| [42733779176](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42733779176) | 53/53 | 22,626 s | Persisten incidencias de acceso |
| [42735422650](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42735422650) | 53/53 | 36,733 s | Reintentos acotados; recorrido parcial |
| [42737102388](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42737102388) | 52/53 | 28,487 s | Falló el acceso a la ficha del contraste en esa corrida |
| [42737639135](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42737639135) | **53/53** | **26,927 s** | 65 referencias totales; queda una ruta mensual con timeout |

La última ruta fallida fue el listado mensual de noviembre con `verTipo=5`. **El control histórico de 53 referencias quedó contrastado, pero el recorrido global de Rosario sigue parcial.** No se equipara Actions en verde con cobertura completa. Hay una regresión reproducible con capturas reales de las 53 referencias y una prueba específica que impide comercializar la ficha 38659 en evaluación.

La comparación de 240 frente a 26,9 segundos corresponde a etapas diferentes: se separó enriquecimiento del descubrimiento. No se presenta como mejora del procesamiento documental completo ni garantía de respuesta futura.

## 2. Barrido territorial realmente ejecutado

- **67 localidades programadas** entre el lote inicial y la continuación.
- **51 sitios institucionales intentados**: 47 en el primer barrido y cuatro adicionales.
- **46 localidades con HTML obtenido y leído**. Cinco sitios no entregaron contenido suficiente.
- **27 identidades verificadas automáticamente**. El resto conserva revisión pendiente de identidad, acceso o contrataciones.
- **16 localidades sin URL institucional comprobada**: no se cuentan como exploración efectiva.
- Tiempo del nivel rápido: **40,911 + 5,837 = 46,748 segundos**. No se incluye aquí la búsqueda asistida ni la validación profunda.

No se afirma haber completado 50 auditorías profundas: se superaron 50 intentos reales, pero sólo 46 devolvieron HTML. Consultar [cobertura_lote.csv](cobertura_lote.csv) y [localidades_sin_revision_efectiva.csv](localidades_sin_revision_efectiva.csv).

El inventario completo conserva 655 localidades identificadas; eso no certifica un padrón vigente ni cobertura completa de sus departamentos. Las distancias geodésicas de Buenos Aires no sustituyen la distancia vial. Ninguna fuente bonaerense dudosa se incorporó automáticamente.

## 3. Dos niveles, prioridades y continuidad

`descubrimiento_rapido.py` consulta hasta tres páginas por localidad: identidad, secciones y señales recientes. No descarga PDF ni ejecuta OCR. Guarda cada resultado al terminar; una falla individual no interrumpe el lote.

La puntuación es reproducible: identidad verificada (4), sección de compras (4), publicación estructurada de los últimos siete días (3), evidencia de convocatorias (2), acceso (1) y documentos publicados (1). Se conservan las razones y los datos desconocidos. **Un dato ausente no resta puntos.** La distancia geodésica sirve para ordenar empates, sin certificar logística vial. La frecuencia histórica completa todavía no está medida: sólo se usa evidencia observada de convocatorias.

Los documentos, fichas y archivos anuales se reservan al nivel profundo. Se corrigió un error del selector que podía escoger un PDF individual como portal: ahora prefiere índices reutilizables y evita entradas sin objeto concreto. En documentos con fecha en la ruta se priorizan los recientes sin descartar permanentemente los restantes.

La integración con el descubridor periódico usa `inventario/fase7_config.json` y conserva sus resultados en el estado existente. El programador y su cron no se modifican. En la prueba real [42737639135](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42737639135), el nivel rápido examinó dos candidatas en **6,147 segundos** y rechazó promocionarlas sin identidad suficiente. No se las declaró sin compras. Una primera ejecución de integración falló al registrar una fuente sectorial sin localidad; se corrigió y se agregó regresión.

El estado del piloto está en `inventario/fase7_estado.json`. Los resultados recientes se reutilizan hasta 24 horas, con intentos y reutilizaciones separados. La segunda pasada sobre dos resultados reales hizo **cero solicitudes HTTP**: [cache_repeticion.json](cache_repeticion.json).

## 4. Fuentes nuevas incorporadas

| Organismo | URL oficial de monitoreo | Extracción de validación | Consulta desde el catálogo |
|---|---|---|---|
| Municipalidad de Villa Cañás, Santa Fe | https://www.muvc.gob.ar/licitaciones.php | OPERATIVA, 27 referencias HTML, 2,174 s | OPERATIVA, 27 referencias |
| Municipalidad de Hasenkamp, Entre Ríos | https://www.hasenkamp.gob.ar/licitaciones/ | OPERATIVA, 33 referencias HTML, 4,997 s | OPERATIVA, 33 referencias |

Quedaron en `inventario/fuentes_auto.json` y el cargador del radar devuelve **105 fuentes**. La extracción HTML no depende de poder leer anexos escaneados. **Los 60 avisos/referencias no son 60 compras activas ni publicaciones nuevas.** La recepción pendiente permanece fuera del informe comercial. No se afirma cobertura integral de todas las modalidades del organismo.

Validación real: [42737102388](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42737102388). Esa ejecución conservó las altas y los resultados, aunque el paso posterior del descubridor periódico falló; su reparación se comprobó en la ejecución siguiente. La evidencia completa contiene todas las referencias; los ejemplos de validación guardados en la configuración son sólo una muestra y no recortan las oportunidades.

[fuentes_nuevas.json](fuentes_nuevas.json) conserva método, identidad y evidencia. [rendimiento_fuentes.csv](rendimiento_fuentes.csv) registra tiempos, páginas, reintentos observados, timeouts, documentos con texto y PDF sin texto. Una página HTTP 200 sin extracción no se promociona.

## 5. Siete localidades incompletas

| Localidad | Resultado comprobado | Pendiente |
|---|---|---|
| Hughes | Lectura del grid JSON publicado en el HTML del delegado Siglo Servicios; diez filas estructuradas en la captura | Fuente parcial: paginación y vigencia sin comprobar; contiene antecedentes, no diez compras actuales |
| San Guillermo | Se conservaron 39 referencias durante la consulta acotada | Documentos externos y plazo agotado; no asumir recepción vigente |
| Totoras | Sitio institucional y páginas oficiales accesibles | No se localizó extracción útil de convocatorias; no “sin compras” |
| Franck | Cuatro referencias conservadas | Documentación/recorrido parcial; los ejemplos contrastados están cerrados |
| Malabrigo | Cuatro referencias en la pasada de 35 segundos | No se verificó completitud; no se borran las capturas anteriores |
| Valle María | 47 referencias preservadas | Archivo/documentos parciales; separar arrendamientos y procesos cerrados |
| San José de la Esquina | 21 referencias conservadas | Archivo extenso y timeout; no se considera fuente completamente recuperada |

Hughes enlaza al delegado desde su [sección oficial de concursos](https://hughes.gob.ar/transparencia/compras-y-contrataciones/concurso-de-precios). Se implementó lectura del dato ya entregado por el servidor, sin login, evasión ni OCR. No se inventó un endpoint. El grid de diez filas no acredita paginación completa.

EPE, Gestiones Santa Fe y Boletín Santa Fe permanecen separados: fallos TLS/timeout documentados, importadores CSV/HTML/PDF conservados. No se gastó este lote repitiendo los mismos accesos fallidos ni se los declaró recuperados.

## 6. Resultado comercial, sin falsas novedades

**A. Publicaciones nuevas y vigentes: 0.**

**B. Oportunidades vigentes desconocidas: 0.**

**C. Conocidas recuperadas: 2**, ambas de San Salvador. Ya estaban registradas en las capturas de Fase 5; ahora se comprobó la recepción mediante lectura visual de sus pliegos enlazados. La extracción automática recuperó número, objeto, fecha y presupuesto; la lectura de esos PDF escaneados no se presenta como automática.

| Procedimiento | Objeto | Presupuesto | Recepción comprobada | Pago documental |
|---|---|---:|---|---|
| [Licitación privada 8/2026](https://sansalvadorer.gob.ar/llamado-a-licitacion-privada-n-08-2026/) | Materiales de construcción para bacheo y reparación de calles pavimentadas | $26.684.000 | **10/11/2026 11:00, Argentina**; generales art. 9, PDF p. 3 | **15 días hábiles** desde factura presentada y remitos conformados; no pago inmediato contra entrega |
| [Concurso de precios 29/2026](https://sansalvadorer.gob.ar/llamado-a-concurso-de-precios-n-29-2026/) | **200 cargas de gas envasado en garrafas de 10 kg** para ayuda directa | $5.000.000 | **11/11/2026 11:00, Argentina**; generales art. 8, PDF p. 2 | Cláusulas contradictorias: art. 4 prevé 30 días desde adjudicación; art. 8 dice contra entrega y remite al decreto. Pendiente de aclaración |

Ambos pliegos admiten presentación personal y vía fax/email, con original o ratificación posterior dentro de dos días hábiles; verificar adquisición de pliego, garantías y demás requisitos antes de ofertar. Los contactos y documentos están en las publicaciones oficiales. No se enviaron ofertas ni mensajes.

Se corrigió la extracción de noticias: el objeto deja de ser sólo “Llamado a concurso”; se recupera el párrafo de compra, `datePublished` y el enlace de Drive efectivamente publicado. No se confunde `dateModified` ni el año del pie de página con publicación.

[comercial_completo.csv](comercial_completo.csv) incluye las dos fichas y distingue pago manual de pago automático pendiente. [control_documental_manual.csv](control_documental_manual.csv) identifica documento, hash, página y artículo. No se descargaron nuevamente ni se hizo OCR sobre esos documentos; se revisaron páginas seleccionadas visualmente. No se publican pliegos íntegros ni datos bancarios.

**D. Pendientes de la muestra: 163 referencias**, separadas en [pendientes_muestra.csv](pendientes_muestra.csv). Incluyen antecedentes y datos insuficientes, no 163 negocios vigentes. Los objetos extensos tienen un resumen expresamente rotulado y enlace al original; no hay límite de filas ni filtro por rubro o monto.

La cola previa de 112 aperturas conserva su archivo original: dos casos quedaron documentalmente resueltos al corte y [110 siguen pendientes](revalidacion_110_pendientes.csv). El overlay persistente `inventario/fase7_revalidacion_resultado.json` no altera respaldos ni presupone vigencia de los demás casos.

No se alcanzó la meta comercial de 10–20 compras inéditas. **No se atribuye el cero al volumen real de publicaciones**, porque la cobertura y la documentación siguen incompletas.

## 7. Rendimiento, idempotencia y métricas

En cuatro sitios idénticos se compararon consultas secuenciales y concurrentes sin compartir caché: **9,711 → 5,465 segundos**, con los mismos enlaces observados y estados. Límite por dominio: una solicitud; concurrencia global: cuatro. La prueba no acredita ausencia de omisiones en otras localidades. [benchmark.json](benchmark.json).

La primera ejecución territorial completa de prueba duró **237,076 segundos**, incluyendo las siete reparaciones, nivel rápido, diez validaciones profundas, registro y benchmark. Las continuaciones fueron dirigidas, sin repetir el lote. Los plazos por fuente se mantuvieron en 35–55 segundos y por procesos separados; un portal fallido no detuvo los demás.

| Indicador | Antes | Después comprobado |
|---|---:|---|
| Fuentes configuradas | 103 | **105** |
| Control Rosario | 52/53 | **53 referencias contrastadas**, con cambio oficial de estado; recorrido global todavía parcial |
| Localidades sin extracción operativa comprobada en el inventario | 619 | **617** |
| Compras verificadas en el catálogo global | 28 | No se hizo nuevo censo global; dos conocidas fueron revalidadas documentalmente |
| Compras inéditas vigentes | 0 | **0** |
| Localidades con sitio intentado en esta fase | 0 | **51** |
| Localidades con HTML leído | 0 | **46** |
| Fuentes nuevas operativas de descubrimiento HTML | 0 | **2** |
| Duplicados comerciales publicados | 0 | **0** |
| Cola previa pendiente de revalidación | 112 | **110** en el informe al corte; original intacto |

La copia restauró **6.771 registros** del respaldo. Se contrastaron además las capturas accesibles de Fase 5; 17 coincidencias evitaron falsas novedades. Se procesaron 253 registros únicos de la muestra. La segunda pasada dejó **cero novedades y cero eventos**. Las 43 primeras detecciones sin fecha suficiente, 188 recuperaciones de línea de base y ocho modificaciones de la primera pasada **no se cuentan como compras nuevas**. [resultado.json](resultado.json).

## 8. Pruebas, límites y conservación

- **515 pruebas Python, una omitida; 28 Node**, aprobadas en Actions. Regresiones con capturas reales: Rosario 53 referencias, ficha en evaluación, grid de Hughes, selección de índice frente a PDF, objeto/publicación/Drive de San Salvador y organismo sin localidad.
- [42737639135](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42737639135): integración periódica reparada, pruebas y auditoría real. El CI del programador también terminó correctamente; no se alteró ni se despachó producción como prueba.
- Integridad por SHA de los **83 archivos requeridos**, además de los workflows preexistentes; main y los respaldos permanecen sin cambios. Ver `proteccion.json`.
- Capturas completas/checkpoints permanecen en artefactos con retención de 90 días; inventario, altas, CSV, hashes y resultados resumidos quedan persistidos en el PR.
- La revisión automática rechazó una captura HTML íntegra por contener una clave del sitio. La prueba publicada utiliza sólo el fragmento de artículo necesario, sin scripts ni claves.

Próxima prioridad: resolver la ruta mensual de Rosario; verificar las 21 localidades sin revisión efectiva de este lote, incluida búsqueda institucional donde falta URL; validar dominios delegados de comunas; completar vigencia de avisos HTML y documentos escaneados sin OCR masivo. Después continuar con el siguiente lote de localidades no revisadas. El inventario y los checkpoints conservan el punto de continuación.

No se declara concluida la cobertura exhaustiva ni alcanzado el objetivo comercial de descubrimientos inéditos. PR #1 abierto, sin merge; sin cambios en main, producción, respaldos o programador.

## Reproducción

Los artefactos `fase7-<run>` de 42733779176, 42735422650 y 42737102388 contienen respectivamente el lote, la continuación y las validaciones de índices HTML. Se extraen bajo `work/fase7/territorial-native`, `work/fase7/continuacion-native` y `work/fase7/validacion-native`. El artefacto de 42737639135 conserva la integración periódica corregida y el último contraste de Rosario. Las capturas de referencia Fase 5 siguen accesibles mediante el flujo `fase5-cierre.yml` y sus ejecuciones originales. `tools/fase7_informe.py` documenta la comparación contra esa referencia y una copia restaurada; rechaza una segunda pasada con eventos duplicados. No se debe ejecutar sobre archivos de producción ni sustituir una captura fallida por datos inventados.
