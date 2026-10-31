"""Resultados por fuente, ventana temporal y replay contra todo el historial aislado."""
import argparse,json,sqlite3,shutil,sys
from pathlib import Path
from hashlib import sha256
from datetime import datetime,timedelta
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
import oportunidades as o


def estado_revision(obs,publicaciones,eventos):
    errores=obs.get('errores',[]);acceso=any(e.get('categoria') in ('RED','ACCESO','PRESUPUESTO') for e in errores)
    valida=obs.get('estado') in ('OPERATIVA','SIN_PUBLICACIONES') and not errores and not obs.get('limites')
    pendientes=obs.get('estado') in ('NO_INICIADA','EN_CURSO')
    novedades=[r for r in eventos if r.get('clasificacion_novedad') in ('NUEVO_CONFIRMADO','NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA','MODIFICADO','RECUPERACION_LINEA_BASE')]
    estado='PENDIENTE' if pendientes else 'ERROR_DE_ACCESO' if acceso and not publicaciones else 'REVISADA_CON_RESULTADOS' if publicaciones and (novedades or not valida) else 'REVISADA_SIN_NOVEDADES' if valida else 'PENDIENTE'
    return {'estado_revision':estado,'consulta_completa':valida,'incidencia_acceso':acceso,'pendiente':not valida,'procedimientos_recuperados':len(publicaciones),'novedades_o_cambios':len(novedades),'errores':errores}


def generar(root):
    root=Path(root);meta=json.load(open(root/'ultima_ejecucion.json'));dir=root/meta['directorio'];dbpath=root/'estado.sqlite3';antes=sha256(dbpath.read_bytes()).hexdigest()
    with sqlite3.connect('file:'+str(dbpath.resolve())+'?mode=ro',uri=True) as db:
        rs=inc.actuales(db,meta['fecha'],meta['corrida']);ev=inc.eventos(db,meta['corrida'],meta['fecha'])
    fuentes=json.load(open(dir/'auditoria_fuentes.json'))['fuentes'];estados=[]
    for obs in fuentes:
        publicaciones=[r for r in rs if r.get('observada_esta_corrida') and obs['url'] in inc.fuentes_de(r)]
        cambios=[r for r in ev if obs['url'] in inc.fuentes_de(r)]
        estados.append({'id':obs['id'],'url':obs['url'],**estado_revision(obs,publicaciones,cambios)})
    fecha=datetime.fromisoformat(meta['fecha']);inicio=(fecha-timedelta(hours=72)).date().isoformat();fin=(fecha+timedelta(days=60)).date().isoformat();hoy=fecha.date().isoformat()
    ventanas={'publicadas_ultimas_72_horas_por_fecha_disponible':[r for r in rs if r.get('fecha_publicacion') and inicio<=r['fecha_publicacion']<=hoy],'convocatorias_proximos_60_dias':[r for r in rs if r.get('vigencia')=='ABIERTA' and hoy<=str(r.get('fecha_limite_presentacion') or r.get('fecha_apertura') or '')<=fin],'sin_fecha_publicacion':[r for r in ev if not r.get('fecha_publicacion')]}
    # Copia desechable: el estado de la corrida, respaldo diario y producción no se escriben.
    replay=root/'replay-deduplicacion.sqlite3';shutil.copy2(dbpath,replay)
    informe=json.load(open(dir/'verificacion.json'));registros=json.load(open(dir/'registros_observados.json'))
    db=inc.abrir(replay)
    try:res=inc.registrar(db,registros,{**informe,'ejecucion_id':informe['ejecucion_id']+'-replay-sin-red'})
    finally:db.close()
    replay.unlink() # Copia de prueba desechable; el resultado queda auditado en JSON.
    correcta=res['novedades']==0 and not any(res['clasificacion'].get(k,0) for k in ('MODIFICADO','DATOS_COMPLETADOS','NUEVO_CONFIRMADO','NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA'))
    salida={'fecha':meta['fecha'],'fuentes':estados,'replay':res,'deduplicacion_correcta':correcta,'historial_intacto':antes==sha256(dbpath.read_bytes()).hexdigest(),'registros_historial':len(rs),'ventanas':{k:len(v) for k,v in ventanas.items()},'criterio_72h':'Con fecha sin hora se incluye el día inicial completo para no perder avisos; no se inventa hora de publicación.','recorte_resultados':False}
    (dir/'estados_revision.json').write_text(json.dumps(salida,ensure_ascii=False,indent=2)+'\n');(dir/'ventanas_revision.json').write_text(json.dumps(ventanas,ensure_ascii=False,indent=2)+'\n')
    print('AUDITORIA_INFORME '+json.dumps({k:v for k,v in salida.items() if k not in ('fuentes','replay')},ensure_ascii=False),flush=True)
    if not correcta or not salida['historial_intacto']:raise ValueError('La deduplicación o integridad requiere revisión')

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--entrada',default='work/cobertura');a=p.parse_args();generar(a.entrada)
