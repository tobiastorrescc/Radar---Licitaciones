"""Métricas derivadas, sin alterar historial, cuotas de extracción ni programación."""
from collections import Counter
from datetime import datetime,timedelta
import json,re
from pathlib import Path
import oportunidades as o

PROVINCIAS=('Santa Fe','Entre Ríos','Buenos Aires')

def provincia(r):
    return next((p for p in PROVINCIAS if o.norm(p)==o.norm(r.get('provincia'))),'Sin jurisdicción comprobada')

def pago_rapido(r):
    p=r.get('pago',{})
    if p.get('estado')!='VERIFICADO' or not p.get('documentos_respaldo',[]) and not p.get('documento_respaldo'):return False
    if p.get('clasificacion') in ('CONTADO','CONTRA_ENTREGA'):return True
    dias=p.get('plazos_dias',[])
    return bool(dias) and max(dias)<=15 and min(dias)>=0 and p.get('clasificacion') not in ('MIXTO','OPCIONES_PUBLICADAS')

def contraste_manual(manual,registros,fecha):
    filas=[];hoy=datetime.fromisoformat(fecha).astimezone(o.ZONA).date()
    for m in manual.get('publicaciones',[]):
        if not m.get('evidencia_url') or not m.get('fecha_revision') or not m.get('comprobada'):continue
        nombres={o.norm(m.get('organismo')),*[o.norm(a) for a in m.get('organismo_aliases',[])]}
        candidatos=[r for r in registros if provincia(r)==provincia(m) and o.norm(r.get('organismo')) in nombres]
        proc=o.procedimiento_canonico(m)
        if proc:candidatos=[r for r in candidatos if o.procedimiento_canonico(r)==proc and o.convocatoria(r)==o.convocatoria(m)]
        else:
            # Un índice general puede contener cientos de avisos: URL sola no basta.
            candidatos=[r for r in candidatos if o.norm(m.get('objeto')) and o.norm(m['objeto']) in o.norm(r.get('objeto')) and (r.get('url')==m.get('url') or m['evidencia_url'] in {d['url'] for d in r.get('documentos',[])})]
        candidatos={o.identidad(r):r for r in candidatos}
        actual=(hoy-datetime.fromisoformat(m['fecha_revision']).date()).days in (0,1)
        directas=[r for r in candidatos.values() if r.get('url')==m.get('url') and m.get('fecha_apertura') and r.get('fecha_apertura')==m['fecha_apertura']]
        estado='DETECTADA' if len(candidatos)==1 or directas else 'AMBIGUA' if candidatos else 'OMITIDA'
        filas.append({**m,'resultado':estado,'evidencia_reciente':actual,'ids_radar':[r.get('id') for r in candidatos.values()]})
    return {'alcance':manual.get('alcance','Muestra comprobada, no cobertura global'),'revisiones':manual.get('revisiones',[]),'publicaciones':filas,'por_provincia':{p:{'comprobadas':sum(provincia(r)==p for r in filas),'detectadas':sum(provincia(r)==p and r['resultado']=='DETECTADA' for r in filas),'omitidas':sum(provincia(r)==p and r['resultado']=='OMITIDA' for r in filas),'ambiguas':sum(provincia(r)==p and r['resultado']=='AMBIGUA' for r in filas),'omitidas_historicas':sum(provincia(r)==p and r['resultado']=='OMITIDA' and bool(r.get('historica')) for r in filas),'omitidas_apertura_futura':sum(provincia(r)==p and r['resultado']=='OMITIDA' and str(r.get('fecha_apertura') or '')>hoy.isoformat() for r in filas)} for p in PROVINCIAS}}

