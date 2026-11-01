"""Reconstruye referencias oficiales de todos los blobs alcanzables, sin red/OCR.

No promueve fuentes: una URL histórica no demuestra acceso ni extracción actual.
"""
import argparse,base64,csv,gzip,json,re,subprocess,sys,time,zlib
from collections import Counter
from hashlib import sha256
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))

URL=re.compile(r'https?://[^\s<>"\'`\\\]]+')
TEXTOS=('.json','.txt','.md','.py','.html','.csv','.yml','.yaml','.b64')

def normalizar_url(u):
    u=unescape(u).rstrip('.,;:)}')
    try:p=urlsplit(u);host=(p.hostname or '').encode('idna').decode().lower()
    except (ValueError,UnicodeError):return None
    if p.scheme not in ('http','https') or not host or p.username or p.password:return None
    try:net=host+(':'+str(p.port) if p.port else '')
    except ValueError:return None
    return urlunsplit((p.scheme,net,p.path or '/',p.query,p.fragment))

def oficial(u,hosts):
    host=(urlsplit(u).hostname or '').removeprefix('www.')
    return host.endswith(('.gob.ar','.gov.ar','.edu.ar')) or host in hosts

def tipo_url(u):
    p=urlsplit(u);t=(p.path+'?'+p.query).lower()
    if any(x in u for x in ('{','}','${')) or u.endswith(('=','?')):return 'PLANTILLA_INCOMPLETA'
    if re.search(r'\.(?:pdf|docx?|xlsx?|jpg|png|zip)(?:$|[?&])',t):return 'DOCUMENTO'
    if re.search(r'ver\.php.*seccion=|/bulletins/\d+|/contents/\d+|idgestion=|/apertura/\d+|/detalle/',t):return 'AVISO_O_BOLETIN_INTERNO'
    if re.search(r'licit|concurso|compras|contrata|boletin|proveedor|cotiza|gestiones',t):return 'PORTAL_O_SECCION'
    return 'REFERENCIA_INSTITUCIONAL'

def extraer_texto(datos,path):
    if path.endswith('.gz.b64'):datos=gzip.decompress(base64.b64decode(datos,validate=False))
    return datos.decode('utf-8-sig')

def referencias(texto,hosts):
    return {u for m in URL.finditer(texto) if (u:=normalizar_url(m.group())) and oficial(u,hosts)}

def contexto_json(obj):
    if isinstance(obj,dict):
        if obj.get('organismo'):
            urls=[obj.get(k) for k in ('url','fuente','evidencia_url','evidencia_descubrimiento','sitio_oficial') if isinstance(obj.get(k),str)]
            identidad=obj.get('id') or sha256(json.dumps([obj.get(k) for k in ('organismo','provincia','numero_procedimiento','tipo_procedimiento','numero_convocatoria')],ensure_ascii=False).encode()).hexdigest()
            for u in urls:yield u,obj,identidad if obj.get('numero_procedimiento') else None
        for v in obj.values():yield from contexto_json(v)
    elif isinstance(obj,list):
        for v in obj:yield from contexto_json(v)

