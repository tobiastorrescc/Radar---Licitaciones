# Alternativas de extracción — Issue #14

**Resultado: no se recuperó el acceso en vivo a EPE, Gestiones de Compras ni Boletín Oficial SF. Hubo cero oportunidades nuevas, vigentes y verificadas adicionales. Esto no demuestra ausencia de publicaciones: cinco fuentes no pudieron consultarse.** Se implementó y comprobó un respaldo por archivos oficiales, además de rutas alternativas y búsqueda complementaria. No se presenta este avance de resiliencia como éxito comercial del descubrimiento.

Comparación con `22deb1e`. Las pruebas ocurrieron el 6/11 UTC, todavía 5/11 en Argentina. Las 16 abiertas corresponden a la hora de las capturas: no garantizan vigencia después de sus aperturas.

## Resultados por fuente

| Fuente | Estado anterior | Estado nuevo | Convocatorias encontradas | Nuevas vigentes | Método |
|---|---|---|---:|---:|---|
| EPE | Inaccesible, 0 en consulta | Inaccesible; respaldo funcional | 0 en vivo + **37 de archivo, ya conocidas** | **0** | Listados/fichas/archivo oficial; búsqueda de URLs oficiales; importación HTML |
| Gestiones Santa Fe | Inaccesible, 0 | Inaccesible | 0 | 0 | Interfaz, listado imprimible publicado, HTTP/HTTPS y búsqueda; CSV preparado, sin endpoint descargable verificado |
| Boletín Santa Fe | Inaccesible, 0 | Inaccesible | 0 | 0 | Secciones diarias por fecha, resumen del día, PDF completo alternativo y búsqueda |
| Cañada de Gómez | HTTP 403, 0 | HTTP 403 | 0 | 0 | Consulta oficial; no se elude la restricción |
| Compras UNR | HTTP 403, 0 | HTTP 403 | 0 | 0 | Consulta oficial; no se elude la restricción |
| ASSA | Operativa, 3 abiertas | Operativa | 3, todas abiertas | 0 | API JSON pública |
| Poder Judicial ER | Operativa, 8 abiertas | Operativa | 58; ocho abiertas | 0 | Listado HTML y fichas concurrentes |
| Aeropuerto Rosario | Parcial, 5 abiertas | Parcial por plazo máximo | 162 procedimientos válidos; cinco abiertos | 0 | Paginación HTML y fichas; 163 registros brutos, uno no confirmado |

El barrido mantiene **16 abiertas verificadas**, sin perder las de las fuentes funcionales. Aeropuerto recuperó diez procedimientos históricos adicionales respecto de los 152 válidos anteriores, ninguno abierto nuevo. El archivo de EPE no añade oportunidades inéditas al historial: sus 37 procedimientos ya estaban registrados.

## EPE: respaldo comprobado sin falsas novedades

Se reutilizó la captura oficial de [la ejecución del 28/10](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40688224634), cuya respuesta HTML original tiene SHA-256 `9364597500792a048744542a19dc384912ed21d8a9ad9956aaba884d55b078e9`. Se conservaron **las 37 tarjetas completas**, retirando scripts, estilos y atributos ejecutables; el recibo conserva URL, fecha, transformación y ambas huellas. La importación fue comprobada desde Actions, no sólo con un fixture local.

Entre estos antecedentes hay **17 con apertura futura según el archivo**, 18 vencidos y dos sin fecha suficiente. Los 17 permanecen **pendientes de revalidación**, fuera del informe comercial actual. Ejemplos documentales para revisar, no nuevas oportunidades verificadas:

- **7050001923**, trailers para cabina de GU móvil: apertura consignada **10/11/2026**.
- **7060002931**, aisladores para mantenimiento: **10/11/2026**.
- **7060002921**, remodelación de LABT en Aarón Castellanos: **16/11/2026**.

