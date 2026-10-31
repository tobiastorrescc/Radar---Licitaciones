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
        for r in rs:
            if publicada:r['fecha_publicacion_texto']=publicada
            r['evidencia_feed']=url
            resultados.append(r)
        if rs or re.search(r'licitaci[oó]n|concurso de precios|cotizaci[oó]n|pedido de presupuesto',titulo,re.I):enlaces.append(link)
    return resultados,enlaces,len(items)
