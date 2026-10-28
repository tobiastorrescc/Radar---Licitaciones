"""Extracción estructural de publicaciones y sus adjuntos; sin ejecutar JavaScript."""
from dataclasses import dataclass, field
from functools import cached_property, lru_cache
from html.parser import HTMLParser
from html import unescape
from urllib.parse import urljoin, urlsplit, urlunsplit, quote, urldefrag
import re
import json
import unicodedata


def norm(t):
    t=re.sub(r'/\s*\(\s*(20\d{2})\s*\)',r'/\1',str(t))
    t=re.sub(r'(\d+)\s*\(\s*(20\d{2})\s*\)',r'\1/\2',t)
    return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFKD',str(t).lower()) if not unicodedata.combining(c))).strip()


TIPO=r'(?:licitacion(?:\s+(?:publica|privada))?|(?:publica|privada)(?=\s+n[º°o.]*\s*\d)|lic\.?\s*(?:pub(?:lica)?|priv(?:ada)?)\.?|concurso\s+(?:(?:publico|privado)(?=\s+n)|de\s+anteproyectos?|(?:(?:publico|privado)\s+)?(?:de\s+)?(?:precios|ofertas))|compras?\s+(?:directas?|menor(?:es)?|agil(?:es)?)|contratacion\s+directa(?:\s+con\s+cotejo(?:\s+de\s+precios)?)?|cotejo\s+de\s+precios|solicitud\s+de\s+cotizacion|compulsa)'
PROCESO=re.compile(r'(?P<tipo>'+TIPO+r')\s*(?:\b(?:gas|bid\w*|programa)\s+)?(?P<marca>n(?:ro|umero)?[.º°o]*\s*)?(?P<numero>\d{1,10}(?:-\d+)?(?:\s*[/–-]\s*\d{2,4})?)(?!\d)',re.I)
EVENTO=re.compile(r'desiert\w*|fracasad\w*|segundo llamado|2do llamado|2[º°o] llamado|segunda convocatoria|reapertura|nuevo llamado')
ADJUNTOS=('.pdf','.docx','.doc','.zip','.xls','.xlsx')


def url_publica(url,base=''):
    u=urldefrag(urljoin(base,unescape(url).strip()))[0]
    p=urlsplit(u)
    if p.scheme not in ('http','https') or not p.hostname:return None
    # No doble codificación de escapes ya presentes ni pérdida de queries opacas.
    host=p.hostname.encode('idna').decode('ascii').lower()
    if p.port:host+=':'+str(p.port)
    return urlunsplit((p.scheme,host,quote(p.path,safe='/%:@!$&\'()*+,;=-._~'),
                       quote(p.query,safe='=&%/:?@!$\'()*+,;~-._'),''))


@lru_cache(maxsize=4096)
def procesos(texto):
    t=norm(texto)
    if re.search(r'(?:telefono|tel\.|cel\.|whatsapp|montos limites|salario minimo|hasta \d+ veces)',t):
        # Excluir contactos/normativa, nunca un rubro o una condición comercial.
        if not re.search(r'\d+\s*[/–-]\s*\d{2,4}',t):return []
    out=[]
    for m in PROCESO.finditer(t):
        numero=re.sub(r'\s+','',m['numero']).replace('–','-')
        if numero.isdigit() and 1900<=int(numero)<=2100 and not m['marca']:continue
        numero=re.sub(r'([/–-])(\d{2})$',lambda x:x[1]+str((2000 if int(x[2])<70 else 1900)+int(x[2])),numero)
        numero=re.sub(r'^0+(?=\d)','',numero)
        tipo=re.sub(r'^lic\.?\s*pub\w*\.?','licitacion publica',m['tipo'])
        tipo=re.sub(r'^lic\.?\s*priv\w*\.?','licitacion privada',tipo)
        if tipo in ('publica','privada'):tipo='licitacion '+tipo
        out.append({'tipo':tipo,'numero':numero,'procedimiento':tipo+' '+numero,
                    'start':m.start(),'end':m.end()})
    # El código no contiene espacios: no absorber Estado, Asunto ni navegación.
    for m in re.finditer(r'\b(LPU|LPR|CPRV|CD)(?:[-\s]+)(20\d{2})-(\d{1,8})(?:\s*-\s*[A-Za-z][A-Za-z0-9]*)*\b',texto,re.I):
        codigo=re.sub(r'\s*-\s*','-',m.group(0)).upper()
        out.append({'tipo':{'LPU':'licitacion publica','LPR':'licitacion privada','CPRV':'concurso privado de precios','CD':'contratacion directa'}[m[1].upper()],
                    'numero':codigo,'procedimiento':codigo.lower(),'start':m.start(),'end':m.end()})
    for m in re.finditer(r'\b(LPU|LPR|CPRV|CD)\s+n[º°o.]*\s*(\d{8})\b',texto,re.I):
        codigo=re.sub(r'\s*-\s*','-',m.group(0)).upper()
        out.append({'tipo':{'LPU':'licitacion publica','LPR':'licitacion privada','CPRV':'concurso privado de precios','CD':'contratacion directa'}[m[1].upper()],
                    'numero':codigo,'procedimiento':codigo.lower(),'start':m.start(),'end':m.end()})
    return out


