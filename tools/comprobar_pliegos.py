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
import fichas
import extractores
import oportunidades as o


def worker(url,consulta_post=None,opciones=None):
    transporte=None
    if consulta_post:
        # Endpoint público de lectura observado en el cliente oficial. No hay
        # soporte genérico para POST de registros, ofertas ni autenticación.
        endpoint=consulta_post.get('url');params=consulta_post.get('json',{})
        if (urlparse(url).hostname!='licitaciones.chajari.gob.ar' or endpoint!='https://licitaciones.chajari.gob.ar/return_file'
            or set(params)!={'atta_id','file_name','licitacion_id'} or params['file_name']!='pliego_y_decreto'
            or not str(params['atta_id']).isdigit() or not str(params['licitacion_id']).isdigit()):raise ValueError('Petición documental pública no admitida')
        def transporte(u,**kwargs):
            import base64
            datos,_,destino=conectores.descargar(endpoint,datos_post=json.dumps(params).encode(),headers_extra={'Content-Type':'application/json'},conexion_timeout=5,lectura_timeout=8)
            if destino!=endpoint:raise ValueError('Redirección del endpoint documental')
            respuesta=json.loads(datos).get('result')
            if not isinstance(respuesta,dict) or not respuesta.get('file64'):raise ValueError('El portal no entregó un documento público')
            contenido=base64.b64decode(respuesta['file64'],validate=True)
            if len(contenido)>12_000_000 or not contenido.startswith(b'%PDF-'):raise ValueError('Respuesta documental no es PDF admisible')
            return contenido,respuesta.get('mime') or 'application/pdf',url,{}
    raw,tipo,final,cache=cache_documentos.obtener(url,transport=transporte)
    if (urlparse(final).hostname or '').removeprefix('www.')!=(urlparse(url).hostname or '').removeprefix('www.'):
        return {'url':url,'url_final':final,'estado':'REDIRECCION_OTRO_DOMINIO'}
    clase='PDF' if raw.startswith(b'%PDF-') else ('ZIP_O_DOCX' if raw.startswith(b'PK') else ('XLS' if raw.startswith(b'\xd0\xcf\x11\xe0') else None))
    if not clase:return {'url':url,'url_final':final,'estado':'NO_ES_DOCUMENTO','tipo':tipo,'error':'Respuesta HTML/u otro contenido; HTTP 200 no valida pliego'}
    r={'url':url,'url_final':final,'consulta_post':consulta_post,'estado':'DOCUMENTO_ACCESIBLE','tipo':clase,'bytes':len(raw),'sha256':sha256(raw).hexdigest(),'cache_estado':cache['cache_estado'],'fecha_descarga':cache.get('descargado'),'revalidado':cache.get('revalidado')}
    try:
        try: texto,texto_meta=cache_documentos.leer_texto(raw,tipo,final,ocr=False)
        except ValueError:
            if clase!='PDF' or not ((opciones or {}).get('ocr_selectivo') or documentos.ocr_en_cache(raw)):raise
            texto='';texto_meta={'cache_texto':'SIN_TEXTO','metodo':'PDF'}
        necesita_ocr=not texto.strip() or any(len(re.sub(r'[^A-Za-zÁÉÍÓÚáéíóúÑñ]','',p))<20 for p in texto.rstrip('\f').split('\f'))
        cache_ocr=documentos.ocr_en_cache(raw) if clase=='PDF' and necesita_ocr else None
        if cache_ocr:
            texto,meta_ocr=cache_ocr;r['ocr_selectivo']=meta_ocr;texto_meta['metodo']='OCR_SELECTIVO_CACHE'
        elif clase=='PDF' and necesita_ocr and (opciones or {}).get('ocr_selectivo'):
            r['ocr_intentado']=True
            texto,meta_ocr=documentos.ocr_selectivo(raw,max_paginas=(opciones or {}).get('max_paginas',4))
            r['ocr_selectivo']=meta_ocr;texto_meta['metodo']='OCR_SELECTIVO'
            if not meta_ocr['completa']:r['lectura_pendiente']='OCR selectivo parcial: quedan páginas sin leer'
        r['cache_texto']=texto_meta['cache_texto']
        paginas=texto.split('\f')
        if paginas and not paginas[-1].strip():paginas=paginas[:-1]
        if not r.get('ocr_selectivo',{}).get('completa') and any(len(re.sub(r'[^A-Za-zÁÉÍÓÚáéíóúÑñ]','',p))<20 for p in paginas):r['lectura_pendiente']='Documento con páginas sin texto suficiente: requiere OCR; no se presume ausencia de cláusulas'
        r['pagos']=pagos.extraer(texto,final,r['sha256'],pdf=clase=='PDF',metodo=texto_meta['metodo'])
        if r.get('lectura_pendiente'):
            r['pagos_pendientes_revision']=r['pagos'];r['pagos']=[]
        r['pago_mencionado']=bool(pagos.INICIO.search(pagos.norm(texto)))
        r['version_pago']=pagos.VERSION
        r['detalles_documento']=fichas.extraer(texto,final,r['sha256'],texto_meta['metodo'])
        ps=extractores.procesos(texto)
        r['procedimientos']=sorted({o.procedimiento_canonico({'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'url':final}) for p in ps}-{None})
        r['encabezado_pliego']=bool(re.search(r'(?im)^\s*pliego\s+(?:de\s+)?(?:bases|condiciones|especificaciones)',texto[:4000]))
        r['encabezado']=o.norm(texto[:500])
        extraido=o.normalizar({'titulo':'Documento oficial','objeto':texto,'texto_documento':texto,'url':final,'evidencia_url':final})
        campos=('fecha_apertura','hora_apertura','fecha_publicacion','fecha_limite_presentacion','hora_limite_presentacion','modalidad_presentacion')
        r['campos_documento']={k:extraido[k] for k in campos if extraido.get(k)}
        r['publicacion_rotulada']=bool(re.search(r'fecha\s+de\s+publicaci[oó]n\s*:',texto,re.I))
        r['evidencias_documento']={k:v for k,v in extraido.get('evidencias_campos',{}).items() if k in campos}
        r['presupuesto'],fragmento=o.monto(o.norm(texto))
        if fragmento:r['evidencia_presupuesto']={'url':final,'texto':fragmento}
    except Exception as e:r['lectura_pendiente']=str(e)
    return r


def pertenece_a(procs,proc,url_documento=None):
    if procs==[proc]:return True
    # Un salto de línea puede cortar el código PDF en APPSF-OD. Se completa
    # únicamente con el código observado en la URL oficial del mismo adjunto.
    if len(procs)==1 and proc and url_documento:
        limpio=lambda t:re.sub(r'[^a-z0-9]','',o.norm(t))
        parcial=limpio(procs[0]);destino=limpio(proc)
        if destino.startswith(parcial):
            for p in extractores.procesos(url_documento):
                codigo=o.procedimiento_canonico({'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo']})
                completo=limpio(codigo)
                if len(completo)>len(parcial) and completo.startswith(parcial) and destino.startswith(completo):return True
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
    if valor.get('encabezado_pliego') and pertenece_a(valor.get('procedimientos',[]),proc,valor['url']):return 1
    return 0


def terminar(proceso):
    try:os.killpg(proceso.pid,signal.SIGKILL)
    except ProcessLookupError:pass
    proceso.wait(timeout=2)


def ordenar_documentos(candidatos,vinculos,fecha):
    # Reparto entre fuentes: un archivo grande no monopoliza todo el plazo.
    anio=fecha[:4];grupos={}
    for url,valor in candidatos.items():
        if valor['estado']!='PENDIENTE':continue
        registros=vinculos.get(url,[])
        prioridad=min((0 if r.get('vigencia')=='ABIERTA' else (1 if anio in str(r.get('numero_procedimiento')) else 2) for r in registros),default=2)
        fuente=next((r.get('fuente') for r in registros if r.get('fuente')),url)
        grupos.setdefault(prioridad,{}).setdefault(fuente,deque()).append(url)
    orden=[]
    for prioridad in sorted(grupos):
        fuentes=grupos[prioridad]
        while any(fuentes.values()):
            for fuente in sorted(fuentes):
                if fuentes[fuente]:orden.append(fuentes[fuente].popleft())
    return deque(orden)


def comprobar(registros,fecha,configuraciones,por_enlace=15,total=180,concurrencia=4,salida_parcial=None,ocr_paginas=4):
    if not 1<=ocr_paginas<=10:raise ValueError('Cupo OCR inválido')
    candidatos={};vinculos={};peticiones={}
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
            if d.get('consulta_post'):peticiones[u]=d['consulta_post']
            vinculos.setdefault(u,[]).append(r)
    def guardar_parcial(valor):
        if salida_parcial:
            ruta=Path(salida_parcial);ruta.parent.mkdir(parents=True,exist_ok=True)
            with ruta.open('a',encoding='utf-8') as archivo:archivo.write(json.dumps(valor,ensure_ascii=False)+'\n')
    inicio=time.monotonic();pendientes=ordenar_documentos(candidatos,vinculos,fecha);activos={};seleccion_ocr=set()
    while pendientes or activos:
        if time.monotonic()-inicio>=total:break
        while pendientes and len(activos)<concurrencia:
            # Descargas POST grandes del mismo portal se serializan para no
            # saturarlo. El resto de las fuentes mantiene su concurrencia.
            url=None
            for _ in range(len(pendientes)):
                candidato=pendientes.popleft()
                if candidato in peticiones and any(u in peticiones and urlparse(u).hostname==urlparse(candidato).hostname for _,u,_ in activos.values()):
                    pendientes.append(candidato);continue
                url=candidato;break
            if url is None:break
            # Cupo de tres documentos, sólo convocatorias abiertas sin pago comprobado.
            ocr=bool(len(seleccion_ocr)<3 and any(r.get('vigencia')=='ABIERTA' and r.get('pago',{}).get('estado')!='VERIFICADO' for r in vinculos.get(url,[])))
            if ocr:seleccion_ocr.add(url)
            p=subprocess.Popen([sys.executable,__file__,'--worker',url,json.dumps(peticiones.get(url)),json.dumps({'ocr_selectivo':ocr,'max_paginas':ocr_paginas})],stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,start_new_session=True)
            activos[p.pid]=(p,url,time.monotonic())
        for pid,(p,url,comienzo) in list(activos.items()):
            if p.poll() is not None:
                out,err=p.communicate()
                try:valor=json.loads(out) if p.returncode==0 else {'url':url,'estado':'ERROR','error':err[-1000:]}
                except ValueError:valor={'url':url,'estado':'ERROR','error':'Worker sin JSON válido'}
                # Los PDF nativos no consumen el cupo de OCR reservado.
                if url in seleccion_ocr and not valor.get('ocr_intentado') and p.returncode==0:seleccion_ocr.remove(url)
                candidatos[url]=valor;guardar_parcial(valor);del activos[pid]
            elif time.monotonic()-comienzo>=(max(por_enlace,75) if url in seleccion_ocr else max(por_enlace,45) if url in peticiones else por_enlace):
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
            pertenece=pertenece_a(procs,proc,valor['url'])
            etiqueta=next((d.get('titulo','') for d in r.get('documentos',[]) if d['url']==valor['url']),'')
            # La vinculación oficial no basta si el texto nombra otro procedimiento.
            compatible=pertenece or not procs
            if compatible and valor.get('detalles_documento'):
                r.setdefault('detalle_documental',{}).update(valor['detalles_documento'])
                for campo in ('objeto','modalidad_presentacion'):
                    if campo in valor['detalles_documento']:r[campo]=valor['detalles_documento'][campo]['valor']
            if compatible and valor.get('pagos'):
                r['pago_evidencias']=pagos.unir_evidencias(r.get('pago_evidencias'),valor['pagos'])
            prioridad=prioridad_pliego(valor,etiqueta,proc)
            if compatible and prioridad and valor['estado']=='DOCUMENTO_ACCESIBLE' and prioridad>r.get('comprobacion_pliego',{}).get('prioridad_identificacion',0):
                r['enlace_pliego']=valor['url'];r['comprobacion_pliego']={**valor,'prioridad_identificacion':prioridad,'identificacion':'ENLACE_OFICIAL_ETIQUETADO' if prioridad==2 else 'ENCABEZADO_Y_PROCEDIMIENTO'}
            if pertenece:
                for campo,contenido in valor.get('campos_documento',{}).items():
                    if campo=='fecha_publicacion' and not valor.get('publicacion_rotulada'):continue
                    if not r.get(campo):
                        r[campo]=contenido
                        if campo in valor.get('evidencias_documento',{}):r.setdefault('evidencias_campos',{})[campo]=valor['evidencias_documento'][campo]
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
    try:print(json.dumps(worker(sys.argv[2],json.loads(sys.argv[3]) if len(sys.argv)>3 else None,json.loads(sys.argv[4]) if len(sys.argv)>4 else None),ensure_ascii=False))
    except Exception as e:print(json.dumps({'url':sys.argv[2],'estado':'ERROR','error':str(e)}))
