"""Conectores auditables. Una respuesta HTTP no prueba detección de publicaciones."""
from collections import deque
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag,urlencode,parse_qs,urlsplit,urlunsplit,unquote
from urllib.request import Request, build_opener, HTTPHandler, HTTPSHandler
from http.client import HTTPConnection, HTTPSConnection
import socket
import time
from http.client import RemoteDisconnected
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
import re
import subprocess
import unicodedata
import extractores
import documentos
import pagos
import oportunidades
import gzip
import json
import ssl


def normalizar(texto):
    return re.sub(r'\s+', ' ', ''.join(c for c in unicodedata.normalize('NFKD', texto.lower())
                                      if not unicodedata.combining(c))).strip()


TIPOS = r'(?:licitacion(?: publica| privada)?|concurso(?: privado| publico)?(?: de precios| de ofertas)?|compras? (?:directas?|menor(?:es)?)|contratacion directa|compulsa|cotejo de precios)'
PUBLICACION = re.compile(TIPOS + r'\b.{0,65}?\d+(?:\s*[/–-]\s*\d{2,4})?', re.I)
ESPECIAL = re.compile(r'desiert\w*|fracasad\w*|segundo llamado|2do llamado|2[º°o] llamado|segunda convocatoria|reapertura|nuevo llamado')


def clasificar(texto):
    t = normalizar(texto)
    m = PUBLICACION.search(t)
    return {'procedimiento': m.group(0) if m else None,
            'llamado_especial': bool(ESPECIAL.search(t)),
            'evento_publicado': '|'.join(sorted(set(ESPECIAL.findall(t)))) or None,
            'situacion_publicada': extractores.situacion(texto)}


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


def descargar(url, conexion_timeout=5, lectura_timeout=10, headers_extra=None, devolver_headers=False,datos_post=None,max_bytes=12_000_000,devolver_estado=False):
    if not 1<=max_bytes<=32_000_000:raise ValueError('Tamaño máximo de respuesta fuera de rango')
    # build_opener conserva proxies del entorno y validación TLS predeterminada.
    opener = build_opener(_HTTPHandler(lectura_timeout), _HTTPSHandler(lectura_timeout))
    url = extractores.url_publica(url)
    with opener.open(Request(url,data=datos_post, headers={'User-Agent': 'RadarLicitaciones/2.0',**(headers_extra or {})}),
                     timeout=conexion_timeout) as r:
        longitud=r.headers.get('Content-Length')
        if longitud and longitud.isdigit() and int(longitud)>max_bytes:raise ValueError(f'Respuesta supera {max_bytes} bytes; recorrido parcial')
        datos = r.read(max_bytes+1)
        if len(datos) > max_bytes:
            raise ValueError(f'Respuesta supera {max_bytes} bytes; recorrido parcial')
        if r.headers.get('Content-Encoding', '').lower()=='gzip' or datos.startswith(b'\x1f\x8b'):
            datos=gzip.decompress(datos)
            if len(datos)>max_bytes:raise ValueError('Contenido descomprimido supera 12 MB')
        resultado=(datos, r.headers.get('Content-Type', ''), r.geturl())
        if devolver_estado:resultado=(*resultado,r.status)
        return (*resultado,dict(r.headers.items())) if devolver_headers else resultado


def clasificar_error(error, fase):
    timeout = isinstance(error, (TimeoutError, socket.timeout)) or (
        isinstance(error, URLError) and isinstance(error.reason, (TimeoutError, socket.timeout)))
    if isinstance(error,AccesoRestringido):
        categoria = 'ACCESO'
    elif fase == 'DESCARGA' and isinstance(error, (URLError, OSError, HTTPError)):
        categoria = 'RED'
    else:
        categoria = 'EXTRACCION'
    result = {'tipo': type(error).__name__, 'categoria': categoria,
              'timeout': timeout or isinstance(error, subprocess.TimeoutExpired), 'error': str(error)}
    if isinstance(error, HTTPError):
        result['http_status'] = error.code
    result.update(diagnostico_error(result))
    return result


def diagnostico_error(error):
    """No equiparar un timeout o HTTP 500 a una restricción de acceso."""
    texto=str(error.get('error','')).lower();status=error.get('http_status')
    if status in (401,403):causa='RESTRICCION_HTTP';acceso=True
    elif error.get('categoria')=='ACCESO':causa='DESAFIO_ACCESO';acceso=True
    elif status==429:causa='LIMITE_SOLICITUDES_TEMPORAL';acceso=False
    elif status and status>=500:causa='ERROR_SERVIDOR_TEMPORAL';acceso=False
    elif error.get('timeout') or 'timed out' in texto:causa='TIEMPO_ESPERA';acceso=False
    elif 'certificate verify failed' in texto or 'self-signed certificate' in texto:causa='ERROR_CERTIFICADO_TLS';acceso=False
    elif 'ssl' in texto or 'eof' in texto:causa='ERROR_CONEXION_TLS';acceso=False
    elif error.get('categoria')=='RED':causa='ERROR_RED_POR_CONFIRMAR';acceso=False
    else:causa='ERROR_EXTRACCION';acceso=False
    return {'causa':causa,'restriccion_acceso_comprobada':acceso,'permanencia':'NO_DETERMINADA'}


class AccesoRestringido(RuntimeError):
    pass


