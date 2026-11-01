# Alcance permanente y meta del radar

La meta comercial es un promedio de al menos **20 publicaciones genuinamente nuevas por día entre las tres jurisdicciones juntas**, condicionado al volumen real. No son20 por provincia ni un límite de resultados. Si se encuentran50, se informan50. La ausencia de una muestra manual o de una ejecución no equivale a cero omisiones ni a cero publicaciones.

## Territorio

Santa Fe y Entre Ríos: toda la provincia, municipios y comunas pequeñas, compras provinciales, boletines, hospitales/SAMCo, universidades, empresas públicas, entes y organismos descentralizados. Prioridad explícita al portal y Boletín de Santa Fe que publica avisos como Ramayón, además de EPE, ASSA y publicaciones municipales. Entre Ríos incluye Paraná, Victoria, Concordia, CAFESG, Chajarí, La Paz, San José, Concepción del Uruguay, Gualeguay, Gualeguaychú, Colón, Crespo, Federación, Diamante, Nogoyá, Villaguay, Rosario del Tala, Seguí, Viale, Oro Verde y localidades pequeñas.

Buenos Aires: municipios dentro del alcance aproximado de280km desde Rosario; incluidos San Nicolás, Ramallo, San Pedro, Baradero, Pergamino, Colón y Rojas. El padrón conserva distancia geodésica y estado pendiente de comprobación por ruta cuando corresponde: una distancia geodésica menor no prueba una distancia vial de280km. Las prioridades y la rotación territorial existentes intercalan las tres provincias. Esto es un objetivo exhaustivo y permanente, no una declaración de cobertura ya alcanzada.

Revisar portales provinciales, boletines, sitios municipales, noticias, decretos, licitaciones públicas/privadas, concursos, directas/menores, solicitudes de cotización, segundos llamados y reaperturas. Un aviso oficial válido se registra aunque falten pliego, presupuesto u objeto detallado. Descubrimiento precede al enriquecimiento. No se excluyen oportunidades por rubro, monto, financiación, pago ni viabilidad. No se calculan costos o rentabilidad automáticamente.

## Informe diario

`metricas_territoriales.json` y el informe Markdown muestran total confirmado y desglose por Santa Fe, Entre Ríos y Buenos Aires. Separan abiertas observadas de abiertas conservadas sólo por historial, vigencia desconocida, pago rápido documentado, errores de fuente y omisiones de la muestra manual. El catálogo, CSV y secciones de primeras detecciones, recuperaciones y cambios conservan todos los registros.

La meta sólo cuenta `NUEVO_CONFIRMADO` con publicación comprobada dentro de la ventana reciente de72horas por día disponible, y deduplicación por identidad, agregando todas las ejecuciones del día argentino. Una repetición no reinicia el contador diario. Históricas, modificaciones, datos completados, duplicados y primeras detecciones sin fecha no integran la meta; siguen visibles en secciones propias. «Primera detección» no equivale a fecha de publicación.

El promedio se calcula sobre siete días calendario con ejecuciones disponibles; mientras falten días se informa pendiente y se muestra por separado el promedio de los días observados. No se imputan los días sin ejecución como cero ni se garantiza el volumen editorial de los organismos. El promedio mide detecciones confirmadas del radar, no la totalidad de las publicaciones oficiales.

Pago rápido exige evidencia documental y contado, contra entrega o todos los plazos nominales comprobados de hasta15días; se excluyen opciones condicionales/mixtas de este contador. Se conservan unidades y eventos iniciales en las fichas. Hasta15días hábiles no promete15días corridos de recuperación ni acreditación inmediata.

## Contraste manual

`inventario/auditoria_manual_tres_provincias.json` conserva cada publicación y URL, fecha de revisión, datos comprobados y límites. El informe distingue detectada, omitida y correspondencia ambigua, por provincia. No tener muestra devuelve sin medición, no cero omisiones. Los avisos históricos sirven como control técnico y no se presentan como novedades comerciales. Las páginas sin convocatorias comprobadas no se contabilizan como localidades cubiertas.

La muestra inicial es dirigida y pequeña, no un censo independiente de todos los municipios. La revisión debe ampliarse y renovarse progresivamente. Las revisiones antiguas se señalan mediante su fecha; no prueban vigencia actual. Los bloqueos y falta de documentación se conservan como pendientes y nunca como ausencia de novedades.

## Conservación

PR#1 y rama `mejora/radar-auditable`. No fusionar, modificar main/producción, respaldos ni programador. Las pruebas reales y comparaciones se ejecutan en copias aisladas bajo `work/`. El reporte se prepara sin activar correo, credenciales ni servicios pagos.

La rotación de descubrimiento conserva también las localidades que ya tienen un conector operativo. Revisa sus portales institucionales y busca fuentes complementarias: un archivo extraído correctamente no acredita cobertura permanente de la localidad. Se reutiliza la cola y los límites existentes, sin modificar el programador.
