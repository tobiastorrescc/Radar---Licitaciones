"""Comparación diaria de sólo lectura: separa eventos y conserva evidencia por organismo."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
import oportunidades as o
import conectores


def instantanea(raiz):
    ruta=Path(raiz)/'estado.sqlite3'
    if not ruta.exists():return {'ids':[],'versiones':[],'corrida':None,'fecha':None,'fuentes':{}}
    with sqlite3.connect('file:'+str(ruta.resolve())+'?mode=ro',uri=True) as db:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Historial dañado; no se modifica')
        ids=[r[0] for r in db.execute('SELECT id FROM procedimientos ORDER BY id')]
        versiones=[list(r) for r in db.execute('SELECT procedimiento,huella FROM versiones ORDER BY procedimiento,huella')]
        ultima=db.execute('SELECT id,fecha,resumen FROM ejecuciones ORDER BY rowid DESC LIMIT 1').fetchone()
        fuentes={}
        for url,dato in db.execute('SELECT fuente,dato FROM auditorias ORDER BY rowid'):
            fuentes[url]=json.loads(dato)
        return {'ids':ids,'versiones':versiones,'corrida':ultima[0] if ultima else None,'fecha':ultima[1] if ultima else None,'fuentes':fuentes}


def comparar(antes,despues,registros,eventos):
    faltan=set(antes['ids'])-set(despues['ids'])
    perdidas=set(map(tuple,antes['versiones']))-set(map(tuple,despues['versiones']))
    realizada=bool(despues['corrida'] and antes['corrida']!=despues['corrida'])
    grupos={k:[] for k in ('nuevas_confirmadas','detecciones_sin_fecha_suficiente','recuperaciones_historicas','modificaciones','datos_completados')}
    por_tipo={'NUEVO_CONFIRMADO':'nuevas_confirmadas','NUEVA_DETECCION_FECHA_DESCONOCIDA':'detecciones_sin_fecha_suficiente','NUEVA_DETECCION_MISMO_DIA':'detecciones_sin_fecha_suficiente','MODIFICADO':'modificaciones','DATOS_COMPLETADOS':'datos_completados'}
    organismos={}
    for r in registros:
        f=organismos.setdefault(r.get('fuente'),{'organismo':r.get('organismo'),'provincia':r.get('provincia'),'localidad':r.get('localidad'),'procedimientos':0,'abiertas':0,'proximas_a_vencer':0,'pagos_verificados':0,'unificaciones_revision':0})
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        f['procedimientos']+=1;f['abiertas']+=r.get('vigencia')=='ABIERTA';f['pagos_verificados']+=r.get('pago',{}).get('estado')=='VERIFICADO'
        f['unificaciones_revision']+=r.get('unificacion_estado')=='REQUIERE_REVISION'
    if realizada:
        for r in eventos:
            tipo=r['clasificacion_novedad'];grupo=por_tipo.get(tipo)
            if tipo.startswith(('RECUPERACION','HISTORICA','LINEA_BASE')):grupo='recuperaciones_historicas'
            if grupo:grupos[grupo].append({k:r.get(k) for k in ('id','organismo','numero_procedimiento','objeto','fecha_publicacion','fecha_apertura','url','clasificacion_novedad','campos_modificados')})
    config=Path(__file__).resolve().parents[1]/'inventario/fuentes.json'
    configuradas={f['url']:f for f in json.loads(config.read_text())} if config.exists() else {}
    for url,obs in despues['fuentes'].items():
        f=organismos.setdefault(url,{'organismo':obs.get('organismo'),'procedimientos':0,'abiertas':0,'pagos_verificados':0})
        anterior=antes['fuentes'].get(url,{})
        for k in ('organismo','localidad','provincia'):
            if not f.get(k):f[k]=configuradas.get(url,{}).get(k) or obs.get(k)
        f.update(url=url,estado_anterior=anterior.get('estado_cobertura',anterior.get('estado')),estado_actual=obs.get('estado_cobertura',obs.get('estado')),errores=[{**e,**conectores.diagnostico_error(e)} for e in obs.get('errores',[])],consultada_esta_corrida=realizada)
    resultado={'corrida_anterior':antes['corrida'],'corrida_actual':despues['corrida'],'fecha':despues['fecha'],'consulta_nueva_realizada':realizada,
        'estado':'SIN_NUEVA_EJECUCION' if not realizada else 'HISTORIAL_PERDIDO' if faltan or perdidas else 'AUDITADA',
        'ids_anteriores':len(antes['ids']),'ids_actuales':len(despues['ids']),'ids_perdidos':sorted(faltan),'versiones_perdidas':sorted(perdidas),
        'conteos':{k:len(v) for k,v in grupos.items()},'eventos':grupos,'cobertura_por_organismo':list(organismos.values())}
    return resultado


def ejecutar(raiz,fase):
    raiz=Path(raiz);p=raiz/'auditoria_antes.json'
    if fase=='antes':
        p.write_text(json.dumps(instantanea(raiz),ensure_ascii=False));return
    antes=json.loads(p.read_text());despues=instantanea(raiz)
    with sqlite3.connect('file:'+str((raiz/'estado.sqlite3').resolve())+'?mode=ro',uri=True) as db:
        registros=inc.actuales(db,despues['fecha'],despues['corrida']);eventos=inc.eventos(db,despues['corrida'],despues['fecha'])
    r=comparar(antes,despues,registros,eventos)
    # Fuentes consultadas se comprueban contra la auditoría de esta corrida, no por su última lectura conocida.
    with sqlite3.connect('file:'+str((raiz/'estado.sqlite3').resolve())+'?mode=ro',uri=True) as db:
        consultadas={x[0] for x in db.execute('SELECT fuente FROM auditorias WHERE corrida=?',(despues['corrida'],))} if r['consulta_nueva_realizada'] else set()
        resumen=json.loads(db.execute('SELECT resumen FROM ejecuciones WHERE id=?',(despues['corrida'],)).fetchone()[0])
    for f in r['cobertura_por_organismo']:f['consultada_esta_corrida']=f['url'] in consultadas
    meta=raiz/'ultima_ejecucion.json'
    if meta.exists():
        ampliado=json.loads(meta.read_text())
        if ampliado.get('corrida')==despues['corrida']:resumen.update(ampliado)
    r['estado_ejecucion']=resumen['estado'];r['cobertura_estricta']=resumen.get('cobertura_estricta',{})
    r['abiertas']=len(o.separar_vigencia(registros,despues['fecha'])['abiertas']);r['proximas_a_vencer']=len(o.separar_vigencia(registros,despues['fecha'])['proximas_a_vencer'])
    progreso=raiz/'progreso_actual.json'
    fallo=json.loads(progreso.read_text()).get('estado')=='INCOMPLETA' if progreso.exists() else False
    if resumen['estado']=='INCOMPLETA' or fallo:r['estado']='EJECUCION_INCOMPLETA';r['estado_ejecucion']='INCOMPLETA'
    (raiz/'auditoria_diaria.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n')
    lineas=['# Comparación diaria del piloto',f"Estado: {r['estado']}; consulta: {r['estado_ejecucion']}.",f"Base: {r['corrida_anterior']}; actual: {r['corrida_actual']}.",f"Historial: {r['ids_anteriores']} → {r['ids_actuales']}; perdidos: {len(r['ids_perdidos'])}; versiones perdidas: {len(r['versiones_perdidas'])}."]
    lineas.extend(f'- {k}: {v}' for k,v in r['conteos'].items())
    for grupo,filas in r['eventos'].items():
        lineas+=['',f'## {grupo}','']
        lineas.extend(f"- {x['organismo']} — {x['numero_procedimiento']}: {x['objeto']} ([oficial]({x['url']}))" for x in filas)
    lineas+=['','## Cobertura por organismo','','| Organismo | Estado anterior | Actual | Procedimientos | Errores |','|---|---|---|---:|---|']
    lineas.extend(f"| {f.get('organismo')} | {f.get('estado_anterior')} | {f.get('estado_actual')} | {f['procedimientos']} | {len(f.get('errores',[]))} |" for f in r['cobertura_por_organismo'])
    (raiz/'auditoria_diaria.md').write_text('\n'.join(lineas)+'\n')
    print('EVOLUCION_DIARIA '+json.dumps({k:r[k] for k in ('estado','conteos','ids_anteriores','ids_actuales','abiertas','proximas_a_vencer')},ensure_ascii=False))
    if r['ids_perdidos'] or r['versiones_perdidas']:raise ValueError('Continuidad perdida: conservar estado y revisar respaldo')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('fase',choices=('antes','despues'));p.add_argument('--salida',required=True);a=p.parse_args();ejecutar(a.salida,a.fase)
