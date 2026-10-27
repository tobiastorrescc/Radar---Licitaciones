"""Comprueba adjuntos de abiertas con procesos aislados, TLS validado y plazo global."""
from collections import deque
from datetime import datetime
from hashlib import sha256
import json
import os
import re
from pathlib import Path
import signal
import subprocess
import sys
import time
from urllib.parse import urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
import documentos
import cache_documentos
import pagos
import extractores
import oportunidades as o


def worker(url):
    raw,tipo,final,cache=cache_documentos.obtener(url)
    if (urlparse(final).hostname or '').removeprefix('www.')!=(urlparse(url).hostname or '').removeprefix('www.'):
        return {'url':url,'url_final':final,'estado':'REDIRECCION_OTRO_DOMINIO'}
    clase='PDF' if raw.startswith(b'%PDF-') else ('ZIP_O_DOCX' if raw.startswith(b'PK') else None)
    if not clase:return {'url':url,'url_final':final,'estado':'NO_ES_DOCUMENTO','tipo':tipo,'error':'Respuesta HTML/u otro contenido; HTTP 200 no valida pliego'}
    r={'url':url,'url_final':final,'estado':'DOCUMENTO_ACCESIBLE','tipo':clase,'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'cache_estado':cache['cache_estado'],'fecha_descarga':cache.get('descargado'),'revalidado':cache.get('revalidado')}
    try:
        texto,texto_meta=cache_documentos.leer_texto(raw,tipo,final,ocr=False)
        r['cache_texto']=texto_meta['cache_texto']
        r['pagos']=pagos.extraer(texto,final,r['sha256'],pdf=clase=='PDF',metodo=texto_meta['metodo'])
        r['pago_mencionado']=bool(pagos.INICIO.search(pagos.norm(texto)))
        r['version_pago']=pagos.VERSION
        ps=extractores.procesos(texto)
        r['procedimientos']=sorted({o.procedimiento_canonico({'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'url':final}) for p in ps}-{None})
        r['encabezado_pliego']=bool(re.search(r'(?im)^\s*pliego\s+(?:de\s+)?(?:bases|condiciones|especificaciones)',texto[:4000]))
        r['encabezado']=o.norm(texto[:500])
        r['presupuesto'],fragmento=o.monto(o.norm(texto))
        if fragmento:r['evidencia_presupuesto']={'url':final,'texto':fragmento}
    except Exception as e:r['lectura_pendiente']=str(e)
    return r


def pertenece_a(procs,proc):
    if procs==[proc]:return True
    def nucleo(p):
        p=(p or '').replace('compra directa ','contratacion directa ')
        codigo=re.search(r'\b(LPU|LPR|CPRV|CD)-(20\d{2})-(\d+)(.*)$',p or '',re.I)
        if codigo:return (p[:codigo.start()].strip(),str(int(codigo[3]))+'/'+codigo[2],bool(codigo[4]))
        m=re.fullmatch(r'(.*?) (\d+/20\d{2})',p or '')
        return (m[1],m[2],False) if m else None
    # Número anual sin serie en el PDF, relacionado explícitamente desde la ficha.
    a=nucleo(procs[0]) if len(procs)==1 else None;b=nucleo(proc)
    return bool(a and b and not a[2] and a[:2]==b[:2])


def prioridad_pliego(valor,etiqueta,proc):
    nombre=valor['url'].rsplit('/',1)[-1].lower()
    if re.search(r'^(?:resconj|resolucion|decreto|adjudicacion)',nombre) or re.match(r'^(?:resolucion|decreto)\b',o.norm(etiqueta)):
        return 0
    if re.search(r'\bplieg(?:o|os)?(?:\b|[-_.])',o.norm(etiqueta)+' '+nombre):return 2
    if valor.get('encabezado_pliego') and pertenece_a(valor.get('procedimientos',[]),proc):return 1
    return 0


def terminar(proceso):
    try:os.killpg(proceso.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proceso.wait(timeout=2)


def comprobar(registros,fecha,configuraciones,por_enlace=15,total=180,concurrencia=4,salida_parcial=None):
    candidatos={};vinculos={}
    configs={f['url']:f for f in configuraciones if f.get('url')}
    ordenados=sorted(registros,key=lambda r:({'ABIERTA':0,'DESCONOCIDA':1,'VENCIDA':2}.get(r.get('vigencia'),1),r.get('fecha_apertura') or '9999',r.get('fuente') or ''))
    for r in ordenados:
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        conf=configs.get(r.get('fuente'),{})
        host=lambda u:(urlparse(u).hostname or '').lower().removeprefix('www.')
        permitidos={host(r.get('fuente') or r['url']),*(h.removeprefix('www.') for h in conf.get('dominios_documentos',[]))}
        for d in r.get('documentos',[]):
            u=d['url']
            if host(u) not in permitidos:
                candidatos.setdefault(u,{'url':u,'estado':'DOMINIO_NO_DECLARADO'});continue
            candidatos.setdefault(u,{'url':u,'estado':'PENDIENTE'})
            vinculos.setdefault(u,[]).append(r)
    def guardar_parcial(valor):
        if salida_parcial:
            ruta=Path(salida_parcial);ruta.parent.mkdir(parents=True,exist_ok=True)
            with ruta.open('a',encoding='utf-8') as archivo:archivo.write(json.dumps(valor,ensure_ascii=False)+'\n')
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
                candidatos[url]=valor;guardar_parcial(valor);del activos[pid]
            elif time.monotonic()-comienzo>=por_enlace:
                terminar(p);p.communicate();candidatos[url]={'url':url,'estado':'TIEMPO_ENLACE'};del activos[pid]
        if activos:time.sleep(0.05)
    for p,url,_ in activos.values():
        terminar(p);p.communicate();candidatos[url]={'url':url,'estado':'TIEMPO_TOTAL'}
    for u in pendientes:candidatos[u]={'url':u,'estado':'NO_INICIADO_PLAZO_TOTAL'}
    for valor in candidatos.values():
        valor['fecha_comprobacion']=datetime.now(o.ZONA).isoformat()
        for r in vinculos.get(valor['url'],[]):
            r.setdefault('auditoria_documentos',[]).append(valor)
            proc=o.procedimiento_canonico(r)
            procs=valor.get('procedimientos',[])
            pertenece=pertenece_a(procs,proc)
            etiqueta=next((d.get('titulo','') for d in r.get('documentos',[]) if d['url']==valor['url']),'')
            # La vinculación oficial no basta si el texto nombra otro procedimiento.
            compatible=pertenece or not procs
            if compatible and valor.get('pagos'):
                r['pago_evidencias']=pagos.unir_evidencias(r.get('pago_evidencias'),valor['pagos'])
            prioridad=prioridad_pliego(valor,etiqueta,proc)
            if prioridad and valor['estado']=='DOCUMENTO_ACCESIBLE' and prioridad>r.get('comprobacion_pliego',{}).get('prioridad_identificacion',0):
                r['enlace_pliego']=valor['url'];r['comprobacion_pliego']={**valor,'prioridad_identificacion':prioridad,'identificacion':'ENLACE_OFICIAL_ETIQUETADO' if prioridad==2 else 'ENCABEZADO_Y_PROCEDIMIENTO'}
            if pertenece and valor.get('presupuesto') and not r.get('presupuesto'):
                r['presupuesto']=valor['presupuesto'];r.setdefault('evidencias_campos',{})['presupuesto']=valor['evidencia_presupuesto']
        print('AUDITORIA_ADJUNTO '+json.dumps({**{k:v for k,v in valor.items() if k!='pagos'},'clausulas_pago':len(valor.get('pagos',[]))},ensure_ascii=False),flush=True)
    for r in registros:
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        if not r.get('pago_evidencias'):
            intentos=[candidatos[d['url']] for d in r.get('documentos',[]) if d['url'] in candidatos]
            if not r.get('documentos'):motivo='SIN_DOCUMENTO_IDENTIFICADO'
            elif any(v['estado'].startswith(('NO_INICIADO','TIEMPO')) for v in intentos):motivo='PENDIENTE_PLAZO_AUDITORIA'
            elif any(v.get('lectura_pendiente') for v in intentos):motivo='REQUIERE_OCR_O_LECTURA'
            elif any(v['estado']!='DOCUMENTO_ACCESIBLE' for v in intentos):motivo='DOCUMENTO_NO_COMPROBADO'
            else:motivo='SIN_CLAUSULA_PAGO_COMPROBADA'
            r['pago_motivo_pendiente']=motivo
        if r.get('vigencia')!='ABIERTA':continue
        u=r.get('enlace_pliego')
        if u and not r.get('comprobacion_pliego'):
            r['comprobacion_pliego']=candidatos.get(u,{'url':u,'estado':'NO_COMPROBADO','fecha_comprobacion':fecha})
        if not u:r['comprobacion_pliego']={'estado':'NO_IDENTIFICADO','fecha_comprobacion':fecha}
    return list(candidatos.values())

if __name__=='__main__':
    try:print(json.dumps(worker(sys.argv[2]),ensure_ascii=False))
    except Exception as e:print(json.dumps({'url':sys.argv[2],'estado':'ERROR','error':str(e)}))