Todos proceden del [listado oficial EPE](https://www.epe.santafe.gov.ar/app2/aperturas). No se inventaron enlaces individuales, publicación ni cierre de recepción. La fecha de apertura no acredita por sí sola un horario límite distinto.

La validación contra la copia del respaldo conservó la última observación de los 37 registros en **28/10/2026 09:42:09 ART** y los dejó **no observados en la corrida actual**. Reimportar un archivo antiguo no rejuvenece un registro, no sustituye datos más recientes y no genera una publicación nueva.

## Alternativas implementadas

1. **Nivel 1:** lectura directa HTML, JSON, CSV y PDF; límites de conexión/lectura y supervisor independiente por fuente. El sondeo registra HTTP, duración, MIME, bytes, extracción y errores. Un campo vacío significa que no se obtuvo ese dato, no HTTP 200 ni cero publicaciones.
2. **Nivel 2:** rutas oficiales alternativas de fichas y archivos de EPE; listado imprimible de Gestiones y variantes oficiales del Boletín. Se corrigió además la declaración del host alternativo `www.santafe.gov.ar` de Gestiones, que antes quedaba fuera del conjunto permitido del conector. Se comprobó que ahora se consultan ambas rutas: ambas agotan la conexión.
3. **Nivel 3:** búsqueda RSS complementaria sólo después de fallar la extracción directa. Sus resultados son candidatos: se intenta consultar la URL oficial y se exige extracción real. No se importan snippets ni se convierten resultados del buscador en oportunidades verificadas. La búsqueda no se utiliza para rodear HTTP 401/403/429. En las pruebas nativas no aportó candidatos oficiales utilizables para estas fuentes.
4. **Nivel 4:** bandeja `entradas_oficiales/` para HTML, CSV y PDF con recibos JSON. Se admite descarga externa mediante CLI o un archivo aportado desde navegador, sin cambiar código. Se controla dominio oficial declarado, ruta local, tamaño, huella y fecha, dejando desconocido lo no publicado. Las capturas con recibo HTTP oficial sólo se consideran recientes dentro de 72 horas. Recibos de procesamiento en SQLite sobreviven a la restauración del respaldo y evitan repetir archivos sin cambios. Una nueva descarga oficial del mismo contenido puede aportar una revalidación nueva sin duplicar el procedimiento.

El lector del Boletín consulta directamente la sección de licitaciones de hoy y tres días hábiles anteriores. No infiere publicación a partir de la fecha de edición. Si falla el HTML, intenta el PDF diario oficial por la estructura publicada. Para el PDF completo identifica la sección Licitaciones, evita el índice y excluye otras secciones; procesa sus avisos completos, sin seleccionar destacados. Los feriados o rutas derivadas sin respuesta siguen pendientes: no se inventa una edición ni se declara ausencia de avisos.

Las tablas normales, el listado imprimible de cuatro columnas y el CSV se normalizan con organismo por fila. “Sin Modalidad” no crea otra identidad para el mismo procedimiento. No se requieren presupuesto, pliego, pago ni requisitos comerciales para incorporarlo.

## Cómo usar el respaldo por archivos

Desde una copia de la rama, cuando un portal permita la descarga en otro entorno:

```bash
python tools/importar_oficiales.py --fuente fuente-003 --url 'https://www.epe.santafe.gov.ar/app2/aperturas'
```

La descarga crea automáticamente el archivo y su recibo en `entradas_oficiales/`, con fecha real, URL final y hash. Para un archivo ya descargado desde navegador:

```bash
python tools/importar_oficiales.py --archivo /ruta/aviso.pdf --fuente fuente-060 --url 'URL_OFICIAL_DEL_DOCUMENTO'
```

Se copia a la bandeja y se genera el recibo. Si se conoce la fecha de captura, puede añadirse `--capturado-en '2026-11-06T10:00:00-03:00'`; si no, queda desconocida. Un archivo aportado sin recibo de descarga oficial comprobable queda pendiente de procedencia/revalidación. No se supone que haberlo registrado hoy signifique que fue descargado o publicado hoy. En Windows, Python necesita la base horaria `tzdata` — instalada explícitamente en el sondeo de compatibilidad.

Para comprobar los archivos sin tocar el historial:

```bash
python tools/importar_oficiales.py --salida work/comprobar-importacion
```

Publicar **el archivo y su JSON** en `entradas_oficiales/` de `mejora/radar-auditable`, dentro del mismo PR. El siguiente piloto los incorpora automáticamente al mismo catálogo, conserva enlaces y evidencia y registra los recibos en su estado persistente. No hay que editar adaptadores ni cargar cada procedimiento manualmente. No se activa ningún envío ni servidor.

El importador usa procesos separados (dos concurrentes), hasta 40 s por archivo y 60 s totales. Conserva parciales y errores. Un archivo inválido no borra datos ni impide procesar otros. Los PDF reutilizan la caché de texto por SHA; no se ejecuta OCR. Si un PDF no tiene texto o falta el lector, queda un error explícito.

## Pruebas reales y límites

- [Diez rutas HTTPS alternativas en Linux](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42137150334): fallos TLS, cierre remoto, HTTP 500 y timeouts; cero convocatorias.
- [Cinco rutas HTTP](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42137816192): EPE HTTP 503; Gestiones y Boletín con timeout.
- [Barrido integrado e importación](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42139240107): **123,15 s de red + 0,26 s de importación**. No se modificó el plazo global ni el programador. Como control positivo, la API ASSA devolvió HTTP 200, JSON de 4.358 bytes y tres convocatorias reconocidas.
- [Gestiones con el host alternativo realmente consultado](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42139811814): **18,82 s**, dos rutas con timeout.
- [Persistencia y segunda pasada](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42142662013): **cero novedades y cero eventos adicionales**, producción y respaldos intactos. Las copias antiguas no alteran la observación oficial anterior.
- [Windows, curl 8.21 / Schannel](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42140790870): mismos errores de acceso en cinco rutas; no hay evidencia de que cambiar el cliente TLS resuelva el problema. Es un workflow aislado sin cron, con permiso de sólo lectura; no interviene en el piloto.
- [CI final del código](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42142661895): **442 pruebas Python ejecutadas, 441 aprobadas y una opcional omitida; 28 Node aprobadas**.
- Regresiones del importador: archivos HTML/CSV/PDF, lectura PDF real sin OCR, sección completa con índice y varias páginas, huellas y rutas inválidas, separación de organismos, fallos aislados, persistencia de recibos, repetición sin novedades y conservación de fechas/observaciones anteriores. Los fixtures PDF sintéticos se usan sólo para probar el lector; no se contabilizan como oportunidades reales.

Se probaron 21 peticiones instrumentadas en los sondeos tabulados, además de las consultas del barrido y la búsqueda complementaria. Esto no equivale a 21 fuentes cubiertas. Los resultados HTTP de investigación no promueven automáticamente una fuente a operativa.

## Archivos de entrega y pendientes

- `fuentes.csv`: estado y resultados de las ocho fuentes.
- `abiertas_observadas.csv`: las **16 abiertas**, sin recortes comerciales.
- `epe_archivo_completo.csv`: los **37 antecedentes**, incluidos vencidos y desconocidos.
- `epe_apertura_futura_pendiente.csv`: los **17 casos a revalidar**, separados del comercial.
- `rutas_probadas.csv`: HTTP, tiempos, tipo, bytes, extracción y errores por ruta/cliente.
- `resultado.json`: métricas y enlaces de auditoría reproducibles.

**Sigue pendiente el objetivo principal de recuperar en vivo las tres fuentes fundamentales.** EPE falla incluso con dos clientes TLS; los dominios provinciales no completan la conexión; Cañada y UNR mantienen 403. No se atribuye automáticamente todo a un bloqueo deliberado ni a un error del extractor. El CSV exacto de Gestiones no pudo descubrirse/verificarse porque no se obtuvo la interfaz/servicio en vivo. La vía de archivos ya está funcional para incorporar documentos oficiales actuales obtenidos desde un acceso permitido.

Sin merge, cambios a main, historial de producción, respaldos existentes o programador. Sin servicios pagos, OCR masivo, análisis de pliegos comerciales ni cálculos de rentabilidad.

Incidencias de validación: el primer sondeo Windows carecía de la base horaria y se corrigió instalando sólo `tzdata`. La CI final agotó inicialmente la preparación de lectores documentales; el segundo intento terminó aprobado, sin modificar el programador ni reducir las pruebas.
