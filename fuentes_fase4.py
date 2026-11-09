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
