"""Descubrimiento incremental: búsqueda pública, identidad estricta y extracción real.

No escribe producción. Los resultados de búsqueda son candidatos, nunca evidencia
de funcionamiento. Cada validación se ejecuta en un proceso con plazo de pared.
"""
import argparse
from collections import Counter
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import time
from urllib.parse import urlparse, urlencode,parse_qs
import xml.etree.ElementTree as ET
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
import extractores
import oportunidades as o
from registro_fuentes import cargar_auto
from tools.verificar_fuentes import ejecutar,guardar

SECTORES=('(hospital OR SAMCo)','(universidad nacional OR universidad provincial)','(empresa pública OR ente descentralizado OR puerto OR vialidad)')
PROVINCIAS=('Santa Fe','Entre Ríos','Buenos Aires')

def host(url):return (urlparse(url).hostname or '').lower().removeprefix('www.')

def oficial(url):
    h=host(url)
    return any(h.endswith('.'+s) for s in ('gob.ar','gov.ar','edu.ar'))

def rss(datos):
    root=ET.fromstring(datos)
    return [{'url':u,'titulo':i.findtext('title') or ''} for i in root.findall('.//item')
            if (u:=extractores.url_publica(i.findtext('link') or '')) and oficial(u)]

def resultados_html(html,base):
    encontrados=[]
    for l in extractores.DOM(html).root.enlaces(base):
        if 'result__a' not in l['node'].attrs.get('class','').split():continue
        url=parse_qs(urlparse(l['url']).query).get('uddg',[l['url']])[0]
        url=extractores.url_publica(url)
        if url and oficial(url):encontrados.append({'url':url,'titulo':l['texto']})
    return encontrados

def objetivos(padron,fuentes):
    cubiertos={(o.norm(f['localidad']),f['provincia']) for f in fuentes if f.get('incorporada') and o.norm(f['organismo']).startswith(('municipalidad','comuna','gobierno de timbues'))}
    territoriales=[{'clave':'territorio:'+m['codigo'],'localidad':m['localidad'],'provincia':m['provincia'],
        'organismo':('Comuna' if 'comuna' in o.norm(m.get('tipo_gobierno')) else 'Municipalidad')+' de '+m['localidad'],
        'consulta':'"'+m['localidad']+'" "'+m['provincia']+'" compras licitaciones sitio oficial','tipo':'TERRITORIAL'}
        for m in padron['municipios'] if (o.norm(m['localidad']),m['provincia']) not in cubiertos]
    por_provincia={p:[q for q in territoriales if q['provincia']==p] for p in PROVINCIAS}
    territoriales=[grupo[i] for i in range(max((len(g) for g in por_provincia.values()),default=0)) for grupo in por_provincia.values() if i<len(grupo)]
    sectoriales=[{'clave':'sector:'+p+':'+s,'provincia':p,'consulta':'"'+p+'" '+s+' compras licitaciones sitio oficial','tipo':'SECTORIAL'} for p in PROVINCIAS for s in SECTORES]
    # Intercalar sectores evita postergarlos detrás de cientos de comunas.
    pendientes_path=Path('inventario/pendientes83.json')
    pendientes=set(json.loads(pendientes_path.read_text())['ids']) if pendientes_path.exists() else set()
    reparacion=[{'clave':'reparar:'+f['id'],'tipo':'TERRITORIAL' if o.norm(f['organismo']).startswith(('municipalidad','comuna')) else 'SECTORIAL',
        'organismo':f['organismo'],'localidad':f['localidad'],'provincia':f['provincia'],
        'consulta':'"'+f['organismo']+'" "'+f['provincia']+'" compras licitaciones sitio oficial'} for f in fuentes if f['id'] in pendientes]
    resultado=[]
    for n,item in enumerate(territoriales):
        if n<len(sectoriales):resultado.append(sectoriales[n])
        resultado.append(item)
    resto=resultado+sectoriales[len(territoriales):];resultado=[]
    for i in range(max(len(resto),len(reparacion))):
        if i<len(reparacion):resultado.append(reparacion[i])
        if i<len(resto):resultado.append(resto[i])
    # Orígenes conocidos y enlaces publicados: alternativa independiente al buscador.
    directorios=[]
    for f in fuentes:
        if f['id'] not in pendientes:continue
        origen=urlparse(f['url']);url=origen.scheme+'://'+origen.netloc+'/'
        directorios.append({'clave':'directorio:'+f['id'],'tipo':'TERRITORIAL' if o.norm(f['organismo']).startswith(('municipalidad','comuna')) else 'SECTORIAL',
            'organismo':f['organismo'],'localidad':f['localidad'],'provincia':f['provincia'],'metodo':'ENLACES_OFICIALES','url_directorio':url})
    # Rotación común: un tercio de los objetivos recorre menús oficiales.
    mezclados=[]
    for i in range(max(len(resultado),len(directorios)*2)):
        if i%2==0 and i//2<len(directorios):mezclados.append(directorios[i//2])
        if i<len(resultado):mezclados.append(resultado[i])
    return mezclados

