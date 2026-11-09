"""Contraste comercial de capturas; historial en copia, sin red ni análisis masivo de fichas."""
import json,sys,csv
from pathlib import Path
from hashlib import sha256
from collections import Counter
from datetime import datetime
from urllib.parse import parse_qs,urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc,extractores
from calidad_comercial import presentacion,escribir
from descubrimiento_territorial import ventanas
from tools.respaldo_piloto import restaurar
from tools.fase2_cerrar import huellas,metrica
from tools.radar_controlado import fuentes_configuradas
from tools.verificar_fuentes import guardar
ROOT=Path('work/fase4-cierre')

def recolectar(plan):
 fs={};obs={};por_fuente={};fechas=[]
 for p in sorted((ROOT/'capturas'/str(plan['base'])).glob('lote-*/resultado.json')):
  d=json.load(open(p));fechas.append(d['fecha'])
  for f in d['fuentes']:
   u=f['url'];fs[u]=f;obs[u]=next(s for s in d['observaciones'] if s['id']==f['id']);por_fuente[u]=[r for r in d['registros'] if r.get('fuente')==u]
 base={'fecha':max(fechas),'fuentes':list(fs.values()),'observaciones':list(obs.values()),'registros':o.deduplicar([r for rs in por_fuente.values() for r in rs],max(fechas))}
 permitidas={f['url']:f for f in fuentes_configuradas()};auditoria=[]
 for run in plan['descubrimiento']:
  root=ROOT/'capturas'/str(run)/'work/fase4/descubrimiento';p=root/'verificacion.json'
  if not p.exists():raise ValueError('Falta captura de descubrimiento '+str(run))
  d=json.load(open(p));fechas.append(d['actualizado'])
  for s in d['observaciones']:
   matches=list(root.rglob(Path(s.get('resultado_archivo','')).name));r=json.load(open(matches[0])) if matches else {};v=r.get('validacion',{});ident=r.get('identidad') or v.get('identidad') or {};u=s['url'];cfg=r.get('config')
   auditoria.append({**s,'run':run,'identidad':ident,'validacion':v})
   if not cfg or not ident.get('verificada') or u not in permitidas:continue
   f=permitidas[u];fs[u]=f;obs[u]={**s,'id':f['id'],'organismo':f.get('organismo'),'provincia':f.get('provincia'),'localidad':f.get('localidad')};rs=r.get('oportunidades',[])
   # Reusar las fichas ya descubiertas por navegación. No introducir IDs manuales.
   if cfg.get('adaptador')=='comuna-cms':
    rs=[]
    htmls=[]
    if matches:
     inicial=matches[0].with_suffix('.oficial.html')
     if inicial.exists():htmls.append((u,inicial,{}))
    for meta in root.rglob('capturas/'+s['id']+'/*.json'):
     m=json.load(open(meta));txt=meta.with_suffix('.txt')
     if txt.exists():htmls.append((m['url'],txt,m))
    for url,html,meta in htmls:
     if parse_qs(urlsplit(url).query).get('pagina')!=['detalle']:continue
     for x in extractores.extraer(html.read_text(),url,cfg)[0]:
      rs.append({**{k:cfg.get(k) for k in ('organismo','localidad','provincia')},**x,'fuente':u,'evidencia_captura':meta,'rango_evidencia':3})
   if cfg.get('adaptador')=='ceres':
    from fuentes_fase4 import refinar_ceres
    rs=[refinar_ceres(x) for x in rs]
   por_fuente[u]=[o.normalizar({**x,**{k:(x.get(k) or cfg.get(k)) for k in ('organismo','localidad','provincia')},'fuente':u},d['actualizado']) for x in rs]
 fecha=max(fechas);despues={'fecha':fecha,'fuentes':list(fs.values()),'observaciones':list(obs.values()),'registros':o.deduplicar([r for rs in por_fuente.values() for r in rs],fecha)}
 return base,despues,auditoria

def comparar(db,registros,observaciones,fecha):
 previas={x[0]:json.loads(x[1]) for x in db.execute('SELECT id,dato FROM procedimientos')};antes_ids=set(previas)
 informe={'ejecucion_id':'fase4-'+str(__import__('os').environ.get('GITHUB_RUN_ID','local')),'actualizado':fecha,'estado_ejecucion':'COMPLETADA','observaciones':observaciones,'resumen':{'configuradas':len(observaciones),'consultadas':len(observaciones),'finalizadas':len(observaciones)}}
 print('FASE4 Registrar primera pasada sobre copia del historial',flush=True)
 primera=inc.registrar(db,registros,informe);eventos=inc.eventos(db,primera['corrida'],fecha);actuales=inc.actuales(db,fecha,primera['corrida']);activas=[r for r in actuales if presentacion(r,fecha)['presentacion_verificada']]
 nuevo_ids={e['id'] for e in eventos if e['id'] not in antes_ids and not e.get('observacion_previa_documentada')};A=[];B=[];C=[]
 for r in activas:
  if r['id'] in nuevo_ids:
   r={**r,'ventanas_publicacion':ventanas(r.get('fecha_publicacion'),fecha)}
   (A if r['ventanas_publicacion']['72h'] else B).append(r)
  elif r['id'] in previas and not presentacion({**previas[r['id']],'observada_esta_corrida':True},fecha)['presentacion_verificada']:C.append(r)
 print('FASE4 Registrar segunda pasada idéntica',flush=True)
 segunda=inc.registrar(db,registros,{**informe,'ejecucion_id':informe['ejecucion_id']+'-repeticion'})
 return primera,segunda,actuales,{'A_PUBLICACIONES_RECIENTES_NUEVAS_VIGENTES':A,'B_VIGENTES_PRIMERA_DETECCION':B,'C_CONOCIDAS_RECUPERADAS':C}

