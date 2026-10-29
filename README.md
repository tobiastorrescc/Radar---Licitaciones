# Radar de licitaciones

Radar de publicaciones públicas sin filtros por rubro, monto ni financiación y sin límite de resultados. El inventario territorial sigue en construcción: ver [informe de cobertura](INFORME_COBERTURA.md). Incorporar una URL a configuración no equivale a verificar que funciona.

## Piloto controlado, sin producción

Ver [puesta en marcha controlada](PUESTA_EN_MARCHA_CONTROLADA.md). En esta rama, Actions valida dos invocaciones reales independientes del piloto, restaurando el estado desde Git entre runners y comprobando que no se pierda historia ni se repitan identidades como nuevas. La inicialización conserva la línea de base sin alertas históricas. Descargar el artefacto **radar-controlado** y abrir **index.html** para consultar todo el catálogo. Producción está cerrada por defecto; no se fusiona ni activa en esta etapa.

Resultado y auditoría individual de las 74 fuentes: [validación controlada](VALIDACION_CONTROLADA.md).

## Ejecutar

Python 3.11+ y `pdftotext` (paquete `poppler-utils`). Desde la raíz:

```sh
python -m unittest discover -s tests -v
python tools/radar_controlado.py --salida work/prueba-doble --doble
python tools/verificar_fuentes.py --salida work/verificacion/verificacion.json
python tools/padron_territorial.py
python tools/informe_cobertura.py
```

`radar.py` exige autorización explícita de producción. El piloto escribe exclusivamente bajo `work/`, sin modificar esos archivos. El ejecutor heredado conserva `radar_estado.json`, resultados completos en `licitaciones_nuevas.json` y auditoría en `auditoria_fuentes.json`. El verificador separado no toca esos archivos. Lectura corrupta falla sin borrar historial. No ejecutar dos procesos contra los mismos archivos. Mantener copias de seguridad del historial.

`fuentes.txt` contiene las consultas activadas; `fuentes.json`, sus metadatos y conector. `inventario/fuentes.json` incluye también las fuentes que necesitan un adaptador; `inventario/territorio.json`, las localidades y categorías pendientes. `inventario/verificacion.json` guarda la observación real del executor, separada de la evidencia web del inventario.

## Estados y extracción

OPERATIVA requiere publicaciones numeradas detectadas; SIN_PUBLICACIONES_NUEVAS requiere extracción válida de publicaciones ya conocidas. PENDIENTE cubre contenido vacío/no reconocido, formatos y adaptadores faltantes; BLOQUEADA indica error de acceso sin contenido; PARCIAL conserva publicaciones con errores o límites. Ninguno implica cobertura exhaustiva. Un sitio JavaScript vacío nunca se marca como sin novedades.

HTML de enlaces, filas y bloques, paginación explícita y PDF con texto. El conector heredado se conserva para compatibilidad, con candidatos no verificados. Nuevas fuentes usan `publicaciones`. PDF escaneado requiere OCR pendiente; JavaScript, formularios ASP.NET y APIs necesitan adaptadores específicos comprobados. Cada portal necesita todavía fixtures y contraste en vivo antes de declararse operativo.

Deduplicación persistente por provincia, organismo, procedimiento y convocatoria, aunque existan diferentes URLs. La primera consulta controlada establece una línea de base; las siguientes distinguen nuevos procedimientos, recuperación histórica, modificaciones y datos completados, conservando versiones y primeras/últimas detecciones. Cuando falta numeración comprobable se conserva una identidad más restrictiva y no se promete deduplicación semántica entre portales. Los contadores de visitas/descargas observados en Timbúes y Armstrong no generan cambios de contenido. Los campos comerciales sin evidencia permanecen nulos. El orden orientativo prioriza pago contado/contra entrega y llamados especiales; no es una estimación de rentabilidad ni confirma que el llamado siga abierto.

## Automatización

El horario objetivo es las 11 UTC (08 Argentina), con pruebas en PR y artefactos por 90 días. El piloto diario restaura SQLite desde respaldos incrementales versionados en Git, sin caducidad automática, y comprueba toda la cadena antes de consultar. Una falta de estado no reinicia silenciosamente la línea de base. Ver [persistencia duradera](PERSISTENCIA_DURADERA.md) y [resultados](RESULTADOS_PERSISTENCIA.md). El piloto de esta rama se invoca por `workflow_dispatch`; producción tiene una habilitación separada y cerrada por defecto. GitHub sólo ejecuta cron desde la rama predeterminada; esta rama del PR no tiene programación activa. No se modifica main ni se fusiona para habilitarla. Ver los pasos y límites de persistencia en la guía del piloto.

RADAR_MAX_PAGINAS y RADAR_MAX_PROFUNDIDAD mantienen límites de seguridad (el segundo aplica al conector heredado). No limitan resultados. Un recorrido truncado se informa en auditoría. Salida 2 ante fuentes bloqueadas, pendientes o parciales; las demás fuentes continúan. Los archivos versionados de resultados previos son históricos, no prueba de esta etapa.

Alternativa de red: ejecutar manualmente el workflow sobre esta rama consulta las fuentes, guarda artefactos y persiste exclusivamente el respaldo del piloto en esta misma rama. No escribe el historial de main. La verificación de red es explícita y separada de las pruebas reproducibles del PR.

