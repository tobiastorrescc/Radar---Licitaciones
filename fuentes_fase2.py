"""Lectura de tarjetas oficiales, sin exigir ni descargar el pliego para descubrir."""
import re
from urllib.parse import urlsplit,parse_qs,urlencode,urlunsplit
import extractores as e

def dpver(dom,url):
 rs=[]
 for card in dom.root.iter():
  if card.tag!='article':continue
  titulo=next((n.text for n in card.iter() if n.tag=='h2'),None)
  campos={}
  for dt in card.iter():
   if dt.tag=='dt':
    dd=next((n.text for n in dt.parent.iter() if n.tag=='dd'),None);campos[e.norm(dt.text)]=dd
  numero=next((v for k,v in campos.items() if 'contrato' in k),None);apertura=campos.get('fecha de apertura')
  tipo=next((n.text for n in card.iter() if n.tag=='span' and n.clase('font-medium')),None)
  doc=next((l['url'] for l in card.enlaces(url) if re.search(r'/api/contrataciones-licitaciones/\d+/adjunto$',urlsplit(l['url']).path)),None)
  if not titulo or not tipo:continue
  id=re.search(r'/contrataciones-licitaciones/(\d+)/',doc)[1] if doc else __import__('hashlib').sha256((tipo+'|'+str(numero)+'|'+titulo+'|'+str(apertura)).encode()).hexdigest();hora=re.search(r'a las\s+(\d{1,2}:\d{2})',e.norm(titulo))
  rs.append({'titulo':tipo+' '+str(numero or '')+' '+titulo,'objeto':re.split(r'\s*[-–]\s*FECHA DE APERTURA',titulo,flags=re.I)[0],'numero_procedimiento':numero,'tipo_procedimiento':e.norm(tipo),'procedimiento':e.norm(tipo)+' '+numero if numero else None,'expediente':campos.get('expediente'),'identidad_ambito':'dpver-'+id,'id_origen':id,'url':doc or url,'evidencia_url':url,'documentos':[{'url':doc,'titulo':'Pliego oficial'}] if doc else [],'fecha_apertura_texto':(apertura+' '+hora[1] if apertura and hora else apertura),'registro_estructurado':True,'detalle_completo':True})
 return rs

def mpba(dom,url,config):
 rs=[]
 for card in dom.root.iter():
  if not card.clase('auction-card'):continue
  cab=next((n.text for n in card.iter() if n.clase('auction-card-titles-block-1')),None)
  if not cab:continue
  m=re.search(r'(.+?)\s+(\d+\s*/\s*\d{2,4})\s*$',cab)
  if not m:continue
  tipo=e.norm(m[1]);num=re.sub(r'\s','',m[2]);num=re.sub(r'/(\d{2})$',r'/20\1',num)
  cuerpo=card.text
  # El filtro oficial de departamento da el ámbito; sin filtro no se atribuye
  # por una mención accidental de una localidad en el objeto.
  id=parse_qs(urlsplit(url).query).get('department_id',[None])[0]
  lugar=config.get('departamentos_publicados',{}).get(id)
  if not lugar:
   for candidata in config.get('localidades_publicadas',[]):
    ciudad=e.norm(candidata)
    if re.search(r'(?:ciudad de|departamento judicial(?: de)?)\s+'+re.escape(ciudad)+r'\b',e.norm(cuerpo)):lugar=candidata;break
  if not lugar:continue
  titulo=next((n for n in card.iter() if n.clase('auction-body-title')),card)
  texto=titulo.text
  obj=re.split(r'\bPresentaci[oó]n\s*:',texto,flags=re.I)[0]
  obj=re.sub(r'^\s*Exp\s+[^\s]+\s*','',obj,flags=re.I).strip()
  fecha=re.search(r'Apertura\s+(.{0,80}?(?:20\d{2})\s+\d{1,2}:\d{2})',cuerpo,re.I)
  if not fecha:fecha=re.search(r'Apertura\s+(.{0,60}?20\d{2})',cuerpo,re.I)
  docs=[{'url':l['url'],'titulo':l['texto']} for l in card.enlaces(url) if re.search(r'pliego|documentacion|res[.]? asoc',e.norm(l['texto']))]
  # URL de la convocatoria está publicada en el enlace de la tarjeta.
  oficial=next((l['url'] for l in card.enlaces(url) if re.search(r'/auctions/\d+/download_attachments/pliego|/(?:licitacion|auction)/\d+|/licitaciones/\d+',urlsplit(l['url']).path)),None) or url
  id_oficial=re.search(r'/auctions/(\d+)/',oficial)
  estado=next((e.norm(n.text) for n in card.iter() if n.clase('auction-card-tag')),'')
  situacion={'cancelada':'CANCELADA','anulada':'CANCELADA','sin efecto':'CANCELADA','adjudicada':'ADJUDICADA','desierta':'DESIERTA','fracasada':'FRACASADA'}.get(estado)
  rs.append({'id_origen':id_oficial[1] if id_oficial else None,'identidad_ambito':'mpba-'+id_oficial[1] if id_oficial else None,'organismo':'Ministerio Público de Buenos Aires','provincia':'Buenos Aires','localidad':lugar,'titulo':cab+' '+obj,'objeto':obj,'numero_procedimiento':num,'tipo_procedimiento':tipo,'procedimiento':tipo+' '+num,'url':oficial,'evidencia_url':url,'documentos':docs,'texto_documento':cuerpo,'registro_estructurado':True,'detalle_completo':True,'fecha_apertura_texto':fecha[1] if fecha else None,'situacion_publicada':situacion})
 return rs
