"""Avisos en noticias institucionales, sin exigir número, monto ni pliego."""
import re
from hashlib import sha256
from urllib.parse import urlsplit,urlunsplit,parse_qsl,urlencode
import extractores as e

EXPRESIONES=r'\b(?:licitacion(?:es)?|concurso(?:s)? (?:de precios|privado)|solicitud(?:es)? de (?:presupuestos?|cotizacion)|pedido(?:s)? de (?:presupuestos?|cotizacion)|convocatoria a proveedores|compra(?:s)? (?:directa|agil|menor)|segundo llamado|prorroga de (?:recepcion|presentacion)|presentacion de ofertas|apertura de sobres)\b'
def es_seccion(texto):
 return bool(re.fullmatch(r'(?:compras(?: y contrataciones)?|licitaciones(?: publicas| privadas)?(?: y concursos)?|concursos(?: y licitaciones)?|concursos de precios)(?: 20\d{2})?',e.norm(texto)))

def pertinente(texto):
 return bool(re.search(EXPRESIONES,e.norm(texto)))

def noticia(dom,url):
 hs=[n for n in dom.root.iter() if n.tag=='h1' and not e.excluido(n)]
 if len(hs)!=1:return []
 h=hs[0];titulo=h.text
 if es_seccion(titulo) or e.norm(titulo).startswith('resultados de busqueda'):return []
 bloque=next((n for n in h.padres() if n.tag=='article'),None)
 if bloque is None:bloque=next((n for n in h.padres() if n.tag=='main'),None)
 if bloque is None:return []
 # No usar una portada con varias noticias como ficha de un procedimiento.
 if sum(n.tag=='h1' for n in bloque.iter())!=1:return []
 texto=bloque.text;t=e.norm(texto);cab=e.norm(titulo)
 if not pertinente(titulo):
  encabezado=re.match(r'(?:aviso|convocatoria|invitacion|decreto|resolucion)\b',cab)
  llamado=re.search(r'\b(?:se solicitan? (?:presupuestos|cotizaciones)|llamase a (?:licitacion|concurso de precios)|convoca a (?:licitacion|concurso de precios|proveedores))\b',t)
  if not encabezado or not llamado:return []
 if re.search(r'concurso.{0,50}(?:cargo|personal|fotograf|literari|cultura)|inscripcion de aspirantes',cab):return []
 if not re.search(r'adquisicion|provision|compra de|servicio|contratacion|material|insumos|obra|presupuesto|ofertas|sobres',t):return []
 ps=e.procesos(titulo);ps=ps or e.procesos(texto)
 if len({(p['tipo'],p['numero']) for p in ps})>1:return []
 p=ps[0] if ps else None
 u=urlsplit(url);q=[(k,v) for k,v in parse_qsl(u.query) if not k.startswith('utm_')]
 estable=urlunsplit((u.scheme,(u.hostname or '').removeprefix('www.'),u.path,urlencode(sorted(q)),''))
 contenido=next((n for n in bloque.iter() if n.clase('entry-content') or n.clase('td-post-content') or n.attrs.get('itemprop')=='articleBody'),bloque)
 parrafos=[n.text.strip() for n in contenido.iter() if n.tag=='p' and n.text.strip()]
 objeto=next((p for p in parrafos if re.search(r'\b(?:objeto|adquisicion|provision|compra de|contratacion de|previsto para la compra)\b',e.norm(p)) and not re.search(r'valor del pliego|costo del pliego',e.norm(p))),titulo)
 r={'titulo':titulo,'objeto':objeto,'texto_documento':texto,'url':url,'evidencia_url':url,'registro_estructurado':True,'detalle_completo':True,'numero_procedimiento':p['numero'] if p else None,'tipo_procedimiento':p['tipo'] if p else 'aviso de contratacion','procedimiento':p['procedimiento'] if p else None,'aviso_oficial_sin_numero':not bool(p),'situacion_publicada':e.situacion(titulo),'documentos':[{'url':l['url'],'titulo':l['texto']} for l in bloque.enlaces(url) if (urlsplit(l['url']).path.lower().endswith(e.ADJUNTOS) or urlsplit(l['url']).hostname=='drive.google.com' and re.search(r'/file/d/[^/]+|/open\?id=',l['url']))]}
 if not p:r['huella_aviso_oficial']=sha256(estable.encode()).hexdigest()
 # Sólo fecha publicada explícitamente. dateModified nunca reemplaza publicación.
 fechas={n.attrs.get('datetime') for n in bloque.iter() if n.tag=='time' and n.attrs.get('datetime') and ('published' in n.attrs.get('class','') or n.attrs.get('itemprop')=='datePublished')}
 fechas.update(n.attrs.get('content') for n in bloque.iter() if n.tag=='meta' and n.attrs.get('itemprop')=='datePublished' and n.attrs.get('content'))
 fechas.update(n.attrs.get('content') for n in dom.root.iter() if n.tag=='meta' and n.attrs.get('property')=='article:published_time' and n.attrs.get('content'))
 if len({f[:10] for f in fechas})==1:r['fecha_publicacion_texto']=next(iter(fechas))[:10]
 from presentacion_documental import clausula
 import oportunidades as o
 r.update(clausula(texto,o.normalizar(r),url))
 if 'sobre cerrado' in t:r['modalidad_presentacion']=['PRESENCIAL']
 return [r]
