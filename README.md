# Radar de licitaciones

Radar exploratorio de enlaces candidatos, sin filtros por monto, rubro o capacidad financiera y sin limite de resultados. **No garantiza detectar todas las oportunidades**. Los candidatos no equivalen a procedimientos verificados.

## Auditoria inicial

- `fuentes.txt` contenia YAML de GitHub Actions: solo se consultaba Rosario por una constante en el codigo.
- La exploracion se detenía a las 40 paginas / profundidad 3 sin avisar. Los errores tampoco afectaban el resultado final.
- No habia pruebas, lectura de PDF, JavaScript, paginacion especializada ni extraccion de fichas de procedimientos.
- El historial deduplicaba por URL; no identificaba republicaciones ni distintos procesos en una misma URL.
- `patrones.txt` y `agente-radar.m` no eran utilizados por `radar.py`.

## Cambios verificables

Fuentes validadas sintacticamente, metadatos separados en `fuentes.json`, escritura atomica de JSON y fallo ante historial corrupto. Estados ERROR, PARCIAL y EXPLORADA con limites y errores por URL. EXPLORADA significa que termino el recorrido de enlaces admitidos, nunca cobertura exhaustiva del portal. Limites de seguridad configurables por RADAR_MAX_PAGINAS y RADAR_MAX_PROFUNDIDAD; no limitan el numero de candidatos informados.

Orden orientativo por pago contado/contra entrega, luego llamados especiales; no se infiere rentabilidad del presupuesto. Los campos sin evidencia permanecen null. Las estimaciones requieren cantidades, cotizaciones de adquisicion, precios de venta, impuestos y logistica; actualmente no hay datos suficientes ni motor de estimacion implementado.

## Ejecucion y pruebas

Python 3.11 o superior, sin dependencias externas:

```sh
python -m unittest discover -s tests -v
python radar.py
```

Ejecutar desde la raiz del repositorio. Codigo de salida 2 si alguna fuente falla totalmente. Los errores parciales quedan en auditoria. No ejecutar dos procesos simultaneos contra los mismos archivos locales.

Actions ejecuta pruebas en PR y cambios relevantes. La ejecucion diaria es a las 11 UTC (08 Argentina) en main, con artefactos 90 dias, logs y persistencia del historial aun con fallas de fuentes. La rama main debe permitir commits de github-actions; de lo contrario el push fallara explicitamente. El cambio del workflow no queda activo hasta fusionar el PR. GitHub no garantiza ejecucion puntual del cron.

## Cobertura real y pendientes

Inventario configurado: **1 fuente**, Municipalidad de Rosario. Fuente heredada con evidencia historica en `auditoria_fuentes.json`, no comprobada en vivo durante esta revision: el proxy del entorno no responde. Fuentes funcionando comprobadas actualmente: **0**. Consulta bloqueada por conectividad: **1**. Nuevas fuentes verificadas incorporadas: **0**.

Santa Fe: falta inventariar y verificar municipios y comunas restantes, organismos provinciales, EPE, ASSA, hospitales, universidades y entes descentralizados. Gran Rosario solo tiene la fuente de Rosario y su extraccion sigue siendo generica.

Entre Rios: sin fuentes incorporadas; faltan provincia y portales individuales de municipios y organismos.

Buenos Aires: sin fuentes incorporadas; falta definir si 280 km se mide por ruta o distancia geodesica, construir el inventario municipal y comprobar cada portal.

El numero total de fuentes faltantes **es desconocido**, porque no existe un inventario territorial exhaustivo. No se declara cobertura provincial. No se agregaron direcciones supuestas. La proxima ampliacion necesita acceso de red a portales oficiales, inventario con evidencia de descubrimiento, adaptadores por portal, muestras reales, extraccion de detalle y pliegos, paginacion y deteccion de cambios de procedimientos y llamados en la misma URL.

Limitaciones conservadas: candidatos por palabras en enlaces, posibles falsos positivos de navegacion, documentos no leidos, datos comerciales incompletos, sin deduplicacion semantica entre portales, sin garantia de todos los tipos ni del 100% de novedades. Los archivos de resultados versionados anteriores son historicos, no una validacion de esta revision.
