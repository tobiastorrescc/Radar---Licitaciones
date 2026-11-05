> Auditoría inicial al corte 01:26 ART. El estado posterior del piloto diario y la vigencia recalculada están en [INFORME.md](INFORME.md).

# Issue #10 — recuperación comprobada de convocatorias de Rosario

Corte de la evidencia oficial: **5/11/2026, 01:26 ART**. Rama `mejora/radar-auditable`, PR #1 abierto. No se modificaron `main`, los datos de producción, el respaldo diario ni el programador.

## Resultado comercial

- **25 convocatorias abiertas inéditas para el historial del piloto**, con fecha oficial de publicación entre el 2 y el 4 de noviembre. Todas corresponden a Rosario. Entre Ríos y Buenos Aires aportan avisos abiertos, pero ninguno de este lote tiene una fecha reciente comprobada que permita sumarlo a ese contador.
- La comparación con el historial persistente del 2/11 utiliza sus **4.823 registros**, además del índice de auditorías anteriores. No se inicializó una base vacía ni se borraron registros.
- **15 fichas vigentes adicionales** respecto de la extracción inicial del 5/11: cinco inéditas con publicación comprobada, tres primeras detecciones sin fecha y siete ya conocidas o modificadas. No se suman las 15 a las 25: cinco pertenecen a ambos conjuntos.
- **87 avisos con fecha vigente extraída en las capturas** de las tres jurisdicciones. El catálogo conservado calcula 145 abiertas; esa cifra incluye fechas documentales previas y registros sólo conservados por historial, y no representa 145 revalidaciones actuales.
- **20 primeras detecciones abiertas sin fecha de publicación**, en archivo separado. No cuentan como nuevas comprobadas. Las 118 primeras detecciones sin fecha de cualquier vigencia permanecen en el CSV íntegro.
- 99 modificaciones/datos completados (26 abiertos) y 175 recuperaciones históricas/de línea de base (dos aún abiertas), separadas de las publicaciones nuevas. Las dos recuperaciones abiertas no cuentan para la meta diaria.

Estas 25 publicaciones son una recuperación incremental desde la última ejecución diaria exitosa, no un promedio diario demostrado. La meta orientativa de 20/día continúa pendiente de medir en jornadas consecutivas con cobertura suficiente.

## Antes y después de Rosario

| Indicador | Extracción inicial | Corrección validada |
|---|---:|---:|
| Fichas oficiales distintas | 48 | 63 |
| Otros registros sueltos | 1 adjunto | 0 oportunidades separadas por ese adjunto |
| Avisos con publicación fechada recuperada | 1 | 48 |
| Objetos conservados del aviso oficial | Incompletos al fallar fichas | 63 |
| Fichas todavía pendientes de completar | No cuantificadas correctamente | 15 |

La corrida HTTP posterior por sí sola recuperó 63 avisos y 30 fichas con publicación; la unión y relectura de capturas oficiales del mismo día completó 48 fichas. No se atribuyen las otras 18 relecturas a nuevas consultas. Los errores del último acceso se conservan: Rosario continúa **PARCIAL**, no se declara cobertura completa.

## Causas corregidas

1. El lector de la ficha Drupal de Rosario existía, pero no participaba en el descubrimiento cotidiano. Ahora recupera número de contratación, expediente separado, objeto, publicación, apertura, presupuesto, recepción y enlaces oficiales.
2. Fichas individuales entraban en la cola de listados y desplazaban la paginación. Se separaron las colas, se recorren enlaces reales de siguiente página y se contrasta la cantidad extraída con el contador publicado por modalidad.
3. Los reintentos no reconocían `URLError` que envolvía un timeout. Ahora se reintenta de forma acotada; las fichas se consultan con hasta tres solicitudes simultáneas y los tiempos máximos siguen supervisados.
4. El número de expediente del listado podía presentarse como número de contratación. Sin ficha comprobada se conserva como identificador sin interpretar, con número de procedimiento pendiente. La identidad por ficha oficial evita otra oportunidad al corregir ese campo.
5. La falta de ficha borraba el objeto publicado en una tarjeta válida. Se conserva ese objeto y la fecha del aviso; el enriquecimiento pendiente no bloquea el descubrimiento.
6. El portal nuevo del Concejo tiene botones «Ver detalle» que no contenían el número. Ahora se siguen. Se extrajeron dos procedimientos, ambos vencidos; no se anuncian como oportunidades actuales. El portal antiguo sigue con error TLS.
7. Las tarjetas estructuradas del Ministerio de Planeamiento ER no incorporaban fechas/presupuestos, y un contenedor mezclaba avisos distintos. Se separan las tarjetas; la recepción de cotizaciones se registra como límite de presentación, no como apertura. No se exige número de procedimiento ni pliego.
8. La CI diaria fallaba antes de consultar fuentes por desajuste entre inventario/configuración y dos pruebas dependientes del día del calendario. Se sincronizó el inventario utilizado por el piloto y las pruebas fijan su fecha de referencia. El inventario habilita 86 fuentes configuradas y dos automáticas validadas; eso no acredita 88 fuentes operativas. Se incorporaron al inventario efectivo cinco rutas que ya estaban en la configuración pero el piloto no tomaba; la sexta entrada es un alias de Rosario delegado al conector principal, para no duplicar el organismo.
9. El informe comercial principal presenta novedades y cambios abiertos; eventos vencidos e inciertos permanecen en la auditoría. Los llamados especiales preceden al pago verificado, presupuesto y vencimiento; no hay filtros por rubro, monto ni financiación.
10. El contraste manual exige la misma ficha de Rosario: otra convocatoria con igual número no satisface el control. Distingue una URL encontrada con campos incompletos de una omisión real.

