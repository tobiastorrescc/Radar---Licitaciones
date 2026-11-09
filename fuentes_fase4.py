"""Tarjetas documentales de compras: avisos separados, no actas como convocatorias."""
import re
from urllib.parse import urlsplit
import extractores as e

def ceres(dom,url):
 salida=[]
 for n in dom.root.iter():
  if not n.clase('feature-carousel-box'):continue
  t=n.text
  if re.search(r'(?i)acta\s+de\s+apertura|adjudicacion|adjudicación',t):continue
  m=re.search(r'(?i)\bLic(?:itaci[oó]n)?\.?\s*[Nnº°o.\s]*(\d+)\s*[-/]\s*(20\d{2})',t)
  if not m:continue
  docs=[{'url':l['url'],'titulo':t} for l in n.enlaces(url) if urlsplit(l['url']).path.lower().endswith(e.ADJUNTOS)]
  if not docs:continue
  num=str(int(m[1]))+'/'+m[2];obj=t[:t.find('Descargar')].strip();mitad=len(obj)//2
  if obj[:mitad].strip()==obj[mitad:].strip():obj=obj[:mitad].strip()
  salida.append({'url':docs[0]['url'],'evidencia_url':url,'titulo':'Licitación '+num+' '+obj,'objeto':obj,'numero_procedimiento':num,'tipo_procedimiento':'licitacion','procedimiento':'licitacion '+num,'documentos':docs,'registro_estructurado':True,'detalle_completo':False})
 return salida


def comuna_cms(dom,url):
 from urllib.parse import parse_qs
 from presentacion_documental import clausula
 import oportunidades as o
 if parse_qs(urlsplit(url).query).get('pagina')!=['detalle']:return None
 art=next((n for n in dom.root.iter() if n.tag=='article' and n.clase('content')),None)
 if not art:return []
 h=next((n for n in art.iter() if n.tag=='h1'),None)
 if not h:return []
 titulo=h.text;norm=e.norm(titulo)
 if not re.search(r'licitacion|concurso de precios|contratacion directa|solicitud de cotizacion',norm):return []
 if re.search(r'personal administrativo|concurso de cargos|empleo|fotografico',norm):return []
 bloque=next((q for q in h.padres() if q.tag=='div'),art);texto=bloque.text
 ps=e.procesos(texto);unicos={(p['tipo'],p['numero']) for p in ps};p=ps[0] if len(unicos)==1 else None
 tipo=p['tipo'] if p else 'concurso de precios' if 'concurso de precios' in norm else 'aviso de contratacion'
 obj=re.search(r'(?i)(?:como objeto la |objeto (?:la )?)(compra de .+?)(?:\.\s|$)',texto)
 docs=[{'url':l['url'],'titulo':l['texto']} for l in bloque.enlaces(url) if urlsplit(l['url']).path.lower().endswith(e.ADJUNTOS)]
 fecha=re.search(r'(?i)publicado[,:]?\s*(.{0,90})',texto)
 r={'url':url,'evidencia_url':url,'titulo':titulo,'objeto':obj[1].strip() if obj else titulo,'texto_documento':texto,'numero_procedimiento':p['numero'] if p else None,'tipo_procedimiento':tipo,'procedimiento':p['procedimiento'] if p else None,'aviso_oficial_sin_numero':p is None,'registro_estructurado':True,'detalle_completo':True,'fecha_publicacion_texto':fecha[1] if fecha else None,'situacion_publicada':'FINALIZADA' if re.search(r'\bcerrad[oa]\b',norm) else e.situacion(titulo),'documentos':docs}
 if p is None:
  from hashlib import sha256
  idp=parse_qs(urlsplit(url).query).get('idp',[None])[0]
  clave=(urlsplit(url).hostname or '').removeprefix('www.')+urlsplit(url).path+'|idp='+str(idp) if idp else url
  r['huella_aviso_oficial']=sha256(clave.encode()).hexdigest()
 r.update(clausula(texto,o.normalizar(r),url))
 if 'en sobre cerrado' in e.norm(texto):r['modalidad_presentacion']=['PRESENCIAL']
 return [r]

def refinar_ceres(r):
 """Objeto acotado al rótulo, conservando íntegro el texto oficial y sus fechas."""
 r=dict(r);texto=r.get('texto_documento') or r.get('objeto') or ''
 m=re.search(r'(?im)^\s*OBJETO\s*:\s*(.+?)(?:\n\s*\n|\n\s*PLAZO|$)',texto,re.S)
 if m:
  r['texto_documento']=texto;r['objeto']=' '.join(m[1].split())
 return r

def naturaleza_convocatoria(r):
 """Una venta de bienes municipales no es una compra a proveedores; no se elimina."""
 obj=e.norm(r.get('objeto') or '')
 return 'VENTA_BIENES_PUBLICOS' if re.search(r'^venta\b.{0,50}(?:lotes|propiedad municipal)',obj) else 'COMPRA_O_SERVICIO'
