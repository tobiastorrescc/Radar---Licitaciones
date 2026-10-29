# Piloto diario instalado y habilitado

**Estado: activado tras validación real, sin fusionar el PR #1 ni modificar el historial de producción.** Main quedó en `dfca1a52c5371929ce6c07741a88fd209a7da852`. Desde el commit inicial `dd96ba9`, el único archivo añadido/modificado en main es `.github/workflows/programar-piloto.yml`.

- Ejecución diaria: **08:00 America/Argentina/Buenos_Aires**, actualmente 11:00 UTC.
- Supervisión: **09:30 Argentina**, actualmente 12:30 UTC, y notificación explícita al finalizar el piloto.
- Agente y datos diarios: rama **mejora/radar-auditable**; main sólo coordina, supervisa y crea alertas.
- Workflow anterior **radar-diario.yml: disabled_manually**. Su archivo y datos históricos no se borraron ni editaron.
- PR #1 abierto, sin merge. No se contrató servidor, servicio de cron, correo ni otro proveedor; se usa GITHUB_TOKEN.

[Archivo exacto instalado](despliegue/github-actions/programar-piloto.yml.instalado) · [Manifiesto y hash](despliegue/github-actions/manifesto.json) · [Controlador de validación real #9](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40859148864).

## Qué se corrigió al instalar

La primera instalación `8f1944b` fue rechazada antes de ejecutar jobs: GitHub no permite que un workflow escuche su propio nombre. La corrección `fbace88` quedó guardada en main y se incorporó su regresión a la rama. No se volvió a instalar ese error ni se activó su cron.

El cron viejo y el piloto compartían el ID de radar-diario.yml. Deshabilitar ese ID habría bloqueado ambos. El worker pasó a programar-piloto.yml **sólo en la rama del piloto**, y el coordinador usa ese archivo en main con otra definición. Así pudo retirarse el workflow viejo sin editar más archivos de main ni escribir su historial.

Se separó la cola de CI de la del piloto para que el controlador no bloquee a la consulta que está esperando. Se canceló únicamente un ensayo CI obsoleto, nunca el piloto ni un run de main. Un intento de retirar de nuevo el cron ya deshabilitado recibió 403; se hizo idempotente la operación y se añadió una regresión.

La señal workflow_run no se entregó con estas definiciones por rama. Se sustituyó por **repository_dispatch**: al terminar, un job pequeño de la rama avisa a main con el ID de la ejecución. Main consulta sus metadatos y pasos por API, comprueba rama, repositorio, tipo, título y respaldo; no ejecuta código ni artefactos del emisor. Una prueba de sólo notificación validó ese recorrido sin volver a consultar fuentes.

Durante la publicación, el bot añadió un incremento del historial. La protección de actualización de rama rechazó una referencia anterior; se reconstruyó el commit sobre el respaldo recién publicado, sin force ni pérdida de ese incremento.

## Pruebas y resultados

**293 pruebas aprobadas en Actions: 265 Python y 28 JavaScript, cero omisiones.** Incluyen autorreferencia, colas distintas, retirada idempotente, duplicados, POST incierto, cierre eventual, aviso explícito y notificación sin consulta, además de conectores, pagos y persistencia. El controlador final terminó success.

| Comprobación real | Resultado / evidencia |
|---|---|
| Despacho desde main | [#4](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40856695843) aceptó el piloto de la rama |
| Consulta diaria del piloto | [#5](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40856721766), success; 74 fuentes consultadas y finalizadas |
| Restauración | RESTAURADO True desde la cadena diaria de Git |
| Historial | 3.691 → **3.697 procedimientos**, 3.750 → **3.758 versiones**; cero identidades anteriores repetidas como nuevas, cero pérdidas ni versiones previas alteradas |
| Respaldo | Tercer segmento, exportación/restauración de prueba y push sin force correctos |
| Aviso sin nueva consulta | [#11](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40859266638), success; job de consulta omitido |
| Supervisor automático | [#12](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40859338554), repository_dispatch real; job ejecutado y COMPLETADO_CON_RESPALDO |
| Supervisión manual | [#13](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40859382969), success |
| Fallo deliberado | [#14](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40859434053), failure esperado, sin despachar otra consulta |
| Alerta real | [Issue #2](https://github.com/tobiastorrescc/Radar---Licitaciones/issues/2) creado por github-actions[bot], comprobado y cerrado como prueba resuelta |
| Repetición del despacho | [#15](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40859484632), success: **una sola consulta diaria**, sin crear otro piloto |
| Producción | Hashes de los archivos antes/después idénticos; la comparación de main sólo muestra el archivo programador |

La consulta real tuvo seis recuperaciones históricas de línea de base, dos cambios del contenido observado y un dato completado. No se anuncian como seis convocatorias recién publicadas. El estado global fue **COMPLETA_CON_INCIDENCIAS**: 34 fuentes operativas estrictas, 14 parciales, 14 bloqueadas, once pendientes y una sin publicaciones confirmada. Que el proceso termine correctamente no demuestra que todos los portales funcionen.

El SQLite descargado pasó quick_check. Su hash lógico coincide con el índice diario: `af90259db6892b9d7821b4d3a03acfc5ecefb6cc9e1ea5599eaa825684ef5815`. El incremento es `000002-7a8f4d882abed58cafe821337a528c4119c332789036a7c3169c101e6888718d.json.gz`. Se conserva junto con base e incrementos anteriores en `piloto_respaldo/diario/`; los artefactos son una copia adicional de 90 días, no el único respaldo.

## Consulta diaria y alertas

Abrir [Actions del programador/piloto](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/workflows/programar-piloto.yml). Las consultas de datos se ejecutan en mejora/radar-auditable y su título termina en **programado**. Descargar **radar-controlado** y abrir **index.html**.

[Informe íntegro de la primera consulta real](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/40856721766/artifacts/12889369516): 3.697 registros conservados, todas las detecciones/cambios, auditoría, enlaces/pliegos, condiciones de pago comprobadas o no informadas y 165 registros no observados en esa consulta señalados. Las 47 abiertas y veinte próximas a vencer se basan en los últimos datos conocidos. Sin filtros por rubro, monto o financiación y sin cálculos automáticos de rentabilidad.

Las incidencias de infraestructura, ausencia/incompleto, respaldo no confirmado y fallos se avisan en Issues y quedan visibles como runs fallidos. Hay un Issue por fecha, actualizado/reabierto si aparece otra incidencia. Los errores parciales por portal siguen en el reporte. Las notificaciones por correo dependen de Watch y de las preferencias personales de GitHub: no se cambió esa configuración ni se asegura entrega de email.

En la página del workflow de main se puede ejecutar manualmente:

- `accion=ejecutar`: solicitar o reconocer el piloto del día, sin duplicarlo.
- `accion=supervisar`: comprobar la consulta y el respaldo sin consultar portales.
- `accion=probar_alerta`: fallo deliberado autorizado para verificar avisos, sin consulta ni cambios de historial.

No usar el antiguo radar-diario.yml deshabilitado ni activar la alternativa externa. El archivo tiene una función distinta por rama; la interfaz manual del coordinador se usa **en main**. Una futura fusión del PR necesitará preservar el coordinador de main: no se debe reemplazar por la definición del worker. El PR permanece sin fusionar. GitHub marca conflicto entre esas definiciones del archivo; no impide el piloto ni sus pruebas por push, pero debe resolverse preservando el coordinador antes de cualquier fusión futura.

## Estado del horario y límites

La habilitación automática se hizo **después** del ensayo exitoso; el cambio final en main sólo pasó la guarda del horario de false a true. La primera pasada del cron posterior a esta habilitación está prevista para el **29/10/2026 a las 08:00 de Argentina**. Al activar todavía no se había observado ese evento por reloj; la consulta manual de ese día ya existe y el cron debe reconocerla sin repetirla. La supervisión horaria siguiente será a las 09:30.

GitHub puede retrasar o descartar cron; no se promete puntualidad con SLA ni avisos durante una caída total del proveedor. Los runners estándar del repositorio público no requieren servidor ni suscripción adicional; revisar almacenamiento y cache. El aviso final suma un job breve y no deja un runner esperando toda la consulta.

Para pausar el horario puede establecerse RADAR_PILOTO_PROGRAMADOR_HABILITADO=false; no se tocó esa variable, observada vacía durante el ensayo. Deshabilitar por completo programar-piloto.yml detiene también su worker. Antes de reactivar el workflow antiguo hay que detener el nuevo; el programador comprueba que el antiguo siga retirado y falla sin despachar si se lo vuelve a habilitar.
