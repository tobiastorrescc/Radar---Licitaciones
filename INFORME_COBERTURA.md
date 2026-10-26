# Cobertura del radar — etapa 1

Observación: 2026-10-25T21:14:16.261623-03:00. Rama `mejora/radar-auditable`, PR #1. Sin fusión.

- Organismos con portal localizado: **50**.
- Portales inventariados: **53**. Un organismo puede tener varios listados.
- Fuentes incorporadas a configuración: **36**, de las cuales 35 se agregan a Rosario.
- Verificadas funcionando mediante conector: **0**.
- Bloqueadas al ejecutar: **36**; todas fallaron antes de obtener contenido. No se detectaron publicaciones en esta ejecución.
- Otras fuentes: **17** sin incorporar: 16 pendientes de adaptar o completar y 1 restringida en origen (Concordia).
- Sin publicaciones nuevas: **0 comprobadas**. Un error, un listado vacío o una página JavaScript no demuestra ausencia de novedades.

| Provincia | Portales | Configuradas | Funcionando comprobadas |
|---|---:|---:|---:|
| Santa Fe | 22 | 13 | 0 |
| Entre Ríos | 23 | 17 | 0 |
| Buenos Aires | 8 | 6 | 0 |

## Evidencia y límites reales

La búsqueda y lectura web separada permitió localizar direcciones oficiales y observar publicaciones, por ejemplo en CAFESG y Aeropuerto Rosario. Esto verifica la existencia de contenido, pero no prueba que el conector pueda descargarlo y extraerlo desde el executor. No se importaron estos hallazgos manuales como novedades del radar.

El executor informa red restringida con Rosario como único destino público adicional. `curl` hacia Rosario y CAFESG falló al conectar con el proxy en el puerto 8080; las 36 consultas Python devolvieron URLError con Operation not permitted. No se deshabilitó el proxy ni TLS. El fallo local no demuestra que los portales estén caídos. `inventario/verificacion.json` conserva cada URL y error observado.

ASSA y contrataciones provinciales de Entre Ríos requieren JavaScript; Colón usa iframes; Concordia declara red municipal o VPN; Armstrong devolvió 403 en lectura web. Estos casos requieren otra ruta pública comprobada o un adaptador específico. Federación y Rosario del Tala muestran publicaciones históricas: no se considera que carezcan de nuevas.

## Trabajo implementado

Conectores HTML de enlaces numerados, filas y bloques con descargas; paginación por rel=next, números en query y rutas /page/; PDF con extracción real mediante pdftotext. Los PDF escaneados sin texto quedan pendientes de OCR. Los límites de recorrido y los errores se informan, nunca se ocultan como éxito.

Historial atómico preservado, identidad por fuente, URL y procedimiento/llamado/estado; detección de cambios de llamado en la misma URL, auditorías persistentes y última detección. No hay deduplicación semántica garantizada entre portales o documentos con URLs distintas. Debe resolverse conservando evidencia para evitar descartar procesos diferentes con igual número.

Todas las novedades detectadas se informan sin límite y sin filtrar por rubro, monto ni financiación. Orden comercial orientativo por evidencia de pago y llamados especiales; no se estima rentabilidad sin costos. Una publicación detectada puede estar adjudicada, desierta o cerrada: se conserva su situación publicada y no se presenta como oferta abierta confirmada.

26 pruebas automáticas aprobadas en Python 3.12: incluye las 8 anteriores, PDF real generado de prueba, tablas con Descargar, paginación y ciclos, JavaScript vacío, bloqueo, extracción parcial, 500 novedades sin límite y dos ejecuciones con historial. Las muestras son sintéticas: no sustituyen fixtures reales de cada portal. Workflow diario y horario 08:00 Argentina se conservan; se instala poppler-utils para leer PDF. Los cambios del PR no se activan en main hasta la fusión.

## Fuentes

