# Casilda (Santa Fe) — fuente para integrar

- Organismo: Municipalidad de Casilda
- URL oficial: https://www.casilda.gob.ar/web/licitaciones-casilda/
- Tipo: licitaciones municipales, decretos, anexos, adjudicaciones y posibles segundos llamados.
- Prioridad: alta; cobertura diaria en Santa Fe.
- Estado de integración: URL incorporada al inventario de pendientes; aún no implica crawler operativo.

## Requisitos de integración

1. Incorporar la URL al catálogo real de fuentes del agente y programar lectura diaria.
2. Descubrir enlaces de avisos y documentos; extraer objeto, expediente/número, publicación, apertura y fecha límite de presentación.
3. Registrar todos los avisos sin filtros por rubro o monto, pero reportar como oportunidades únicamente aquellos con presentación aún vigente.
4. Detectar reaperturas, segundos llamados y desiertas; no confundir adjudicaciones ni antecedentes vencidos con oportunidades abiertas.
5. Desduplicar frente al catálogo histórico y conservar URL directa y evidencia.
6. Registrar forma de pago si figura, sin bloquear descubrimiento si falta.
7. Probar con publicaciones reales y documentar fecha de última lectura, errores y cantidad de oportunidades nuevas.

No modificar main ni flujos productivos hasta validar la integración.