def inventariar(salida,referencias_usuario='inventario/referencias_historicas_solicitadas.json'):
    inicio=time.monotonic();root=Path(salida);root.mkdir(parents=True,exist_ok=True)
    run=lambda *args:subprocess.check_output(['git',*args])
    shallow=run('rev-parse','--is-shallow-repository').decode().strip()=='true'
    if shallow:raise ValueError('Checkout superficial: usar fetch-depth:0; no se declara historial completo')
    fs=json.loads(Path('inventario/fuentes.json').read_text());hosts={(urlsplit(f['url']).hostname or '').removeprefix('www.') for f in fs}
    hosts.update((urlsplit(x).hostname or '').removeprefix('www.') for f in fs for x in ['https://'+h for h in f.get('dominios_documentos',[])])
    referencias_user=json.loads(Path(referencias_usuario).read_text())['fuentes']
    fuentes_por_url={normalizar_url(f['url']):f for f in fs};por_host={}
    for f in fs:por_host.setdefault((urlsplit(f['url']).hostname or '').removeprefix('www.'),[]).append(f)
    # Un único recorrido de diffs obtiene commit y ruta donde cada blob existe.
    evidencia={};commit=None
    for l in run('log','--all','--format=COMMIT %H','--raw','--no-abbrev','--no-renames').decode(errors='replace').splitlines():
        if l.startswith('COMMIT '):commit=l.split()[1]
        elif l.startswith(':') and '\t' in l:
            meta,path=l.split('\t',1);campos=meta.split()
            if len(campos)==5 and re.fullmatch('[0-9a-f]{40}',campos[3]) and campos[3]!='0'*40:evidencia.setdefault(campos[3],(commit,path))
    objetos={l.split(' ',1)[0]:l.split(' ',1)[1] for l in run('rev-list','--objects','--all').decode(errors='replace').splitlines() if ' ' in l}
    entradas={};leidos=0;bytes_leidos=0;omitidos=[];errores=[]
    def agregar(u,prueba):
        if u not in entradas:
            f=fuentes_por_url.get(u);candidatas=por_host.get((urlsplit(u).hostname or '').removeprefix('www.'),[])
            meta=f or (candidatas[0] if len(candidatas)==1 else {})
            entradas[u]={'url':u,'tipo_url':tipo_url(u),'organismo':meta.get('organismo'),'localidad':meta.get('localidad'),'provincia':meta.get('provincia'),'incorporada_exactamente':bool(f and f.get('incorporada')),'estado_extraccion':'PENDIENTE_VALIDACION_ACTUAL','estado_previo':f.get('estado_verificacion') if f else None,'estado_es_historico':True,'evidencias':[],'organismos_en_documentos':set(),'registros_asociados':set(),'publicaciones':['No determinado; requiere validación de la sección'],'alcance':'Pendiente contrastar organismo y localidad; no alta automática'}
        r=entradas[u]
        if prueba not in r['evidencias']:r['evidencias'].append(prueba)
    proc=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    try:
        for n,(sha,path_original) in enumerate(objetos.items()):
            path=evidencia.get(sha,(None,path_original))[1]
            if not path.endswith(TEXTOS) or path.startswith(('tests/','.git/')):continue
            proc.stdin.write((sha+'\n').encode());proc.stdin.flush();cab=proc.stdout.readline().decode().split()
            if len(cab)!=3:raise ValueError('Respuesta cat-file incompleta')
            tam=int(cab[2]);datos=proc.stdout.read(tam);proc.stdout.read(1)
            if cab[1]!='blob':continue
            if tam>64_000_000:omitidos.append({'sha':sha,'path':path,'motivo':'Tamaño superior a64MB; pendiente revisión explícita'});continue
            leidos+=1;bytes_leidos+=tam
            try:texto=extraer_texto(datos,path)
            except (ValueError,UnicodeError,OSError,EOFError,zlib.error) as e:
                errores.append({'sha':sha,'path':path,'tipo':type(e).__name__});continue
            ev={'blob_sha':sha,'commit':evidencia.get(sha,(None,None))[0],'archivo':path}
            us=referencias(texto,hosts)
            for u in us:agregar(u,ev)
            if path.endswith(('.json','.gz.b64')):
                try:obj=json.loads(texto)
                except ValueError:obj=None
                for raw,meta,identidad in contexto_json(obj):
                    u=normalizar_url(raw)
                    if u not in us:continue
                    r=entradas[u];org=meta.get('organismo');r['organismos_en_documentos'].add(org)
                    if not r.get('organismo') and meta.get('provincia') in ('Santa Fe','Entre Ríos','Buenos Aires'):
                        for k in ('organismo','localidad','provincia'):r[k]=meta.get(k)
                    if identidad:
                        r['registros_asociados'].add(str(identidad))
                        if r['tipo_url'] not in ('DOCUMENTO','PLANTILLA_INCOMPLETA') and u not in fuentes_por_url:
                            r['tipo_url']='PORTAL_O_SECCION' if normalizar_url(str(meta.get('fuente') or ''))==u else 'AVISO_O_LISTADO_CON_PROCEDIMIENTOS'
            if leidos%100==0:print(json.dumps({'blobs_leidos':leidos,'urls':len(entradas),'segundos':round(time.monotonic()-inicio,1)}),flush=True)
    finally:
        proc.stdin.close();proc.wait(timeout=5)
    for f in referencias_user:
        u=normalizar_url(f['url']);agregar(u,{'origen':'REFERENCIA_EXPLICITA_USUARIO','archivo':referencias_usuario})
        r=entradas[u];r['referencia_solicitada']=True
        for k in ('organismo','localidad','provincia','publicaciones'):r[k]=f.get(k,r.get(k))
    filas=[]
    for u,r in sorted(entradas.items()):
        r['organismos_en_documentos']=sorted(r['organismos_en_documentos']);r['registros_historicos_asociados']=len(r.pop('registros_asociados'));r['cantidad_evidencias']=len(r['evidencias']);filas.append(r)
    summary={'head':run('rev-parse','HEAD').decode().strip(),'commits_alcanzables':len(run('rev-list','--all').splitlines()),'referencias_git':run('show-ref').decode().splitlines(),'blobs_texto_revisados':leidos,'bytes_revisados':bytes_leidos,'urls_oficiales':len(filas),'por_tipo':dict(Counter(r['tipo_url'] for r in filas)),'referencias_solicitadas':len(referencias_user),'configuradas':sum(f.get('incorporada',False) for f in fs),'omitidos':omitidos,'ilegibles':errores,'segundos':round(time.monotonic()-inicio,2),'advertencia':'Completo sobre objetos alcanzables y textos legibles enumerados. No incluye mensajes manuales fuera de Git ni historia borrada/inaccesible. URL inventariada no demuestra extracción. Registros históricos asociados no son oportunidades nuevas ni vigencias comprobadas.'}
    (root/'inventario.json').write_text(json.dumps({'resumen':summary,'fuentes':filas},ensure_ascii=False)+'\n')
    cols=['url','tipo_url','organismo','localidad','provincia','publicaciones','incorporada_exactamente','estado_extraccion','estado_es_historico','referencia_solicitada','cantidad_evidencias','registros_historicos_asociados','alcance']
    with (root/'inventario.csv').open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=cols);w.writeheader()
        for r in filas:w.writerow({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r.get(k),(list,dict)) else r.get(k) for k in cols})
    (root/'resumen.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n');print(json.dumps(summary,ensure_ascii=False),flush=True)
    return summary

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--salida',default='work/historial-fuentes');p.add_argument('--referencias',default='inventario/referencias_historicas_solicitadas.json');a=p.parse_args();inventariar(a.salida,a.referencias)
