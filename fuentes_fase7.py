"""Publicaciones del grid público GeneXus, sin ejecutar scripts ni autenticación."""
import json,re
from datetime import datetime
from urllib.parse import urljoin
import extractores

def siglo(html,url):
 dom=extractores.DOM(html);n=next((n for n in dom.root.iter() if n.tag=='input' and n.attrs.get('name')=='GridContainerDataV'),None)
 if n is None:raise ValueError('Grid oficial no reconocido; no se presume vacío')
 rows=json.loads(n.attrs.get('value',''));out=[]
 if not isinstance(rows,list):raise ValueError('Grid con estructura desconocida')
 for a in rows:
  if not isinstance(a,list) or len(a)<83:raise ValueError('Columnas de grid incompletas')
  titulo=a[23];doc=a[29];numero=a[11];anio=a[17];entidad=a[82]
  if not all(isinstance(v,str) for v in (titulo,doc,numero,anio,entidad)):raise ValueError('Tipos de grid cambiaron')
  if not re.fullmatch(r'/PublicDoc/PublicTempStorage/[^?]+\.pdf',doc,re.I):continue
  procesos=extractores.procesos(titulo)
  if not procesos:continue
  p=procesos[0];r={'url':urljoin(url,doc),'evidencia_url':url,'titulo':titulo,'objeto':titulo,'procedimiento':p['procedimiento'],'tipo_procedimiento':p['tipo'],'numero_procedimiento':p['numero'],'registro_estructurado':True,'detalle_completo':True,'organismo':entidad,'documentos':[{'url':urljoin(url,doc),'titulo':titulo}],'situacion_publicada':extractores.situacion(titulo)}
  try:r['fecha_publicacion']=datetime.strptime(a[5],'%d/%m/%y').date().isoformat()
  except ValueError:pass
  out.append(r)
 return out,len(rows)