| Organismo / localidad | Provincia | Tipo | Configurada | Estado observado | URL |
|---|---|---|---|---|---|
| Municipalidad de Rosario / Rosario | Santa Fe | html | Sí | BLOQUEADA | [Portal](https://www.rosario.gob.ar/inicio/compras-y-licitaciones) |
| Gobierno de Santa Fe / Santa Fe | Santa Fe | tabla | Sí | BLOQUEADA | [Portal](https://compras.santafe.gob.ar/) |
| EPE / Santa Fe | Santa Fe | tabla | Sí | BLOQUEADA | [Portal](https://www.epe.santafe.gov.ar/app2/aperturas) |
| ASSA / Rosario | Santa Fe | javascript | No | PENDIENTE_ADAPTADOR | [Portal](https://www.aguassantafesinas.com.ar/portal/licitaciones) |
| UNR / Rosario | Santa Fe | siu_diaguita | No | PENDIENTE_ADAPTADOR | [Portal](https://compras.unr.edu.ar/) |
| Poder Judicial de Santa Fe / Santa Fe | Santa Fe | html_pdf | Sí | BLOQUEADA | [Portal](https://www.justiciasantafe.gov.ar/index.php/poder-judicial/informacion-general/compras-y-licitaciones/) |
| Aeropuerto Internacional Rosario / Rosario | Santa Fe | html_paginado_pdf | Sí | BLOQUEADA | [Portal](https://aeropuertorosario.com/institucional/licitaciones/) |
| Municipalidad de Casilda / Casilda | Santa Fe | html_pdf | Sí | BLOQUEADA | [Portal](https://www.casilda.gob.ar/web/licitaciones-casilda/) |
| Municipalidad de Carcarañá / Carcarañá | Santa Fe | institucional | No | PENDIENTE_ADAPTADOR | [Portal](https://xn--carcaraa-j3a.gob.ar/) |
| Municipalidad de Cañada de Gómez / Cañada de Gómez | Santa Fe | html_pdf | Sí | BLOQUEADA | [Portal](https://cdg.gob.ar/transparencia/licitaciones-y-concursos/) |
| Municipalidad de Armstrong / Armstrong | Santa Fe | html | No | PENDIENTE_ADAPTADOR | [Portal](https://armstrong.gov.ar/index.php/transparencia) |
| Municipalidad de Las Parejas / Las Parejas | Santa Fe | institucional | No | PENDIENTE_ADAPTADOR | [Portal](https://lasparejas.gov.ar/) |
| Municipalidad de Funes / Funes | Santa Fe | institucional | No | PENDIENTE_ADAPTADOR | [Portal](https://funes.gob.ar/) |
| Municipalidad de Roldán / Roldán | Santa Fe | html_pdf | Sí | BLOQUEADA | [Portal](https://www.roldan.gov.ar/wp/documents/licitaciones-y-contrataciones/) |
| Municipalidad de Pérez / Pérez | Santa Fe | datos_abiertos | No | PENDIENTE_ADAPTADOR | [Portal](https://perez.opendata.junar.com/home/) |
| Municipalidad de Villa Gobernador Gálvez / Villa Gobernador Gálvez | Santa Fe | javascript | No | PENDIENTE_ADAPTADOR | [Portal](https://vggmunicipalidad.gov.ar/licitaciones/) |
| Municipalidad de Santo Tomé / Santo Tomé | Santa Fe | boletin_pdf | Sí | BLOQUEADA | [Portal](https://municipiosantotome.gob.ar/boletin-oficial/) |
| Municipalidad de Santa Fe / Santa Fe | Santa Fe | html_paginado_pdf | Sí | BLOQUEADA | [Portal](https://transparencia.santafeciudad.gov.ar/compras-y-contrataciones/) |
| Municipalidad de Santa Fe / Santa Fe | Santa Fe | html_paginado_pdf | Sí | BLOQUEADA | [Portal](https://transparencia.santafeciudad.gov.ar/contrataciones-obra/) |
| Municipalidad de Rafaela / Rafaela | Santa Fe | aspx | No | PENDIENTE_ADAPTADOR | [Portal](https://www.rafaela.gob.ar/gobiernoabierto/Licitaciones.aspx) |
| Municipalidad de Venado Tuerto / Venado Tuerto | Santa Fe | html_pdf | Sí | BLOQUEADA | [Portal](https://venadotuerto.gob.ar/licitaciones/) |
| Municipalidad de Reconquista / Reconquista | Santa Fe | html_pdf | Sí | BLOQUEADA | [Portal](https://reconquista.gob.ar/licitaciones/) |
| Gobierno de Entre Ríos / Paraná | Entre Ríos | javascript | No | PENDIENTE_ADAPTADOR | [Portal](https://portal.entrerios.gov.ar/haciendayfinanzas/contrataciones/) |
| Ministerio de Planeamiento e Infraestructura / Paraná | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://www.entrerios.gov.ar/minplan/licitaciones) |
| CAFESG / Concordia | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://cafesg.gob.ar/cafesg2/licitaciones/) |
| Poder Judicial de Entre Ríos / Paraná | Entre Ríos | html_paginado_pdf | Sí | BLOQUEADA | [Portal](https://www.jusentrerios.gov.ar/contrataciones/) |
| ATER / Paraná | Entre Ríos | tabla_pdf | Sí | BLOQUEADA | [Portal](https://www.ater.gob.ar/ater2/licitaciones.asp) |
| Vialidad Entre Ríos / Paraná | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://aplicaciones.vialidadentrerios.gob.ar/obralic/web/licitacion/listado) |
| ENERSA / Paraná | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://www.enersa.com.ar/area-proveedores/) |
| Instituto Becario / Paraná | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://institutobecario.gov.ar/licitaciones.php) |
| Municipalidad de Victoria / Victoria | Entre Ríos | institucional | No | PENDIENTE_ADAPTADOR | [Portal](https://victoria.gob.ar/es/) |
| Municipalidad de San José / San José | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://sanjose.gob.ar/concursos-licitaciones/) |
| Municipalidad de Colón / Colón | Entre Ríos | iframe | No | PENDIENTE_ADAPTADOR | [Portal](https://colon.gov.ar/compras-contratos-suministros/licitaciones/) |
| Municipalidad de Concordia / Concordia | Entre Ríos | restringido | No | BLOQUEADA_ORIGEN | [Portal](https://compras.concordia.gob.ar/) |
| Municipalidad de Concepción del Uruguay / Concepción del Uruguay | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://www.cdeluruguay.gob.ar/index.php/servicios-web/data-gov/licitaciones) |
| Municipalidad de Gualeguaychú / Gualeguaychú | Entre Ríos | tramite | No | PENDIENTE_ADAPTADOR | [Portal](https://w3.gualeguaychu.gov.ar/tramites/compras-y-licitaciones/acceso-a-licitaciones-p%C3%BAblicas) |
| Municipalidad de Gualeguay / Gualeguay | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://municipalidad.gualeguay.gob.ar/modulos/transparencia/licitaciones_publicas.php) |
| Municipalidad de Crespo / Crespo | Entre Ríos | tabla_pdf | Sí | BLOQUEADA | [Portal](https://www.crespo.gob.ar/licitaciones-privadas-2026/) |
| Municipalidad de Crespo / Crespo | Entre Ríos | html_paginado_pdf | Sí | BLOQUEADA | [Portal](https://www.crespo.gob.ar/category/licitacion-publica/) |
| Municipalidad de Chajarí / Chajarí | Entre Ríos | institucional | No | PENDIENTE_ADAPTADOR | [Portal](https://chajari.gob.ar/) |
| Municipalidad de Federación / Federación | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://www.federacion.gob.ar/licitaciones) |
| Municipalidad de Nogoyá / Nogoyá | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://nuevo.nogoya.gob.ar/compras-licitaciones-y-concursos-nuevo/) |
| Municipalidad de La Paz / La Paz | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://haciendalapaz.gob.ar/compras/) |
| Municipalidad de Villaguay / Villaguay | Entre Ríos | boletin_pdf | Sí | BLOQUEADA | [Portal](https://villaguay.gob.ar/boletindigital/) |
| Municipalidad de Rosario del Tala / Rosario del Tala | Entre Ríos | html_pdf | Sí | BLOQUEADA | [Portal](https://www.rosariodeltala.gob.ar/?q=licitaciones-publicas) |
| Municipalidad de San Nicolás / San Nicolás | Buenos Aires | html_pdf | Sí | BLOQUEADA | [Portal](https://www.sannicolasciudad.gob.ar/areas/economia-y-finanzas/licitacionesyconcursos) |
| Municipalidad de San Pedro / San Pedro | Buenos Aires | institucional | No | PENDIENTE_ADAPTADOR | [Portal](https://sanpedro.net.ar/portal.php) |
| Municipalidad de Ramallo / Ramallo | Buenos Aires | pdf_historico | No | PENDIENTE_ADAPTADOR | [Portal](https://www.ramallo.gob.ar/sites/default/files/descargas/decretos_abril_2024_pdf_-_boletin_oficial_virtual.pdf) |
| Municipalidad de Pergamino / Pergamino | Buenos Aires | html | Sí | BLOQUEADA | [Portal](https://compras.pergamino.gob.ar/) |
| Municipalidad de Arrecifes / Arrecifes | Buenos Aires | html_pdf | Sí | BLOQUEADA | [Portal](https://arrecifes.gob.ar/informacion-publica/licitaciones/) |
| Municipalidad de Baradero / Baradero | Buenos Aires | html | Sí | BLOQUEADA | [Portal](https://gobiernoabierto.baradero.gob.ar/precios-y-licitaciones) |
| Municipalidad de Rojas / Rojas | Buenos Aires | html_pdf | Sí | BLOQUEADA | [Portal](https://transparencia.rojas.gov.ar/index.php?action=17) |
| Municipalidad de Rojas / Rojas | Buenos Aires | tabla | Sí | BLOQUEADA | [Portal](https://transparencia.rojas.gov.ar/index.php?action=18) |

## Territorio todavía sin cobertura operativa

**Las tres provincias carecen de cobertura operativa demostrada en esta revisión. El inventario aún no es exhaustivo.** El total de organismos/portales faltantes sigue siendo desconocido. La lista siguiente contiene 83 localidades de trabajo; no representa todos los municipios y comunas.

**Santa Fe:** Rosario, Casilda, Carcarañá, Cañada de Gómez, Armstrong, Las Parejas, Alvear, Funes, Roldán, Pérez, Villa Gobernador Gálvez, Santo Tomé, Santa Fe, Rafaela, Venado Tuerto, Reconquista, San Lorenzo, Capitán Bermúdez, Fray Luis Beltrán, Granadero Baigorria, Puerto General San Martín, Pueblo Esther, General Lagos, Arroyo Seco, Ibarlucea, Soldini, Zavalla, Álvarez, Piñero, Acebal, Luis Palacios, Ricardone, Timbúes, Pujato, Villa Constitución, Correa, Bustinza, Arequito, Chabás, Bigand, Fuentes, Arteaga, San Jerónimo Sud, San Jerónimo Norte, Esperanza, Sunchales, Firmat, Rufino.

**Entre Ríos:** Paraná, Victoria, San José, Colón, Concordia, Concepción del Uruguay, Gualeguaychú, Gualeguay, Crespo, Chajarí, Federación, Diamante, Nogoyá, La Paz, Villaguay, Rosario del Tala.

**Buenos Aires:** San Nicolás, San Pedro, Ramallo, Pergamino, Arrecifes, Baradero, Rojas, Colón, Salto, Capitán Sarmiento, San Antonio de Areco, Carmen de Areco, Zárate, Campana, San Andrés de Giles, Junín, General Arenales, Leandro N. Alem, Chacabuco.

Falta cerrar el padrón completo de comunas pequeñas de Santa Fe, hospitales, SAMCo y entes descentralizados, y completar municipios entrerrianos fuera de la prioridad inicial. Para Buenos Aires se mantiene una lista amplia de candidatos; las distancias por ruta desde Rosario todavía no están medidas y no se afirma que todos cumplan 280 km.

## Próximas etapas

1. Restaurar el proxy y habilitar mediante la configuración del entorno los dominios oficiales del inventario. Ejecutar `python tools/verificar_fuentes.py`; no requiere modificar el historial de producción. Como alternativa verificable, el workflow manual sobre esta rama ejecuta el verificador en GitHub Actions con permisos de lectura y conserva su evidencia como artefacto; no se ha disparado desde esta sesión.
2. Priorizar CAFESG, Aeropuerto Rosario, Santa Fe capital, Casilda y EPE: guardar respuestas HTML/PDF reales, ajustar extracción de fichas, recorrer todas las páginas y comparar publicaciones detectadas con el listado oficial. Promover cada fuente solo con conteos y evidencia.
3. Resolver API pública de ASSA y Entre Ríos, iframes de Colón, SIU-Diaguita UNR y alternativa pública de Concordia. No inventar endpoints ni usar portales de prueba como producción.
4. Importar y actualizar el padrón oficial completo santafesino (códigos publicados desde 2018), cruzarlo con fuentes y registrar explícitamente cada comuna sin portal. El archivo oficial se localizó, pero su descarga posterior agotó tiempo; no se declara importado. Repetir para municipios, comunas y entes entrerrianos.
5. Medir distancias por ruta de los partidos bonaerenses; completar partidos cercanos y boletines complementarios, hospitales/SAMCo/entes. Añadir OCR donde exista PDF escaneado y resolver duplicados documentales con identidad del organismo y expediente.
6. Volver a ejecutar con historial real preservado y actualizar este informe con `python tools/informe_cobertura.py`. Mantener PR #1 abierto para revisión; no fusionar automáticamente.