def generar(db,actuales,eventos,fuentes,fecha,manual=None):
    hoy=datetime.fromisoformat(fecha).astimezone(o.ZONA).date();dias=[(hoy-timedelta(days=i)).isoformat() for i in range(6,-1,-1)]
    # Todas las ejecuciones del día: una repetición no reinicia el contador diario.
    confirmadas={};dias_observados=set()
    for id,f,res in db.execute('SELECT id,fecha,resumen FROM ejecuciones'):
        d=datetime.fromisoformat(f).astimezone(o.ZONA).date().isoformat()
        if d in dias:dias_observados.add(d)
    for id,f,clave,dato in db.execute("SELECT e.procedimiento,x.fecha,e.corrida,v.dato FROM eventos e JOIN ejecuciones x ON x.id=e.corrida JOIN versiones v ON v.procedimiento=e.procedimiento AND v.huella=e.huella WHERE e.tipo='NUEVO_CONFIRMADO' ORDER BY x.fecha"):
        r=json.loads(dato);d=datetime.fromisoformat(f).astimezone(o.ZONA).date().isoformat();publicada=o.fecha(r.get('fecha_publicacion'))
        if publicada and publicada<=d and provincia(r) in PROVINCIAS:confirmadas.setdefault(o.identidad(r),(d,r))
    nuevas=[r for d,r in confirmadas.values() if d==hoy.isoformat()]
    fuente_prov={f['url']:provincia(f) for f in fuentes};manual=manual or {'publicaciones':[]}
    auditoria=contraste_manual(manual,actuales,fecha)
    resultado={}
    for p in PROVINCIAS:
        rs=[r for r in actuales if provincia(r)==p and r.get('clasificacion_registro')=='PROCEDIMIENTO'];fs=[f for f in fuentes if fuente_prov.get(f.get('url'))==p]
        fallas=[{'url':f['url'],'estado':f['estado'],'errores':f.get('errores',[]),'limites':f.get('limites',[])} for f in fs if f.get('estado_cobertura',f.get('estado')) not in ('OPERATIVA','SIN_PUBLICACIONES_CONFIRMADO','SIN_PUBLICACIONES') or f.get('errores') or f.get('limites')]
        abiertas=[r for r in rs if r.get('vigencia')=='ABIERTA'];observadas=[r for r in abiertas if r.get('observada_esta_corrida')]
        a=auditoria['por_provincia'][p]
        resultado[p]={'nuevas_confirmadas':sum(provincia(r)==p for r in nuevas),'primeras_detecciones_no_comprobadas':sum(provincia(r)==p and r.get('clasificacion_novedad') in ('NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA') for r in eventos),'abiertas_observadas':len(observadas),'abiertas_solo_historial':len(abiertas)-len(observadas),'vigencia_pendiente':sum(r.get('vigencia')=='DESCONOCIDA' for r in rs),'pago_rapido_verificado_abiertas':sum(pago_rapido(r) for r in abiertas),'pago_rapido_observadas':sum(pago_rapido(r) for r in observadas),'fuentes_consultadas':len(fs),'fuentes_con_incidencias':fallas,'auditoria_manual':a,'omitidas_muestra':a['omitidas'] if a['comprobadas'] else None}
    serie=[{'fecha':d,'nuevas_confirmadas':sum(v[0]==d for v in confirmadas.values()),'ejecucion_disponible':d in dias_observados} for d in dias]
    disponibles=[x for x in serie if x['ejecucion_disponible']]
    return {'fecha':fecha,'jurisdicciones':resultado,'total_nuevas_confirmadas':len(nuevas),'meta_promedio_diario':20,'meta_alcance':'Conjunto de Santa Fe, Entre Ríos y Buenos Aires dentro del alcance de Rosario; condicionado al volumen real. Sin límite de resultados.','serie_7_dias':serie,'dias_con_ejecucion':len(disponibles),'promedio_dias_observados':sum(x['nuevas_confirmadas'] for x in disponibles)/len(disponibles) if disponibles else None,'promedio_7_dias':sum(x['nuevas_confirmadas'] for x in serie)/7 if len(disponibles)==7 else None,'criterio':'Sólo NUEVO_CONFIRMADO con fecha publicada comprobada. Históricas, duplicados, primeras detecciones sin fecha y modificaciones no integran la meta. Días sin ejecución no se imputan como cero. Abierta observada no acredita exhaustividad de la fuente.','auditoria_manual':auditoria,'fuentes_sin_jurisdiccion_comprobada':[f for f in fuentes if provincia(f) not in PROVINCIAS]}

def markdown(m):
    lineas=['## Descubrimiento diario en las tres jurisdicciones','',f"Total de publicaciones genuinamente nuevas confirmadas del día: **{m['total_nuevas_confirmadas']}**.",'','| Provincia | Nuevas confirmadas | Abiertas observadas | Abiertas sólo por historial | Vigencia pendiente | Pago rápido en abiertas | Omitidas / comprobadas en muestra | Fuentes con incidencias |','|---|---:|---:|---:|---:|---:|---|---:|']
    for p,r in m['jurisdicciones'].items():
        a=r['auditoria_manual'];muestra=f"{a['omitidas']} / {a['comprobadas']}" if a['comprobadas'] else 'Sin muestra comprobada'
        lineas.append(f"| {p} | {r['nuevas_confirmadas']} | {r['abiertas_observadas']} | {r['abiertas_solo_historial']} | {r['vigencia_pendiente']} | {r['pago_rapido_verificado_abiertas']} | {muestra} | {len(r['fuentes_con_incidencias'])} |")
    lineas+=['',m['meta_alcance'],m['criterio'],'',f"Promedio de siete días: {m['promedio_7_dias'] if m['promedio_7_dias'] is not None else 'Pendiente: faltan días con ejecución'}. Días disponibles: {m['dias_con_ejecucion']}/7. La muestra manual se limita a sus URLs y fechas de revisión.",'','[Métricas completas](metricas_territoriales.json) · [Comparación de avisos y omisiones](auditoria_manual.json)']
    return '\n'.join(lineas)


def html_resumen(m):
    from html import escape
    texto=f'<section><h2>Publicaciones genuinamente nuevas confirmadas: {m["total_nuevas_confirmadas"]}</h2><p>Meta: promedio conjunto de20 por día, condicionado al volumen real. Sin límite de resultados.</p><table><thead><tr><th>Provincia</th><th>Nuevas confirmadas</th><th>Abiertas observadas</th><th>Abiertas sólo por historial</th><th>Vigencia pendiente</th><th>Pago rápido en abiertas</th><th>Omitidas en muestra</th><th>Fuentes con incidencias</th></tr></thead><tbody>'
    for p,r in m['jurisdicciones'].items():
        a=r['auditoria_manual'];om=str(a['omitidas'])+'/'+str(a['comprobadas']) if a['comprobadas'] else 'Sin muestra'
        valores=[p,r['nuevas_confirmadas'],r['abiertas_observadas'],r['abiertas_solo_historial'],r['vigencia_pendiente'],r['pago_rapido_verificado_abiertas'],om,len(r['fuentes_con_incidencias'])]
        texto+='<tr>'+''.join('<td>'+escape(str(v))+'</td>' for v in valores)+'</tr>'
    return texto+'</tbody></table><p>La muestra no demuestra cobertura provincial completa. Pago nominal hasta15días conserva sus unidades e hito; no promete acreditación inmediata. Los fallos no significan ausencia de publicaciones.</p></section>'
