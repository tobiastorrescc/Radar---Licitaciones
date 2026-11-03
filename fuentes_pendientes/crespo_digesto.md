# Fuente candidata prioritaria — Digesto Municipalidad de Crespo (Entre Ríos)

URL canónica: https://municrespo.gov.ar/digesto/consulta.php?s=consulta
Jurisdicción: Crespo, Entre Ríos, Argentina.
Estado: pendiente de integración y prueba del extractor; no declarar fuente operativa hasta validar extracción de registros.
Prioridad: alta; revisión diaria.

## Objetivo
Descubrir decretos de licitaciones públicas y privadas, concursos de precios, contrataciones directas, segundos llamados, reaperturas y declaraciones de desierta. Navegar resultados, paginación y vínculos a decretos/PDF. Registrar número de procedimiento, objeto, organismo, fecha de publicación, apertura/cierre, presupuesto, URL de aviso y documento. Si faltan pliego/presupuesto/pago, registrar aviso de todos modos y enriquecer después.

## Criterios
- Incluir en reporte comercial únicamente procedimientos con presentación todavía posible y vigencia comprobada; si la fecha es incierta, enviar a verificación, no declarar abierto.
- Sin filtros por rubro o monto.
- Dedupe por organismo + tipo + número + año, con comprobación de objeto y anexos.
- No confundir decreto de adjudicación con convocatoria abierta.
- Marcar cambios que habiliten nueva presentación.
- Verificar acceso y extracción real; HTTP 200 por sí solo no basta.
- No alterar main, producción, respaldos ni programador al implementar desde PR #1.

Solicitud del usuario: incorporar esta fuente al radar de descubrimiento y validar oportunidades vigentes.
