# Radar de licitaciones

Radar de publicaciones públicas sin filtros por rubro, monto ni financiación y sin límite de resultados. El inventario territorial sigue en construcción: ver [informe de cobertura](INFORME_COBERTURA.md). Incorporar una URL a configuración no equivale a verificar que funciona.

## Ejecutar

Python 3.11+ y `pdftotext` (paquete `poppler-utils`). Desde la raíz:

```sh
python -m unittest discover -s tests -v
python radar.py
python tools/verificar_fuentes.py
python tools/informe_cobertura.py
```

`radar.py` conserva `radar_estado.json`, resultados completos en `licitaciones_nuevas.json` y auditoría en `auditoria_fuentes.json`. El verificador separado no toca esos archivos. Lectura corrupta falla sin borrar historial. No ejecutar dos procesos contra los mismos archivos. Mantener copias de seguridad del historial.

`fuentes.txt` contiene las consultas activadas; `fuentes.json`, sus metadatos y conector. `inventario/fuentes.json` incluye también las fuentes que necesitan un adaptador; `inventario/territorio.json`, las localidades y categorías pendientes. `inventario/verificacion.json` guarda la observación real del executor, separada de la evidencia web del inventario.

## Estados y extracción

OPERATIVA requiere publicaciones numeradas detectadas; SIN_PUBLICACIONES_NUEVAS requiere extracción válida de publicaciones ya conocidas. PENDIENTE cubre contenido vacío/no reconocido, formatos y adaptadores faltantes; BLOQUEADA indica error de acceso sin contenido; PARCIAL conserva publicaciones con errores o límites. Ninguno implica cobertura exhaustiva. Un sitio JavaScript vacío nunca se marca como sin novedades.

HTML de enlaces, filas y bloques, paginación explícita y PDF con texto. El conector heredado se conserva para compatibilidad, con candidatos no verificados. Nuevas fuentes usan `publicaciones`. PDF escaneado requiere OCR pendiente; JavaScript, formularios ASP.NET y APIs necesitan adaptadores específicos comprobados. Cada portal necesita todavía fixtures y contraste en vivo antes de declararse operativo.

Deduplicación persistente por fuente/URL/procedimiento/llamado/situación, conservando primeras y últimas detecciones. Cambios de llamado o declaración de desierta pueden generar una novedad. No hay garantía de deduplicación semántica entre portales o URLs documentales diferentes. Los campos comerciales sin evidencia permanecen nulos. El orden orientativo prioriza pago contado/contra entrega y llamados especiales; no es una estimación de rentabilidad ni confirma que el llamado siga abierto.

## Automatización

Se conserva el workflow diario a las 11 UTC (08 Argentina), con pruebas en PR, logs/artefactos por 90 días y persistencia del historial ante fallas de consulta. Usa main: los cambios de esta rama no están activos hasta fusionar el PR, acción todavía no autorizada. GitHub puede retrasar el cron. Se requiere que github-actions pueda escribir historial en main.

RADAR_MAX_PAGINAS y RADAR_MAX_PROFUNDIDAD mantienen límites de seguridad (el segundo aplica al conector heredado). No limitan resultados. Un recorrido truncado se informa en auditoría. Salida 2 ante fuentes bloqueadas, pendientes o parciales; las demás fuentes continúan. Los archivos versionados de resultados previos son históricos, no prueba de esta etapa.

Alternativa de red: ejecutar manualmente el workflow sobre esta rama activa un trabajo de verificación con permisos de lectura y artefactos. No escribe el historial de main. La verificación de red es explícita y separada de las pruebas reproducibles del PR.

## Verificador acotado y auditable

El verificador usa procesos aislados, hasta 4 simultáneos (configurable entre 1 y 8). Por defecto: 5 s para conexión TCP/proxy/TLS, 10 s de inactividad de lectura de cabeceras/cuerpo, 60 s de plazo absoluto por fuente y 600 s para toda la ejecución, más el cierre de procesos y guardado. El plazo de fuente también corta DNS bloqueado, descarga por goteo, paginación interminable o extracción PDF trabada. Los timeouts de sockets por sí solos no limitan la duración total de una descarga.

```sh
python -u tools/verificar_fuentes.py --concurrencia 4 --conexion 5 --lectura 10 --por-fuente 60 --total 600
```

Cada consulta muestra INICIO, CONSULTANDO, PROGRESO y FIN con URL, fase, duración y estado. Hay checkpoint atómico antes de cada descarga, antes de extraer y al terminar cada página. El supervisor guarda el resumen incremental, todas las publicaciones sin recortarlas y la auditoría JSONL en `<salida>_ejecuciones/<id>/`. SIGINT/SIGTERM y límites conservan avances y detienen los workers y sus subprocesos. Una terminación forzada del runner puede impedir el último guardado/subida; los checkpoints ya escritos permanecen en disco.

`resumen.consultadas` cuenta fuentes que iniciaron una consulta, no fuentes validadas. `funcionaron` exige extracción de publicaciones y recorrido sin errores/límites; `con_publicaciones` también cuenta parciales. RED identifica errores HTTP/DNS/TLS/conexión/lectura; EXTRACCION incluye PDF/formato/no reconocimiento de publicaciones; INTERNO identifica un worker que falla; PRESUPUESTO distingue el plazo global o cancelación. Un timeout por fuente conserva su fase. Los conteos de categorías pueden solaparse si una fuente tuvo varios errores. NO_INICIADA nunca cuenta como fallo de red ni como fuente consultada. El total final no permite inferir que un portal esté caído fuera de este entorno.

Actions ejecuta esta verificación de diagnóstico al actualizar un PR del mismo repositorio y en disparos manuales sobre ramas distintas de main. Corre con permisos de lectura y límite de 15 minutos de job / 12 de paso, mientras el supervisor impone sus 10 minutos. Los fallos de portales se informan en el resumen y artefactos, separados del resultado de las pruebas unitarias; no bloquean su evaluación. Guarda `work/verificacion/` durante 90 días, incluso ante fallos/cancelación: esta ruta nueva evita subir la auditoría histórica versionada por equivocación. El job diario de producción y su historial se conservan. Ver [informe del verificador](INFORME_VERIFICADOR.md).
