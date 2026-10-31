"""Rutas publicadas y feeds oficiales: descubrimiento sin enriquecer documentos."""
import re
from html import escape,unescape
from email.utils import parsedate_to_datetime
from urllib.parse import urlsplit
import xml.etree.ElementTree as ET
import extractores


def endpoints_publicados(html,config):
    """Sólo rutas explícitas del HTML y aprobadas para ese organismo; no ejecutar JS."""
    texto=unescape(html).replace('\\/','/');salida=[]
    for ruta in config.get('endpoints_publicados',[]):
        u=extractores.url_publica(ruta.get('url',''))
        if u and u in texto:
            salida.append((u,'AJAX_PUBLICADO',{'post':{ruta.get('campo','limiteInfConsulta'):0},'campo':ruta.get('campo','limiteInfConsulta'),'paso':int(ruta.get('paso',6))}))
    return salida


def feeds_publicados(dom,base):
    for n in dom.root.iter():
        if n.tag=='link' and n.attrs.get('type') in ('application/rss+xml','application/atom+xml'):
            u=extractores.url_publica(n.attrs.get('href',''),base)
            if u and urlsplit(u).hostname==urlsplit(base).hostname and not re.search(r'comments|comentarios',u,re.I):yield u


def extraer_feed(datos,url,config):
    raiz=ET.fromstring(datos);resultados=[];enlaces=[]
    if raiz.tag.split('}')[-1] not in ('rss','feed'):raise ValueError('El XML no es un feed de publicaciones')
    atom='{http://www.w3.org/2005/Atom}';items=raiz.findall('./channel/item') if raiz.tag=='rss' else raiz.findall(atom+'entry')
    for item in items:
        titulo=item.findtext('title') or item.findtext(atom+'title') or ''
        link=item.findtext('link') or next((x.attrib.get('href','') for x in item.findall(atom+'link') if x.attrib.get('rel','alternate')=='alternate'),'')
        link=extractores.url_publica(link,url)
        if not link or urlsplit(link).hostname!=urlsplit(url).hostname:continue
        texto=item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or item.findtext('description') or item.findtext(atom+'content') or ''
        rs,_,_=extractores.extraer('<article><h1>'+escape(titulo)+'</h1>'+texto+'</article>',link,config)
        fecha=item.findtext('pubDate') or item.findtext(atom+'published')
        try:publicada=parsedate_to_datetime(fecha).date().isoformat() if fecha and not re.match(r'^\d{4}-',fecha) else fecha[:10] if fecha else None
        except (TypeError,ValueError):publicada=None
        individual=len({r.get('procedimiento') or r.get('numero_procedimiento') or r.get('titulo') for r in rs})==1 and not re.fullmatch(r'(?:compras(?: y contrataciones)?|licitaciones(?: y concursos)?|concursos|transparencia)',extractores.norm(titulo))
        for r in rs:
            if publicada and individual:r['fecha_publicacion_texto']=publicada
            elif publicada:r['fecha_feed_contenedor']=publicada
            r['evidencia_feed']=url
            resultados.append(r)
        if rs or re.search(r'licitaci[oó]n|concurso de precios|cotizaci[oó]n|pedido de presupuesto',titulo,re.I):enlaces.append(link)
    return resultados,enlaces,len(items)


def busquedas_publicadas(dom,base):
    """Usar únicamente formularios GET de búsqueda presentes en la web oficial."""
    from urllib.parse import urljoin,urlencode,parse_qsl,urlunsplit
    salida=set()
    for n in dom.root.iter():
        if n.tag!='form' or n.attrs.get('method','get').lower()!='get':continue
        campos=[c for c in n.iter() if c.tag=='input' and c.attrs.get('name') in ('s','q','search') and c.attrs.get('type','text') in ('search','text')]
        if not campos:continue
        if n.attrs.get('role')!='search' and not any(c.attrs.get('type')=='search' for c in campos) and campos[0].attrs.get('name')!='s':continue
        u=extractores.url_publica(n.attrs.get('action') or base,base)
        if not u or urlsplit(u).hostname!=urlsplit(base).hostname:continue
        p=urlsplit(u)
        for termino in ('licitacion','concurso','cotizacion','contratacion','compra'):
            params=dict(parse_qsl(p.query));params[campos[0].attrs['name']]=termino
            salida.add(urlunsplit((p.scheme,p.netloc,p.path,urlencode(params),'')))
    return sorted(salida)


def ediciones_entre_rios(datos):
    """Rutas según el cliente público oficial 5326.824a7ea1.chunk.js."""
    import json
    from datetime import date,timedelta
    filas=json.loads(datos)
    if not isinstance(filas,list) or not filas:raise ValueError('Índice de ediciones ER ausente o inválido')
    meses=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    fechas=[]
    for f in filas:
        if not isinstance(f,dict) or not f.get('nro') or not f.get('fecha'):raise ValueError('Edición ER sin número/fecha')
        d=date.fromisoformat(f['fecha']);fechas.append(d)
    inicio=max(fechas)-timedelta(days=60)
    return [('https://www.entrerios.gov.ar/boletin/calendario/Boletin/'+str(d.year)+'/'+meses[d.month-1]+'/'+d.strftime('%d-%m-%y')+'.pdf',d.isoformat()) for d in sorted(set(fechas),reverse=True) if d>=inicio]


