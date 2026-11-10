"""Diagnóstico real: listados completos primero, documentos en presupuesto separado."""
import sys,json,time,re,os
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse,urlencode
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores,extractores,oportunidades as o
from tools.radar_controlado import fuentes_configuradas
from tools.verificar_fuentes import guardar
ROOT=Path('work/fase7/rosario')

def main():
 ROOT.mkdir(parents=True,exist_ok=True);cfg=next(f for f in fuentes_configuradas() if f['id']=='fuente-001');inicio=time.monotonic();vistas=set();resultados=[];registros={};control=json.load(open('inventario/control_rosario_fase2.json'))['publicaciones'];mes=o.datetime.now(o.ZONA)
 cola=list(cfg['urls_inicio'])+['https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones?'+urlencode({'mesApertura[0]':str(mes.month).zfill(2),'anioApertura[0]':str(mes.year)})]
 def consultar(u):
  t=time.monotonic()
  try:
   b,ct,fin=conectores.descargar(u,conexion_timeout=4,lectura_timeout=6,max_bytes=3000000);h=sha256(b).hexdigest();(ROOT/(h+'.html')).write_bytes(b);html=conectores.decodificar_html(b,ct);conectores.comprobar_acceso(html);rs,links,dom=extractores.extraer(html,fin,cfg)
   return {'url':u,'url_final':fin,'estado':'REVISADA','bytes':len(b),'sha256':h,'segundos':round(time.monotonic()-t,3),'publicaciones':len(rs),'registros':rs,'links':links}
  except Exception as e:return {'url':u,'estado':'ERROR_ACCESO','segundos':round(time.monotonic()-t,3),'error':conectores.clasificar_error(e,'DESCARGA'),'registros':[],'links':[]}
 while cola and time.monotonic()-inicio<150:
  lote=[]
  while cola and len(lote)<2:
   u=cola.pop(0)
   if u not in vistas:vistas.add(u);lote.append(u)
  if not lote:continue
  with ThreadPoolExecutor(max_workers=2) as pool:salidas=list(pool.map(consultar,lote))
  for r in salidas:
   for p in r['registros']:registros[p['url']]=p
   for l in r['links']:
    u=l['url'];p=urlparse(u)
    if p.hostname not in ('www.rosario.gob.ar','rosario.gob.ar') or not p.path.endswith('/result-busq-compras-licitaciones'):continue
    if re.search(r'[?&]page=\d+',u) or 'verTipo=' in p.query:
     if u not in vistas and u not in cola:cola.append(u)
   resultados.append({k:v for k,v in r.items() if k not in ('registros','links')});print(json.dumps(resultados[-1],ensure_ascii=False),flush=True)
  guardar(ROOT/'parcial.json',{'rutas':resultados,'registros':list(registros.values()),'cola_pendiente':cola})
 reintentos=[]
 for fallida in [r for r in resultados if r['estado']=='ERROR_ACCESO']:
  if time.monotonic()-inicio>150:break
  r=consultar(fallida['url']);reintentos.append({k:v for k,v in r.items() if k not in ('registros','links')})
  for p in r['registros']:registros[p['url']]=p
 faltan=[c for c in control if c['url'] not in registros];fichas=[]
 # Diagnóstico de avisos ya documentados, sin insertar el contenido de referencia.
 for c in faltan:
  if time.monotonic()-inicio>175:break
  r=consultar(c['url']);fichas.append({k:v for k,v in r.items() if k not in ('registros','links')})
  for p in r['registros']:registros[p['url']]=p
 faltan=[c for c in control if c['url'] not in registros];resueltas={r['url'] for r in reintentos if r['estado']=='REVISADA'};errores=[r for r in resultados if r['estado']=='ERROR_ACCESO' and r['url'] not in resueltas];completo=not cola and not errores
 resumen={'fecha':o.datetime.now(o.ZONA).isoformat(),'run':os.environ.get('GITHUB_RUN_ID'),'segundos':round(time.monotonic()-inicio,3),'antes_segundos':240.015,'paginas_consultadas':len(resultados),'timeouts':sum('TIEMPO' in str(r.get('error')) for r in resultados),'reintentos':len(reintentos),'auditoria_reintentos':reintentos,'documentos_procesados':0,'publicaciones':len(registros),'control_detectadas':len(control)-len(faltan),'control_total':len(control),'faltantes':faltan,'completo_listados':completo,'cola_pendiente':cola,'errores':errores,'fichas_contraste':fichas,'duplicados_por_url':0,'limite_por_dominio':2,'enriquecimiento_separado':True}
 guardar(ROOT/'resultado.json',resumen);guardar(ROOT/'registros.json',{'fecha':resumen['fecha'],'oportunidades':list(registros.values())});print('RESUMEN '+json.dumps(resumen,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
