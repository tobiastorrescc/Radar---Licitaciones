# Recuperación de fuentes críticas — Issue #14

Resultado parcial, verificado el 5/11/2026. PR #1 abierto, sin merge. **EPE, Gestiones de Compras y Boletín Oficial SF continúan inaccesibles desde GitHub Actions: no están recuperados.** No se atribuye la causa a una prohibición de acceso cuando sólo hay timeout o errores de servidor/TLS.

## Resultado comercial

- Ocho fuentes comparadas: **1 → 2 operativas**, **2 → 1 parciales**, cinco inaccesibles. Sin altas nominales nuevas.
- **14 → 16 convocatorias abiertas observadas**, incluidas dos cuya vigencia antes no pudo extraerse. No se perdió ningún registro de la captura de control.
- **Cero publicaciones genuinamente nuevas con fecha comprobada**. Las dos vigencias recuperadas ya tenían registro: no se cuentan como publicaciones nuevas del día.
- 93 → 213 procedimientos reconocidos en esta muestra. Los 120 adicionales son 119 vencidos y uno de vigencia desconocida; se excluyen del listado comercial. Este crecimiento histórico no es la métrica de éxito.
- El CSV `abiertas_observadas.csv` contiene las 16 abiertas, sin recortes. El artefacto conserva todos los registros y los checkpoints, incluidos candidatos, vencidos y desconocidos. El catálogo heredado contiene otras oportunidades, pero esta prueba no revalida fuentes ajenas al lote.

### Dos vigencias recuperadas