def verificar_identidad(html,url,candidato):
    dom=extractores.DOM(html);texto=o.norm(dom.root.text)
    prov=o.norm(candidato['provincia'])
    jurisdiccion=bool(re.search(r'\b'+re.escape(prov)+r'\b',texto))
    cabeceras=' '.join(n.text for n in dom.root.iter() if n.tag in ('title','h1','h2') or n.tag=='meta' and n.attrs.get('property')=='og:site_name')
    if candidato.get('tipo')=='TERRITORIAL':
        loc=o.norm(candidato['localidad'])
        nombre=bool(re.search(r'\b(?:municipalidad|municipio|comuna|gobierno)(?:\s+de)?\s+'+re.escape(loc)+r'\b',o.norm(cabeceras)))
        organismo=candidato['organismo'];localidad=candidato['localidad']
    else:
        # Nombre publicado en título, nunca derivado del dominio o búsqueda.
        nombres=[n.text.strip() for n in dom.root.iter() if n.tag in ('h1','title') and re.search(r'hospital|samco|s\.a\.m\.c\.o|universidad (?:nacional|provincial)|empresa|\bente\b|puerto|vialidad',o.norm(n.text)) and len(n.text.strip())<200]
        organismo=nombres[0] if nombres else None;localidad=None
        nombre=bool(organismo)
    # El radio BA no se infiere de una mera mención provincial en un organismo.
    alcance=candidato.get('tipo')=='TERRITORIAL' or candidato['provincia']!='Buenos Aires'
    publico=host(url).endswith(('.gob.ar','.gov.ar')) or bool(re.search(r'universidad (?:nacional|provincial)',o.norm(organismo)))
    valida=oficial(url) and publico and nombre and jurisdiccion and alcance
    return {'verificada':valida,'organismo':organismo,'localidad':localidad,
        'dominio_oficial':oficial(url),'nombre_publicado':nombre,'jurisdiccion_publicada':jurisdiccion,
        'url':url,'sha256':sha256(html.encode()).hexdigest(),'cabecera':cabeceras[:1000],
        'motivo':None if valida else 'Falta dominio oficial, identidad, provincia explícita o ubicación sectorial dentro del alcance; requiere contraste'}

def aceptacion(resultado,identidad):
    validos=[r for raw in resultado.get('oportunidades',[]) if (r:=o.normalizar(raw)).get('clasificacion_registro')=='PROCEDIMIENTO' and r.get('procedimiento_canonico') and r.get('objeto') and r.get('detalle_completo')]
    ok=identidad.get('verificada') and bool(validos) and resultado.get('estado')=='OPERATIVA' and not resultado.get('errores') and not resultado.get('limites')
    return {'estado':'VALIDADA' if ok else 'PENDIENTE','identidad_verificada':identidad.get('verificada',False),
        'identidad':identidad,'procedimientos_con_objeto':len(validos),'fecha':datetime.now(timezone.utc).isoformat(),
        'motivo':None if ok else identidad.get('motivo') or 'Extracción incompleta, sin procedimiento/objeto comprobado o con incidencias',
        'ejemplos':[{k:r.get(k) for k in ('organismo','numero_procedimiento','objeto','fecha_apertura','fecha_publicacion','vigencia','url','evidencia_url')} for r in validos]}