@dataclass(eq=False)
class Nodo:
    tag:str
    attrs:dict=field(default_factory=dict)
    parent:object=None
    children:list=field(default_factory=list)
    @cached_property
    def text(self):
        if self.tag in ('script','style','head','noscript'):return ''
        return re.sub(r'\s+',' ',' '.join(c.text if isinstance(c,Nodo) else c for c in self.children)).strip()
    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c,Nodo):yield from c.iter()
    def clase(self,c):return c in self.attrs.get('class','').split()
    def padres(self):
        p=self
        while p:
            yield p;p=p.parent
    def enlaces(self,base):
        links=[]
        for n in self.iter():
            href=n.attrs.get('href') or n.attrs.get('data-next-page')
            onclick=n.attrs.get('onclick','')
            m=re.search(r"DownloadFile\(\s*'([^']+)'\s*,\s*'([^']+)'",onclick)
            if m:href=m[1]+m[2]
            if n.tag=='iframe':href=n.attrs.get('src')
            if not href:continue
            url=url_publica(href,base)
            if url:links.append({'url':url,'texto':n.text,'rel':n.attrs.get('rel','next' if n.attrs.get('data-next-page') else ''),
                                 'tag':n.tag,'node':n})
        return links


class DOM(HTMLParser):
    VOID={'area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'}
    def __init__(self,html):
        super().__init__(convert_charrefs=True)
        self.root=Nodo('root');self.stack=[self.root]
        self.feed(html)
    def handle_starttag(self,tag,attrs):
        n=Nodo(tag,dict(attrs),self.stack[-1]);self.stack[-1].children.append(n)
        if tag not in self.VOID:self.stack.append(n)
    def handle_startendtag(self,tag,attrs):
        self.handle_starttag(tag,attrs)
        if tag not in self.VOID:self.handle_endtag(tag)
    def handle_endtag(self,tag):
        for i in range(len(self.stack)-1,0,-1):
            if self.stack[i].tag==tag:
                del self.stack[i:];break
    def handle_data(self,data):self.stack[-1].children.append(data)


def excluido(n,permitir_aside=False):
    for p in n.padres():
        if p.tag in ('head','script','style','nav','footer') or (p.tag=='header' and not any(a.tag in ('main','article') for a in p.padres())) or (p.tag=='aside' and not permitir_aside):return True
        cl=p.attrs.get('class','')
        if re.search(r'(?:^|\s)(?:menu-item|header-mobile-menu|related-posts|site-footer|main-navigation)',cl):return True
    return False


def situacion(texto):
    t=norm(texto)
    t=re.sub(r'proveedor adjudicado(?: y monto)?\s*:?','',t)
    t=re.sub(r'(?:sera|seran|podra ser|una vez)\s+adjudicad[oa]','',t)
    t=re.sub(r'(?:se declarara|sera declarada|podra ser declarada)\s+desierta','',t)
    t=re.sub(r'(?:sera|podra ser|se declarara|resultare|resultara)\s+(?:declarad[ao]\s+)?(?:desiert[ao]\s+o\s+)?fracasad[ao]','',t)
    return next((valor for patron,valor in [(r'\badjudicad[oa]\b','ADJUDICADA'),(r'\bdesiert\w*','DESIERTA'),(r'\bfracasad\w*','FRACASADA'),(r'\bfinalizad[oa]\b','FINALIZADA'),(r'\ben evaluacion\b','EN_EVALUACION')] if re.search(patron,t)),None)