def comprobar_acceso(html):
    # Firmas específicas de una pantalla de desafío, no menciones en un pliego.
    texto=normalizar(html)
    if (re.search(r'<title[^>]*>\s*(?:one moment,? please|just a moment|attention required)[^<]*</title>',html,re.I)
        and re.search(r'request is being verified|checking your browser|verify you are human|challenge-platform|enable javascript and cookies',texto)):
        raise AccesoRestringido('Desafío de acceso HTTP 200; requiere revisión del acceso oficial, sin eludirlo')


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
    except UnicodeDecodeError:
        # HTML mixto: una tilde Latin-1 no debe corromper los href UTF-8 válidos.
        # surrogateescape conserva cada byte inválido para decodificar sólo ese byte.
        texto=datos.decode('utf-8',errors='surrogateescape')
        return ''.join(bytes([ord(c)-0xdc00]).decode('cp1252',errors='replace')
                       if 0xdc80<=ord(c)<=0xdcff else c for c in texto)


def _host(url):
    return (urlparse(url).hostname or '').lower().removeprefix('www.')


def explorar(fuente, config, fetch=None, max_paginas=1000, progreso=None):
    if fetch is None:
        from functools import partial
        fetch=partial(descargar)
        transporte=fetch
        def fetch(url,datos_post=None):
            if datos_post is not None:return transporte(url,datos_post=datos_post)
            if urlparse(url).path.lower().endswith((*extractores.ADJUNTOS,'.jpg','.jpeg','.png')) or any(re.search(p,url) for p in config.get('patrones_documentos',[])):
                import cache_documentos
                return cache_documentos.obtener(url,transport=transporte)[:3]
            return transporte(url)
    # Reintentos de lectura idempotente, acotados por el supervisor de fuente.
    intentos_http=[]
    reintentos=int(config.get('reintentos_transitorios',0))
    if not 0<=reintentos<=2:raise ValueError('Reintentos fuera de rango')
    if reintentos:
        original_fetch=fetch
        def fetch(url,datos_post=None):
            for intento in range(reintentos+1):
                inicio=time.monotonic()
                try:
                    respuesta=original_fetch(url,datos_post=datos_post) if datos_post is not None else original_fetch(url)
                    intentos_http.append({'url':url,'intento':intento+1,'estado':'RESPUESTA_RECIBIDA','segundos':round(time.monotonic()-inicio,3)})
                    return respuesta
                except Exception as error:
                    transitorio=(isinstance(error,HTTPError) and error.code in (500,502,503,504)) or isinstance(error,(RemoteDisconnected,TimeoutError,socket.timeout,ssl.SSLEOFError)) or (isinstance(error,URLError) and isinstance(error.reason,(RemoteDisconnected,TimeoutError,socket.timeout,ssl.SSLEOFError)))
                    intentos_http.append({'url':url,'intento':intento+1,'estado':'ERROR','http_status':getattr(error,'code',None),'error':str(error),'segundos':round(time.monotonic()-inicio,3),'reintentable':transitorio})
                    if not transitorio or intento==reintentos:raise
                    time.sleep(min(1,0.25*(2**intento)))
    pending=deque([(extractores.url_publica(u) or u,'LISTADO',{'tipo_contexto':config.get('contextos_listado',{}).get(parse_qs(urlparse(u).query).get('tipoRecomendada',[''])[0])}) for u in config.get('urls_inicio',[fuente])])
    if config.get('adaptador')=='boletin-sf':
        from fuentes_criticas import ediciones_santafe
        for u in reversed(ediciones_santafe(fuente,config.get('boletin_sf_dias',3))):pending.appendleft((u,'LISTADO',{}))
    seen=set();items={};errors=[];limits=[];correctas=0;documentos_leidos=0
    respuestas_detalles={}
    respaldo_intentado=False;respaldo_pdf_intentado=False;rutas_respaldo=[]
    conteos_rosario={}
    paginas_gestiones=set();totales_gestiones=[];totales_dpv=[]
    reintentos_diferidos={}
    if config.get('adaptador')=='rosario' and config.get('consultar_meses_rosario'):
        hoy=oportunidades.datetime.now(oportunidades.ZONA)
        for delta in (0,1):
            mes=(hoy.month-1+delta)%12+1;anio=hoy.year+(hoy.month-1+delta)//12
            # Parámetros obtenidos del formulario público, ver evidencia del 7/11.
            alternativa='https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones?'+urlencode({'mesApertura[0]':str(mes).zfill(2),'anioApertura[0]':str(anio)})
            pending.append((alternativa,'LISTADO',{}))

    hosts={_host(fuente),*(_host('https://'+h) for h in config.get('dominios_documentos',[]))}
    documento_pendiente={};vacios=[];paginas_api=set()
    modo=config.get('lectura_adjuntos','todos')
    semillas_listado={u for u,c,_ in pending if c=='LISTADO'}
    def snapshot(fase,actual=None,finalizado=False):
        if config.get('adaptador')=='ceres':
            from fuentes_fase4 import refinar_ceres
            for k,v in list(items.items()):items[k]=refinar_ceres(v)
        r={'oportunidades':list(items.values()),'errores':list(errors),'limites':list(limits),
           'paginas_visitadas':len(seen),'paginas_correctas':correctas,'documentos_leidos':documentos_leidos,
           'cobertura_completa':False,'fase':fase,'url_actual':actual,'finalizado':finalizado,
           'alcance':config.get('alcance_publicaciones','Listado completo de publicaciones reconocidas y sus enlaces; adjuntos necesarios para extraer objeto'),
           'totales_publicados_rosario':{t:sorted(v) for t,v in conteos_rosario.items()},'intentos_http':list(intentos_http),'documentos_pendientes':list(documento_pendiente.values()),'evidencias_listado_vacio':list(vacios),'rutas_respaldo_descubiertas':list(rutas_respaldo),'busqueda_respaldo_intentada':respaldo_intentado}
        if progreso:progreso(r)
        return r
    def agregar(r):
        provisional=sha256('|'.join((fuente,r['url'],normalizar(r['titulo']))).encode()).hexdigest()
        registro={'id':provisional,'fuente':fuente,'estado':'PUBLICACION_DETECTADA',
             'requiere_revalidacion':False,'organismo':config.get('organismo'),'localidad':config.get('localidad'),'provincia':config.get('provincia'),
             **clasificar(r['titulo']),**r}
        if config.get('organismos_multiples') and not r.get('organismo'):registro['identidad_ambito']=r['url']
        registro=oportunidades.normalizar(registro)
        key=oportunidades.identidad(registro)
        registro=oportunidades.fusionar(items.get(key),registro)
        registro['id']=key
        items[key]=registro
        return key
    def texto_documento(texto,url,referencia=None,hash_documento=None):
        referencia=referencia if isinstance(referencia,str) else None
        if config.get('adaptador') in ('boletin-sf','boletin-er'):
            from extractores_lotes import boletin_texto
            from barrido_institucional import boletin_entre_rios
            registros=boletin_entre_rios(texto,url) if config.get('adaptador')=='boletin-er' else boletin_texto(texto,url,config)
            for registro in registros:
                registro['documentos']=[{'url':url,'titulo':'Boletín complementario'}]
                registro['pago_evidencias']=pagos.extraer(registro['objeto'],url,hash_documento=hash_documento,metodo='SECCION_DOCUMENTO')
                agregar(registro)
            return
        if config.get('exigir_llamado_documental') and not re.search(r'(?:llamase|llamese|convocase|convoca\s+a|se\s+llama|se\s+solicitan?)\b.{0,250}(?:licitacion|concurso|compra|cotizacion)',normalizar(texto),re.S):return
        lineas=texto.splitlines()
        posiciones=[i for i,l in enumerate(lineas) if extractores.procesos(l) and (re.search(r'licitaci[oó]n|concurso|cotejo|compra|contrataci[oó]n|compulsa',l,re.I) or re.match(r'^\s*(?:p[uú]blica|privada)\b',l,re.I))]
        unicos={p['procedimiento'] for i in posiciones for p in extractores.procesos(lineas[i])}
        if len(unicos)==1:posiciones=posiciones[:1]
        if not posiciones and referencia and texto.strip():
            p=dict(items[referencia]);p['objeto']=texto;p['texto_documento']=texto;p['detalle_completo']=True;p['evidencia_url']=url
            p['pago_evidencias']=pagos.unir_evidencias(p.get('pago_evidencias'),pagos.extraer(texto,url,hash_documento=hash_documento,metodo='TEXTO_DOCUMENTO'))
            items[referencia]=oportunidades.normalizar(p)
            return
        for n,i in enumerate(posiciones):
            t=' '.join(lineas[i:posiciones[n+1] if n+1<len(posiciones) else len(lineas)])
            ps=extractores.procesos(t)
            if not ps:continue
            p=ps[0]
            cabecera=re.split(r'pliego de bases',normalizar(t),maxsplit=1)[0] if re.search(r'pliego de bases',normalizar(t)) else normalizar(t)
            evento='|'.join(sorted(set(extractores.EVENTO.findall(cabecera)))) or None
            r={'titulo':cabecera[:1200],'objeto':t,'url':url,'evidencia_url':url,'documentos':[{'url':url,'titulo':'Documento'}],
               'procedimiento':p['procedimiento'],'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'evento_publicado':evento,'situacion_publicada':extractores.situacion(cabecera),'llamado_especial':bool(evento),'detalle_completo':True,'rango_evidencia':3,'pago_evidencias':pagos.extraer(t,url,hash_documento=hash_documento,metodo='SECCION_DOCUMENTO')}
            if config.get('correlativos_publicados') and re.fullmatch(r'\d{1,6}',p['numero']) and p['tipo']=='cotejo de precios':
                r['registro_estructurado']=True
                plazo=re.search(r'para el\s*:\s*(\d{1,2}/\d{1,2}/20\d{2}\s+a las\s+\d{1,2}[.:]\d{2})',normalizar(t))
                if plazo:r['fecha_limite_presentacion_texto']=plazo[1]

            if config.get('resolver_numero_documental'):
                if re.fullmatch(r'\d{1,6}',p['numero']):
                    # Numeración literal estable por documento; no inferir año de la apertura.
                    r.update(titulo=p['procedimiento'],registro_estructurado=True,numero_oficial_sin_interpretar=p['numero'])
                rotulo=re.search(r'apertura\s*:\s*dia\s*:\s*(\d{1,2})\s+mes\s*:\s*([a-z]+)\s+ano\s*:\s*(20\d{2})\s+hora\s*:\s*(\d{1,2})\s*:\s*(\d{2})',normalizar(t))
                if rotulo:
                    r['fecha_apertura_texto']=rotulo[1]+' de '+rotulo[2]+' de '+rotulo[3]+' a las '+rotulo[4]+':'+rotulo[5]
            previo=items.get(referencia,{})
            if (config.get('resolver_numero_documental') and len(unicos)==1 and previo.get('tipo_procedimiento')=='licitacion' and p['tipo'] in ('licitacion publica','licitacion privada') and previo.get('numero_procedimiento')==p['numero'] and url in {d['url'] for d in previo.get('documentos',[])}):
                items.pop(referencia)
                r={**previo,**r,'documentos':list({d['url']:d for d in previo.get('documentos',[])+r['documentos']}.values())}
                referencia=agregar(r)
            anual=re.fullmatch(r'(\d{1,6})/(20\d{2})',p['numero'])
            if (config.get('resolver_numero_documental') and len(unicos)==1 and (anual or re.fullmatch(r'\d{1,6}',p['numero']))
                and re.fullmatch(r'\d{1,6}',str(previo.get('numero_procedimiento') or ''))
                and int(previo['numero_procedimiento'])==int(anual[1] if anual else p['numero'])
                and previo.get('tipo_procedimiento')==p['tipo']):
                # Únicamente el documento enlazado del mismo procedimiento aporta el año.
                numero_previo=previo['numero_procedimiento']
                items.pop(referencia)
                r={**previo,**r,'documentos':list({d['url']:d for d in previo.get('documentos',[])+r['documentos']}.values()),
                   'numero_documental_previo':numero_previo,'evidencia_numero_documental':{'url':url,'sha256':hash_documento,'numero':p['numero']}}
                referencia=agregar(r)
            else:agregar(r)
            if referencia in items and items[referencia].get('procedimiento')==p['procedimiento']:
                # Un aviso con varios llamados no puede asignar a todos el primer presupuesto/fecha.
                unicos={p['procedimiento'] for linea in lineas for p in extractores.procesos(linea)}
                detalle=texto if len(unicos)==1 else t
                items[referencia]['objeto']=detalle
                items[referencia]['texto_documento']=detalle
                items[referencia]['pago_evidencias']=pagos.unir_evidencias(items[referencia].get('pago_evidencias'),pagos.extraer(detalle,url,hash_documento=hash_documento,metodo='SECCION_DOCUMENTO'))
                items[referencia]['evidencia_url']=url
                items[referencia]['detalle_completo']=True
                items[referencia]=oportunidades.normalizar(items[referencia])
        if referencia in items and config.get('numeracion_compuesta'):
            m=re.search(r'\bn[º°o.]*\s*(\d+(?:\s*-\s*\d+)+)\s*/\s*(20\d{2})',normalizar(items[referencia]['titulo']))
            if m:
                esperados={oportunidades.procedimiento_canonico({'numero_procedimiento':n+'/'+m[2],'tipo_procedimiento':items[referencia].get('tipo_procedimiento')}) for n in re.findall(r'\d+',m[1])}
                recuperados={oportunidades.procedimiento_canonico({'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo']}) for linea in lineas for p in extractores.procesos(linea)}
                if esperados and None not in esperados and esperados<=recuperados:
                    # El enlace colectivo es un índice, no una oportunidad adicional.
                    items[referencia]['documento_desglosado']={'procedimientos':sorted(esperados),'url':url,'sha256':hash_documento}
    while pending or (((not respaldo_intentado and config.get('consultas_respaldo')) or (not respaldo_pdf_intentado and config.get('pdf_diario_alternativo'))) and not items and (errors or not vacios) and not any(e.get('http_status') in (401,403,429) for e in errors)):
        if not pending:
            if config.get('pdf_diario_alternativo') and not respaldo_pdf_intentado:
                from fuentes_criticas import pdf_santafe
                respaldo_pdf_intentado=True
                pending.append((pdf_santafe(fuente),'DOCUMENTO',None))
                snapshot('PDF_OFICIAL_ALTERNATIVO')
                continue
            respaldo_intentado=True
            from tools.descubrir_fuentes import rss
            for consulta in config['consultas_respaldo']:
                consulta=consulta.replace('{anio}',str(oportunidades.datetime.now(oportunidades.ZONA).year))
                buscador='https://www.bing.com/search?'+urlencode({'q':consulta,'format':'rss','setlang':'es','cc':'ar'})
                snapshot('BUSQUEDA_COMPLEMENTARIA',buscador)
                try:
                    datos,_,_=fetch(buscador)
                    candidatos=[c for c in rss(datos) if _host(c['url']) in hosts]
                    for c in candidatos:
                        if c['url'] not in seen:
                            rutas_respaldo.append(c);pending.append((c['url'],'LISTADO',{}))
                except Exception as error:
                    errors.append({'url':buscador,**clasificar_error(error,'DESCARGA'),'metodo':'BUSCADOR_COMPLEMENTARIO'})
                snapshot('BUSQUEDA_COMPLEMENTARIA_FINALIZADA',buscador)
            if not pending:break
        if len(seen)>=max_paginas:limits.append('max_paginas');break
        url,clase,referencia=pending.popleft();url=extractores.url_publica(url)
        post=urlencode(referencia['post']).encode() if clase in ('DATATABLES','AJAX_PUBLICADO') else (b'{"":""}' if config.get('adaptador')=='chajari-api' and re.search(r'/licitaciones/(?:para_apertura|en_evaluacion|adjudicada)/\d+$',url or '') else None)
        peticion=url+('#POST:'+sha256(post).hexdigest() if post is not None else '') if url else None
        if not url or peticion in seen or _host(url) not in hosts:continue
        seen.add(peticion);fase='DESCARGA';snapshot(fase,url)
        try:
            if clase=='DETALLE' and int(config.get('concurrencia_detalles',1))>1:
                if url not in respuestas_detalles:
                    from concurrent.futures import ThreadPoolExecutor
                    lote=[url]
                    for u,c,_ in pending:
                        u=extractores.url_publica(u)
                        if c=='DETALLE' and u and u not in seen and u not in lote and u not in respuestas_detalles and _host(u) in hosts:lote.append(u)
                        if len(lote)>=min(3,int(config['concurrencia_detalles'])):break
                    def obtener(u):
                        try:return u,(True,fetch(u))
                        except Exception as e:return u,(False,e)
                    # Sólo HTTP en paralelo: análisis y checkpoints permanecen secuenciales.
                    with ThreadPoolExecutor(max_workers=min(3,int(config['concurrencia_detalles']))) as pool:
                        respuestas_detalles.update(pool.map(obtener,lote))
                ok,respuesta=respuestas_detalles.pop(url)
                if not ok:raise respuesta
                datos,tipo,final=respuesta
            else:datos,tipo,final=fetch(url,datos_post=post) if post is not None else fetch(url)
            if reintentos_diferidos.get(url):
                for incidencia in errors:
                    if incidencia.get('url')==url and incidencia.get('reintento_diferido'):incidencia.update(acceso_recuperado=True,permanencia='TRANSITORIA_RECUPERADA')
            fase='EXTRACCION';snapshot(fase,url)
            if _host(final) not in hosts:raise ValueError('Redirección fuera de dominios oficiales declarados')
            if clase=='CSV_PUBLICADO':
                from fuentes_criticas import gestiones_csv
                registros,fallos=gestiones_csv(datos,final,fuente)
                for r in registros:agregar(r)
                errors.extend({'url':url,**e} for e in fallos)
                if not registros and not fallos:vacios.append({'url':url,'texto':'CSV oficial con columnas de convocatorias y sin filas'})
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if config.get('barrido_institucional') and ('rss' in tipo.lower() or 'atom+xml' in tipo.lower() or ('xml' in tipo.lower() and re.search(br'<(?:rss|feed)\b',datos[:1000]))):
                from barrido_institucional import extraer_feed
                registros,enlaces,cantidad=extraer_feed(datos,final,config)
                for r in registros:agregar(r)
                for u in enlaces:pending.append((u,'LISTADO',{}))
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if config.get('adaptador')=='boletin-er' and 'json' in tipo.lower():
                from barrido_institucional import ediciones_entre_rios
                for u,fecha_edicion in ediciones_entre_rios(datos):pending.append((u,'DOCUMENTO',{'fecha_edicion':fecha_edicion}))
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if config.get('adaptador')=='entre-rios-api':
                if 'json' not in tipo.lower():raise ValueError('ER devolvió HTML en lugar del listado JSON público')
                from extractores_lotes import extraer_entre_rios_api
                registros=extraer_entre_rios_api(datos,final,config)
                for r in registros:agregar(r)
                if not registros:vacios.append({'url':url,'texto':'API pública ER devuelve success=true y data=[]; sólo alcance de este listado'})
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if config.get('adaptador')=='chajari-api' and 'json' in tipo.lower():
                from extractores_lotes import extraer_chajari
                registros,cantidad=extraer_chajari(datos,final)
                huella=sha256(json.dumps(registros,sort_keys=True).encode()).hexdigest()
                if registros and huella in paginas_api:raise ValueError('Chajarí repite página; recorrido incompleto')
                if registros:paginas_api.add(huella)
                for r in registros:agregar(r)
                if cantidad==50:
                    m=re.search(r'/([0-9]+)$',url)
                    pending.append((url[:m.start()]+ '/'+str(int(m[1])+50),'LISTADO',None))
                if not registros:vacios.append({'url':url,'texto':'Consulta pública devuelve result=[]'})
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if config.get('adaptador')=='assa-api' and 'json' in tipo.lower():
                from extractores_lotes import extraer_assa
                registros,meta,detalle=extraer_assa(datos,final)
                huella=sha256(json.dumps(registros,sort_keys=True).encode()).hexdigest()
                if registros and not detalle and huella in paginas_api:raise ValueError('ASSA repite página; recorrido incompleto')
                if not detalle:paginas_api.add(huella)
                for r in registros:
                    agregar(r)
                    if not detalle:pending.append((r['url'],'DETALLE',None))
                if not detalle:
                    if not registros and meta['totalElements']:raise ValueError('ASSA vacío antes de alcanzar total')
                    if meta['number']+1<meta['totalPages']:
                        p=urlsplit(final);q=parse_qs(p.query);q['page']=[str(meta['number']+1)]
                        pending.append((urlunsplit((p.scheme,p.netloc,p.path,urlencode(q,doseq=True),'')),'LISTADO',None))
                    if meta['totalElements']==0:vacios.append({'url':url,'texto':'API pública informa totalElements=0'})
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if clase=='DATATABLES':
                from extractores_lotes import extraer_funes
                registros,total,filas=extraer_funes(datos,final)
                huella=sha256(json.dumps(filas,sort_keys=True).encode()).hexdigest()
                if filas and huella in paginas_api:raise ValueError('DataTables repite una página: no se declara completo')
                paginas_api.add(huella)
                for r in registros:
                    key=agregar(r)
                    for doc in r.get('documentos',[]):
                        destino=doc['url']
                        if (modo=='todos' or not r.get('detalle_completo')) and _host(destino) in hosts and destino not in seen:
                            documento_pendiente[destino]={'url':destino,'publicacion_id':key}
                            pending.append((destino,'DOCUMENTO',key))
                parametros=referencia['post'];siguiente=int(parametros['start'])+len(filas)
                if siguiente<total:
                    if not filas:raise ValueError('DataTables vacío antes de alcanzar el total publicado')
                    pending.append((url,'DATATABLES',{'post':{**parametros,'start':siguiente,'draw':int(parametros['draw'])+1}}))
                if total==0:vacios.append({'url':url,'texto':'DataTables oficial informa recordsTotal=0'})
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            if config.get('adaptador')=='vgg' and 'json' in tipo.lower():
                from extractores_lotes import extraer_vgg
                registros=extraer_vgg(datos,final)
                for r in registros:agregar(r)
                if not registros:vacios.append({'url':url,'texto':'Listado JSON oficial vacío'})
                correctas+=1;snapshot('PAGINA_FINALIZADA',url);continue
            es_html='html' in tipo.lower() and not datos.startswith(b'%PDF-')
            if not es_html:
                import cache_documentos
                texto,_=cache_documentos.leer_texto(datos,tipo,url,ocr=config.get('ocr',False),
                    progreso=lambda t:(texto_documento(t,url,referencia,sha256(datos).hexdigest()),snapshot('EXTRACCION',url)))
                texto_documento(texto,url,referencia,sha256(datos).hexdigest());documentos_leidos+=1;correctas+=1
                documento_pendiente.pop(url,None)
                snapshot('PAGINA_FINALIZADA',url);continue
            html=decodificar_html(datos,tipo)
            comprobar_acceso(html)
            if clase=='AJAX_PUBLICADO':
                huella='ajax:'+url+':'+sha256(datos).hexdigest()
                if huella in paginas_api:raise ValueError('El servicio delegado repite página: navegación incompleta')
                paginas_api.add(huella)
                if html.strip() and not re.search(r'id=[\"\']finResultados',html,re.I):
                    post_siguiente={**referencia['post'],referencia['campo']:int(referencia['post'][referencia['campo']])+referencia['paso']}
                    pending.append((url,'AJAX_PUBLICADO',{**referencia,'post':post_siguiente}))
            if config.get('endpoints_publicados'):
                from barrido_institucional import endpoints_publicados
                pending.extend(endpoints_publicados(html,config))
            from extractores_lotes import endpoint_funes
            endpoint=endpoint_funes(html,final)
            if endpoint:
                parametros={'draw':1,'start':0,'length':100,'search[value]':'','order[0][column]':0,'order[0][dir]':'desc'}
                for i,campo in enumerate(('numero_licitacion','date_created_licitacion','titulo_licitacion','documentos')):parametros[f'columns[{i}][data]']=campo
                pending.append((endpoint,'DATATABLES',{'post':parametros}))
            pagina_config={**config,**(referencia if isinstance(referencia,dict) else {})}
            registros,links,dom=extractores.extraer(html,final,pagina_config)
            if config.get('adaptador')=='gestiones-sf':
                from fuentes_criticas import enlaces_csv,gestiones_html,total_gestiones
                estructurados=gestiones_html(dom,final)
                if estructurados:
                    firma=sha256(json.dumps(sorted(oportunidades.identidad(r) for r in estructurados)).encode()).hexdigest()
                    if pagina_config.get('es_paginacion') and firma in paginas_gestiones:
                        errors.append({'url':url,'tipo':'PaginacionGestionesRepetida','categoria':'EXTRACCION','timeout':False,'error':'La página siguiente repite procedimientos; recorrido no confirmado'})
                        snapshot('PAGINA_FINALIZADA',url);continue
                    paginas_gestiones.add(firma);registros=estructurados
                total=total_gestiones(dom.root.text)
                if total is not None:totales_gestiones.append(total)
                for u in enlaces_csv(dom,final):pending.appendleft((u,'CSV_PUBLICADO',None))
            if config.get('adaptador')=='dpver-tarjetas':
                contador=re.search(r'mostrando\s+\d+\s*[-–]\s*\d+\s+de\s+(\d+)\s+publicaciones',normalizar(dom.root.text))
                if contador:totales_dpv.append(int(contador[1]))
            if config.get('adaptador')=='rosario' and clase=='LISTADO' and 'recomendada=apertura' in urlparse(url).query:
                for nodo in dom.root.iter():
                    if nodo.clase('contrataciones-resumen__conteo-item'):
                        m=re.match(r'^(\d+)\s+(.+)$',nodo.text.strip())
                        if m:conteos_rosario.setdefault(normalizar(m[2]),set()).add(int(m[1]))
                    elif nodo.clase('contrataciones-resumen__total-titulo') and normalizar(nodo.text)!='contrataciones':
                        numero=next((x.text for x in nodo.parent.iter() if x.tag=='strong' and x.text.isdigit()),None)
                        if numero:conteos_rosario.setdefault(normalizar(nodo.text),set()).add(int(numero))
            if config.get('adaptador')=='vgg':
                from extractores_lotes import endpoints_vgg
                for endpoint in endpoints_vgg(dom,html,final):pending.append((endpoint,'LISTADO',None))
            correctas+=1
            texto=normalizar(dom.root.text)
            # El vacío debe estar publicado explícitamente; no se infiere de falta de matches.
            m=re.search(r'no (?:hay|existen|se encontraron) (?:licitaciones|publicaciones|procesos de compra)|sin licitaciones vigentes',texto)
            if not m and config.get('marcador_vacio'):m=re.search(config['marcador_vacio'],texto)
            if clase=='LISTADO' and config.get('detectar_carga_dinamica') and re.search(r'cargas? mas|load more',texto) and not any('next' in l.get('rel','').split() for l in links):
                errors.append({'url':url,'tipo':'PaginacionDinamicaPendiente','categoria':'EXTRACCION','timeout':False,'error':'Control cargar más sin enlace de siguiente página verificable'})
            if m and config.get('adaptador')!='epe':vacios.append({'url':url,'texto':m.group(0)})
            if config.get('adaptador')=='epe' and clase=='LISTADO' and not registros:
                errors.append({'url':url,'tipo':'EPEListadoNoReconocido','categoria':'EXTRACCION','timeout':False,'error':'HTTP responde pero no hay procedimientos EPE reconocidos; no se presume listado vacío'})
            if not registros and re.search(r'inicia sesi[oó]n para|solo esta disponible dentro de la red|debe iniciar sesi[oó]n',texto):
                errors.append({'url':url,'tipo':'AccesoRestringido','categoria':'ACCESO','timeout':False,'error':'El portal requiere autenticación o red privada; no se elude'})
            for r in registros:
                r['rango_evidencia']=3 if clase=='DETALLE' else 1
                if clase=='DETALLE':r.setdefault('texto_documento',r['titulo'])
                if config.get('requerir_ficha') and clase=='LISTADO':r['detalle_completo']=False
                if (config.get('adaptador')=='rosario' and clase=='DETALLE' and referencia in items
                    and r.get('id_origen') and r.get('id_origen')==items[referencia].get('id_origen')
                    and extractores.url_publica(r['url'])==extractores.url_publica(items[referencia]['url'])):
                    # El listado muestra expediente; la ficha publica número de contratación.
                    previo=items.pop(referencia)
                    r={**previo,**r,'texto_listado':previo.get('texto_listado') or previo.get('titulo')}
                key=agregar(r)
                if clase=='DETALLE' and referencia in items and oportunidades.procedimiento_canonico(r)==oportunidades.procedimiento_canonico(items[referencia]):
                    detalle={**r,'texto_documento':r['titulo'],'rango_evidencia':3}
                    items[referencia]=oportunidades.fusionar(items[referencia],detalle)
                for doc in r.get('documentos',[]):
                    destino=doc['url']
                    necesario=modo=='todos' or not r.get('detalle_completo') or (config.get('documentos_para_descubrimiento') and not r.get('fecha_apertura'))
                    if necesario and (not config.get('solo_descubrimiento') or config.get('documentos_para_descubrimiento')) and _host(destino) in hosts and destino not in seen:
                        documento_pendiente[destino]={'url':destino,'publicacion_id':key}
                        pending.append((destino,'DOCUMENTO',key))
                if (not r.get('detalle_completo') or config.get('enriquecer_fichas')) and r['url']!=url and not urlparse(r['url']).path.lower().endswith(extractores.ADJUNTOS):
                    pending.appendleft((r['url'],'DETALLE',key))
            if config.get('barrido_institucional') and not config.get('ignorar_suscripciones_feed'):
                from barrido_institucional import feeds_publicados
                for u in feeds_publicados(dom,final):pending.append((u,'LISTADO',{}))
            if config.get('buscador_institucional'):
                from barrido_institucional import busquedas_publicadas
                for u in busquedas_publicadas(dom,final):pending.append((u,'LISTADO',{}))
            for l in links:
                destino=l['url'];et=normalizar(l['texto'])
                if config.get('barrido_institucional'):
                    from barrido_institucional import sin_calendario_widget
                    destino=sin_calendario_widget(destino)
                path=urlparse(destino).path
                if config.get('ignorar_suscripciones_feed') and path.rstrip('/').endswith('/feed'):continue
                if _host(destino) not in hosts or destino in seen or destino==url:continue
                if config.get('adaptador')=='mpba-tarjetas' and urlparse(destino).path.rstrip('/') in ('/licitaciones','/v2021/licitaciones') and not any(k in parse_qs(urlparse(destino).query) for k in ('department_id','keyword')):continue
                raices={urlparse(u).path.rstrip('/') for u in config.get('urls_inicio',[fuente])}
                raices.update((urlparse(fuente).path.rstrip('/'),urlparse(url).path.rstrip('/')))
                pagina=clase=='LISTADO' and (('next' in l['rel'].split() or et in ('siguiente','siguiente »','next','»','›') or
                          bool(re.search(r'/page/\d+|[?&](?:page|pagina|paged|start)=\d+',destino))) and any(path.startswith(raiz) for raiz in raices))
                navegar=any(re.search(patron,destino) for patron in config.get('seguir_patrones',[]))
                if config.get('descubrir_contrataciones') and clase=='LISTADO' and len(et)<120 and not extractores.procesos(et):
                    navegar=navegar or bool(re.search(r'\b(?:licitacion(?:es)?|concursos? de precios|compras|contrataciones|bolet(?:in|ines) oficial(?:es)?)\b',et))
                if config.get('barrido_institucional') and clase=='LISTADO' and len(et)<120:
                    navegar=navegar or bool(re.fullmatch(r'(?:todas? las? )?(?:noticias(?: y eventos)?|informacion y noticias|ordenanzas y presupuestos|novedades|boletines?(?: oficiales?)?|decretos|resoluciones|publicaciones administrativas|transparencia|gobierno abierto|cuentas claras|informacion publica|normativa municipal|digesto municipal)',et))
                if config.get('adaptador')=='rosario' and path.endswith('/result-busq-compras-licitaciones') and 'verTipo=' in urlparse(destino).query:
                    navegar=True
                if config.get('adaptador')=='rosario' and re.fullmatch(r'/inicio/compras-licitaciones/detalle/\d+',path):
                    # Nunca reclasificar la ficha como LISTADO por seguir_patrones.
                    if not any(u==destino and c=='DETALLE' for u,c,_ in pending):pending.append((destino,'DETALLE',None))
                    continue
                if config.get('noticias_comunales') and clase=='LISTADO':
                    from descubrimiento_noticias import pertinente,es_seccion
                    if pertinente(l['texto']) and not es_seccion(l['texto']) and len(l['texto'])<600 and not path.lower().endswith(extractores.ADJUNTOS):
                        pending.appendleft((destino,'DETALLE',None))
                if pagina or navegar:
                    contexto={'tipo_contexto':l.get('tipo_contexto',pagina_config.get('tipo_contexto')),'es_paginacion':bool(pagina)}
                    pending.append((destino,'LISTADO',contexto))
                # Un documento del índice de boletines puede contener llamados sin título HTML.
                if not registros and config.get('indice_documentos') and path.lower().endswith(extractores.ADJUNTOS):
                    pending.append((destino,'DOCUMENTO',None))
            posiciones={k:i for i,k in enumerate(items)}
            def orden_pendiente(entrada):
                u,c,ref=entrada
                if config.get('priorizar_listados') and c=='LISTADO' and u in semillas_listado:return (-2,0,0,'',u)
                if c=='CSV_PUBLICADO':return (-1,0,0,'',u)
                if config.get('adaptador')=='boletin-sf':
                    edicion=re.search(r'(20\d{2}-\d{2}-\d{2})licitaciones[.]html',unquote(u))
                    if edicion:return (-1,-int(edicion[1].replace('-','')),0,'',u)
                item=items.get(ref,{}) if isinstance(ref,str) else {}
                anios=re.findall(r'20\d{2}',item.get('numero_procedimiento') or '')
                if clase=='LISTADO' and not anios:
                    # Archivos anuales publicados: recorrer primero los recientes,
                    # manteniendo todos los anteriores en la cola y en la auditoría.
                    anios=re.findall(r'(?<!\d)20\d{2}(?!\d)',urlparse(u).path+'?'+urlparse(u).query)
                # Presupuesto de lectura: documentos recientes primero; no se descarta el archivo.
                if config.get('adaptador')=='rosario' and c=='DETALLE' and config.get('priorizar_listados'):
                    ficha=re.search(r'/detalle/(\d+)',u)
                    return (1,-int(ficha[1]) if ficha else 0,0,'',u)
                if config.get('adaptador')=='sibom':
                    boletin=re.search(r'/bulletins/(\d+)',u)
                    return (0 if c=='LISTADO' else 1,-int(boletin[1]) if boletin else 0,u)
                if config.get('priorizar_listados'):
                    return (0 if c in ('LISTADO','DATATABLES') else 1,-int(anios[-1]) if anios else 0,posiciones.get(ref,10**9) if config.get('priorizar_fichas_recientes') and isinstance(ref,str) else 10**9,item.get('fecha_apertura') or '9999',u)
                return (0 if c=='DETALLE' and item.get('vigencia')=='ABIERTA' else (1 if c=='DETALLE' else 2),-int(anios[-1]) if anios else 0,item.get('fecha_apertura') or '9999',u)
            pending=deque(sorted(pending,key=orden_pendiente))
            snapshot('PAGINA_FINALIZADA',url)
        except Exception as e:
            incidencia={'url':url,**clasificar_error(e,fase)}
            limite=min(1,max(0,int(config.get('reintentar_listados_diferidos',0))))
            # Un error transitorio de paginación no corta permanentemente la cadena.
            # Una sola segunda oportunidad después de las demás páginas/fichas;
            # los plazos del supervisor siguen limitando todo el trabajo.
            if clase=='LISTADO' and fase=='DESCARGA' and incidencia['categoria']=='RED' and not incidencia.get('restriccion_acceso_comprobada') and (incidencia.get('timeout') or incidencia.get('http_status') in (502,503,504)) and reintentos_diferidos.get(url,0)<limite:
                reintentos_diferidos[url]=reintentos_diferidos.get(url,0)+1
                incidencia['reintento_diferido']=True;seen.discard(peticion);pending.append((url,clase,referencia))
            errors.append(incidencia)
            snapshot('PAGINA_FINALIZADA',url)
            if isinstance(e,HTTPError) and e.code==429:
                limits.append('HTTP_429_REINTENTO_POSPUESTO');break
    if config.get('adaptador')=='rosario' and conteos_rosario:
        reales={t:{r['url'] for r in items.values() if r.get('tipo_procedimiento')==t and (not config.get('consultar_meses_rosario') or r.get('vigencia')=='ABIERTA')} for t in conteos_rosario}
        faltantes={t:{'publicadas':max(v),'extraidas':len(reales.get(t,set()))} for t,v in conteos_rosario.items() if len(reales.get(t,set()))<max(v)}
        if faltantes:errors.append({'url':fuente,'tipo':'ConteoRosarioIncompleto','categoria':'EXTRACCION','timeout':False,'error':'El recorrido no alcanza el total publicado por el portal; no se declara cobertura completa','por_tipo':faltantes})
    if totales_dpv and len(items)<max(totales_dpv):
        errors.append({'url':fuente,'tipo':'ConteoDPVIncompleto','categoria':'EXTRACCION','timeout':False,'error':'No se alcanzó el total publicado de tarjetas; no se declara cobertura completa','publicadas':max(totales_dpv),'extraidas':len(items)})
    if totales_gestiones and len(items)<max(totales_gestiones):
        errors.append({'url':fuente,'tipo':'ConteoGestionesIncompleto','categoria':'EXTRACCION','timeout':False,'error':'No se alcanzó el total publicado; conservar parciales','publicadas':max(totales_gestiones),'extraidas':len(items)})
    incompletas=[r['id'] for r in items.values() if not r.get('detalle_completo') and not r.get('documento_desglosado')]
    if incompletas:
        errors.append({'url':fuente,'tipo':'DetalleIncompleto','categoria':'EXTRACCION','timeout':False,
                       'error':'Fichas o datos complementarios pendientes; se conservan los campos comprobados del aviso','publicaciones':incompletas})
    estado='OPERATIVA' if items else 'PENDIENTE'
    if not items and vacios and not errors and not limits:estado='SIN_PUBLICACIONES'
    if not correctas and errors:estado='BLOQUEADA' if all(e['categoria'] in ('RED','ACCESO') for e in errors) else 'PENDIENTE'
    if items and (errors or limits):estado='PARCIAL'
    if not items and not vacios and not errors:
        errors.append({'url':fuente,'tipo':'SinPublicacionesDetectadas','categoria':'EXTRACCION','timeout':False,
                       'error':'Listado no reconocido; no se declara vacío'})
    result=snapshot('FINALIZADA',finalizado=True);result['estado']=estado
    if progreso:progreso(result)
    return result