## Verificador acotado y auditable

El verificador usa procesos aislados, hasta 4 simultáneos (configurable entre 1 y 8). Por defecto: 5 s para conexión TCP/proxy/TLS, 10 s de inactividad de lectura de cabeceras/cuerpo, 60 s de plazo absoluto por fuente y 600 s para toda la ejecución, más el cierre de procesos y guardado. El plazo de fuente también corta DNS bloqueado, descarga por goteo, paginación interminable o extracción PDF trabada. Los timeouts de sockets por sí solos no limitan la duración total de una descarga.

```sh
python -u tools/verificar_fuentes.py --concurrencia 4 --conexion 5 --lectura 10 --por-fuente 60 --total 600
```

Cada consulta muestra INICIO, CONSULTANDO, PROGRESO y FIN con URL, fase, duración y estado. Hay checkpoint atómico antes de cada descarga, antes de extraer y al terminar cada página. El supervisor guarda el resumen incremental, todas las publicaciones sin recortarlas y la auditoría JSONL en `<salida>_ejecuciones/<id>/`. SIGINT/SIGTERM y límites conservan avances y detienen los workers y sus subprocesos. Una terminación forzada del runner puede impedir el último guardado/subida; los checkpoints ya escritos permanecen en disco.

`resumen.consultadas` cuenta fuentes que iniciaron una consulta, no fuentes validadas. `funcionaron` exige extracción de publicaciones y recorrido sin errores/límites; `con_publicaciones` también cuenta parciales. RED identifica errores HTTP/DNS/TLS/conexión/lectura; EXTRACCION incluye PDF/formato/no reconocimiento de publicaciones; INTERNO identifica un worker que falla; PRESUPUESTO distingue el plazo global o cancelación. Un timeout por fuente conserva su fase. Los conteos de categorías pueden solaparse si una fuente tuvo varios errores. NO_INICIADA nunca cuenta como fallo de red ni como fuente consultada. El total final no permite inferir que un portal esté caído fuera de este entorno.

El verificador sigue disponible como diagnóstico independiente. En el PR, Actions reutiliza su supervisor para la prueba doble controlada, con hasta 600 segundos por consulta completa y 120 para documentos por corrida, un paso de 28 minutos y job de 35. Los fallos de portales se informan separados de las pruebas unitarias. Se guardan todos los checkpoints bajo `work/controlado/` durante 90 días. El historial de producción se conserva y su ejecución requiere autorización independiente. Ver [informe del verificador](INFORME_VERIFICADOR.md) para el método original y [guía actual del piloto](PUESTA_EN_MARCHA_CONTROLADA.md).

## Conectores reparados con evidencia real

Ver [auditoría individual y reparación](REPARACION_CONECTORES.md) de las 36 fuentes de #35. `extractores.py` interpreta tarjetas, encabezados, tablas y datos JSON públicos (Joomla/React) sin ejecutar JS. Normaliza tipos y números, une los anexos de un mismo llamado y conserva sus eventos. El teléfono de Rosario ya no se cuenta como llamado; la fuente de Santo Tomé se corrigió porque la anterior correspondía a Corrientes.

Las fuentes usan `lectura_adjuntos: necesarios`: si el HTML/JSON publica el procedimiento y el objeto, se conservan sus documentos como enlaces; no se exige descargar todos los formularios para extraer la publicación. Si falta el objeto, el documento o ficha es obligatorio y una falla deja la extracción parcial. `documentos.py` lee PDF, DOCX y ZIP; puede aplicar OCR con tesseract español/inglés a PDF escaneados. Los límites de tiempo y los checkpoints continúan vigentes. No se eliminan publicaciones por monto, rubro o financiación.

SIN_PUBLICACIONES exige evidencia explícita de un listado vacío, y no equivale a PENDIENTE por estructura desconocida. Los 403, TLS inválido o autenticación no se eluden ni se presentan como extracción correcta. El resultado de la verificación se refiere al alcance declarado del listado; no garantiza cobertura exhaustiva del organismo o lectura de todos los pliegos.

La ruta histórica action18 de Rojas era ejecución de órdenes de compra. Se reemplazó por la sección de licitaciones privadas enlazada oficialmente (action24); no se suman órdenes de compra sin objeto a la cantidad de licitaciones extraídas. El historial anterior permanece intacto.

## Ampliación territorial por lotes

`inventario/base_36.json` permite comprobar que se mantienen las fuentes anteriores. `tools/padron_territorial.py` importa el padrón oficial con su procedencia; el radio bonaerense es geodésico y no mide rutas. `tools/informe_cobertura.py` cruza el padrón, las fuentes y los checkpoints de una corrida para generar `work/verificacion/cobertura/`. Sus estados requieren extracción real; los archivos históricos de la etapa inicial no son el estado actual. Ver [informe de cobertura](INFORME_COBERTURA.md).

El programador externo de las 08:00 de Argentina está preparado y **desactivado**: [configuración, permisos, costos y activación posterior](PROGRAMADOR_EXTERNO.md). No se instaló un servicio ni se autorizó producción.

[Resultados de esta etapa del programador externo y auditorías](RESULTADOS_PROGRAMADOR.md).