## Auditoría de fuentes

Se auditaron **44 URLs**, con capturas y resultados parciales persistidos: **11 operativas, 18 parciales, 10 inaccesibles, cuatro pendientes y una sin publicaciones confirmada**. Son URLs, no 44 municipios nuevos. Véase [cobertura por fuente](cobertura_fuentes.csv).

Se revisaron 39 rutas solicitadas/complementarias en el barrido ampliado. Otras cinco rutas del control inicial completan las 44 distintas. Los estados provienen de extracción efectiva; los sondeos HTTP por sí solos no validan fuentes.

- **ASSA:** tres convocatorias con fechas futuras extraídas del API oficial.
- **Aeropuerto Rosario:** cinco convocatorias abiertas recuperadas; extracción parcial por límite de tiempo.
- **Poder Judicial de Entre Ríos:** seis avisos con fechas futuras extraídas; cobertura parcial por tiempo. Los datos documentales ya conservados pueden ampliar la vista calculada y se mantienen diferenciados.
- **Ministerio de Planeamiento ER:** ocho avisos con plazo futuro, incluidos cotejos y emergencias sin número publicado; la falta de pliego no los excluye.
- **Salto:** LP 03/2026, terminación de escuela en calle Francia y J. C. Salaverry, apertura 25/11 a las 10:00. Publicación sin fecha comprobada: visible, pero no se cuenta como nueva fechada.
- **Concejo Rosario:** nuevo portal operativo, dos procedimientos vencidos. Cero oportunidades abiertas comprobadas en esa muestra.

### Accesos todavía no resueltos

| Fuente | Evidencia y estado real |
|---|---|
| EPE, rutas `app2/aperturas` con/sin `www` | Fallo TLS `UNEXPECTED_EOF_WHILE_READING` desde el runner. El diagnóstico anterior también documenta HTTP 500 en `app2/compras`. No se declara recuperada. |
| Compras Santa Fe y Gestiones de Compras | Timeout desde GitHub Actions. Se ensayaron rutas provinciales oficiales; no hay evidencia para atribuirlo a un bloqueo permanente. |
| Boletín Oficial de Santa Fe | Timeout en índice, sección de licitaciones por fecha y PDF de edición. Ramayón sigue como referencia histórica de regresión, no como oportunidad vigente recuperada. |
| Santa Fe Ciudad y Cañada de Gómez | HTTP 403. El concurso de nomencladores sigue como omisión de control: no se cargó manualmente para simular recuperación automática. |
| Compras UNR | HTTP 403; la ruta institucional de obras aporta antecedentes, sin convocatoria abierta comprobada en esta consulta. |
| Poder Judicial Santa Fe | Timeout. |
| Concejo Rosario, portal antiguo | Error de cadena de certificados TLS. No se desactivó la validación de certificados. |
| San José | Respuesta sin publicaciones reconocibles; queda pendiente, no «sin novedades». Su extracción exitosa anterior no prueba acceso actual. |
| San Lorenzo y San Pedro | Listados no reconocidos; no se declara ausencia de publicaciones. |
| Pergamino | Requiere autenticación/red institucional según la página. No se eluden restricciones. |

Casilda, Roldán, Armstrong, Sunchales, Viale, Oro Verde, Gualeguaychú, DPV ER, Victoria, San Nicolás y Ramallo conservan extracciones parciales con motivos individuales en el CSV. Las rutas no auditadas en esta etapa se identifican expresamente en el [inventario](inventario_fuentes.csv); no se cuentan como cubiertas.

## Control manual y limitaciones

