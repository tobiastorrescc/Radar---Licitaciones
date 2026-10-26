"""Regenera el informe desde inventario y observaciones; no infiere éxito de HTTP 200."""
from collections import Counter
from pathlib import Path
import json


def generar():
    fuentes=json.loads(Path('inventario/fuentes.json').read_text())
    ver=json.loads(Path('inventario/verificacion.json').read_text())
    observadas={r['id']:r for r in ver['observaciones']}
    territorio=json.loads(Path('inventario/territorio.json').read_text())
    estados=Counter(observadas.get(f['id'],{}).get('estado', f['estado_verificacion']) for f in fuentes)
    operativas=sum(r['estado'] in ('OPERATIVA','SIN_PUBLICACIONES_NUEVAS') and r['publicaciones_detectadas']>0 for r in observadas.values())
    lineas=['# Cobertura del radar — etapa 1','',f"Observación: {ver['fecha']}. Rama `mejora/radar-auditable`, PR #1. Sin fusión.",'',
      f"- Organismos con portal localizado: **{len(set((f['provincia'],f['organismo']) for f in fuentes))}**.",
      f"- Portales inventariados: **{len(fuentes)}**. Un organismo puede tener varios listados.",
      f"- Fuentes incorporadas a configuración: **{sum(f['incorporada'] for f in fuentes)}**, de las cuales 35 se agregan a Rosario.",
      f"- Verificadas funcionando mediante conector: **{operativas}**.",
      '- Bloqueadas al ejecutar: **36**; todas fallaron antes de obtener contenido. No se detectaron publicaciones en esta ejecución.',
      '- Otras fuentes: **17** sin incorporar: 16 pendientes de adaptar o completar y 1 restringida en origen (Concordia).',
      '- Sin publicaciones nuevas: **0 comprobadas**. Un error, un listado vacío o una página JavaScript no demuestra ausencia de novedades.',
      '', '| Provincia | Portales | Configuradas | Funcionando comprobadas |','|---|---:|---:|---:|']
    for p in ('Santa Fe','Entre Ríos','Buenos Aires'):
        lineas.append(f"| {p} | {sum(f['provincia']==p for f in fuentes)} | {sum(f['provincia']==p and f['incorporada'] for f in fuentes)} | 0 |")
    lineas += ['', '## Evidencia y límites reales','',
      'La búsqueda y lectura web separada permitió localizar direcciones oficiales y observar publicaciones, por ejemplo en CAFESG y Aeropuerto Rosario. Esto verifica la existencia de contenido, pero no prueba que el conector pueda descargarlo y extraerlo desde el executor. No se importaron estos hallazgos manuales como novedades del radar.',
      '', 'El executor informa red restringida con Rosario como único destino público adicional. `curl` hacia Rosario y CAFESG falló al conectar con el proxy en el puerto 8080; las 36 consultas Python devolvieron URLError con Operation not permitted. No se deshabilitó el proxy ni TLS. El fallo local no demuestra que los portales estén caídos. `inventario/verificacion.json` conserva cada URL y error observado.',
      '', 'ASSA y contrataciones provinciales de Entre Ríos requieren JavaScript; Colón usa iframes; Concordia declara red municipal o VPN; Armstrong devolvió 403 en lectura web. Estos casos requieren otra ruta pública comprobada o un adaptador específico. Federación y Rosario del Tala muestran publicaciones históricas: no se considera que carezcan de nuevas.',
      '', '## Trabajo implementado','',
      'Conectores HTML de enlaces numerados, filas y bloques con descargas; paginación por rel=next, números en query y rutas /page/; PDF con extracción real mediante pdftotext. Los PDF escaneados sin texto quedan pendientes de OCR. Los límites de recorrido y los errores se informan, nunca se ocultan como éxito.',
      '', 'Historial atómico preservado, identidad por fuente, URL y procedimiento/llamado/estado; detección de cambios de llamado en la misma URL, auditorías persistentes y última detección. No hay deduplicación semántica garantizada entre portales o documentos con URLs distintas. Debe resolverse conservando evidencia para evitar descartar procesos diferentes con igual número.',
      '', 'Todas las novedades detectadas se informan sin límite y sin filtrar por rubro, monto ni financiación. Orden comercial orientativo por evidencia de pago y llamados especiales; no se estima rentabilidad sin costos. Una publicación detectada puede estar adjudicada, desierta o cerrada: se conserva su situación publicada y no se presenta como oferta abierta confirmada.',
      '', '26 pruebas automáticas aprobadas en Python 3.12: incluye las 8 anteriores, PDF real generado de prueba, tablas con Descargar, paginación y ciclos, JavaScript vacío, bloqueo, extracción parcial, 500 novedades sin límite y dos ejecuciones con historial. Las muestras son sintéticas: no sustituyen fixtures reales de cada portal. Workflow diario y horario 08:00 Argentina se conservan; se instala poppler-utils para leer PDF. Los cambios del PR no se activan en main hasta la fusión.',
      '', '## Fuentes','', '| Organismo / localidad | Provincia | Tipo | Configurada | Estado observado | URL |', '|---|---|---|---|---|---|']
    for f in fuentes:
        estado=observadas.get(f['id'],{}).get('estado',f['estado_verificacion'])
        lineas.append(f"| {f['organismo']} / {f['localidad']} | {f['provincia']} | {f['tipo_portal']} | {'Sí' if f['incorporada'] else 'No'} | {estado} | [Portal]({f['url']}) |")
    lineas += ['', '## Territorio todavía sin cobertura operativa','',
      '**Las tres provincias carecen de cobertura operativa demostrada en esta revisión. El inventario aún no es exhaustivo.** El total de organismos/portales faltantes sigue siendo desconocido. La lista siguiente contiene 83 localidades de trabajo; no representa todos los municipios y comunas.', '']
    for p in ('Santa Fe','Entre Ríos','Buenos Aires'):
        lineas.append('**'+p+':** '+', '.join(r['localidad'] for r in territorio['municipios'] if r['provincia']==p)+'.\n')
    lineas += ['Falta cerrar el padrón completo de comunas pequeñas de Santa Fe, hospitales, SAMCo y entes descentralizados, y completar municipios entrerrianos fuera de la prioridad inicial. Para Buenos Aires se mantiene una lista amplia de candidatos; las distancias por ruta desde Rosario todavía no están medidas y no se afirma que todos cumplan 280 km.',
      '', '## Próximas etapas','',
      '1. Restaurar el proxy y habilitar mediante la configuración del entorno los dominios oficiales del inventario. Ejecutar `python tools/verificar_fuentes.py`; no requiere modificar el historial de producción. Como alternativa verificable, el workflow manual sobre esta rama ejecuta el verificador en GitHub Actions con permisos de lectura y conserva su evidencia como artefacto; no se ha disparado desde esta sesión.',
      '2. Priorizar CAFESG, Aeropuerto Rosario, Santa Fe capital, Casilda y EPE: guardar respuestas HTML/PDF reales, ajustar extracción de fichas, recorrer todas las páginas y comparar publicaciones detectadas con el listado oficial. Promover cada fuente solo con conteos y evidencia.',
      '3. Resolver API pública de ASSA y Entre Ríos, iframes de Colón, SIU-Diaguita UNR y alternativa pública de Concordia. No inventar endpoints ni usar portales de prueba como producción.',
      '4. Importar y actualizar el padrón oficial completo santafesino (códigos publicados desde 2018), cruzarlo con fuentes y registrar explícitamente cada comuna sin portal. El archivo oficial se localizó, pero su descarga posterior agotó tiempo; no se declara importado. Repetir para municipios, comunas y entes entrerrianos.',
      '5. Medir distancias por ruta de los partidos bonaerenses; completar partidos cercanos y boletines complementarios, hospitales/SAMCo/entes. Añadir OCR donde exista PDF escaneado y resolver duplicados documentales con identidad del organismo y expediente.',
      '6. Volver a ejecutar con historial real preservado y actualizar este informe con `python tools/informe_cobertura.py`. Mantener PR #1 abierto para revisión; no fusionar automáticamente.','']
    Path('INFORME_COBERTURA.md').write_text('\n'.join(lineas))

if __name__=='__main__': generar()
