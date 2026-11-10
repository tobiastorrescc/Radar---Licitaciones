"""Nivel rápido: evidencia observada y cola persistente, nunca altas por HTTP 200."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from datetime import datetime,timedelta
from hashlib import sha256
import json,re,time,threading
from pathlib import Path
from urllib.parse import urlparse
import oportunidades as o,conectores,extractores

PESOS={'identidad_verificada':4,'seccion_compras':4,'publicacion_ultimos_7_dias':3,'historial_convocatorias':2,'accesible':1,'documentos_publicados':1}

def puntuar(e):
 razones=[{'criterio':k,'peso':p,'evidencia':e[k]} for k,p in PESOS.items() if e.get(k) is True]
 # Datos desconocidos no restan; antigüedad ordena empates para rotar revisiones.
 return {'puntos':sum(x['peso'] for x in razones),'razones':razones,'desconocidos':[k for k in PESOS if e.get(k) is None],'distancia_geodesica_km':e.get('distancia_geodesica_rosario_km'),'ultima_revision':e.get('ultima_revision')}

class TransporteLimitado:
 def __init__(self):self.lock=threading.Lock();self.dominios={};self.cache={};self.contadores={}
 def obtener(self,u):
  h=urlparse(u).hostname
  with self.lock:sem=self.dominios.setdefault(h,threading.Semaphore(1))
  with sem:
   with self.lock:
    if u in self.cache:return self.cache[u]
    self.contadores[h]=self.contadores.get(h,0)+1
   try:r=(True,conectores.descargar(u,conexion_timeout=3,lectura_timeout=4,max_bytes=2000000))
   except Exception as e:r=(False,conectores.clasificar_error(e,'DESCARGA'))
   with self.lock:self.cache[u]=r
   time.sleep(.15)
   return r

def explorar(c,raiz,transporte):
 from tools.descubrir_fuentes import verificar_identidad
 inicio=time.monotonic();r={**c,'nivel':'RAPIDO','fecha':datetime.now(o.ZONA).isoformat(),'paginas':[],'enlaces_candidatos':[],'documentos':[],'identidad_verificada':None,'accesible':None,'seccion_compras':None,'publicacion_ultimos_7_dias':None,'historial_convocatorias':None,'documentos_publicados':None,'estado':'SIN_SITIO_LOCALIZADO','procedimientos_muestra':[]}
 if not c.get('url'):r['prioridad']=puntuar(r);r['segundos']=0;return r
 cola=[c['url']];vistas=set();identidad={};raiz=Path(raiz);raiz.mkdir(parents=True,exist_ok=True)
 while cola and len(vistas)<3 and time.monotonic()-inicio<22:
  u=cola.pop(0)
  if u in vistas:continue
  vistas.add(u);ok,respuesta=transporte.obtener(u)
  if not ok:r['paginas'].append({'url':u,'estado':'ERROR_ACCESO','error':respuesta});continue
  b,t,f=respuesta;r['accesible']=True
  if 'html' not in t:r['paginas'].append({'url':u,'estado':'DOCUMENTO_PENDIENTE','tipo':t});continue
  html=conectores.decodificar_html(b,t);h=sha256(b).hexdigest();(raiz/(h+'.html')).write_bytes(b)
  try:conectores.comprobar_acceso(html)
  except Exception as e:r['paginas'].append({'url':u,'estado':'ACCESO_RESTRINGIDO','error':str(e)});continue
  if not identidad:identidad=verificar_identidad(html,f,c)
  dom=extractores.DOM(html);links=dom.root.enlaces(f);candidatos=[]
  for l in links:
   texto=o.norm(l['texto']);url=l['url'];path=urlparse(url).path
   doc=path.lower().endswith(extractores.ADJUNTOS)
   if doc:r['documentos'].append({'url':url,'texto':l['texto'][:200]});r['documentos_publicados']=True
   compras=bool(re.search(r'\b(?:compras|contrataciones|licitacion(?:es)?|concursos? de precios|cotizacion|presupuestos)\b',texto))
   noticias=bool(re.fullmatch(r'(?:noticias(?: y eventos)?|novedades|decretos|resoluciones|transparencia|boletin(?: oficial)?)',texto))
   if compras or noticias:
    r['enlaces_candidatos'].append({'url':url,'texto':l['texto'][:200]})
    if compras:r['seccion_compras']=True
    if not doc and urlparse(url).hostname==urlparse(f).hostname:candidatos.append((0 if compras else 1,url))
  # No interpretar el año del pie de página como fecha reciente.
  fechas=[n.attrs.get('datetime') for n in dom.root.iter() if n.tag=='time' and n.attrs.get('datetime')]
  fechas += [n.attrs.get('content') for n in dom.root.iter() if n.tag=='meta' and n.attrs.get('property')=='article:published_time']
  hoy=datetime.now(o.ZONA).date()
  for fe in fechas:
   try:
    if hoy-timedelta(days=7)<=datetime.fromisoformat(fe[:10]).date()<=hoy:r['publicacion_ultimos_7_dias']=True
   except (ValueError,TypeError):pass
  rs=extractores.extraer(html,f,{'noticias_comunales':True,'admitir_avisos_sin_numero':True})[0]
  from tools.descubrir_fuentes import objeto_comprobado
  concretos=[x for x in rs if objeto_comprobado(x)]
  if concretos:r['historial_convocatorias']=True;r['procedimientos_muestra']+=concretos
  r['paginas'].append({'url':u,'url_final':f,'estado':'REVISADA','bytes':len(b),'sha256':h,'publicaciones_muestra':len(concretos)})
  for _,url in sorted(set(candidatos)):
   if url not in vistas and url not in cola:cola.append(url)
 r['identidad']=identidad;r['identidad_verificada']=identidad.get('verificada') if identidad else None;r['navegacion_adicional_pendiente']=cola
 r['estado']='CANDIDATA_CON_SENALES' if r['identidad_verificada'] and (r['seccion_compras'] or r['historial_convocatorias']) else 'PENDIENTE_IDENTIDAD_O_CONVOCATORIAS' if r['accesible'] else 'INACCESIBLE'
 r['segundos']=round(time.monotonic()-inicio,3);r['prioridad']=puntuar(r);return r

def ejecutar(candidatos,raiz,estado,concurrencia=4):
 raiz=Path(raiz);raiz.mkdir(parents=True,exist_ok=True);trans=TransporteLimitado();inicio=time.monotonic();prev=json.load(open(estado)) if Path(estado).exists() else {'schema_version':1,'localidades':{}};salidas=[]
 # Cada resultado terminado se guarda antes de esperar a los demás.
 with ThreadPoolExecutor(max_workers=concurrencia) as pool:
  futuros={pool.submit(explorar,c,raiz/'capturas',trans):c for c in candidatos}
  for f in as_completed(futuros):
   c=futuros[f]
   try:r=f.result()
   except Exception as e:r={**c,'estado':'ERROR_INDIVIDUAL','error':str(e),'paginas':[]}
   prev['localidades'][c['id']]=r;salidas.append(r);guardar(estado,prev);print('RAPIDA '+json.dumps({'localidad':c['localidad'],'estado':r['estado'],'paginas':len(r['paginas']),'segundos':r.get('segundos')},ensure_ascii=False),flush=True)
 resumen={'segundos':round(time.monotonic()-inicio,3),'programadas':len(candidatos),'con_sitio_consultado':sum(bool(r['paginas']) for r in salidas),'con_respuesta_html':sum(any(p['estado']=='REVISADA' for p in r['paginas']) for r in salidas),'con_identidad_automatica':sum(r.get('identidad_verificada') is True for r in salidas),'dominios_solicitudes':trans.contadores,'limite_por_dominio':1,'concurrencia_global':concurrencia,'documentos_descargados':0}
 guardar(raiz/'resultado.json',{'resumen':resumen,'localidades':salidas});return salidas,resumen

def guardar(p,v):
 p=Path(p);p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix(p.suffix+'.tmp');t.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n');t.replace(p)
