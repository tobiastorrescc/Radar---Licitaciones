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