def worker(entrada,salida):
    c=json.loads(Path(entrada).read_text());url=c['url']
    try:
        datos,tipo,final=conectores.descargar(url,conexion_timeout=4,lectura_timeout=6)
        if host(url)!=host(final):raise ValueError('Redirección a otro dominio: requiere contraste independiente')
        if 'html' not in tipo:raise ValueError('La identidad requiere una página HTML oficial; PDF aislado queda pendiente')
        html=conectores.decodificar_html(datos,tipo)
        identidad=verificar_identidad(html,final,c)
        if not identidad['verificada']:
            guardar(salida,{'estado':'PENDIENTE','finalizado':True,'validacion':aceptacion({},identidad),'oportunidades':[]});return
        config={'organismo':identidad['organismo'],'localidad':identidad['localidad'],'provincia':c['provincia'],
            'conector':'publicaciones','descubrir_menu':True,'descubrir_contrataciones':True,'lectura_adjuntos':'necesarios','ocr':True}
        inicial={url:(datos,tipo,final)}
        def fetch(u,datos_post=None):
            if u in inicial:return inicial.pop(u)
            import cache_documentos
            from functools import partial
            transporte=partial(conectores.descargar,conexion_timeout=4,lectura_timeout=6)
            if datos_post is not None:return transporte(u,datos_post=datos_post)
            if urlparse(u).path.lower().endswith(extractores.ADJUNTOS):return cache_documentos.obtener(u,transport=transporte)[:3]
            return transporte(u)
        def progreso(r):guardar(salida,{**r,'identidad':identidad,'config':config,'finalizado':False})
        resultado=conectores.explorar(url,config,fetch=fetch,progreso=progreso)
        guardar(salida,{**resultado,'config':config,'validacion':aceptacion(resultado,identidad),'finalizado':True})
    except Exception as e:
        guardar(salida,{'estado':'PENDIENTE','finalizado':True,'oportunidades':[],
            'errores':[conectores.clasificar_error(e,'DESCARGA')],
            'validacion':{'estado':'PENDIENTE','motivo':str(e),'identidad_verificada':False,'procedimientos_con_objeto':0}})

def worker_busqueda(entrada,salida):
    q=json.loads(Path(entrada).read_text());url=q['url']
    try:
        datos,_,_=conectores.descargar(url,conexion_timeout=3,lectura_timeout=4)
        archivo=Path(salida).with_suffix('.respuesta');archivo.write_bytes(datos)
        if q.get('metodo')=='ENLACES_OFICIALES':
            dom=extractores.DOM(conectores.decodificar_html(datos,'text/html'))
            resultados=[{'url':l['url'],'titulo':l['texto'],'evidencia_enlace':url} for l in dom.root.enlaces(url)
                if l['tag']=='a' and host(l['url'])==host(url) and re.search(r'licitaciones|compras|contrataciones|concursos|boletin',o.norm(l['texto'])+' '+l['url']) and l['url']!=url]
        else:
            resultados=rss(datos)
            if not resultados:
                alternativa='https://html.duckduckgo.com/html/?'+urlencode({'q':q['consulta']})
                datos2,_,_=conectores.descargar(alternativa,conexion_timeout=3,lectura_timeout=4)
                Path(salida).with_suffix('.alternativa.html').write_bytes(datos2)
                texto=conectores.decodificar_html(datos2,'text/html')
                if re.search(r'anomaly-modal|challenge-form',texto):raise ValueError('Buscador alternativo requiere verificación humana; no se elude')
                resultados=[{**r,'evidencia_busqueda':alternativa} for r in resultados_html(texto,alternativa)]
        guardar(salida,{'estado':'OPERATIVA','finalizado':True,'oportunidades':[], 'resultados':resultados,'paginas_correctas':1,
            'respuesta_archivo':str(archivo),'respuesta_sha256':sha256(datos).hexdigest()})
    except Exception as e:
        guardar(salida,{'estado':'PENDIENTE','finalizado':True,'oportunidades':[], 'errores':[conectores.clasificar_error(e,'DESCARGA')]})

def plan_busquedas(obj,estado,limite):
    hechos=estado.setdefault('busquedas',{})
    return sorted(obj,key=lambda q:hechos.get(q['clave'],''))[:limite]

def contar_portales(candidatos):
    """Un URL puede aparecer en varias búsquedas: conservar evidencia, contar una vez."""
    grupos={}
    for c in candidatos:
        u=extractores.url_publica(c['url'])
        grupos[u]='VALIDADA' if c.get('validacion',{}).get('estado')=='VALIDADA' or grupos.get(u)=='VALIDADA' else 'PENDIENTE'
    return dict(Counter(grupos.values()))

