"""Orden de Fase 7: siete reparaciones, nivel rápido, selección y validación profunda."""
import json,sys,os,time
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.fase2_cerrar import huellas
from tools.descubrir_fuentes import aceptacion
from descubrimiento_rapido import ejecutar as rapido,explorar,TransporteLimitado,elegir_seccion
from calidad_comercial import escribir,presentacion
ROOT=Path('work/fase7/territorial')

def validar(cs,nombre,segundos=35,total=240):
 root=ROOT/nombre;root.mkdir(parents=True,exist_ok=True);entrada=root/'entradas';entrada.mkdir(exist_ok=True)
 for c in cs:guardar(entrada/(c['id']+'.json'),c)
 inf=ejecutar(cs,root/'auditoria.json',concurrencia=3,por_fuente=segundos,total=total,comando=lambda c,s:[sys.executable,'tools/descubrir_fuentes.py','--worker',str(entrada/(c['id']+'.json')),'--salida',str(s)])
 ds=[]
 for obs in inf['observaciones']:
  p=Path(obs.get('resultado_archivo',''));r=json.load(open(p)) if p.is_file() else {};ds.append({'candidato':next(c for c in cs if c['id']==obs['id']),'auditoria':obs,'resultado':r})
 guardar(root/'resultado.json',{'fecha':inf['actualizado'],'fuentes':ds});return ds,inf

