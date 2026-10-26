"""Conectores auditables. Una respuesta HTTP no prueba detección de publicaciones."""
from collections import deque
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler
from http.client import HTTPConnection, HTTPSConnection
import socket
from urllib.error import HTTPError, URLError
import re
import subprocess
import unicodedata
import extractores
import documentos
import gzip
import json


def normalizar(texto):
    return re.sub(r'\s+', ' ', ''.join(c for c in unicodedata.normalize('NFKD', texto.lower())
                                      if not unicodedata.combining(c))).strip()


TIPOS = r'(?:licitacion(?: publica| privada)?|concurso(?: privado| publico)?(?: de precios| de ofertas)?|compras? (?:directas?|menor(?:es)?)|contratacion directa|compulsa|cotejo de precios)'
PUBLICACION = re.compile(TIPOS + r'\b.{0,65}?\d+(?:\s*[/–-]\s*\d{2,4})?', re.I)
ESPECIAL = re.compile(r'desiert\w*|segundo llamado|2do llamado|2[º°o] llamado|segunda convocatoria|reapertura|nuevo llamado')


def clasificar(texto):
    t = normalizar(texto)
    m = PUBLICACION.search(t)
    return {'procedimiento': m.group(0) if m else None,
            'llamado_especial': bool(ESPECIAL.search(t)),
            'evento_publicado': '|'.join(sorted(set(ESPECIAL.findall(t)))) or None,
            'situacion_publicada': next((v for k, v in [('desiert', 'DESIERTA'), ('adjudic', 'ADJUDICADA'),
                ('en evaluacion', 'EN_EVALUACION'), ('finalizada', 'FINALIZADA') ] if k in t), None)}


