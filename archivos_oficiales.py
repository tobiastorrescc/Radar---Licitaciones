"""Respaldo local auditable de descargas oficiales; no red, OCR ni análisis comercial."""
from datetime import datetime,timedelta
from hashlib import sha256
from pathlib import Path
from urllib.parse import urlsplit
import json,re
import conectores,extractores,oportunidades as o

RAIZ=Path('entradas_oficiales')

def clave(entrada):
    return sha256('|'.join(str(entrada.get(k,'')) for k in ('fuente_id','url_oficial','sha256')).encode()).hexdigest()


def configuracion(entrada):
    fs=json.loads(Path('inventario/fuentes.json').read_text())
    f=next((x for x in fs if x['id']==entrada['fuente_id']),None)
    if not f:raise ValueError('Fuente no configurada')
    u=extractores.url_publica(entrada['url_oficial']);p=urlsplit(u or '')
    permitidos={conectores._host(f['url']),*(conectores._host(x) for x in f.get('urls_inicio',[]))}
    permitidos.update(conectores._host('https://'+h) for h in f.get('dominios_documentos',[]))
    if p.scheme not in ('https','http') or conectores._host(u) not in permitidos or re.search(r'(?:token|password|api_key|access_key)=',p.query,re.I):raise ValueError('URL fuera de los dominios oficiales de la fuente')
    return f,u

def leer(entrada,raiz=RAIZ,ahora=None):
    f,url=configuracion(entrada);raiz=Path(raiz).resolve();p=(raiz/entrada['archivo']).resolve()
    if not p.is_relative_to(raiz) or not p.is_file():raise ValueError('Archivo fuera de la bandeja o inexistente')
    if p.stat().st_size>12_000_000:raise ValueError('Archivo excede 12 MB')
    b=p.read_bytes();digest=sha256(b).hexdigest()
    if digest!=entrada['sha256']:raise ValueError('La huella no coincide con el archivo')
    ahora=datetime.fromisoformat(ahora) if isinstance(ahora,str) else ahora or datetime.now(o.ZONA)
    fecha=datetime.fromisoformat(entrada['capturado_en']) if entrada.get('capturado_en') else None
    if fecha is not None and (not fecha.tzinfo or fecha>ahora+timedelta(minutes=5)):raise ValueError('Fecha de captura sin zona o futura')
    tipo=entrada['tipo'];errores=[]
    if tipo=='text/csv':
        from fuentes_criticas import gestiones_csv
        rs,errores=gestiones_csv(b,url,url)
    elif tipo=='application/pdf':
        import cache_documentos
        texto,_=cache_documentos.leer_texto(b,tipo,url,ocr=False)
        if f.get('adaptador')=='boletin-sf':
            from extractores_lotes import boletin_texto
            rs=boletin_texto(texto,url,f)
        elif f.get('adaptador')=='boletin-er':
            from barrido_institucional import boletin_entre_rios
            rs=boletin_entre_rios(texto,url)
        else:
            config={**f,'urls_inicio':[url],'solo_descubrimiento':False,'ocr':False,'reintentos_transitorios':0,'consultas_respaldo':[]}
            resultado=conectores.explorar(url,config,max_paginas=1,fetch=lambda u:(b,tipo,url))
            rs=resultado['oportunidades'];errores=resultado['errores']
    elif tipo=='text/html':
        html=conectores.decodificar_html(b,tipo);rs,_,dom=extractores.extraer(html,url,f)
        if f.get('adaptador')=='gestiones-sf':
            from fuentes_criticas import gestiones_html
            rs=gestiones_html(dom,url) or rs
    else:raise ValueError('Formato de archivo no admitido: '+tipo)
    if not rs:raise ValueError('Archivo sin convocatorias reconocidas; no equivale a ausencia de novedades')
    recibo=entrada.get('recibo',{})
    reciente=fecha is not None and timedelta(0)<=ahora-fecha<=timedelta(hours=72)
    procedencia=(recibo.get('metodo')=='HTTP_OFICIAL' and recibo.get('codigo_http')==200 and recibo.get('url_final')==url and recibo.get('sha256')==digest)
    pendiente=not(procedencia and reciente)
    salida=[]
    for r in rs:
        registro={k:f.get(k) for k in ('organismo','localidad','provincia')}
        registro.update(r);registro.update(fuente=f['url'],rango_evidencia=-1 if pendiente else 1,requiere_revalidacion=pendiente,
            recuperacion_archivo={'sha256':digest,'url_oficial':url,'capturado_en':entrada.get('capturado_en'),'metodo':'ARCHIVO_OFICIAL','procedencia':'RECIBO_HTTP_OFICIAL' if procedencia else 'PROCEDENCIA_PENDIENTE','revalidacion_pendiente':pendiente})
        salida.append(o.normalizar(registro,ahora))
    return o.deduplicar(salida,ahora),errores


def importar(salida,manifest='entradas_oficiales',total=60,vistos=()):
    """Procesos con plazo duro: un PDF ilegible no detiene los otros archivos."""
    from tools.verificar_fuentes import ejecutar,guardar
    import sys
    root=Path(manifest);fs=[];omitidos=0
    if not root.exists():return [],{'archivos':0,'observaciones':[]}
    for p in sorted(root.glob('*.json')):
        try:
            if clave(json.loads(p.read_text())) in vistos:omitidos+=1;continue
        except (ValueError,TypeError):pass
        fs.append({'id':'archivo-'+sha256(str(p).encode()).hexdigest()[:20],'url':'archivo://'+p.name,'archivo_entrada':str(p)})
    destino=Path(salida);destino.mkdir(parents=True,exist_ok=True)
    if not fs:return [],{'archivos':0,'observaciones':[],'ya_importados':omitidos}
    informe=ejecutar(fs,destino/'importacion.json',concurrencia=2,por_fuente=40,total=total,
        comando=lambda f,path:[sys.executable,'tools/importar_oficiales.py','--worker',f['archivo_entrada'],'--checkpoint',str(path)])
    informe['ya_importados']=omitidos
    informe['metodo']='IMPORTACION_LOCAL_ARCHIVOS_OFICIALES; no acredita acceso en vivo al portal'
    informe['fuentes_recuperadas_en_vivo']=0
    guardar(destino/'importacion.json',informe)
    rs=[]
    for obs in informe['observaciones']:
        p=Path(obs.get('resultado_archivo',''))
        if p.is_file():rs.extend(json.loads(p.read_text()).get('oportunidades',[]))
    guardar(destino/'registros.json',rs)
    return rs,informe


def vistos(dbpath):
    import sqlite3
    p=Path(dbpath)
    if not p.exists():return set()
    with sqlite3.connect('file:'+str(p)+'?mode=ro',uri=True) as db:
        return {x[0].split(':',1)[1] for x in db.execute("SELECT clave FROM meta WHERE clave LIKE 'archivo_importado:%'")}


def registrar_recibos(db,informe):
    from tools.verificar_fuentes import leer_checkpoint
    with db:
        for obs in informe.get('observaciones',[]):
            if obs['estado']!='OPERATIVA':continue
            dato=leer_checkpoint(obs['resultado_archivo']);digest=dato.get('archivo_clave')
            if digest:db.execute('INSERT OR IGNORE INTO meta VALUES (?,?)',('archivo_importado:'+digest,json.dumps({'fecha':informe['actualizado'],'archivo':dato.get('archivo_entrada')})))
