# Reparación de conectores basada en auditoría individual

[Auditoría original #35](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40253451095) y muestras oficiales obtenidas en los diagnósticos #37/#39. Se revisan las 36 fuentes activadas, no se incorporan sitios supuestos.

El resultado anterior de Rosario era un falso positivo: el teléfono de Compras Menores. La URL anterior de Santo Tomé correspondía a Corrientes. Ambas clasificaciones se corrigen y no se usan para afirmar cobertura.

| Fuente #35 | Estado anterior | Causas observadas | Corrección / pendiente |
|---|---|---|---|
| fuente-001 | OPERATIVA | Sin error técnico; revisar calidad de detección | Tarjetas reales del buscador y enlaces a listados por tipo; excluir contactos. |
| fuente-002 | BLOQUEADA | URLError | Timeout de conexión pasa a 12 s con límite absoluto 60 s; no se elude acceso. |
| fuente-003 | PENDIENTE | SinPublicacionesDetectadas | Tarjetas SSR con botones, sin anchors; extraer número, tipo y objeto. |
| fuente-006 | BLOQUEADA | URLError | Timeout de conexión pasa a 12 s; no desactivar TLS. |
| fuente-007 | TIEMPO_FUENTE | TIEMPO_FUENTE | Códigos LPU/LPR/CPRV/CD, objeto del card y paginación; evitar descargar todos los pliegos para extraer el listado. |
| fuente-008 | TIEMPO_FUENTE | TIEMPO_FUENTE, UnicodeEncodeError, ValueError | Abreviaturas LIC PUB/PRIV, UTF-8 en enlaces N°, anexos unidos por procedimiento/llamado/situación. Normativa no es llamado. |
| fuente-010 | BLOQUEADA | HTTPError | 403 de origen: conservar bloqueo sin intentar eludirlo. |
| fuente-014 | TIEMPO_FUENTE | TIEMPO_FUENTE | Consultar fichas reales descubiertas en navegación; no contar el menú como publicación extraída. |
| fuente-017 | PENDIENTE | SinPublicacionesDetectadas | Se descarta el dominio de Corrientes y se consulta el sitio santafesino; cobertura pendiente si no publica un listado. |
| fuente-018 | BLOQUEADA | HTTPError | 403: acceso restringido. No se atribuye a extracción. |
| fuente-019 | BLOQUEADA | HTTPError | 403: acceso restringido. No se atribuye a extracción. |
| fuente-021 | PARCIAL | UnicodeEncodeError, ValueError | Encabezados con cuerpo y adjuntos; codificar enlaces, reunir páginas del mismo PDF y OCR cuando el PDF es necesario. |
| fuente-022 | TIEMPO_FUENTE | TIEMPO_FUENTE, ValueError | Secciones de cada llamado con objeto y enlaces, sin recorrer formularios auxiliares como oportunidades. |
| fuente-024 | TIEMPO_FUENTE | TIEMPO_FUENTE | Tarjetas con organismo/objeto; concursos sin número conservan el campo desconocido. No seguir cientos de fichas si el listado ya contiene la publicación. |
| fuente-025 | TIEMPO_FUENTE | TIEMPO_FUENTE | Número, objeto, situación y apertura en cada tarjeta; un solo registro por llamado, sin repetir ficha/adjuntos. |
| fuente-026 | TIEMPO_FUENTE | TIEMPO_FUENTE, ValueError | Tarjetas y paginación acotada a colección; ZIP y DOCX legibles cuando son necesarios para el objeto. |
| fuente-027 | TIEMPO_FUENTE | InvalidURL, TIEMPO_FUENTE | Respeta charset, LIC. Privada y tarjetas con objeto; codifica espacios en URLs sin doble escape. |
| fuente-028 | BLOQUEADA | HTTPError | URL anterior 404. Alternativa oficial enlazada: dpver.gov.ar/category/licitaciones-2026/. |
| fuente-029 | BLOQUEADA | URLError | Certificado sin cadena de confianza: se mantiene validación TLS y fallo identificable; no se inventa una solución. |
| fuente-030 | BLOQUEADA | URLError | Certificado sin cadena de confianza: se mantiene fallo hasta corregir origen o verificar alternativa oficial. |
| fuente-032 | OPERATIVA | Sin error técnico; revisar calidad de detección | Pública/Privada en acordeón heredan tipo y conservan objeto; adjuntos de Drive se enlazan sin inventar una API. |
| fuente-035 | PENDIENTE | ValueError | Datos JSON de LICITACIONES_DATA: lectura sin ejecutar JS; número, año, llamado, objeto y documentos. |
| fuente-037 | PENDIENTE | SinPublicacionesDetectadas | Página HTML volumétrica y estructura específica: se valida en la nueva corrida, no se declara vacía por falta de coincidencias. |
| fuente-038 | TIEMPO_FUENTE | TIEMPO_FUENTE, UnicodeEncodeError, ValueError | Número en primera columna + tipo en título de tabla + objeto; no inferir número de una fecha o un PDF. |
| fuente-039 | PENDIENTE | SinPublicacionesDetectadas | Seguir los archivos anuales enlazados y sus tablas, no confundirlos con un procedimiento. |
| fuente-041 | TIEMPO_FUENTE | TIEMPO_FUENTE, ValueError | Texto del llamado y adjuntos; OCR solo si falta el objeto, no descargar todo el sitio. |
| fuente-042 | PENDIENTE | SinPublicacionesDetectadas | La ruta inicial era descriptiva. Consultar el listado real enlazado en transparencia, con objetos y pliegos. |
| fuente-043 | PENDIENTE | SinPublicacionesDetectadas | Seguir listados públicos de licitaciones y concursos; número/objeto/fecha en cadacompra. |
| fuente-044 | PENDIENTE | SinPublicacionesDetectadas | Seguir índices anuales de licitaciones y sus documentos; pendiente si son formatos no legibles. |
| fuente-045 | TIEMPO_FUENTE | TIEMPO_FUENTE, ValueError | No seguir PDF de rendiciones ajenas; el objeto del PDF es necesario si el HTML solo muestra el número. |
| fuente-046 | PARCIAL | ValueError | Leer adjuntos del aside que sí son llamados. OCR en PDF sin texto. Mantener evidencia si la lectura queda parcial. |
| fuente-049 | PENDIENTE | ValueError | Redirección oficial a aplicativos.pergamino.gob.ar permitida; es portal con autenticación, se identifica como tal y no se fuerza acceso. |
| fuente-050 | PARCIAL | ValueError | Objetos en HTML, DOCX y anexos; pliegos auxiliares no se contabilizan como llamados distintos. |
| fuente-051 | PENDIENTE | SinPublicacionesDetectadas | Datos React públicos serializados: objeto/motivo, año y documento sin ejecutar JS ni inventar endpoints. |
| fuente-052 | PENDIENTE | SinPublicacionesDetectadas | Recuperar URL pública del botón DownloadFile, unir la carátula y el objeto. |
| fuente-053 | OPERATIVA | Sin error técnico; revisar calidad de detección | La ruta action18 era ejecución de órdenes de compra, no licitaciones privadas. Se reemplaza por action24 enlazada por el municipio; el mensaje explícito sin documentos se informa por separado. No se cuentan 1.641 órdenes de compra como llamados. |

La clasificación OPERATIVA se limita al alcance declarado del conector: extraer las publicaciones del listado y su objeto, con enlaces de documentos. No certifica que todos los adjuntos estén descargados ni que el organismo publique todos sus procedimientos. Si el objeto depende de un PDF/DOCX/ZIP, su extracción es obligatoria y un error deja la fuente parcial. No se truncan novedades ni se filtra por monto, rubro o financiación.

Un listado sin coincidencias queda PENDIENTE. SIN_PUBLICACIONES requiere una declaración explícita del portal y ausencia de errores. Fechas, montos y número permanecen desconocidos cuando no hay evidencia; un registro histórico/adjudicado no se presenta como oportunidad abierta confirmada.

Se preserva el historial de producción. Las muestras de regresión incluyen extractos reales con URL, run y hash de la respuesta en tests/fixtures/reales/proveniencia.json. La comparación de cantidades contra #35 debe considerar eliminación de falsos positivos, anexos duplicados y números tomados de teléfonos/fechas.

La nueva corrida de Actions y sus resultados individuales se enlazan en la descripción del PR #1. El PR permanece sin fusionar.

La segunda revisión corrige el acceso a todos los tipos de Rosario, data-next-page de Elementor, títulos de Baradero con año entre paréntesis y exige la ficha para obtener el objeto de Vialidad. Cargar más sin URL verificable queda parcial. Imágenes de llamados pueden leerse con OCR. Los listados sin documentos se informan como tales, sin inventar oportunidades.