def main():
 ROOT.mkdir(parents=True,exist_ok=True);antes=huellas();ini=time.monotonic();prev={f['url'] for f in fuentes_configuradas()};viejas=json.load(open('inventario/fase6_lotes.json'))['lotes'][0]['localidades'];nombres=['Hughes','San Guillermo','Totoras','Franck','Malabrigo','Valle María','San José de la Esquina'];cs=[c for c in viejas if c['localidad'] in nombres]
 recuperadas,ir=validar(cs,'recuperacion',segundos=35,total=130)
 # Mismo delegado publicado por la Comuna: extracción de datos ya incluidos en HTML.
 hughes=next(c for c in cs if c['localidad']=='Hughes');u='https://sigloservicios.com/PublicDoc/PublicDoc.aspx?3,7='
 from fuentes_fase7 import siglo
 import conectores
 try:
  b,t,f=conectores.descargar(u,conexion_timeout=3,lectura_timeout=5);rs,n=siglo(conectores.decodificar_html(b,t),f);guardar(ROOT/'hughes-delegado.json',{'url':u,'filas':n,'registros':rs,'estado':'PARCIAL_PAGINACION_PENDIENTE','delegacion':'https://hughes.gob.ar/transparencia/compras-y-contrataciones/concurso-de-precios','vigencia':'No comprobada por fecha de publicación; no comercializar sin recepción verificada'})
 except Exception as e:guardar(ROOT/'hughes-delegado.json',{'url':u,'estado':'ERROR_ACCESO','error':str(e)[:250]})
 candidatas=json.load(open('inventario/fase7_semillas.json'))['candidatos'];ya={(o.norm(f['localidad']),f['provincia']) for f in fuentes_configuradas()};candidatas=[c for c in candidatas if (o.norm(c['localidad']),c['provincia']) not in ya]
 todos,res=rapido(candidatas,ROOT/'rapida',ROOT/'estado_rapido.json',concurrencia=4)
 validables=[r for r in todos if r.get('identidad_verificada') and r.get('estado')=='CANDIDATA_CON_SENALES' and r['url'] not in prev]
 validables.sort(key=lambda r:(-r['prioridad']['puntos'],r.get('fecha',''),r.get('distancia_geodesica_rosario_km') or 99999,r['id']))
 seleccion=[]
 for r in validables[:10]:
  # Sección oficial publicada antes de archivo completo; identidad en raíz.
  secciones=[x['url'] for x in r['enlaces_candidatos'] if any(t in o.norm(x['texto']) for t in ['licitacion','concurso de precios','compras']) and not __import__('extractores').procesos(x['texto']) and not __import__('urllib.parse',fromlist=['urlparse']).urlparse(x['url']).path.lower().endswith(__import__('extractores').ADJUNTOS) and x['url'].startswith(r['url'].split('/',3)[0]+'//'+r['url'].split('/')[2])]
  seleccion.append({**{k:r[k] for k in ['id','organismo','localidad','provincia','tipo']},'url':elegir_seccion(r),'identidad_url':r['url'],'config_publica':{'documentos_para_descubrimiento':True,'noticias_comunales':True},'prioridad_rapida':r['prioridad']})
 profundas,ip=validar(seleccion,'profunda',segundos=40,total=180) if seleccion else ([],{'actualizado':o.datetime.now(o.ZONA).isoformat(),'observaciones':[],'duracion_segundos':0})
 auto=json.load(open('inventario/fuentes_auto.json'));incorporadas=[]
 for d in profundas:
  c=d['candidato'];obs=d['auditoria'];r=d['resultado'];v=r.get('validacion',{})
  if obs['estado']=='OPERATIVA' and v.get('estado')=='VALIDADA' and c['url'] not in prev:
   item={'id':'auto-'+c['id'],'url':c['url'],'config':r['config'],'validacion':v,'origen_busqueda':c.get('identidad_url')};auto['fuentes'].append(item);prev.add(c['url']);incorporadas.append(item)
 guardar(ROOT/'altas.json',{'fuentes':incorporadas});guardar('inventario/fuentes_auto.json',auto)
 # Deben ejecutarse desde el catálogo real, no sólo desde la propuesta.
 fs=[{**f,'solo_descubrimiento':True,'ocr':False,'tiempo_maximo_fuente_segundos':40} for f in fuentes_configuradas() if f['id'] in {x['id'] for x in incorporadas}]
 ic=ejecutar(fs,ROOT/'consulta_catalogo.json',concurrencia=3,por_fuente=40,total=130) if fs else {'actualizado':ip['actualizado'],'observaciones':[],'duracion_segundos':0}
 fecha=ic['actualizado'];rs=[]
 for d in recuperadas+profundas:
  c=d['candidato'];rs += [o.normalizar({**r,'fuente':c['url']},fecha) for r in d['resultado'].get('oportunidades',[])]
 rs+=registros_checkpoint(ic);rs=o.deduplicar(rs,fecha);guardar(ROOT/'observadas.json',{'fecha':fecha,'registros':rs})
 comercio=escribir(rs,fecha,ROOT/'comercial',fuentes=ir['observaciones']+ip['observaciones']+ic['observaciones'])
 # Una copia de laboratorio nueva comprueba idempotencia, sin modificar historial.
 db=inc.abrir(ROOT/'idempotencia.sqlite3');base={'ejecucion_id':'fase7-'+str(os.environ.get('GITHUB_RUN_ID')),'actualizado':fecha,'estado_ejecucion':'COMPLETADA','observaciones':ir['observaciones']+ip['observaciones']+ic['observaciones'],'resumen':{'configuradas':len(cs)+len(seleccion)+len(fs),'consultadas':len(cs)+len(seleccion)+len(fs),'finalizadas':len(cs)+len(seleccion)+len(fs)}}
 uno=inc.registrar(db,rs,base);dos=inc.registrar(db,rs,{**base,'ejecucion_id':base['ejecucion_id']+'-repeticion'});db.close()
 # Medición secuencial y concurrente sobre las mismas cuatro localidades, sin cache compartida.
 muestra=[c for c in candidatas if c.get('url')][:4];t=time.monotonic();tr=TransporteLimitado();s=[explorar(c,ROOT/'benchmark/secuencial',tr) for c in muestra];sec=time.monotonic()-t
 p,pr=rapido(muestra,ROOT/'benchmark/concurrente',ROOT/'benchmark/estado.json',concurrencia=4)
 comparacion={'localidades':len(muestra),'secuencial_segundos':round(sec,3),'concurrente_segundos':pr['segundos'],'comparables':{r['id']:{'secuencial_estado':r['estado'],'concurrente_estado':next(x['estado'] for x in p if x['id']==r['id']),'mismos_enlaces':{x['url'] for x in r['enlaces_candidatos']}=={x['url'] for x in next(x for x in p if x['id']==r['id'])['enlaces_candidatos']}} for r in s},'alcance':'Nivel rápido sobre cuatro sitios; no prueba ausencia de omisiones en toda la provincia'}
 guardar(ROOT/'rendimiento.json',comparacion)
 estado={'schema_version':1,'fecha':fecha,'localidades':{r['id']:{k:v for k,v in r.items() if k not in ['procedimientos_muestra']} for r in todos},'lote_pendiente':[r['id'] for r in todos if not r.get('paginas') or r.get('estado') in ['INACCESIBLE','ERROR_INDIVIDUAL']]};guardar('inventario/fase7_estado.json',estado)
 resumen={'fecha':fecha,'run':os.environ.get('GITHUB_RUN_ID'),'segundos_totales':round(time.monotonic()-ini,3),'recuperacion_segundos':ir['duracion_segundos'],'rapida':res,'profunda_consultadas':len(seleccion),'profunda_segundos':ip['duracion_segundos'],'fuentes_nuevas_incorporadas':len(incorporadas),'consulta_catalogo':ic['observaciones'],'comercial_muestra':comercio,'segunda_pasada_novedades':dos['novedades'],'segunda_pasada_eventos':dos['eventos_emitidos'],'protegidos_intactos':antes==huellas(),'ocr_nuevo':0,'benchmark':comparacion,'advertencia':'Los avisos vigentes deben contrastarse contra historial accesible antes de contarlos como inéditos. No se contarán los resultados de línea de base del laboratorio como publicaciones nuevas.'}
 guardar(ROOT/'resultado.json',resumen);print('FASE7_TERRITORIAL '+json.dumps(resumen,ensure_ascii=False),flush=True)
 if dos['novedades'] or dos['eventos_emitidos'] or not resumen['protegidos_intactos']:raise ValueError('Falló integridad o idempotencia')
if __name__=='__main__':main()
