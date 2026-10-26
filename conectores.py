"""Conectores auditables. Una respuesta HTTP no prueba detección de publicaciones."""
from collections import deque
from hashlib import sha256
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
import re
import subprocess
import unicodedata


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


def descargar(url):
    with urlopen(Request(url, headers={'User-Agent': 'RadarLicitaciones/2.0'}), timeout=15) as r:
        datos = r.read(12_000_001)
        if len(datos) > 12_000_000:
            raise ValueError('Respuesta supera 12 MB; recorrido parcial')
        return datos, r.headers.get('Content-Type', ''), r.geturl()


def identidad(fuente, titulo, url):
    # Diferentes llamados en una URL y documentos en distintos portales se conservan.
    p = clasificar(titulo)
    clave = '|'.join((fuente, urldefrag(url)[0], p['procedimiento'] or normalizar(titulo),
                      p['evento_publicado'] or '', p['situacion_publicada'] or ''))
    return sha256(clave.encode()).hexdigest()


def explorar(fuente, config, fetch=None, max_paginas=1000):
    fetch = fetch or descargar
    pending, seen, items, errors = deque([fuente]), set(), {}, []
    limits, correctas, documentos = [], 0, 0
    hosts = {urlparse(fuente).netloc, *config.get('dominios_documentos', [])}
    while pending:
        if len(seen) >= max_paginas:
            limits.append('max_paginas'); break
        url = urldefrag(pending.popleft())[0]
        if url in seen or urlparse(url).scheme not in ('https', 'http') or urlparse(url).netloc not in hosts:
            continue
        seen.add(url)
        try:
            datos, tipo, final = fetch(url)
            if urlparse(final).netloc not in hosts:
                raise ValueError('Redirección fuera de dominios declarados')
            if 'pdf' in tipo.lower() or datos.startswith(b'%PDF-'):
                texto = extraer_pdf(datos)
                documentos += 1
                # Separación por encabezados de procedimiento dentro de boletines.
                lineas = texto.splitlines()
                inicios = [i for i, line in enumerate(lineas) if PUBLICACION.search(normalizar(line))]
                registros = [(' '.join(lineas[i:inicios[n+1] if n+1 < len(inicios) else len(lineas)]), url)
                             for n, i in enumerate(inicios)]
                parser = None
            elif 'html' in tipo.lower():
                registros, parser = extraer_html(datos.decode('utf-8', errors='replace'), final)
            else:
                raise ValueError('Formato pendiente de adaptador: ' + tipo)
            correctas += 1
            for titulo, target in registros:
                if urlparse(target).scheme not in ('http', 'https'):
                    continue
                c = clasificar(titulo)
                key = identidad(fuente, titulo, target)
                items[key] = {'id': key, 'titulo': titulo.strip(), 'objeto': titulo.strip(), 'url': target,
                    'fuente': fuente, 'evidencia_url': url, **c, 'estado': 'PUBLICACION_DETECTADA',
                    'organismo': config.get('organismo'), 'localidad': config.get('localidad'),
                    'provincia': config.get('provincia'), 'pago_prioritario': any(x in normalizar(titulo)
                      for x in ('pago contado', 'pago al contado', 'contra entrega', 'pago inmediato')),
                    'fecha_apertura': None, 'presupuesto': None, 'condiciones_pago': None,
                    'estimacion_comercial': None, 'motivo_sin_estimacion': 'Faltan costos y precios comprobables',
                    'enlace_pliego': target if urlparse(target).path.lower().endswith('.pdf') else None}
            if parser:
                for link in parser.links:
                    target = urljoin(final, link['url'])
                    t = normalizar(link['texto'])
                    path = urlparse(target).path.lower()
                    paginacion = ('next' in link['rel'].split() or t in ('siguiente', 'siguiente »', 'next', '»', '›')
                                  or bool(re.search(r'/page/\d+|[?&](?:page|pagina|start)=\d+', target)))
                    documento = path.endswith('.pdf')
                    detalle = bool(PUBLICACION.search(t))
                    if paginacion or documento or detalle:
                        if target not in seen:
                            pending.append(target)
        except Exception as e:
            errors.append({'url': url, 'tipo': type(e).__name__, 'error': str(e)})
    estado = 'OPERATIVA' if items else 'PENDIENTE'
    if not correctas and errors:
        estado = 'BLOQUEADA' if all(e['tipo'] in ('HTTPError', 'URLError', 'ConnectionError', 'TimeoutError', 'OSError') for e in errors) else 'PENDIENTE'
    if items and (errors or limits):
        estado = 'PARCIAL'
    return {'estado': estado, 'oportunidades': list(items.values()), 'errores': errors,
            'limites': limits, 'paginas_visitadas': len(seen), 'paginas_correctas': correctas,
            'documentos_leidos': documentos, 'cobertura_completa': False}