class Listado(HTMLParser):
    """Enlaces y bloques: conserva títulos en filas cuyo vínculo solo dice Descargar."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links, self.blocks, self.stack = [], [], []
        self.anchor = None
        self.hidden = 0
        self.texto = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag in ('script', 'style'):
            self.hidden += 1
        if tag in ('tr', 'article', 'li', 'section'):
            self.stack.append({'tag': tag, 'texto': [], 'links': []})
        if tag == 'a' and attrs.get('href'):
            self.anchor = {'url': attrs['href'], 'texto': '', 'rel': attrs.get('rel', '')}
        if tag == 'iframe' and attrs.get('src'):
            self.links.append({'url': attrs['src'], 'texto': '', 'rel': 'iframe'})

    def handle_data(self, data):
        if self.hidden:
            return
        self.texto.append(data)
        if self.anchor is not None:
            self.anchor['texto'] += data
        for block in self.stack:
            block['texto'].append(data)

    def handle_endtag(self, tag):
        if tag in ('script', 'style'):
            self.hidden = max(0, self.hidden - 1)
        if tag == 'a' and self.anchor is not None:
            self.links.append(self.anchor)
            for block in self.stack:
                block['links'].append(self.anchor)
            self.anchor = None
        if self.stack and self.stack[-1]['tag'] == tag:
            block = self.stack.pop()
            block['texto'] = ' '.join(block['texto'])
            self.blocks.append(block)


def extraer_html(html, url):
    parser = Listado()
    parser.feed(html)
    registros = []
    for link in parser.links:
        if PUBLICACION.search(normalizar(link['texto'])):
            registros.append((link['texto'], urljoin(url, link['url'])))
    for block in parser.blocks:
        texto = re.sub(r'\s+', ' ', block['texto']).strip()
        # No convertir un contenedor de muchos procedimientos en una publicación.
        if len(PUBLICACION.findall(normalizar(texto))) != 1:
            continue
        links = block['links']
        target = next((x['url'] for x in links if urlparse(x['url']).path.lower().endswith('.pdf')),
                      links[0]['url'] if links else url)
        registros.append((texto, urljoin(url, target)))
    return registros, parser


def extraer_pdf(datos):
    if not datos.startswith(b'%PDF-'):
        raise ValueError('Respuesta no es PDF')
    result = subprocess.run(['pdftotext', '-layout', '-', '-'], input=datos, capture_output=True,
                            timeout=40, check=True)
    texto = result.stdout.decode('utf-8')
    if not texto.strip():
        raise ValueError('PDF sin texto: requiere OCR; no se declara vacío')
    return texto


class _LecturaAcotada:
    """DNS/TCP/proxy/TLS usan timeout de conexión; headers/body, de lectura.

    El supervisor del verificador impone además un plazo de pared, incluso ante
    DNS bloqueado o un servidor que envía bytes indefinidamente.
    """
    def __init__(self, *args, lectura_timeout=10, **kwargs):
        self.lectura_timeout = lectura_timeout
        super().__init__(*args, **kwargs)

    def connect(self):
        super().connect()
        self.sock.settimeout(self.lectura_timeout)


class _HTTPAcotada(_LecturaAcotada, HTTPConnection):
    pass


class _HTTPSAcotada(_LecturaAcotada, HTTPSConnection):
    pass


class _HTTPHandler(HTTPHandler):
    def __init__(self, lectura_timeout):
        super().__init__()
        self.lectura_timeout = lectura_timeout

    def http_open(self, req):
        return self.do_open(lambda *a, **kw: _HTTPAcotada(*a, lectura_timeout=self.lectura_timeout, **kw), req)


class _HTTPSHandler(HTTPSHandler):
    def __init__(self, lectura_timeout):
        super().__init__()
        self.lectura_timeout = lectura_timeout

    def https_open(self, req):
        return self.do_open(lambda *a, **kw: _HTTPSAcotada(*a, lectura_timeout=self.lectura_timeout, **kw),
                            req, context=self._context)


def descargar(url, conexion_timeout=5, lectura_timeout=10):
    # build_opener conserva proxies del entorno y validación TLS predeterminada.
    opener = build_opener(_HTTPHandler(lectura_timeout), _HTTPSHandler(lectura_timeout))
    url = extractores.url_publica(url)
    with opener.open(Request(url, headers={'User-Agent': 'RadarLicitaciones/2.0'}),
                     timeout=conexion_timeout) as r:
        datos = r.read(12_000_001)
        if len(datos) > 12_000_000:
            raise ValueError('Respuesta supera 12 MB; recorrido parcial')
        if r.headers.get('Content-Encoding', '').lower()=='gzip' or datos.startswith(b'\x1f\x8b'):
            datos=gzip.decompress(datos)
            if len(datos)>12_000_000:raise ValueError('Contenido descomprimido supera 12 MB')
        return datos, r.headers.get('Content-Type', ''), r.geturl()


def clasificar_error(error, fase):
    timeout = isinstance(error, (TimeoutError, socket.timeout)) or (
        isinstance(error, URLError) and isinstance(error.reason, (TimeoutError, socket.timeout)))
    if fase == 'DESCARGA' and isinstance(error, (URLError, OSError, HTTPError)):
        categoria = 'RED'
    else:
        categoria = 'EXTRACCION'
    result = {'tipo': type(error).__name__, 'categoria': categoria,
              'timeout': timeout or isinstance(error, subprocess.TimeoutExpired), 'error': str(error)}
    if isinstance(error, HTTPError):
        result['http_status'] = error.code
    return result


def identidad(fuente, titulo, url):
    # Diferentes llamados en una URL y documentos en distintos portales se conservan.
    p = clasificar(titulo)
    clave = '|'.join((fuente, urldefrag(url)[0], p['procedimiento'] or normalizar(titulo),
                      p['evento_publicado'] or '', p['situacion_publicada'] or ''))
    return sha256(clave.encode()).hexdigest()


def decodificar_html(datos,tipo):
    m=re.search(r'charset=["\']?([\w-]+)',tipo,re.I)
    if not m:
        m=re.search(rb'charset=["\']?([\w-]+)',datos[:6000],re.I)
    encoding=m[1] if m else None
    if isinstance(encoding,bytes):encoding=encoding.decode('ascii')
    if encoding:
        try:return datos.decode(encoding)
        except (UnicodeDecodeError,LookupError):pass
    try:return datos.decode('utf-8-sig')
    except UnicodeDecodeError:return datos.decode('cp1252',errors='replace')


def _host(url):
    return (urlparse(url).hostname or '').lower().removeprefix('www.')


def explorar(fuente, config, fetch=None, max_paginas=1000, progreso=None):
    fetch=fetch or descargar
    pending=deque([(u,'LISTADO',None) for u in config.get('urls_inicio',[fuente])])
    seen=set();items={};errors=[];limits=[];correctas=0;documentos_leidos=0
    hosts={_host(fuente),*(_host('https://'+h) for h in config.get('dominios_documentos',[]))}
    documento_pendiente={};vacios=[]
    modo=config.get('lectura_adjuntos','todos')
    def snapshot(fase,actual=None,finalizado=False):
        r={'oportunidades':list(items.values()),'errores':list(errors),'limites':list(limits),
           'paginas_visitadas':len(seen),'paginas_correctas':correctas,'documentos_leidos':documentos_leidos,
           'cobertura_completa':False,'fase':fase,'url_actual':actual,'finalizado':finalizado,
           'alcance':'Listado completo de publicaciones reconocidas y sus enlaces; adjuntos necesarios para extraer objeto',
           'documentos_pendientes':list(documento_pendiente.values()),'evidencias_listado_vacio':list(vacios)}
        if progreso:progreso(r)
        return r
    def agregar(r):
        key=sha256('|'.join((fuente,r['url'],normalizar(r['titulo']))).encode()).hexdigest()
        # Agrupar los anexos de la misma publicación, preservando nuevos llamados/situaciones.
        if r.get('procedimiento'):
            entidad=r['url'] if config.get('organismos_multiples') else ''
            key=sha256('|'.join((fuente,r['procedimiento'],r.get('evento_publicado') or '',r.get('situacion_publicada') or '',entidad)).encode()).hexdigest()
        anterior=items.get(key,{})
        docs={d['url']:d for d in anterior.get('documentos',[])+r.get('documentos',[])}
        if anterior and len(anterior['titulo'])>len(r['titulo']):
            r={**r,**anterior}
        c=clasificar(r['titulo'])
        registro={'id':key,'fuente':fuente,'estado':'PUBLICACION_DETECTADA',
             'organismo':config.get('organismo'),'localidad':config.get('localidad'),'provincia':config.get('provincia'),
             'presupuesto':None,'fecha_apertura':None,'condiciones_pago':None,'estimacion_comercial':None,
             'motivo_sin_estimacion':'Faltan costos y precios comprobables',**c,**r,
             'documentos':list(docs.values()),'pago_prioritario':any(x in normalizar(r['titulo']) for x in ('pago contado','pago al contado','contra entrega','pago inmediato'))}
        registro['enlace_pliego']=next((d['url'] for d in registro['documentos'] if 'pliego' in normalizar(d.get('titulo') or '')),registro['documentos'][0]['url'] if registro['documentos'] else None)
        items[key]=registro
        return key
    def texto_documento(texto,url,referencia=None):
        lineas=texto.splitlines()
        posiciones=[i for i,l in enumerate(lineas) if extractores.procesos(l)]
        if not posiciones and referencia and texto.strip():
            p=dict(items[referencia]);p['objeto']=texto;p['texto_documento']=texto;p['detalle_completo']=True
            items[referencia]=p
            return
        for n,i in enumerate(posiciones):
            t=' '.join(lineas[i:posiciones[n+1] if n+1<len(posiciones) else len(lineas)])
            ps=extractores.procesos(t)
            if not ps:continue
            p=ps[0]
            evento='|'.join(sorted(set(extractores.EVENTO.findall(normalizar(t))))) or None
            r={'titulo':t,'objeto':t,'url':url,'evidencia_url':url,'documentos':[{'url':url,'titulo':'Documento'}],
               'procedimiento':p['procedimiento'],'evento_publicado':evento,'detalle_completo':True}
            agregar(r)
            if referencia in items:
                items[referencia]['objeto']=texto
                items[referencia]['texto_documento']=texto
                items[referencia]['detalle_completo']=True
    while pending:
        if len(seen)>=max_paginas:limits.append('max_paginas');break
        url,clase,referencia=pending.popleft();url=extractores.url_publica(url)
        if not url or url in seen or _host(url) not in hosts:continue
        seen.add(url);fase='DESCARGA';snapshot(fase,url)
        try:
            datos,tipo,final=fetch(url)
            fase='EXTRACCION';snapshot(fase,url)
            if _host(final) not in hosts:raise ValueError('Redirección fuera de dominios oficiales declarados')
            es_html='html' in tipo.lower() and not datos.startswith(b'%PDF-')
            if not es_html:
                texto=documentos.leer(datos,tipo,url,ocr=config.get('ocr',False),
                    progreso=lambda t:(texto_documento(t,url,referencia),snapshot('EXTRACCION',url)))
                texto_documento(texto,url,referencia);documentos_leidos+=1;correctas+=1
                documento_pendiente.pop(url,None)
                snapshot('PAGINA_FINALIZADA',url);continue
            html=decodificar_html(datos,tipo)
            pagina_config={**config,**(referencia if isinstance(referencia,dict) else {})}
            registros,links,dom=extractores.extraer(html,final,pagina_config)
            correctas+=1
            texto=normalizar(dom.root.text)
            # El vacío debe estar publicado explícitamente; no se infiere de falta de matches.
            m=re.search(r'no (?:hay|existen|se encontraron) (?:licitaciones|publicaciones|procesos de compra)|sin licitaciones vigentes',texto)
            if not m and config.get('marcador_vacio'):m=re.search(config['marcador_vacio'],texto)
            if clase=='LISTADO' and config.get('detectar_carga_dinamica') and re.search(r'cargas? mas|load more',texto):
                errors.append({'url':url,'tipo':'PaginacionDinamicaPendiente','categoria':'EXTRACCION','timeout':False,'error':'Control cargar más sin enlace de siguiente página verificable'})
            if m:vacios.append({'url':url,'texto':m.group(0)})
            if not registros and re.search(r'inicia sesi[oó]n para|solo esta disponible dentro de la red|debe iniciar sesi[oó]n',texto):
                errors.append({'url':url,'tipo':'AccesoRestringido','categoria':'ACCESO','timeout':False,'error':'El portal requiere autenticación o red privada; no se elude'})
            for r in registros:
                if config.get('requerir_ficha') and clase=='LISTADO':r['detalle_completo']=False
                key=agregar(r)
                if clase=='DETALLE' and referencia in items and r.get('detalle_completo'):
                    items[referencia]['objeto']=r['objeto'];items[referencia]['detalle_completo']=True
                for doc in r.get('documentos',[]):
                    destino=doc['url']
                    necesario=modo=='todos' or not r.get('detalle_completo')
                    if necesario and _host(destino) in hosts and destino not in seen:
                        documento_pendiente[destino]={'url':destino,'publicacion_id':key}
                        pending.append((destino,'DOCUMENTO',key))
                if not r.get('detalle_completo') and r['url']!=url and not urlparse(r['url']).path.lower().endswith(extractores.ADJUNTOS):
                    pending.append((r['url'],'DETALLE',key))
            for l in links:
                destino=l['url'];et=normalizar(l['texto']);path=urlparse(destino).path
                if _host(destino) not in hosts or destino in seen or destino==url:continue
                raices={urlparse(u).path.rstrip('/') for u in config.get('urls_inicio',[fuente])}
                raices.update((urlparse(fuente).path.rstrip('/'),urlparse(url).path.rstrip('/')))
                pagina=clase=='LISTADO' and (('next' in l['rel'].split() or et in ('siguiente','siguiente »','next','»','›') or
                          bool(re.search(r'/page/\d+|[?&](?:page|pagina|start)=\d+',destino))) and any(path.startswith(raiz) for raiz in raices))
                navegar=any(re.search(patron,destino) for patron in config.get('seguir_patrones',[]))
                if pagina or navegar:
                    contexto={'tipo_contexto':l.get('tipo_contexto',pagina_config.get('tipo_contexto'))}
                    pending.appendleft((destino,'LISTADO',contexto))
                # Un documento del índice de boletines puede contener llamados sin título HTML.
                if not registros and config.get('indice_documentos') and path.lower().endswith(extractores.ADJUNTOS):
                    pending.append((destino,'DOCUMENTO',None))
            snapshot('PAGINA_FINALIZADA',url)
        except Exception as e:
            errors.append({'url':url,**clasificar_error(e,fase)})
            snapshot('PAGINA_FINALIZADA',url)
    incompletas=[r['id'] for r in items.values() if not r.get('detalle_completo')]
    if incompletas:
        errors.append({'url':fuente,'tipo':'DetalleIncompleto','categoria':'EXTRACCION','timeout':False,
                       'error':'Publicaciones identificadas sin objeto completo','publicaciones':incompletas})
    estado='OPERATIVA' if items else 'PENDIENTE'
    if not items and vacios and not errors and not limits:estado='SIN_PUBLICACIONES'
    if not correctas and errors:estado='BLOQUEADA' if all(e['categoria']=='RED' for e in errors) else 'PENDIENTE'
    if items and (errors or limits):estado='PARCIAL'
    if not items and not vacios and not errors:
        errors.append({'url':fuente,'tipo':'SinPublicacionesDetectadas','categoria':'EXTRACCION','timeout':False,
                       'error':'Listado no reconocido; no se declara vacío'})
    result=snapshot('FINALIZADA',finalizado=True);result['estado']=estado
    if progreso:progreso(result)
    return result