def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 plan=json.load(open('tools/plan_fase4_cierre.json'));protegidos=huellas();base,d,fuentes=recolectar(plan)
 guardar(ROOT/'antes.json',base);guardar(ROOT/'observadas.json',d);guardar(ROOT/'auditoria_descubrimiento.json',fuentes)
 copia=ROOT/'historial-aislado';restaurar('piloto_respaldo/diario',copia);db=inc.abrir(copia/'estado.sqlite3')
 primera,segunda,actuales,categorias=comparar(db,d['registros'],d['observaciones'],d['fecha']);total=db.execute('select count(*) from procedimientos').fetchone()[0];db.close()
 print('FASE4 Generar informe comercial y controles',flush=True)
 resumen_comercial=escribir(actuales,d['fecha'],ROOT/'comercial',fuentes=d['observaciones'])
 for nombre,rs in categorias.items():guardar(ROOT/(nombre+'.json'),{'fecha':d['fecha'],'total':len(rs),'oportunidades':sorted(rs,key=o.prioridad)})
 # Nuevas verificadas: sólo el conjunto A+B, sin modificaciones ni recuperaciones C.
 nuevas=categorias['A_PUBLICACIONES_RECIENTES_NUEVAS_VIGENTES']+categorias['B_VIGENTES_PRIMERA_DETECCION']
 escribir(nuevas,d['fecha'],ROOT/'nuevas',fuentes=d['observaciones'])
 # Exportación completa con primera detección y última observación, sin top-N.
 for carpeta in ('comercial','nuevas'):
  p=ROOT/carpeta/'informe_comercial.csv';filas=list(csv.DictReader(p.open()));js=json.load(open(p.with_suffix('.json')))
  byurl={r['url']:r for r in js['oportunidades']};campos=list(filas[0]) if filas else next(csv.reader(p.open()))
  campos+=['primera_deteccion','ultima_observacion']
  with p.open('w',newline='') as out:
   w=csv.DictWriter(out,fieldnames=campos);w.writeheader()
   for fila in filas:
    r=byurl.get(fila['url'],{});w.writerow({**fila,'primera_deteccion':r.get('primera_deteccion'),'ultima_observacion':r.get('ultima_deteccion')})
 controles=json.load(open('tools/fase4_control_manual.json'));capturadas={r['url'] for r in d['registros']};previas_urls={r['url'] for r in base['registros']}
 controles['resultados']=[{**c,'detectada_antes':c['url'] in previas_urls,'detectada_despues':c['url'] in capturadas} for c in controles['casos']]
 guardar(ROOT/'control_omisiones.json',controles)
 control=json.load(open('inventario/control_rosario_fase2.json'))['publicaciones'];urls={r['url'] for r in d['registros']};manual={'muestra':len(control),'detectadas':sum(c['url'] in urls for c in control),'omisiones':[c for c in control if c['url'] not in urls],'alcance':'Muestra fija 7/11, no porcentaje territorial global'};guardar(ROOT/'control_rosario.json',manual)
 from fuentes_fase4 import naturaleza_convocatoria
 resultado={'nuevas_compras_vigentes':sum(naturaleza_convocatoria(r)=='COMPRA_O_SERVICIO' for r in nuevas),'otras_convocatorias_vigentes_venta':sum(naturaleza_convocatoria(r)=='VENTA_BIENES_PUBLICOS' for r in nuevas),'fecha':d['fecha'],'plan':plan,'base_medida':metrica(base),'despues_medido':metrica(d),'catalogo_vigentes_observadas':resumen_comercial['vigentes_presentacion_verificada'],'categorias':{k:len(v) for k,v in categorias.items()},'nuevas_vigentes_no_catalogadas_antes':len(nuevas),'ventanas':{str(n)+'h':sum(ventanas(r.get('fecha_publicacion'),d['fecha'])[str(n)+'h'] for r in nuevas) for n in (24,48,72)},'primera':primera,'segunda':segunda,'historial_total':total,'protegidos_intactos':protegidos==huellas(),'control_rosario':manual,'ocr_nuevo':0}
 guardar(ROOT/'resultado.json',resultado)
 if not resultado['protegidos_intactos'] or segunda['novedades'] or segunda.get('eventos_emitidos'):raise ValueError('Falló integridad o repetición')
 print(json.dumps({k:v for k,v in resultado.items() if k not in ('primera','segunda','control_rosario')},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
