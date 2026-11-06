# Recuperación y controles sin escribir producción

## Descarga e importación

Se reutiliza el importador existente; no se agrega OCR. Los identificadores son `fuente-003` (EPE), `fuente-087` (Gestiones SF) y `fuente-060` (Boletín SF).

Desde un equipo donde la URL oficial sea accesible:

```sh
python tools/importar_oficiales.py --fuente fuente-087 --url 'URL_OFICIAL_COMPROBADA_DEL_CSV' --bandeja entradas_oficiales
```

`URL_OFICIAL_COMPROBADA_DEL_CSV` es un marcador a sustituir con el enlace observado en el portal. Todavía no se pudo comprobar una URL de exportación CSV; no se ha inventado un endpoint.

Para un archivo ya descargado:

```sh
python tools/importar_oficiales.py --fuente fuente-087 --url 'URL_OFICIAL_DE_ORIGEN' --archivo /ruta/exportacion.csv --bandeja entradas_oficiales
python tools/importar_oficiales.py --fuente fuente-060 --url 'URL_OFICIAL_DE_LA_EDICION' --archivo /ruta/edicion.pdf --bandeja entradas_oficiales
python tools/importar_oficiales.py --bandeja entradas_oficiales --salida work/importados-control
```

Se admiten CSV, HTML y PDF con texto, hasta 12 MB. La última orden solamente procesa archivos locales. Conserva URL, fecha de captura cuando existe y SHA-256; no atribuye la fecha de registro a la publicación. Un archivo aportado sin recibo comprobable se incorpora como pendiente de revalidación, nunca como oportunidad comercial vigente. No editar recibos para simular una descarga HTTP. Para compartir una captura hay que conservar el archivo **y** su JSON, sin credenciales ni datos privados.

La bandeja ya se lee en el barrido y en el radar controlado. Los recibos se guardan en el estado incremental y sus respaldos para evitar reprocesar archivos sin cambios. No se modifica `piloto_respaldo/diario` con estas instrucciones.

## Navegador controlado

`.github/workflows/gestiones-navegador.yml` utiliza Chrome estándar del runner y Playwright, con TLS normal y presupuesto de tiempo. No añade un programador ni modifica el existente. Se dispara sólo al cambiar `tools/plan_gestiones_navegador.json` en la rama de mejoras. Registra estados HTTP, tiempo, MIME, tamaño, campos de formularios y enlaces públicos; no registra cookies ni credenciales.

Si la página carga, busca una exportación CSV publicada y recorre la paginación real. Conserva capturas HTML importables con recibo. Una repetición de página, un total publicado mayor a las filas extraídas o un límite de tiempo producen resultado parcial. Los máximos de recursos no se interpretan como cobertura completa.

La prueba real de esta etapa no llegó a cargar ningún portal: el navegador queda implementado, **no validado como vía de recuperación**. No repetir indefinidamente consultas a las mismas rutas inaccesibles.

## Boletín completo

El lector consulta directamente secciones diarias de Licitaciones y busca enlaces oficiales a documentos, con respaldo PDF de la edición actual y ventana acotada de días hábiles. El parser procesa la sección completa disponible, incluidos avisos sin número y encabezados repetidos del PDF, sin exigir pliego, presupuesto ni pago. Conserva el enlace de la edición y el texto del aviso. Los fallos de descarga y límites siguen siendo errores; no certifican una edición sin avisos ni una cobertura completa.

## Comparación con controles manuales

```sh
python tools/comparar_control_manual.py --automaticas work/barrido/resultado.json --manuales inventario/auditoria_manual_tres_provincias.json --salida work/control-manual
python tools/revalidar_epe.py --barrido work/barrido/resultado.json --salida work/control-epe
```

El comparador admite CSV o JSON. Para un control comprobado se necesitan organismo, objeto, URL, `comprobada=true`, `evidencia_url` y `fecha_revision`; número y fechas se agregan si constan. Emite grupos automáticas, manuales y ambas, con todas las omisiones en CSV. La causa es probable hasta investigar el extractor. Las fuentes fuera del lote y los controles antiguos se señalan separadamente; no representan una auditoría territorial vigente.

Las 17 EPE se contrastan contra una sola consulta compartida, sin 17 descargas idénticas. Una apertura futura archivada no acredita recepción vigente hoy. El informe comercial exige cierre de recepción futuro explícito o cláusula expresa que permita presentar hasta la fecha y hora de apertura. Las demás permanecen en el catálogo y en `presentacion_pendiente.json`.
