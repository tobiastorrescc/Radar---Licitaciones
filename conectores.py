"""Conectores auditables. Una respuesta HTTP no prueba detección de publicaciones."""
from collections import deque
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag,urlencode,parse_qs,urlsplit,urlunsplit
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


def descargar(url, conexion_timeout=5, lectura_timeout=10, headers_extra=None, devolver_headers=False,datos_post=None,max_bytes=12_000_000):
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
                    transitorio=(isinstance(error,HTTPError) and error.code in (500,502,503,504)) or isinstance(error,(RemoteDisconnected,TimeoutError,socket.timeout))
                    intentos_http.append({'url':url,'intento':intento+1,'estado':'ERROR','http_status':getattr(error,'code',None),'error':str(error),'segundos':round(time.monotonic()-inicio,3),'reintentable':transitorio})
                    if not transitorio or intento==reintentos:raise
                    time.sleep(min(1,0.25*(2**intento)))
    pending=deque([(extractores.url_publica(u) or u,'LISTADO',{'tipo_contexto':config.get('contextos_listado',{}).get(parse_qs(urlparse(u).query).get('tipoRecomendada',[''])[0])}) for u in config.get('urls_inicio',[fuente])])
    seen=set();items={};errors=[];limits=[];correctas=0;documentos_leidos=0
    hosts={_host(fuente),*(_host('https://'+h) for h in config.get('dominios_documentos',[]))}
    documento_pendiente={};vacios=[];paginas_api=set()
    modo=config.get('lectura_adjuntos','todos')
    def snapshot(fase,actual=None,finalizado=False):
        r={'oportunidades':list(items.values()),'errores':list(errors),'limites':list(limits),
           'paginas_visitadas':len(seen),'paginas_correctas':correctas,'documentos_leidos':documentos_leidos,
           'cobertura_completa':False,'fase':fase,'url_actual':actual,'finalizado':finalizado,
           'alcance':'Listado completo de publicaciones reconocidas y sus enlaces; adjuntos necesarios para extraer objeto',
           'intentos_http':list(intentos_http),'documentos_pendientes':list(documento_pendiente.values()),'evidencias_listado_vacio':list(vacios)}
        if progreso:progreso(r)
        return r
    def agregar(r):
        provisional=sha256('|'.join((fuente,r['url'],normalizar(r['titulo']))).encode()).hexdigest()
        registro={'id':provisional,'fuente':fuente,'estado':'PUBLICACION_DETECTADA',
             'organismo':config.get('organismo'),'localidad':config.get('localidad'),'provincia':config.get('provincia'),
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
            for registro in boletin_texto(texto,url,config):
                registro['documentos']=[{'url':url,'titulo':'Boletín complementario'}]
                registro['pago_evidencias']=pagos.extraer(registro['objeto'],url,hash_documento=hash_documento,metodo='SECCION_DOCUMENTO')
                agregar(registro)
            return
        lineas=texto.splitlines()
        posiciones=[i for i,l in enumerate(lineas) if extractores.procesos(l)]
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
            evento='|'.join(sorted(set(extractores.EVENTO.findall(normalizar(t))))) or None
            r={'titulo':t,'objeto':t,'url':url,'evidencia_url':url,'documentos':[{'url':url,'titulo':'Documento'}],
               'procedimiento':p['procedimiento'],'numero_procedimiento':p['numero'],'tipo_procedimiento':p['tipo'],'evento_publicado':evento,'detalle_completo':True,'rango_evidencia':3,'pago_evidencias':pagos.extraer(t,url,hash_documento=hash_documento,metodo='SECCION_DOCUMENTO')}
            agregar(r)
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
    while pending:
        if len(seen)>=max_paginas:limits.append('max_paginas');break
        url,clase,referencia=pending.popleft();url=extractores.url_publica(url)
        post=urlencode(referencia['post']).encode() if clase=='DATATABLES' else (b'{"":""}' if config.get('adaptador')=='chajari-api' and re.search(r'/licitaciones/(?:para_apertura|en_evaluacion|adjudicada)/\d+$',url or '') else None)
        peticion=url+('#POST:'+sha256(post).hexdigest() if post is not None else '') if url else None
        if not url or peticion in seen or _host(url) not in hosts:continue
        seen.add(peticion);fase='DESCARGA';snapshot(fase,url)
        try:
            datos,tipo,final=fetch(url,datos_post=post) if post is not None else fetch(url)
            fase='EXTRACCION';snapshot(fase,url)
            if _host(final) not in hosts:raise ValueError('Redirección fuera de dominios oficiales declarados')
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
            from extractores_lotes import endpoint_funes
            endpoint=endpoint_funes(html,final)
            if endpoint:
                parametros={'draw':1,'start':0,'length':100,'search[value]':'','order[0][column]':0,'order[0][dir]':'desc'}
                for i,campo in enumerate(('numero_licitacion','date_created_licitacion','titulo_licitacion','documentos')):parametros[f'columns[{i}][data]']=campo
                pending.append((endpoint,'DATATABLES',{'post':parametros}))
            pagina_config={**config,**(referencia if isinstance(referencia,dict) else {})}
            registros,links,dom=extractores.extraer(html,final,pagina_config)
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
                if clase=='DETALLE':r['texto_documento']=r['titulo']
                if config.get('requerir_ficha') and clase=='LISTADO':r['detalle_completo']=False
                key=agregar(r)
                if clase=='DETALLE' and referencia in items and oportunidades.procedimiento_canonico(r)==oportunidades.procedimiento_canonico(items[referencia]):
                    detalle={**r,'texto_documento':r['titulo'],'rango_evidencia':3}
                    items[referencia]=oportunidades.fusionar(items[referencia],detalle)
                for doc in r.get('documentos',[]):
                    destino=doc['url']
                    necesario=modo=='todos' or not r.get('detalle_completo')
                    if necesario and not config.get('solo_descubrimiento') and _host(destino) in hosts and destino not in seen:
                        documento_pendiente[destino]={'url':destino,'publicacion_id':key}
                        pending.append((destino,'DOCUMENTO',key))
                if (not r.get('detalle_completo') or config.get('enriquecer_fichas')) and r['url']!=url and not urlparse(r['url']).path.lower().endswith(extractores.ADJUNTOS):
                    pending.appendleft((r['url'],'DETALLE',key))
            for l in links:
                destino=l['url'];et=normalizar(l['texto']);path=urlparse(destino).path
                if config.get('ignorar_suscripciones_feed') and path.rstrip('/').endswith('/feed'):continue
                if _host(destino) not in hosts or destino in seen or destino==url:continue
                raices={urlparse(u).path.rstrip('/') for u in config.get('urls_inicio',[fuente])}
                raices.update((urlparse(fuente).path.rstrip('/'),urlparse(url).path.rstrip('/')))
                pagina=clase=='LISTADO' and (('next' in l['rel'].split() or et in ('siguiente','siguiente »','next','»','›') or
                          bool(re.search(r'/page/\d+|[?&](?:page|pagina|start)=\d+',destino))) and any(path.startswith(raiz) for raiz in raices))
                navegar=any(re.search(patron,destino) for patron in config.get('seguir_patrones',[]))
                if config.get('descubrir_contrataciones') and clase=='LISTADO' and len(et)<120 and not extractores.procesos(et):
                    navegar=navegar or bool(re.search(r'licitaciones|concursos? de precios|compras|contrataciones|boletines? oficiales?',et))
                if pagina or navegar:
                    contexto={'tipo_contexto':l.get('tipo_contexto',pagina_config.get('tipo_contexto'))}
                    pending.append((destino,'LISTADO',contexto))
                # Un documento del índice de boletines puede contener llamados sin título HTML.
                if not registros and config.get('indice_documentos') and path.lower().endswith(extractores.ADJUNTOS):
                    pending.append((destino,'DOCUMENTO',None))
            def orden_pendiente(entrada):
                u,c,ref=entrada
                item=items.get(ref,{}) if isinstance(ref,str) else {}
                anios=re.findall(r'20\d{2}',item.get('numero_procedimiento') or '')
                if clase=='LISTADO' and not anios:
                    # Archivos anuales publicados: recorrer primero los recientes,
                    # manteniendo todos los anteriores en la cola y en la auditoría.
                    anios=re.findall(r'(?<!\d)20\d{2}(?!\d)',urlparse(u).path+'?'+urlparse(u).query)
                # Presupuesto de lectura: documentos recientes primero; no se descarta el archivo.
                if config.get('priorizar_listados'):
                    return (0 if c in ('LISTADO','DATATABLES') else 1,-int(anios[-1]) if anios else 0,item.get('fecha_apertura') or '9999',u)
                return (0 if c=='DETALLE' and item.get('vigencia')=='ABIERTA' else (1 if c=='DETALLE' else 2),-int(anios[-1]) if anios else 0,item.get('fecha_apertura') or '9999',u)
            pending=deque(sorted(pending,key=orden_pendiente))
            snapshot('PAGINA_FINALIZADA',url)
        except Exception as e:
            errors.append({'url':url,**clasificar_error(e,fase)})
            snapshot('PAGINA_FINALIZADA',url)
            if isinstance(e,HTTPError) and e.code==429:
                limits.append('HTTP_429_REINTENTO_POSPUESTO');break
    incompletas=[r['id'] for r in items.values() if not r.get('detalle_completo') and not r.get('documento_desglosado')]
    if incompletas:
        errors.append({'url':fuente,'tipo':'DetalleIncompleto','categoria':'EXTRACCION','timeout':False,
                       'error':'Publicaciones identificadas sin objeto completo','publicaciones':incompletas})
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
