# Persistencia y disparador del piloto

El piloto permanece en `mejora/radar-auditable`, PR #1. No se fusiona ni se activa producción.

## Respaldos duraderos

`tools/respaldo_piloto.py` guarda una base inicial y segmentos incrementales comprimidos en `piloto_respaldo/diario/`. El índice ordena los segmentos, sus SHA-256, el hash lógico de las tablas, los conteos y las ejecuciones respaldadas. Cada segmento referencia el hash del anterior. Los archivos se versionan en la misma rama mediante commits limitados a ese directorio; no caducan con los artefactos de Actions.

Se conserva el estado actual, todas las versiones, eventos, auditorías, ejecuciones y bases por fuente. El primer segmento contiene todo; los siguientes incluyen filas nuevas o actualizadas y reutilizan el historial previo. Antes de publicar se restaura la cadena completa en un directorio temporal y se comprueba igualdad exacta de contenido. Una pérdida o alteración de historia inmutable rechaza el nuevo respaldo. La restauración falla si falta un segmento, no coincide su hash o ya existe estado en destino; no reinicia una base vacía silenciosamente.

Los artefactos SQLite siguen disponibles como copia adicional y para consultar reportes, pero dejan de ser el almacenamiento primario del historial. La retención de 90 días afecta esos artefactos, no los segmentos en Git. El respaldo durable depende de conservar el repositorio/rama: conviene mantener además una copia externa del repositorio; esta etapa no configura otro proveedor ni afirma redundancia entre proveedores.

## Dos ejecuciones independientes

El PR solicita dos `workflow_dispatch` reales del workflow diario. Cada una tiene su propio runner y consulta las fuentes. La primera importa explícitamente el estado auditado de #116 cuando el canal está vacío, valida su procedencia e integridad, publica su segmento en Git y termina. Se conserva la evidencia de la prueba importada sin presentarla como resultado de la nueva consulta. La segunda hace un nuevo checkout, restaura la cadena y continúa sin inicializar. Se comprueba que no desaparezcan procedimientos ni versiones anteriores, que haya una nueva corrida y que las identidades existentes no reaparezcan como nuevas.

Las validaciones usan `piloto_respaldo/validaciones/<SHA>/`, separado de `piloto_respaldo/diario/`. No reemplazan el estado del piloto diario ni producción. Los resultados quedan en `continuidad.json`, el resumen de Actions y los artefactos de cada consulta.

## Disparador diario

El mismo punto de entrada acepta `modo=controlado`, `canal=piloto`, sobre esta rama. La primera vez requiere `inicializar=true` cuando no existe respaldo o estado migrable. El input opcional `semilla_run` permite importar un artefacto con estado completo de una ejecución exitosa de este mismo workflow y rama; no puede sobrescribir un respaldo existente. En adelante se restaura Git y se deja `inicializar=false`. El workflow sólo persiste en `mejora/radar-auditable` y tiene guardas separadas de producción.

El cron preparado para las 08:00 Argentina sigue sujeto a la limitación de GitHub: sólo se ejecuta desde la rama predeterminada. Las pruebas validan el disparador API de esta rama, no activan un cron en ella. Para ejecutarlo cada día sin merge se necesita un programador autorizado que invoque ese `workflow_dispatch`; no se modifica `main` para conseguirlo.

```sh
gh workflow run radar-diario.yml --ref mejora/radar-auditable \
  -f modo=controlado -f canal=piloto -f inicializar=true -f semilla_run=40688224634
```

No usar inicialización para resolver una falla de integridad. Conservar segmentos e índice juntos. Todos los procedimientos y oportunidades se mantienen, sin filtros comerciales; las condiciones de pago requieren respaldo y no se calcula rentabilidad.
