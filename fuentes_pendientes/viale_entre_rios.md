# Viale — Entre Ríos

URL canónica: https://viale.gob.ar/pliegos/
Organismo: Municipalidad de Viale, Entre Ríos.
Prioridad: alta.
Estado: fuente candidata registrada; integración al crawler y validación de extracción pendientes.

Implementación requerida:
- Revisar diariamente listado y paginación, enlaces de detalle y PDF.
- Detectar licitaciones, cotejos de precios y concursos sin filtros de rubro o monto.
- Extraer objeto, número, fecha de publicación, apertura/cierre, modalidad de presentación, presupuesto y pago si constan.
- Publicar únicamente oportunidades con plazo vigente verificado; no confundir fecha de publicación con cierre.
- Deduplicar por organismo, procedimiento, año y URL.
- Incorporar al inventario operativo y pruebas de regresión una vez comprobada extracción real.
- No alterar main, producción, programadores ni respaldos sin validación.