def seleccionar_validaciones(candidatos,existentes,auto,limite,revisar_pendientes=False):
    por_url={}
    for c in candidatos:
        if c['url'] in existentes and c['url'] not in auto:continue
        vencida=c.get('version_verificador')!=4 or not c.get('ultima_revision') or datetime.fromisoformat(c['ultima_revision'])<datetime.now(timezone.utc)-timedelta(days=7)
        forzada=revisar_pendientes and c['url'] not in auto and c.get('validacion',{}).get('estado')!='VALIDADA'
        if not vencida and not forzada:continue
        anterior=por_url.get(c['url'])
        if anterior is None or (c.get('validacion',{}).get('identidad_verificada',False) and not anterior.get('validacion',{}).get('identidad_verificada',False)):
            por_url[c['url']]=c
    return sorted(por_url.values(),key=lambda c:(c.get('ultima_revision',''),c.get('fecha_descubrimiento',''),c['id']))[:limite]

def ejecutar_descubrimiento(salida,total=240,busquedas=12,candidatos=24,revisar_pendientes=False):
    inicio=time.monotonic();raiz=Path(salida);raiz.mkdir(parents=True,exist_ok=True)
    estado_path=Path('inventario/descubrimiento_estado.json');auto_path=Path('inventario/fuentes_auto.json')
    estado=json.loads(estado_path.read_text()) if estado_path.exists() else {'schema_version':1,'busquedas':{},'candidatos':{}}
    urls_previas={c['url'] for c in estado['candidatos'].values()}
    fs=json.loads(Path('inventario/fuentes.json').read_text());auto=cargar_auto()
    existentes={f['url'] for f in fs if f.get('incorporada')}|set(auto)
    fecha=datetime.now(timezone.utc).isoformat();errores=[];descubiertos=set();nuevos=[]
    padron=json.loads(Path('inventario/territorio.json').read_text())
    consultas=plan_busquedas(objetivos(padron,fs),estado,busquedas)
    def persistir():guardar(estado_path,estado);guardar(raiz/'estado.json',estado)
    entradas_busqueda=raiz/'consultas';entradas_busqueda.mkdir(exist_ok=True)
    trabajos=[]
    for q in consultas:
        q={**q,'id':sha256(q['clave'].encode()).hexdigest()[:20], 'url':q.get('url_directorio') or 'https://www.bing.com/search?'+urlencode({'q':q['consulta'],'format':'rss','setlang':'es','cc':'ar'})}
        guardar(entradas_busqueda/(q['id']+'.json'),q);trabajos.append(q)
    consultas_por_id={q['id']:q for q in trabajos}
    busqueda_informe=ejecutar(trabajos,raiz/'busquedas.json',concurrencia=3,por_fuente=12,total=min(60,total*.3),
        comando=lambda f,path:[sys.executable,__file__,'--buscar-worker',str(entradas_busqueda/(f['id']+'.json')),'--salida',str(path)],emitir=lambda s:print('BUSQUEDA '+s,flush=True))
    for obs in busqueda_informe['observaciones']:
        if not obs['iniciada']:continue
        q=consultas_por_id[obs['id']];url=q['url'];p=Path(obs.get('resultado_archivo',''))
        r=json.loads(p.read_text()) if p.is_file() else {}
        resultados=r.get('resultados',[])
        if obs['estado']=='OPERATIVA':
            for r in resultados:
                if r['url'] in existentes:continue
                key=sha256((r['url']+'|'+q['clave']).encode()).hexdigest()[:20]
                c={**q,**r,'id':'auto-'+key,'busqueda_url':url,'fecha_descubrimiento':fecha}
                anterior=estado['candidatos'].get(key)
                if not anterior:descubiertos.add(key);estado['candidatos'][key]=c
            estado['busquedas'][q['clave']]=fecha
            print('DESCUBRIMIENTO_BUSQUEDA '+json.dumps({'objetivo':q['clave'],'candidatos':len(resultados),'url':url}),flush=True)
        else:
            # Rotar también búsquedas fallidas: no bloquear el padrón en el primer error.
            estado['busquedas'][q['clave']]=fecha
            errores.append({'objetivo':q['clave'],'url':url,'errores':obs.get('errores',[])})
        persistir()
    # Portales no incorporados ya inventariados son candidatos, no descubrimientos nuevos.
    for f in fs:
        if f.get('incorporada'):continue
        key='inventario-'+f['id']
        estado['candidatos'].setdefault(key,{**f,'tipo':'TERRITORIAL','id':'auto-'+key,'clave':key,'origen':'INVENTARIO_PREVIO','fecha_descubrimiento':fecha})
    lote=seleccionar_validaciones(estado['candidatos'].values(),existentes,auto,candidatos,revisar_pendientes)
    limite=max(1,total-(time.monotonic()-inicio)-3)
    entradas=raiz/'entradas';entradas.mkdir(exist_ok=True)
    for c in lote:guardar(entradas/(c['id']+'.json'),c)
    informe=ejecutar(lote,raiz/'verificacion.json',concurrencia=3,por_fuente=35,total=limite,
        comando=lambda f,path:[sys.executable,__file__,'--worker',str(entradas/(f['id']+'.json')),'--salida',str(path)],emitir=lambda s:print('DESCUBRIMIENTO '+s,flush=True))
    registro=json.loads(auto_path.read_text()) if auto_path.exists() else {'schema_version':1,'fuentes':[]}
    validadas=set()
    por_id={c['id']:c for c in estado['candidatos'].values()}
    for obs in informe['observaciones']:
        if not obs['iniciada']:continue
        c=por_id[obs['id']];p=Path(obs.get('resultado_archivo',''))
        r=json.loads(p.read_text()) if p.is_file() else {}
        v=r.get('validacion') or {'estado':'PENDIENTE','motivo':'Plazo agotado o worker incompleto; resultados parciales conservados'}
        # El supervisor decide completitud; un checkpoint anterior no autoriza promoción.
        if obs['estado']!='OPERATIVA':v={**v,'estado':'PENDIENTE','motivo':v.get('motivo') or 'Consulta no finalizada sin incidencias'}
        c.update(ultima_revision=fecha,version_verificador=4,validacion=v,errores=obs.get('errores',[]),resultado_archivo=str(p))
        if v['estado']=='VALIDADA':
            validadas.add(c['url'])
            for anterior in registro['fuentes']:
                if anterior['url']==c['url']:anterior.update(validacion=v,config=r['config'])
            if c['url'] not in existentes:
                entrada={'id':c['id'],'url':c['url'],'config':r['config'],'validacion':v,'origen_busqueda':c.get('busqueda_url') or c.get('evidencia_descubrimiento')}
                registro['fuentes'].append(entrada);existentes.add(c['url']);nuevos.append(entrada)
        persistir()
    guardar(auto_path,registro)
    portales=contar_portales(estado['candidatos'].values())
    urls_nuevas={estado['candidatos'][k]['url'] for k in descubiertos}-urls_previas
    resumen={'fecha':fecha,'github_run_id':__import__('os').environ.get('GITHUB_RUN_ID'),'descubiertas_automaticamente':len(urls_nuevas),
        'hallazgos_nuevos':len(descubiertos),'candidatos_acumulados':sum(portales.values()),'hallazgos_acumulados':len(estado['candidatos']),
        'consultadas':len({r['url'] for r in informe['observaciones'] if r['iniciada']}),'validadas':len(validadas),'validadas_acumuladas':portales.get('VALIDADA',0),'incorporadas':len(nuevos),
        'incorporadas_acumuladas':len(registro['fuentes']),'pendientes':portales.get('PENDIENTE',0),
        'errores_busqueda':errores,'duracion_segundos':round(time.monotonic()-inicio,2),'cobertura_completa':False}
    guardar(raiz/'resumen.json',{'resumen':resumen,'incorporadas':nuevos});persistir()
    print('DESCUBRIMIENTO_RESUMEN '+json.dumps(resumen,ensure_ascii=False),flush=True)
    for f in nuevos:
        for e in f['validacion']['ejemplos']:print('DESCUBRIMIENTO_OPORTUNIDAD '+json.dumps(e,ensure_ascii=False),flush=True)
    return resumen

def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--buscar-worker');p.add_argument('--salida',default='work/descubrimiento');p.add_argument('--total',type=float,default=240);p.add_argument('--busquedas',type=int,default=12);p.add_argument('--candidatos',type=int,default=24);p.add_argument('--revisar-pendientes',action='store_true');a=p.parse_args()
    if a.buscar_worker:worker_busqueda(a.buscar_worker,a.salida)
    elif a.worker:worker(a.worker,a.salida)
    else:
        if not 15<=a.total<=600 or not 1<=a.busquedas<=100 or not 1<=a.candidatos<=100:p.error('Límites fuera de rango')
        ejecutar_descubrimiento(a.salida,a.total,a.busquedas,a.candidatos,a.revisar_pendientes)

if __name__=='__main__':main()
