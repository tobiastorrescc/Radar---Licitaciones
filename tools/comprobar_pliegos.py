"""Comprueba adjuntos de abiertas con procesos aislados, TLS validado y plazo global."""
from collections import deque
from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
import documentos
import extractores
import oportunidades as o


def worker(url):
    raw,tipo,final=conectores.descargar(url,conexion_timeout=5,lectura_timeout=8)
    if (urlparse(final).hostname or '').removeprefix('www.')!=(urlparse(url).hostname or '').removeprefix('www.'):
        return {'url':url,'url_final':final,'estado':'REDIRECCION_OTRO_DOMINIO'}
    clase='PDF' if raw.startswith(b'%PDF-') else ('ZIP_O_DOCX' if raw.startswith(b'PK') else None)
    if not clase:return {'url':url,'url_final':final,'estado':'NO_ES_DOCUMENTO','tipo':tipo,'error':'Respuesta HTML/u otro contenido; HTTP 200 no valida pliego'}
    r={'url':url,'url_final':final,'estado':'DOCUMENTO_ACCESIBLE','tipo':clase,'bytes':len(raw),'sha256':sha256(raw).hexdigest()}
    try:
        texto=documentos.leer(raw,tipo,final,ocr=False)
        ps=extractores.procesos(texto)
        r['procedimientos']=sorted({o.procedimiento_canonico({'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'url':final}) for p in ps}-{None})
        r['contiene_pliego']='pliego' in o.norm(texto[:16000])
        r['presupuesto'],fragmento=o.monto(o.norm(texto))
        if fragmento:r['evidencia_presupuesto']={'url':final,'texto':fragmento}
    except Exception as e:r['lectura_pendiente']=str(e)
    return r


def terminar(proceso):
    try:os.killpg(proceso.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proceso.wait(timeout=2)


def comprobar(registros,fecha,configuraciones,por_enlace=15,total=180,concurrencia=4):
    candidatos={};vinculos={}
    configs={f['url']:f for f in configuraciones if f.get('url')}
    for r in registros:
        if r.get('vigencia')!='ABIERTA' or r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        conf=configs.get(r.get('fuente'),{})
        host=lambda u:(urlparse(u).hostname or '').lower().removeprefix('www.')
        permitidos={host(r.get('fuente') or r['url']),*(h.removeprefix('www.') for h in conf.get('dominios_documentos',[]))}
        for d in r.get('documentos',[]):
            u=d['url']
            if host(u) not in permitidos:
                candidatos.setdefault(u,{'url':u,'estado':'DOMINIO_NO_DECLARADO'});continue
            candidatos.setdefault(u,{'url':u,'estado':'PENDIENTE'})
            vinculos.setdefault(u,[]).append(r)
    inicio=time.monotonic();pendientes=deque(u for u,v in candidatos.items() if v['estado']=='PENDIENTE');activos={}
    while pendientes or activos:
        if time.monotonic()-inicio>=total:break
        while pendientes and len(activos)<concurrencia:
            url=pendientes.popleft()
            p=subprocess.Popen([sys.executable,__file__,'--worker',url],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
            activos[p.pid]=(p,url,time.monotonic())
        for pid,(p,url,comienzo) in list(activos.items()):
            if p.poll() is not None:
                out,err=p.communicate()
                try:valor=json.loads(out) if p.returncode==0 else {'url':url,'estado':'ERROR','error':err[-1000:]}
                except ValueError:valor={'url':url,'estado':'ERROR','error':'Worker sin JSON válido'}
                candidatos[url]=valor;del activos[pid]
            elif time.monotonic()-comienzo>=por_enlace:
                terminar(p);p.communicate();candidatos[url]={'url':url,'estado':'TIEMPO_ENLACE'};del activos[pid]
        if activos:time.sleep(0.05)
    for p,url,_ in activos.values():
        terminar(p);p.communicate();candidatos[url]={'url':url,'estado':'TIEMPO_TOTAL'}
    for u in pendientes:candidatos[u]={'url':u,'estado':'NO_INICIADO_PLAZO_TOTAL'}
    for valor in candidatos.values():
        valor['fecha_comprobacion']=fecha
        for r in vinculos.get(valor['url'],[]):
            r.setdefault('auditoria_documentos',[]).append(valor)
            proc=o.procedimiento_canonico(r)
            procs=valor.get('procedimientos',[])
            pertenece=procs==[proc]
            etiqueta=next((d.get('titulo','') for d in r.get('documentos',[]) if d['url']==valor['url']),'')
            es_pliego='pliego' in o.norm(etiqueta) or (pertenece and valor.get('contiene_pliego'))
            if es_pliego and valor['estado']=='DOCUMENTO_ACCESIBLE':
                r['enlace_pliego']=valor['url'];r['comprobacion_pliego']={**valor,'identificacion':'ENLACE_OFICIAL_ETIQUETADO' if 'pliego' in o.norm(etiqueta) else 'CONTENIDO_Y_PROCEDIMIENTO'}
            if pertenece and valor.get('presupuesto') and not r.get('presupuesto'):
                r['presupuesto']=valor['presupuesto'];r.setdefault('evidencias_campos',{})['presupuesto']=valor['evidencia_presupuesto']
        print('AUDITORIA_ADJUNTO '+json.dumps(valor,ensure_ascii=False),flush=True)
    for r in registros:
        if r.get('vigencia')!='ABIERTA':continue
        u=r.get('enlace_pliego')
        if u and not r.get('comprobacion_pliego'):
            r['comprobacion_pliego']=candidatos.get(u,{'url':u,'estado':'NO_COMPROBADO','fecha_comprobacion':fecha})
        if not u:r['comprobacion_pliego']={'estado':'NO_IDENTIFICADO','fecha_comprobacion':fecha}
    return list(candidatos.values())

if __name__=='__main__':
    try:print(json.dumps(worker(sys.argv[2]),ensure_ascii=False))
    except Exception as e:print(json.dumps({'url':sys.argv[2],'estado':'ERROR','error':str(e)}))