def extraer(html,url,config=None):
    config=config or {}
    dom=DOM(html);raiz=dom.root
    if config.get('adaptador')=='villa-elisa' and not urlsplit(url).path.strip('/'):
        # La portada enlaza avisos; no convertir toda su navegación en un objeto.
        return [],dom.root.enlaces(url),dom
    regiones=[n for n in raiz.iter() if n.tag=='main']
    # Los anexos de San Nicolás están en aside; son contenido de contratación real.
    if config.get('incluir_aside'):regiones=[]
    if regiones and not config.get('usar_documento_entero'):raiz=regiones[0]
    if config.get('adaptador')=='villa-elisa':
        articulos=[n for n in raiz.iter() if n.tag=='article' and n.clase('type-post')]
        if len(articulos)==1:raiz=articulos[0]
    if config.get('adaptador')=='junin':
        paneles=[n for n in raiz.iter() if n.clase('panel-info') and procesos(n.text)]
        if len(paneles)==1:raiz=paneles[0]
    allow_aside=config.get('incluir_aside',False)
    candidatos=[]
    año=None
    for n in raiz.iter():
        if excluido(n,allow_aside):continue
        texto=n.text
        if n.tag in ('h1','h2','h3','h4','h5','h6') and re.fullmatch(r'20\d{2}',texto):año=texto
        if config.get('adaptador')=='rosario' and n.clase('contrataciones-resumen__tarjeta'):
            sec=next((p for p in n.padres() if p.clase('contrataciones-resumen__seccion')),None)
            if sec:
                cabecera=next((x.text for x in sec.iter() if x.clase('contrataciones-resumen__seccion-header')),'')
                tipo=re.sub(r'\s+\d+$','',cabecera)
                candidatos.append((tipo+' '+texto,n))
        if config.get('adaptador')=='lapaz' and n.clase('cadacompra'):
            tipo='Concurso de precios' if 'concursos-de-precios' in url else 'Licitación Pública'
            candidatos.append((tipo+' '+re.sub(r'^N[uú]mero:\s*','',texto),n))
        if config.get('adaptador')=='rosario' and n.tag=='a' and re.fullmatch(r'\d+/\d{4}',texto):
            tipo=config.get('tipo_contexto')
            if tipo:
                elegido=n
                for parent in list(n.padres())[1:]:
                    destinos={l['url'] for l in parent.enlaces(url) if '/compras-licitaciones/detalle/' in l['url']}
                    if len(destinos)!=1 or len(parent.text)>12000:break
                    elegido=parent
                candidatos.append((tipo+' '+elegido.text,elegido))
        # Tablas con tipo en el título y número/objeto en columnas separadas.
        if n.tag=='tr' and config.get('adaptador')=='rojas-compras':
            cells=[c for c in n.children if isinstance(c,Nodo) and c.tag=='td']
            if len(cells)>=6 and re.fullmatch(r'20\d{2}',cells[0].text) and re.fullmatch(r'\d+',cells[2].text):
                candidatos.append((cells[4].text+' '+cells[2].text+'/'+cells[0].text+' '+texto,n))
            continue
        if n.tag=='tr' and config.get('tipo_tabla'):
            cells=[c for c in n.children if isinstance(c,Nodo) and c.tag in ('td','th')]
            if cells and re.fullmatch(r'\d+\s*/\s*\d{2,4}',cells[0].text):
                candidatos.append((config['tipo_tabla']+' '+texto,n))
        # La etiqueta singular Pública/Privada de San José hereda Licitación.
        if config.get('adaptador')=='rojas-compras':continue
        if n.tag in ('h1','h2','h3','h4','h5','h6','p','strong','b','span','a','button','td','div','li','article','section'):
            if n.tag=='div' and any(isinstance(x,Nodo) and x.tag not in ('span','strong','b','a','br') for x in n.children):continue
            etiqueta=texto
            if re.match(r'^(?:publica|privada)\s+n[º°o.]*\s*\d',norm(texto)):etiqueta='Licitación '+texto
            ps=procesos(etiqueta)
            if not ps:continue
            # Una etiqueta no debe abarcar varias publicaciones distintas.
            if len({p['procedimiento'] for p in ps})!=1:continue
            elegido=n
            for parent in list(n.padres())[1:]:
                if parent is raiz.parent:break
                if parent.tag in ('html','body','root','main') or excluido(parent,allow_aside):break
                pp=procesos(parent.text)
                if len({p['procedimiento'] for p in pp})!=1 or len(parent.text)>16000:break
                elegido=parent
            if etiqueta!=texto and elegido is n:texto=etiqueta
            else:texto=elegido.text
            if not procesos(texto):texto=etiqueta+' '+texto
            if año and '/' not in ps[0]['numero'] and '-' not in ps[0]['numero']:
                texto=texto.replace(ps[0]['numero'],ps[0]['numero']+'/'+año,1)
            candidatos.append((texto,elegido))
    registros=[]
    for texto,n in candidatos:
        ps=procesos(texto)
        if not ps:continue
        p=ps[0]
        if re.search(r'montos limites|regimen de contrataciones|hasta \d+ veces',norm(texto)):continue
        links=n.enlaces(url)
        documents=[{'url':l['url'],'titulo':l['texto']} for l in links if urlsplit(l['url']).path.lower().endswith(ADJUNTOS)]
        detail=next((l['url'] for l in links if not urlsplit(l['url']).path.lower().endswith(ADJUNTOS)
                     and procesos(l['texto'])),None)
        destino=detail or (documents[0]['url'] if documents else url)
        # Campos dedicados, donde existen, evitan confundir número con objeto.
        objeto=next((x.text for x in n.iter() if x.clase('objeto')),None)
        if not objeto and config.get('adaptador')=='epe':
            objeto=next((x.text for x in n.iter() if x.tag=='button' and x.text),None)
        celdas=[x for x in n.children if isinstance(x,Nodo) and x.tag=='td']
        tabla=next((x for x in n.padres() if x.tag=='table'),None)
        cabeceras=[x.text for x in tabla.iter() if x.tag=='th'] if tabla else []
        campos_tabla={norm(k):v.text for k,v in zip(cabeceras,celdas)}
        if config.get('tipo_tabla') and campos_tabla.get('objeto'):objeto=campos_tabla['objeto']
        if not objeto:objeto=texto
        evento='|'.join(sorted(set(EVENTO.findall(norm(texto))))) or None
        epe=(config.get('adaptador')=='epe' and urlsplit(url).hostname in ('www.epe.santafe.gov.ar','epe.santafe.gov.ar')
             and re.fullmatch(r'\d{10}',p['numero']) is not None
             and any(x.tag=='button' and x.text==objeto for x in n.iter()))
        apertura_epe=re.search(r'\b\d{1,2}-\d{1,2}-20\d{2}\b',texto) if epe else None
        registros.append({'titulo':texto,'objeto':objeto,'procedimiento':p['procedimiento'],
            'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'url':destino,
            'presupuesto_texto':next((v for k,v in campos_tabla.items() if k.startswith('presupuesto')),None),
            'fecha_publicacion_texto':next((x.attrs.get('datetime') or x.text for x in n.iter() if x.tag=='time' and ('published' in x.attrs.get('class','') or x.attrs.get('itemprop')=='datePublished')),None),
            'documentos':documents,'evento_publicado':evento,'llamado_especial':bool(evento),
            'fecha_apertura_texto':apertura_epe[0] if apertura_epe else (next((x.text for x in n.children if isinstance(x,Nodo) and x.tag=='td' and re.search(r'\d{1,2}/\d{1,2}/20\d{2}',x.text)),None) if config.get('tipo_tabla') else None),
            'registro_estructurado':bool(epe),
            'evidencia_url':url,'detalle_completo':bool(set(re.findall(r'\b[a-z]{4,}\b',norm(objeto)[p['end']:] if objeto==texto else norm(objeto)))-{'pliego','descargar','anexo','numero','apertura','fecha','vigente','tramite','documento','descarga'}),
            'situacion_publicada':situacion(texto)})
    # Mismo procedimiento repetido en menús, encabezados, pliegos y anexos: uno con todos sus enlaces.
    agrupados={}
    for r in registros:
        # El enlace de ficha separa procesos distintos que comparten número en un portal provincial.
        clave=(r['procedimiento'],r['evento_publicado'],r['situacion_publicada'])
        if config.get('organismos_multiples'):clave+=(r['url'],)
        anterior=agrupados.get(clave)
        if anterior:
            docs={d['url']:d for d in anterior['documentos']+r['documentos']}
            if len(r['titulo'])>len(anterior['titulo']):agrupados[clave]=r
            agrupados[clave]['documentos']=list(docs.values())
        else:agrupados[clave]=r
    if config.get('adaptador')=='minplan':
        for n in raiz.iter():
            if not n.clase('contratacion'):continue
            tipo=next((x.text for x in n.iter() if x.clase('contratacion-tipo')),'')
            objeto=next((x.text for x in n.iter() if x.clase('contratacion-titulo')),'')
            entidad=next((x.text for x in n.iter() if x.clase('contratacion-org')),None)
            if tipo and objeto:
                key=(norm(tipo),norm(objeto),entidad)
                agrupados[key]={'titulo':tipo+' '+objeto,'objeto':objeto,'organismo':entidad or config.get('organismo'),
                    'procedimiento':None,'numero_procedimiento':None,'registro_estructurado':True,'url':url,'evidencia_url':url,
                    'documentos':[{'url':l['url'],'titulo':l['texto']} for l in n.enlaces(url) if urlsplit(l['url']).path.lower().endswith(ADJUNTOS)],
                    'detalle_completo':True,'evento_publicado':None,'llamado_especial':False,'situacion_publicada':None}
    if config.get('adaptador')=='baradero':
        for script in dom.root.iter():
            if script.tag!='script':continue
            t=''.join(x for x in script.children if isinstance(x,str))
            for m in re.finditer(r'self\.__next_f\.push\(',t):
                try:args,_=json.JSONDecoder().raw_decode(t[m.end():])
                except ValueError:continue
                if not isinstance(args,list) or len(args)<2 or not isinstance(args[1],str):continue
                flight=args[1]
                for start in re.finditer(r'\{\s*"id"\s*:',flight):
                    try:f,_=json.JSONDecoder().raw_decode(flight[start.start():])
                    except ValueError:continue
                    if not all(k in f for k in ('titulo','motivo','pdfUrl')):continue
                    title=f['titulo']
                    if f.get('año') and procesos(title) and not re.search(r'[/–-]\d{2,4}$',procesos(title)[0]['numero']):
                        title=title.rstrip('/ ')+'/'+str(f['año'])
                    title+=' '+f['motivo'];ps=procesos(title)
                    if not ps:continue
                    p=ps[0];evento='|'.join(sorted(set(EVENTO.findall(norm(title))))) or None
                    agrupados[(p['procedimiento'],evento,None)]={'titulo':title,'objeto':f['motivo'],
                        'procedimiento':p['procedimiento'],'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],
                        'url':url,'documentos':[{'url':url_publica(f['pdfUrl'],url),'titulo':f.get('botonTexto','Pliego')}],
                        'evidencia_url':url,'detalle_completo':bool(f['motivo']),'situacion_publicada':None,
                        'evento_publicado':evento,'llamado_especial':bool(evento),'id_origen':f['id']}
    if config.get('adaptador')=='cdelu':
        for script in dom.root.iter():
            if script.tag!='script':continue
            t=''.join(x for x in script.children if isinstance(x,str))
            m=re.search(r'licitaciones\s*:\s*(\[)',t)
            if not m or 'LICITACIONES_DATA' not in t:continue
            datos,_=json.JSONDecoder().raw_decode(t[m.start(1):])
            for f in datos:
                if not all(k in f for k in ('numero','anio','titulo')):raise ValueError('Datos de licitaciones incompletos')
                titulo=f"Licitación Pública {f['numero']}/{f['anio']} "+f['titulo']
                if f.get('llamado',1)>1:titulo+=f" - llamado {f['llamado']}"
                key='publicacion-'+str(f.get('id',str(f['numero'])+'-'+str(f['anio'])))
                documentos=[{'titulo':d.get('nombre'),'url':url_publica(d['url'],urljoin(url,'/'))} for d in f.get('documentos',[])]
                agrupados[key]={'titulo':titulo,'objeto':f['titulo'],'procedimiento':f"licitacion publica {f['numero']}/{f['anio']}",
                   'numero_procedimiento':str(f['numero'])+'/'+str(f['anio']),'tipo_procedimiento':'licitacion publica',
                   'url':url,'documentos':documentos,'evento_publicado':str(f.get('llamado',1)),
                   'llamado_especial':f.get('llamado',1)>1,'evidencia_url':url,'detalle_completo':True,
                   'situacion_publicada':None,'id_origen':f.get('id'),'fecha_apertura_texto':f.get('aperturaTexto')}
    if config.get('adaptador')=='aeropuerto':
        # La ficha separa tabla de identificación, presupuesto y descargas.
        # Los nombres de anexos no son convocatorias adicionales.
        for tabla in raiz.iter():
            if tabla.tag!='table':continue
            campos={}
            for fila in tabla.iter():
                if fila.tag!='tr':continue
                th=next((n for n in fila.children if isinstance(n,Nodo) and n.tag=='th'),None)
                td=next((n for n in fila.children if isinstance(n,Nodo) and n.tag=='td'),None)
                if th and td:campos[norm(th.text)]=td.text
            if not campos.get('numero') or not campos.get('asunto'):continue
            numero=re.sub(r'\s*-\s*','-',campos['numero'])
            docs=[{'url':l['url'],'titulo':l['texto']} for l in raiz.enlaces(url) if urlsplit(l['url']).path.lower().endswith(ADJUNTOS) and not excluido(l['node'],allow_aside)]
            ps=procesos(numero)
            if not ps:continue
            p=ps[0]
            corto=re.fullmatch(r'(LPU|LPR|CPRV|CD)\s+n[º°o.]*\s*(\d+)',numero,re.I)
            if corto:
                completos=[p for d in docs for p in procesos(d['titulo']) if re.match(r'^'+corto[1]+r'-20\d{2}-0*'+str(int(corto[2]))+r'(?:-|$)',p['numero'],re.I)]
                if completos:p=completos[0]
            numero=p['numero']
            presupuestos=[n.text for n in raiz.iter() if n.tag=='p' and re.match(r'^presupuesto oficial\b',norm(n.text)) and not excluido(n,allow_aside)]
            r={'titulo':numero+' '+campos['asunto'],'objeto':campos['asunto'],'numero_procedimiento':numero,'tipo_procedimiento':p['tipo'],
               'procedimiento':p['procedimiento'],'url':url,'evidencia_url':url,'documentos':docs,'detalle_completo':True,'registro_estructurado':True,
               'fecha_apertura_texto':campos.get('fecha de apertura'),'presupuesto_texto':presupuestos[0] if len(presupuestos)==1 else None,
               'evento_publicado':None,'llamado_especial':False,'situacion_publicada':situacion(campos.get('estado','')),'campos_oficiales':campos}
            agrupados={(p['procedimiento'],None,None):r}
            break
    if config.get('adaptador') in ('boletin-sf','boletin-er'):
        from extractores_lotes import boletin_santafe
        agrupados={(r['organismo'],r['procedimiento'],r['evento_publicado']):r for r in boletin_santafe(raiz,url,config)}
    if config.get('adaptador') in ('encabezados','colon-pba'):
        from extractores_lotes import encabezados
        secciones=encabezados(raiz,url,config)
        if secciones:agrupados={(r['procedimiento'],r['evento_publicado']):r for r in secciones}
    if config.get('adaptador')=='villa-elisa':
        from extractores_lotes import fichas_villaelisa
        secciones=fichas_villaelisa(raiz,url)
        if secciones:agrupados={(r['procedimiento'],r['evento_publicado']):r for r in secciones}
    if config.get('adaptador')=='ramirez':
        from extractores_lotes import fichas_ramirez
        # No conservar candidatos genéricos procedentes de cifras del menú.
        agrupados={(r['procedimiento'],r['evento_publicado']):r for r in fichas_ramirez(raiz,url)}
    if config.get('adaptador')=='zarate':
        from extractores_lotes import acordeones_zarate
        secciones=acordeones_zarate(raiz,url)
        if secciones:agrupados={(r['procedimiento'],r['evento_publicado']):r for r in secciones}
    enlaces=(dom.root if config.get('descubrir_menu') else raiz).enlaces(url)
    if config.get('adaptador')=='rosario':
        for l in enlaces:
            sec=next((p for p in l['node'].padres() if p.clase('contrataciones-resumen__seccion')),None)
            if sec:
                cabecera=next((x.text for x in sec.iter() if x.clase('contrataciones-resumen__seccion-header')),'')
                l['tipo_contexto']=re.sub(r'\s+\d+$','',cabecera)
    return list(agrupados.values()),enlaces,dom
