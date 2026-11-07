"""Vigencia de presentación comprobada, separada de apertura y del historial."""
import csv,json,re
from datetime import datetime
from pathlib import Path
import oportunidades as o

PENDIENTE='Pendiente de verificar'

def presentacion(registro,fecha):
    r=o.normalizar(registro,fecha);ahora=datetime.fromisoformat(fecha) if isinstance(fecha,str) else fecha
    if not ahora.tzinfo:ahora=ahora.replace(tzinfo=o.ZONA)
    estado='PENDIENTE_VERIFICAR_PRESENTACION';motivo='Apertura futura no acredita por sí sola un cierre de recepción vigente';limite=None
    if r['vigencia']=='VENCIDA':estado='VENCIDA_O_CERRADA';motivo=r.get('motivo_vigencia')
    elif r.get('requiere_revalidacion') or registro.get('observada_esta_corrida') is False:
        estado='PENDIENTE_REVALIDACION';motivo='Evidencia anterior o no observada en esta corrida'
    elif r.get('fecha_limite_presentacion'):
        limite=r.get('fecha_hora_limite_presentacion')
        if limite:
            dt=datetime.fromisoformat(limite)
            if not dt.tzinfo:dt=dt.replace(tzinfo=o.ZONA)
            vigente=dt>ahora
        else:vigente=r['fecha_limite_presentacion']>ahora.astimezone(o.ZONA).date().isoformat()
        if vigente and r['vigencia']=='ABIERTA':estado='VIGENTE_VERIFICADA';motivo='Plazo de presentación explícito y no vencido'
        elif not vigente and limite:estado='VENCIDA_O_CERRADA';motivo='Plazo de recepción vencido'
    else:
        texto=o.norm(' '.join(str(r.get(k) or '') for k in ('titulo','objeto','texto_documento','fecha_limite_presentacion_texto')))
        regla=re.search(r'(?:presentacion|recepcion|recibiran|presentarse)\b.{0,120}\bhasta\s+(?:el\s+mismo\s+|la\s+)?(?:dia y hora|fecha y hora|momento)\s+de\s+(?:la\s+)?apertura',texto)
        if regla and r.get('fecha_hora_apertura') and r['vigencia']=='ABIERTA':
            estado='VIGENTE_VERIFICADA';motivo='El aviso permite recepción hasta la fecha y hora de apertura';limite=r['fecha_hora_apertura']
    return {'estado_comercial':estado,'presentacion_verificada':estado=='VIGENTE_VERIFICADA','motivo_comercial':motivo,'limite_presentacion_comprobado':limite or r.get('fecha_limite_presentacion'),'evidencia_url':r.get('evidencia_url') or r.get('url')}

def escribir(registros,fecha,destino,fuentes=None):
    root=Path(destino);root.mkdir(parents=True,exist_ok=True)
    revisadas=[{**r,**presentacion(r,fecha)} for r in registros if r.get('clasificacion_registro')=='PROCEDIMIENTO']
    vigentes=sorted([r for r in revisadas if r['presentacion_verificada']],key=o.prioridad)
    pendientes=[r for r in revisadas if r['estado_comercial'].startswith('PENDIENTE')]
    (root/'informe_comercial.json').write_text(json.dumps({'fecha':fecha,'total':len(vigentes),'oportunidades':vigentes},ensure_ascii=False,indent=2)+'\n')
    (root/'presentacion_pendiente.json').write_text(json.dumps({'fecha':fecha,'total':len(pendientes),'oportunidades':pendientes},ensure_ascii=False,indent=2)+'\n')
    campos=['organismo','provincia','localidad','numero','objeto','fecha_publicacion_comprobada','apertura','limite_presentacion','estado_vigencia','presupuesto','pago','modalidad_presentacion','url','pliego']
    filas=[]
    for r in vigentes:
        filas.append({'provincia':r.get('provincia') or PENDIENTE,'localidad':r.get('localidad') or PENDIENTE,'fecha_publicacion_comprobada':r.get('fecha_publicacion') or PENDIENTE,'estado_vigencia':'REABIERTA_O_PRORROGADA' if r.get('reapertura') or 'prorroga' in o.norm(r.get('evento_publicado')) else 'VIGENTE_CONFIRMADA','organismo':r.get('organismo') or PENDIENTE,'numero':r.get('numero_procedimiento') or PENDIENTE,'objeto':r.get('objeto') or PENDIENTE,'apertura':r.get('fecha_hora_apertura') or r.get('fecha_apertura') or PENDIENTE,'limite_presentacion':r['limite_presentacion_comprobado'],'presupuesto':json.dumps(r['presupuesto'],ensure_ascii=False) if r.get('presupuesto') else PENDIENTE,'pago':r.get('condiciones_pago') if r.get('pago',{}).get('estado')=='VERIFICADO' else PENDIENTE,'modalidad_presentacion':', '.join(r.get('modalidad_presentacion') or []) or PENDIENTE,'url':r.get('url') or PENDIENTE,'pliego':r.get('enlace_pliego') or PENDIENTE})
    with (root/'informe_comercial.csv').open('w',newline='') as out:
        w=csv.DictWriter(out,fieldnames=campos);w.writeheader()
        for fila in filas:
            w.writerow({k:("'"+str(v) if str(v).startswith(('=','+','-','@','\t','\r')) else v) for k,v in fila.items()})
    escapar=lambda x:str(x).replace('|','/').replace('\n',' ')
    lineas=['# Convocatorias con recepción vigente comprobada','',f'Fecha: {fecha}. Total: {len(filas)}. Sin recortes por rubro, monto ni pago.','', '| '+' | '.join(campos)+' |','|'+'|'.join(['---']*len(campos))+'|']
    lineas+=['| '+' | '.join(escapar(r[k]) for k in campos)+' |' for r in filas]
    revision=[f for f in (fuentes or []) if f.get('estado') not in ('OPERATIVA','SIN_PUBLICACIONES')]
    lineas+=['','## Fuentes que requieren revisión manual','']
    lineas+=['- ['+str(f.get('organismo') or f.get('id'))+']('+f['url']+'): '+str(f.get('estado','PENDIENTE')) for f in revision]
    if not revision:lineas.append('Sin incidencias registradas en esta muestra.' if fuentes is not None else 'No se adjuntó auditoría de fuentes; no acredita cobertura completa.')
    (root/'informe_comercial.md').write_text('\n'.join(lineas)+'\n')
    return {'vigentes_presentacion_verificada':len(vigentes),'pendientes_presentacion_o_revalidacion':len(pendientes)}