La muestra actual es de **14 publicaciones oficiales**: nueve de Rosario, cuatro de Planeamiento ER y una de Salto. Las 14 se localizan; **nueve completan los campos de control y cinco quedan incompletas** por fichas de Rosario inaccesibles. No se afirma cobertura comercial completa porque el enlace del aviso aparezca.

Los ocho controles anteriores, incluidos Ramayón y el concurso de Cañada de Gómez, permanecen separados con sus fechas originales. No se presentan como revisión manual reciente. No se calculan porcentajes provinciales/globales a partir de esta muestra dirigida. La fecha de publicación sigue pendiente en los avisos ER/BA donde no está expresamente publicada; no es posible certificar un censo de los últimos siete días allí.

El archivo [comparación manual](comparacion_manual.json) identifica cada control, fuente y campo pendiente. La captura «antes» consultó diez fuentes: no se atribuye una falla de extractor a una fuente que esa captura no consultó.

## Ejemplos y entrega completa

Las **25 convocatorias** están en [CSV de nuevas confirmadas vigentes](nuevas_confirmadas_corte_0126.csv) y [listado con enlaces](nuevas_confirmadas_corte_0126.md), sin recorte:

- Rosario, Compra Ágil **88/2026**, descartables de clínica, publicación 4/11, apertura 11/11 a las 10:00: [ficha oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38714).
- Rosario, Compra Ágil **71/2026**, herramientas menores Hospital Alberdi, publicación 4/11, apertura 12/11 a las 10:00: [ficha oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38718).
- Rosario, **217/2026**, productos de pinturería Hospital Vilela, publicación 4/11, apertura 11/11: [ficha oficial](https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38724).

Las condiciones de pago de estos 25 casos continúan **pendientes de verificar**. No se inventaron anticipos, pago contado, financiación ni rentabilidad. Los pliegos se identifican por el rótulo oficial de la ficha: un enlace publicado no implica que su descarga haya sido comprobada en esta relectura.

Archivos adicionales:

- [87 avisos abiertos con fecha extraída en las capturas](abiertas_observadas.csv).
- [15 avisos de Rosario que omitió la extracción inicial](rosario_avisos_omitidos_antes.csv).
- [Primeras detecciones de fecha pendiente, de toda vigencia](primeras_detecciones_fecha_pendiente.csv).
- [Todos los eventos, cambios y antecedentes](eventos_completos.csv).
- [Cobertura del lote](cobertura_fuentes.csv), [inventario configurado](inventario_fuentes.csv) y [resultado reproducible](resultado_validacion.json).

## Validación y continuidad

- Suite: **413 pruebas ejecutadas, 412 aprobadas y una omisión opcional**. Regresiones de fichas reales de Rosario, paginación más allá de cuatro páginas, timeout envuelto, conservación del objeto cuando falla la ficha, identidad estable, avisos ER sin número y exclusión de vencidos/inciertos del informe comercial principal.
- Segunda pasada idéntica: **cero novedades, cero cambios y cero eventos emitidos**. Los registros/las versiones anteriores se conservan.
- Cero oportunidades duplicadas y cero vencidas en el CSV de 25 nuevas abiertas.
- Relectura de 48 fichas sin red ni OCR. Estado restaurado desde el respaldo diario en un directorio de trabajo independiente; integridad de producción y respaldo comprobada antes/después.
- CI de código [41969428905](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41969428905); barrido HTTP de Rosario [41967362168](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41967362168); barrido ampliado [41965803234](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41965803234); contraste y repetición final [41969428731](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/41969428731). las capturas y reportes completos están en sus artefactos por 90 días. Este informe y sus CSV quedan versionados en la rama.

El programador no se modificó. Las ejecuciones diarias del 3 y 4 de noviembre se habían detenido en pruebas previas al escaneo; la CI corregida y el piloto controlado ya pasan, pero todavía debe comprobarse la siguiente corrida diaria completa con su despacho y respaldo. No se activó correo ni se contrataron servicios.

## Siguientes acciones que aumentan descubrimiento

1. Completar las 15 fichas de Rosario pendientes, reutilizando las capturas y conservando los 63 avisos aunque falle el detalle.
2. Recuperar Boletín/Compras Santa Fe, EPE y Cañada con rutas oficiales y diagnóstico de acceso; contrastar cada aviso recuperado con Ramayón y el concurso omitido, sin altas manuales que oculten fallas.
3. Priorizar las fuentes parciales con convocatorias recientes y las localidades pequeñas no auditadas; ampliar el control manual documentado de ER y Buenos Aires.
4. Medir días consecutivos de nuevas publicaciones fechadas y abiertas. El lote actual no demuestra el promedio de 20/día ni cobertura exhaustiva de las tres provincias.
