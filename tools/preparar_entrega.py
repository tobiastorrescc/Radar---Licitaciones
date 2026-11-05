"""Entrega íntegra sin envíos: informe persistible, CSV y correo .eml con adjuntos.

No usa red, credenciales ni destinatarios. La activación de SMTP es una etapa posterior.
"""
import argparse
import csv
from email.message import EmailMessage
from email.policy import SMTP
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o
import shutil


def preparar(directorio,salida=None):
    root=Path(directorio);destino=Path(salida) if salida else root/'entrega';destino.mkdir(parents=True,exist_ok=True)
    eventos=json.loads((root/'eventos.json').read_text());fecha=eventos['fecha'];todos=eventos['oportunidades']
    recuperadas={'HISTORICA_RECUPERADA','HISTORICA_ANIO_PROCEDIMIENTO','RECUPERACION_LINEA_BASE'}
    grupos={
        'recuperadas_vigentes':[r for r in todos if r.get('clasificacion_novedad') in recuperadas and r.get('vigencia')=='ABIERTA'],
        'nuevas_confirmadas':[r for r in todos if r.get('clasificacion_novedad')=='NUEVO_CONFIRMADO' and r.get('vigencia')=='ABIERTA'],
        'publicaciones_nuevas_no_cotizables':[r for r in todos if r.get('clasificacion_novedad')=='NUEVO_CONFIRMADO' and r.get('vigencia')!='ABIERTA'],
        'detecciones_sin_fecha_o_mismo_dia':[r for r in todos if r.get('clasificacion_novedad') in ('NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA')],
        'cambios':[r for r in todos if r.get('clasificacion_novedad') in ('MODIFICADO','DATOS_COMPLETADOS')],
        'recuperaciones_historicas':[r for r in todos if r.get('clasificacion_novedad') in recuperadas and r.get('vigencia')=='VENCIDA'],
        'recuperaciones_vigencia_pendiente':[r for r in todos if r.get('clasificacion_novedad') in recuperadas and r.get('vigencia') not in ('ABIERTA','VENCIDA')],
    }
    reportadas=sorted([r for datos in grupos.values() for r in datos],key=o.prioridad)
    resumen=json.loads((root/'resumen.json').read_text());run=__import__('os').environ.get('GITHUB_RUN_ID')
    enlace=f'https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/{run}' if run else None
    meta={'fecha':fecha,'estado':resumen['estado'],'totales':{k:len(v) for k,v in grupos.items()},
          'linea_base_sin_alerta':sum(r.get('clasificacion_novedad')=='LINEA_BASE' for r in todos),
          'total_informadas':len(reportadas),'limite_cantidad':None,'envio_activado':False,'ejecucion':enlace,
          'cobertura_estricta':resumen.get('cobertura_estricta'),
          'aviso':'No hay novedades confirmadas no significa ausencia de licitaciones si hay incidencias. Detecciones sin fecha no son publicaciones nuevas comprobadas.'}
    meta['totales_comerciales']={k:sum(r.get('vigencia')=='ABIERTA' for r in grupos[k]) for k in ('nuevas_confirmadas','detecciones_sin_fecha_o_mismo_dia','cambios','recuperadas_vigentes')}
    (destino/'resumen.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
    (destino/'oportunidades.json').write_text(json.dumps({'resumen':meta,'grupos':grupos},ensure_ascii=False,indent=2)+'\n')
    for nombre in ('metricas_territoriales.json','auditoria_manual.json','cola_enriquecimiento.json','fichas.json','cola_documental.json','observaciones_previas_sin_revalidar.json','fichas_abiertas.md','oportunidades_abiertas.md','oportunidades_proximas_a_vencer.md'):
        if (root/nombre).exists():shutil.copy2(root/nombre,destino/nombre)
    campos=['etiqueta_novedad','primera_deteccion','ultima_deteccion','detalle_documental','provincia','localidad','organismo','numero_procedimiento','objeto','presupuesto','condiciones_pago','enlace_condiciones_pago','fecha_publicacion','fecha_apertura','hora_apertura','fecha_hora_apertura','fecha_limite_presentacion','hora_limite_presentacion','fecha_hora_limite_presentacion','vigencia','modalidad_presentacion','url','enlace_pliego','clasificacion_novedad']
    with (destino/'oportunidades.csv').open('w',encoding='utf-8-sig',newline='') as archivo:
        w=csv.DictWriter(archivo,fieldnames=campos);w.writeheader()
        for r in reportadas:
            fila={k:json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(dict,list)) else str(r.get(k) or '') for k in campos}
            # Apertura en planillas sin ejecutar fórmulas suministradas por terceros.
            fila={k:"'"+v if v.startswith(('=','+','-','@','\t','\r')) else v for k,v in fila.items()};w.writerow(fila)
    total_recuperaciones=sum(len(grupos[k]) for k in ('recuperadas_vigentes','recuperaciones_historicas','recuperaciones_vigencia_pendiente'))
    lineas=['# Informe diario del piloto', '',f'Fecha: {fecha}. Estado: **{resumen["estado"]}**.','',meta['aviso'],'',
            f'Nuevas vigentes con publicación comprobada: {len(grupos["nuevas_confirmadas"])}. Primeras detecciones abiertas con publicación pendiente: {meta["totales_comerciales"]["detecciones_sin_fecha_o_mismo_dia"]}. Cambios abiertos: {meta["totales_comerciales"]["cambios"]}. El archivo de auditoría conserva {len(reportadas)} eventos de toda vigencia, incluidas {total_recuperaciones} recuperaciones.','',
            '[CSV completo](oportunidades.csv) · [JSON completo](oportunidades.json). Sin límite de cantidad.']
    territorial=root/'metricas_territoriales.json'
    if territorial.exists():
        from metricas_territoriales import markdown
        lineas+=['',markdown(json.loads(territorial.read_text()))]
    if enlace:lineas+=['',f'[Auditoría, abiertas, próximas a vencer y catálogo íntegro]({enlace}) (artefacto radar-controlado).']
    auditoria=['# Auditoría íntegra de eventos, incluidos vencidos e inciertos','',fecha,'','Estos registros se conservan, pero no se presentan todos como oportunidades cotizables.']
    for nombre,datos in grupos.items():
        titulo='Primera detección, fecha pendiente o sin ventana horaria suficiente' if nombre=='detecciones_sin_fecha_o_mismo_dia' else 'Modificaciones, circulares y datos completados' if nombre=='cambios' else nombre.replace('_',' ').capitalize()
        if nombre=='recuperadas_vigentes':titulo='Convocatorias recuperadas que siguen abiertas (no son publicaciones nuevas comprobadas del día)'
        if nombre=='recuperaciones_vigencia_pendiente':titulo='Recuperaciones con vigencia pendiente de comprobar'
        auditoria+=['','## '+titulo,'',o.reporte(datos,fecha)]
        if nombre in ('nuevas_confirmadas','detecciones_sin_fecha_o_mismo_dia','cambios','recuperadas_vigentes'):
            lineas+=['','## '+titulo,'',o.reporte([r for r in datos if r.get('vigencia')=='ABIERTA'],fecha)]
    lineas+=['','[Auditoría de todos los eventos, vencidos y vigencia pendiente](auditoria_eventos.md). El CSV y JSON conservan la totalidad, sin recorte.']
    previo=root/'observaciones_previas_sin_revalidar.json'
    if previo.exists():
        prev=json.loads(previo.read_text());pendientes=prev.get('pendientes_revalidacion',[])
        if pendientes:
            auditoria+=['','## Observaciones previas pendientes de revalidación','',f"{len(pendientes)} registros detectados en la auditoría {prev.get('origen_run')}, a {prev.get('fecha_observacion')}. No se anuncian como nuevas publicaciones del día ni se presume que sigan abiertas.",'','| Organismo | Procedimiento | Objeto | Enlace oficial |','|---|---|---|---|']
            for r in pendientes:
                limpio=lambda v:str(v or '').replace('|','/').replace('\n',' ')
                auditoria.append('| '+limpio(r.get('organismo'))+' | '+limpio(r.get('procedimiento'))+' | '+limpio(r.get('objeto'))+' | [Oficial]('+str(r.get('url') or '')+') |')
    (destino/'auditoria_eventos.md').write_text('\n'.join(auditoria)+'\n')
    lineas+=['','## Fichas y seguimiento documental','','[Fichas completas de abiertas](fichas_abiertas.md) · [Cola documental](cola_documental.json) · [Observaciones previas sin revalidar](observaciones_previas_sin_revalidar.json)']
    proximas=root/'oportunidades_proximas_a_vencer.md'
    if proximas.exists():lineas+=['','## Próximas a vencer','','[Consultar vencimientos y estado de revalidación](oportunidades_proximas_a_vencer.md). Las calculadas sólo por historial requieren confirmar nuevamente la fuente.']
    contenido='\n'.join(lineas)+'\n';(destino/'informe.md').write_text(contenido)
    mensaje=EmailMessage(policy=SMTP)
    mensaje['Subject']=f'Radar {fecha[:10]}: {len(grupos["nuevas_confirmadas"])} nuevas confirmadas; {len(reportadas)} registros informados'
    mensaje.set_content(contenido)
    for nombre,tipo in [('oportunidades.csv','csv'),('oportunidades.json','json')]:
        mensaje.add_attachment((destino/nombre).read_bytes(),maintype='text' if tipo=='csv' else 'application',subtype=tipo,filename=nombre)
    (destino/'informe.eml').write_bytes(mensaje.as_bytes())
    return meta

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--directorio',required=True);p.add_argument('--salida');a=p.parse_args()
    print('ENTREGA_PREPARADA '+json.dumps(preparar(a.directorio,a.salida),ensure_ascii=False))