| Organismo | Procedimiento y objeto | Apertura oficial | Evidencia |
|---|---|---|---|
| Poder Judicial ER | Solicitud de Cotización **268/2026**, servicio de viandas para juicios por jurados en Gualeguay | **6/11/2026, 11:00** | [Aviso oficial](https://www.jusentrerios.gov.ar/compras/solicitud-de-cotizacion-no-268-26-por-contratacion-de-servicio-de-viandas-para-los-juicios-por-jurados-a-realizarse-en-la-ciudad-de-gualeguay/) |
| Poder Judicial ER | Concurso de Precios **5/2026**, pintura y reparaciones de Tribunales de La Paz. Presupuesto publicado: **ARS 82.950.075,67** | **6/11/2026, 10:30** | [Aviso oficial](https://www.jusentrerios.gov.ar/compras/concurso-de-precios-no-05-26-por-obra-pintura-y-reparaciones-tribunales-de-la-paz/) |

Se respeta la distinción entre apertura y cierre de presentación. Los avisos indican recepción en Oficina de Compras y Asesoramiento del Poder Judicial, planta baja, Tribunales de Paraná. Si no publican un horario límite independiente, no se inventa. La vigencia corresponde a la fecha de observación; estos enlaces no garantizan disponibilidad después de la apertura.

## Estado real por fuente

| Fuente | Control → después | Procedimientos después | Abiertas | Segundos integrados | Incidencia |
|---|---|---:|---:|---:|---|
| EPE | Inaccesible → inaccesible | 0 | 0 | 3,15 | EOF/TLS; otras pruebas oficiales devuelven HTTP 500 o respuesta vacía |
| Gestiones SF | Inaccesible → inaccesible | 0 | 0 | 9,03 | Timeout, también con conexión de 12 s en diagnóstico posterior |
| Boletín SF | Inaccesible → inaccesible | 0 | 0 | 43,48 | Timeout en raíz y cuatro secciones diarias completas |
| Cañada de Gómez | Inaccesible → inaccesible | 0 | 0 | 0,31 | HTTP 403; también API pública de páginas. No se elude |
| Compras UNR | Inaccesible → inaccesible | 0 | 0 | 1,51 | HTTP 403; la ruta alternativa institucional sólo incrusta el mismo portal |
| ASSA | Operativa → operativa | 3 | 3 | 3,75 | API pública con número, objeto y apertura; sin errores en este lote |
| Aeropuerto Rosario | Parcial → parcial | 152 | 5 | 120,04 | Corte del supervisor durante paginación histórica; se preservan 153 registros brutos, uno no confirmado |
| Poder Judicial ER | Parcial → operativa | 58 | 8 | 104,73 | Recorrido completado sin errores; validación final adicional: **84,68 s**, mismo total, objeto de La Paz conservado |

Tiempo del barrido integrado: **123,26 segundos**, frente a 63,78 del control. El aumento proviene del presupuesto explícito de 120 s para dos fuentes antes cortadas a los 60 s; no es una mejora de velocidad global. No se afirma cobertura completa de todos los portales de estos organismos.

## Correcciones implementadas

1. **Boletín SF:** siembra directa de la sección completa `ver.php?seccion=AÑO/AAAA-MM-DDlicitaciones.html`, hoy y tres días anteriores, primero la edición más reciente. No depende de avisos destacados ni de navegar el calendario. El caso histórico de Ramayón sigue como regresión, nunca como oportunidad vigente. Se reconoce la numeración oficial EPE de diez dígitos en avisos del Boletín con organismo explícito.
2. **Gestiones SF:** lectura reutilizable de tablas y CSV cuyo enlace publique el portal. Conserva organismo por fila, objeto, número/año, apertura y fechas independientes cuando existen. HTML de error, columnas irreconocibles y filas incompletas generan error de extracción, no un listado vacío. No se inventó un endpoint de exportación: **la URL exacta de CSV sigue pendiente porque el portal no abre en vivo**. Sus pruebas son de formato; no acreditan recuperación actual.
3. **EPE:** reintento acotado de EOF TLS, además de errores transitorios ya soportados; sin desactivar certificados ni reintentar restricciones 403/429. Se probaron listados, compras, bundles Nuxt publicados y la API `/app2/api` expuesta en el HTML oficial histórico. Ninguna ruta extrajo procedimientos en vivo.
4. **PJER y Aeropuerto:** hasta tres lecturas HTTP de fichas por fuente en paralelo, análisis y checkpoints secuenciales; presupuesto duro por fuente de 120 s, supervisor global intacto. PJER lee fichas antes de archivos secundarios. El bloque administrativo de un detalle ya no reemplaza el objeto concreto del mismo llamado.
5. **Alertas:** EPE, Gestiones y Boletín fallidos/parciales quedan en `alertas_fuentes_criticas`, auditoría JSONL y anotaciones `warning` de Actions. La ejecución puede continuar conservando resultados de las otras fuentes. No se activaron correo ni servicios externos.
6. **Contraste aislado:** el workflow de investigación acepta capturas de barrido para restaurar una copia del respaldo, generar informes y repetir sin red. No se cambió el programador. El sondeo permite una lista explícita vacía de raíces para consultar únicamente las peticiones indicadas.

## Evidencia y pruebas

- [Control anterior, ocho fuentes](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42102758579).
- [Extracción integrada corregida](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42106222026), artefacto `cobertura-42106222026`.
- [Persistencia y segunda pasada](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42106834312): **cero novedades y cero eventos adicionales**; `produccion_y_respaldos_intactos=true`.
- Primera comparación contra el respaldo: 97 recuperaciones de línea de base, 32 datos completados, 24 modificaciones, dos primeras detecciones sin fecha de publicación y 58 sin cambios. Estas categorías no equivalen a publicaciones nuevas verificadas. Una de las primeras detecciones sin fecha es abierta (obra de Villa Mantero) y la otra tiene vigencia desconocida; no se presentan como inéditas con fecha confirmada.
- [Validación final PJER y transporte de fuentes críticas](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42107794847): 58 procedimientos, ocho abiertos, objeto completo de La Paz. Los cuatro sondeos críticos siguen fallando aun con TLS 1.2/IPv4/HTTP 1.1 y tiempos de conexión mayores. Una respuesta 200 de una página institucional o API de metadatos no cuenta como extracción de licitaciones.
- [CI del código final](https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42107794794): **425 pruebas Python ejecutadas, 424 aprobadas y una opcional omitida; 28 pruebas Node aprobadas**. Regresiones: CSV/tabla, filas parciales, errores no vacíos, cambio de año del Boletín, Ramayón, numeración EPE, reintento EOF, no reintento de 403/certificado, concurrencia sin solicitudes duplicadas y conservación del objeto de La Paz.
- Cero OCR nuevo. Capturas reutilizadas para el contraste; archivos de resultados con hash en `huellas_capturas.json`. `rutas_investigadas.json` documenta rutas oficiales y errores, sin promover capturas HTTP a fuentes operativas.

## Pendiente prioritario

La prioridad principal **sigue sin resolverse**: obtener acceso funcional desde Actions a EPE, Gestiones y Boletín. Se necesitan respuestas oficiales utilizables para comprobar CSV y la sección completa diaria. Los fallos observados no permiten concluir que los portales carezcan de convocatorias. Próxima iteración: contrastar disponibilidad en una ejecución posterior y solicitar a los organismos un listado/exportación público si persiste el fallo; conservar los adaptadores preparados sin declararlos operativos.

Aeropuerto necesita terminar el recorrido paginado sin consumir el presupuesto en fichas vencidas, conservando los avisos ya descubiertos y sin omitir páginas con llamados vigentes. Cañada y UNR requieren rutas públicas de publicaciones accesibles o aclaración del organismo sobre los 403. No se sortearon restricciones.

No se modificaron main, el historial de producción, archivos de respaldo ni el programador. No se crearon servicios pagos ni se fusionó el PR. Las métricas corresponden exclusivamente a esta muestra auditada, no a cobertura territorial global.