def boletin_entre_rios(texto,url):
    """Separación por sección e ID editorial; sin OCR ni herencia entre avisos."""
    import re
    from extractores import norm,procesos,EVENTO,situacion
    limpio=re.sub(r'(?m)^.*BOLETIN OFICIAL.*$','',texto)
    lineas=limpio.splitlines();activo=False;bloque=[];registros=[]
    def emitir(lineas):
        cuerpo='\n'.join(lineas).strip()
        if not cuerpo:return
        ls=[l.strip() for l in lineas if l.strip() and not re.fullmatch(r'[- ]+',l.strip())]
        pos=next((i for i,l in enumerate(ls) if procesos(l) or re.search(r'concursos? de precios',norm(l))),None)
        if pos is None:return
        cab=ls[:pos]
        org=next((l for l in cab if re.search(r'municipalidad|municipio|comuna|ministerio|enersa|direccion|instituto|hospital|universidad|poder judicial|cafesg|sistema de previs',norm(l))),None)
        if not org:return
        if norm(org).startswith('sistema de previs'):
            org=' '.join(cab[cab.index(org):])
        publicado=org
        org=re.sub(r'\s*-\s*Entre R[ií]os\s*$','',org,flags=re.I).strip(' -')
        org=re.sub(r'\s*\(E\.\s*R\.\s*\)\s*$','',org,flags=re.I).strip()
        aliases={'ministerio de salud':'MIN. SALUD - PODER EJECUTIVO','direccion provincial de vialidad':'Vialidad Entre Ríos','instituto de ayuda financiera a la accion social':'IAFAS'}
        org=aliases.get(norm(org),org)
        localidad=None
        m=re.match(r'(?:municipalidad|municipio|comuna)\s+(?:de\s+)?(.+)',org,re.I)
        if m:
            localidad=m[1].strip()
            # Texto nativo con letras separadas por la tipografía: resolver sólo
            # si coincide inequívocamente con el padrón provincial, nunca por fuzzy.
            from pathlib import Path
            import json
            padron=json.loads(Path(__file__).with_name('inventario').joinpath('territorio.json').read_text())
            exactas=[x['localidad'] for x in padron['municipios'] if x['provincia']=='Entre Ríos' and re.sub(r'\s+','',norm(x['localidad']))==re.sub(r'\s+','',norm(localidad))]
            if len(set(exactas))==1:localidad=exactas[0]
            org=('Comuna de ' if norm(org).startswith('comuna') else 'Municipalidad de ')+localidad
        ps=procesos(cuerpo)
        if 'enersa' in norm(org):
            tipo='concurso de precios' if re.search(r'concursos? de precios',norm(cuerpo)) else 'licitacion publica'
            ns=list(re.finditer(r'(?im)^\s*(?:N[.º°o\s]*|Licitaci[oó]n[^\n]{0,60}?)(20\d{2}-\d{3,6})',cuerpo))
            partes=[(m[1],tipo,cuerpo[m.start():ns[i+1].start() if i+1<len(ns) else len(cuerpo)]) for i,m in enumerate(ns)]
            org='ENERSA (Energía de Entre Ríos S.A.)'
        else:
            # Una publicación con varios procedimientos debe segmentarse, nunca copiar la primera fecha.
            unicos={p['procedimiento'] for p in ps}
            if len(unicos)!=1:return
            p=ps[0];partes=[(p['numero'],p['tipo'],cuerpo)]
        for numero,tipo,contenido in partes:
            evento='|'.join(sorted(set(EVENTO.findall(norm(contenido))))) or None
            apertura=re.search(r'apertura.{0,700}?(\d{1,2}\s*/\s*\d{1,2}\s*/\s*20\d{2}(?:\s+a las\s+\d{1,2}\s*:\s*\d{2})?)',norm(contenido),re.S)
            presupuesto=re.search(r'presupuesto(?:\s+oficial)?(?:\s+estimado)?[^\n]{0,180}?(?<![uU])\$\s*([\d.,]+)',contenido,re.I)
            presupuesto_texto=(('ARS ' if re.search(r'\bpesos\b',presupuesto[0],re.I) else '$ ')+presupuesto[1]) if presupuesto else None
            registros.append({'presupuesto_texto':presupuesto_texto,'organismo':org,'organismo_publicado':publicado,'localidad':localidad,'provincia':'Entre Ríos','numero_procedimiento':numero,'numero_oficial_sin_interpretar':numero,'tipo_procedimiento':tipo,'procedimiento':tipo+' '+numero,'titulo':tipo+' '+numero+' '+contenido,'objeto':contenido,'url':url,'evidencia_url':url,'registro_estructurado':True,'detalle_completo':True,'es_fuente_complementaria':True,'evento_publicado':evento,'situacion_publicada':situacion(contenido),'fecha_apertura_texto':re.sub(r'\s*/\s*','/',apertura[1]) if apertura else None,'documentos':[{'url':url,'titulo':'Boletín Oficial Entre Ríos'}]})
    for l in lineas:
        n=norm(l.strip())
        if n in ('licitaciones','concursos','compras directas','contrataciones directas','solicitudes de cotizacion'):
            if activo:emitir(bloque)
            bloque=[];activo=True;continue
        if n in ('designacion de autoridades','comunicados','citaciones','notificaciones','edictos','concursos y quiebras','resoluciones','decretos'):
            if activo:emitir(bloque)
            bloque=[];activo=False;continue
        if activo:
            if re.search(r'\bID:\s*\d+',l):emitir(bloque);bloque=[]
            else:bloque.append(l)
    if activo:emitir(bloque)
    return registros
