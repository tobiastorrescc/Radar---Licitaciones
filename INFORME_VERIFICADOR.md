# Corrección del verificador — PR #1

## Causa comprobada

La ejecución manual [#31](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40249325239) inició el paso de verificación a las 21:26:53 y fue cancelada a las 22:04:18 de Argentina del 25/10/2026: aproximadamente 37 minutos y 24 segundos. No emitió avances entre esos eventos.

El código usaba ThreadPoolExecutor con cuatro hilos y list(pool.map(...)): esperaba todas las fuentes y recién entonces escribía el JSON e imprimía el resumen. Cada fuente podía recorrer 1.000 páginas y cada petición tenía su propio timeout de 15 segundos; no había plazo total por fuente ni global. Tampoco había checkpoint antes de terminar. Por eso un portal lento podía prolongar la ejecución y la cancelación dejaba como artefacto el archivo histórico versionado, sin evidencia nueva de ese run. Los logs no permiten determinar cuántas fuentes llegaron a consultar o extraer en #31.

## Corrección

- 5 s de conexión, 10 s de inactividad de lectura; 60 s absolutos por fuente y 600 s globales.
- Hasta cuatro workers concurrentes en procesos independientes. Se detienen por grupo para incluir pdftotext; no se espera un hilo bloqueado al salir.
- Logs inmediatos por portal y heartbeat cada cinco segundos: URL, fase, duración, publicaciones y errores.
- Checkpoints atómicos por página/fase, resumen incremental y eventos JSONL. Al cortar por plazo o señal se preservan todas las publicaciones encontradas; las fuentes que no arrancaron quedan NO_INICIADA.
- Categorías RED / EXTRACCION / INTERNO / PRESUPUESTO, HTTP status cuando corresponde y marca de timeout. Detectar HTML sin publicaciones no significa funcionar ni ausencia comprobada de novedades.
- Diagnóstico automático del PR en Actions y manual en rama, con permisos de lectura, job de 15 minutos y paso de 12. Disponibilidad de fuentes se informa separada de las pruebas. Artefactos en una ruta nueva de work, sin copiar una auditoría histórica como si fuera nueva.
- No se cambia radar.py, el historial ni los resultados de producción. No se agrega filtro ni límite de oportunidades. El límite temporal solo hace explícita la cobertura parcial de una ejecución.

## Verificación real desde el executor

Nueva ejecución con la configuración predeterminada: 36 fuentes configuradas, 36 consultas iniciadas y finalizadas. 0 funcionaron; 36 fallaron por red; 0 llegaron a procesar respuesta; 0 errores de extracción observados; 0 timeouts; 0 fuentes sin iniciar. Duración aproximada: 1,5 segundos. Los errores URLError/Operation not permitted ocurren antes de obtener contenido; curl también falla al conectar al proxy. Esto no demuestra que los portales estén caídos ni comprueba su extracción.

La auditoría actual está en inventario/verificacion.json. Esta medición es independiente de #31; no se atribuyen sus conteos al run cancelado. El diagnóstico de Actions de esta actualización tendrá sus propios conteos y artefactos.

## Pruebas

41 pruebas descubiertas: 40 aprobadas en el executor, 1 integración HTTP local omitida porque el entorno prohíbe abrir sockets locales. Las pruebas nuevas cubren workers lentos y que ignoran SIGTERM, timeout de fuente y global, concurrencia efectiva, bloqueo de red, fallo de extracción, caída del worker, cancelación, guardado durante la ejecución y conservación de 500 publicaciones parciales. Se prueban por separado la configuración de conexión/lectura y las categorías de error. La integración HTTP con portales locales rápido/lento/403/HTML vacío se ejecuta en Actions, donde se permite crear el servidor local.

Los fixtures son sintéticos y no cuentan como fuentes oficiales verificadas. El PR #1 permanece abierto y sin fusionar.
