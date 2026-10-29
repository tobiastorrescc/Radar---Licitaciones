"""Cache documental compartida: validadores HTTP, bytes por hash y texto extraído."""
from datetime import datetime, timezone
from hashlib import sha256
import json
import os
from pathlib import Path
import time
from urllib.error import HTTPError
import uuid


def raiz():
    return Path(os.environ.get('RADAR_CACHE_DOCUMENTOS','work/cache-documentos'))


def atomico(path,data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name(path.name+'.'+uuid.uuid4().hex+'.tmp')
    tmp.write_bytes(data if isinstance(data,bytes) else json.dumps(data,ensure_ascii=False).encode())
    os.replace(tmp,path)


def obtener(url,transport=None,fresco=300,sin_validadores=21600,reloj=time.time):
    if transport is None:
        import conectores
        transport=conectores.descargar
    base=raiz()/'http';meta_path=base/'urls'/(sha256(url.encode()).hexdigest()+'.json')
    anterior={};datos=None
    try:
        anterior=json.loads(meta_path.read_text())
        blob=base/'bytes'/(anterior['sha256']+'.bin')
        datos=blob.read_bytes()
        if sha256(datos).hexdigest()!=anterior['sha256']:datos=None
    except (OSError,ValueError,KeyError,TypeError,AttributeError):anterior={}
    ahora=reloj();edad=ahora-anterior.get('comprobado_epoch',0)
    if datos is not None and 0<=edad<(fresco if anterior.get('etag') or anterior.get('last_modified') else sin_validadores):
        os.utime(blob,None)
        return datos,anterior['tipo'],anterior['final'],{**anterior,'cache_estado':'CACHE_RECIENTE','edad_segundos':round(edad,3)}
    headers={}
    if datos is not None:
        if anterior.get('etag'):headers['If-None-Match']=anterior['etag']
        if anterior.get('last_modified'):headers['If-Modified-Since']=anterior['last_modified']
    try:
        resultado=transport(url,conexion_timeout=5,lectura_timeout=8,headers_extra=headers,devolver_headers=True)
    except HTTPError as e:
        if e.code!=304 or datos is None:raise
        meta={**anterior,'comprobado_epoch':ahora,'revalidado':datetime.fromtimestamp(ahora,timezone.utc).isoformat()}
        atomico(meta_path,meta);os.utime(blob,None)
        return datos,meta['tipo'],meta['final'],{**meta,'cache_estado':'HTTP_304','edad_segundos':0}
    if len(resultado)==4:datos,tipo,final,h=resultado
    else:datos,tipo,final=resultado;h={}
    h={k.lower():v for k,v in h.items()}
    documento=datos.startswith((b'%PDF-',b'PK',b'\xff\xd8',b'\x89PNG'))
    meta={'url':url,'final':final,'tipo':tipo,'sha256':sha256(datos).hexdigest(),'bytes':len(datos),
          'etag':h.get('etag'),'last_modified':h.get('last-modified'),'descargado':datetime.fromtimestamp(ahora,timezone.utc).isoformat(),'comprobado_epoch':ahora}
    if documento:
        atomico(base/'bytes'/(meta['sha256']+'.bin'),datos);atomico(meta_path,meta)
    return datos,tipo,final,{**meta,'cache_estado':'HTTP_200' if documento else 'NO_DOCUMENTO_NO_CACHEADO','edad_segundos':0}


def leer_texto(datos,tipo,url,ocr=False,progreso=None):
    import documentos
    digest=sha256(datos).hexdigest();path=raiz()/'textos'/(digest+'.json')
    try:
        r=json.loads(path.read_text())
        if r.get('version')==1 and r.get('sha256')==digest:return r['texto'],{**r,'cache_texto':True}
    except (OSError,ValueError,KeyError,TypeError,AttributeError):pass
    legacy=raiz()/(sha256(datos+b'ocr-v1').hexdigest()+'.txt')
    if legacy.exists():texto=legacy.read_text();metodo='CACHE_LEGADO'
    else:
        texto=documentos.leer(datos,tipo,url,ocr=ocr,progreso=progreso);metodo='TEXTO_O_OCR' if ocr else 'TEXTO'
    r={'version':1,'sha256':digest,'texto':texto,'metodo':metodo}
    # Nunca guardar como completo el avance de un OCR interrumpido.
    if texto.strip():atomico(path,r)
    return texto,{**r,'cache_texto':False}


def limpiar(max_bytes=512*1024*1024):
    archivos=list((raiz()/'http'/'bytes').glob('*.bin'))
    tamano=sum(p.stat().st_size for p in archivos)
    eliminados=0
    for p in sorted(archivos,key=lambda p:p.stat().st_mtime):
        if tamano<=max_bytes:break
        tamano-=p.stat().st_size;p.unlink();eliminados+=1
    return {'bytes_conservados':tamano,'archivos_evictados':eliminados,'max_bytes':max_bytes}
