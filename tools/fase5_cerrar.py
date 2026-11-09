"""Contraste de capturas nativas, referencia Fase 4 y segunda pasada sobre copia."""
import json,sys,csv,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc
from tools.verificar_fuentes import guardar
from tools.respaldo_piloto import restaurar
from tools.radar_controlado import fuentes_configuradas
from tools.fase2_cerrar import huellas,metrica
from calidad_comercial import escribir,presentacion
from informe_descubrimiento import clasificar,escribir as diario
from cobertura_territorial import generar
ROOT=Path('work/fase5-cierre')

def main():
 plan=json.load(open(os.environ.get('FASE5_CIERRE_PLAN','tools/plan_fase5_cierre.json')));ROOT.mkdir(parents=True,exist_ok=True);protegidos=huellas();base=json.load(open(ROOT/'referencia/observadas.json'));fs={};obs={};rs=[];fechas=[]
 for p in sorted((ROOT/'barrido').glob('lote-*/resultado.json')):
  d=json.load(open(p));fechas.append(d['fecha']);fs.update({f['url']:f for f in d['fuentes']});obs.update({f['url']:f for f in d['observaciones']});rs+=d['registros']
 if len(fs)<101:raise ValueError('Barrido incompleto: faltan fuentes configuradas; no declarar cero novedades')
 candidatas=[];permitidas={f['url']:f for f in fuentes_configuradas()}
 for run in plan['descubrimientos']:
  r=ROOT/'descubrimiento'/str(run)/'work/fase5/descubrimiento';d=json.load(open(r/'verificacion.json'));fechas.append(d['actualizado'])
  for s in d['observaciones']:
   nombre=Path(s.get('resultado_archivo','')).name;matches=[p for p in r.rglob(nombre) if p.is_file()] if nombre else [];cp=json.load(open(matches[0])) if matches else {};ident=cp.get('identidad') or cp.get('validacion',{}).get('identidad',{});cfg=cp.get('config');candidatas.append({**s,'identidad_verificada':ident.get('verificada',False),'validacion':cp.get('validacion',{}),'config':cfg})
   if not ident.get('verificada') or not cfg or s['url']=='https://acebal.gob.ar/acebal/':continue
   u=s['url'];f=permitidas.get(u) or {**cfg,'url':u,'id':s['id'],'incorporada':False,'estado_verificacion':'PARCIAL_NO_INCORPORADA'}
   fs[u]=f;obs[u]={**s,**{k:f.get(k) for k in ('organismo','provincia','localidad')}}
   rs=[x for x in rs if x.get('fuente')!=u]+[o.normalizar({**raw,**{k:raw.get(k) or cfg.get(k) for k in ('organismo','provincia','localidad')},'fuente':u},d['actualizado']) for raw in cp.get('oportunidades',[])]
 recuperacion=ROOT/'recuperacion/resultado.json'
 if recuperacion.exists():
  d=json.load(open(recuperacion));fechas.append(d['fecha'])
  for f in d['fuentes']:
   s=next(s for s in d['observaciones'] if s['id']==f['id']);fs[f['url']]=f;obs[f['url']]=s
   rs=[x for x in rs if x.get('fuente')!=f['url']]+[x for x in d['registros'] if x.get('fuente')==f['url']]
 critica=ROOT/'criticas/resultado.json'
 if critica.exists():
  d=json.load(open(critica));fechas.append(d['fecha'])
  for f in d['fuentes']:
   s=next(s for s in d['observaciones'] if s['id']==f['id']);extra=[r for r in d['registros'] if r.get('fuente')==f['url']]
   if extra:
    fs[f['url']]=f;obs[f['url']]={**s,'metodo':'macOS curl nativo TLS verificado'};rs+=extra
 fecha=max(fechas);rs=o.deduplicar(rs,fecha);fuentes=list(fs.values());observaciones=list(obs.values());snapshot={'fecha':fecha,'fuentes':fuentes,'observaciones':observaciones,'registros':rs};guardar(ROOT/'observadas.json',snapshot)
 copia=ROOT/'historial-aislado';restaurar('piloto_respaldo/diario',copia);db=inc.abrir(copia/'estado.sqlite3')
 # Reconstruir sólo el catálogo ya observado en Fase 4. No volver a informar sus dos hallazgos.
 informe={'ejecucion_id':'referencia-fase4-'+plan['revision'],'actualizado':base['fecha'],'estado_ejecucion':'COMPLETADA','observaciones':base['observaciones'],'resumen':{'configuradas':len(base['fuentes']),'consultadas':len(base['fuentes']),'finalizadas':len(base['fuentes'])}}
 print('FASE5 Reconstruir referencia Fase 4 sin red ni OCR',flush=True);inc.registrar(db,base['registros'],informe)
 previas={x[0]:json.loads(x[1]) for x in db.execute('SELECT id,dato FROM procedimientos')};actuales_antes=inc.actuales(db,base['fecha'],informe['ejecucion_id']);antes_comercial=sum(presentacion(r,base['fecha'])['presentacion_verificada'] for r in actuales_antes)
 informe={**informe,'ejecucion_id':'fase5-'+plan['revision'],'actualizado':fecha,'observaciones':observaciones,'resumen':{'configuradas':len(fuentes),'consultadas':len(fuentes),'finalizadas':len(fuentes)}}
 print('FASE5 Registrar primera pasada',flush=True);primera=inc.registrar(db,rs,informe);actuales=inc.actuales(db,fecha,primera['corrida']);eventos=inc.eventos(db,primera['corrida'],fecha);grupos=clasificar(actuales,eventos,fecha,previas,inc.cargar_indice_auditorias());resumen_diario=diario(grupos,fecha,ROOT/'descubrimiento_diario');comercial=escribir(actuales,fecha,ROOT/'comercial',fuentes=observaciones)
 print('FASE5 Comprobar segunda pasada idéntica',flush=True);segunda=inc.registrar(db,rs,{**informe,'ejecucion_id':informe['ejecucion_id']+'-repeticion'});db.close()
 cobertura=generar(fuentes,observaciones,rs,fecha,ROOT)
 control=json.load(open('inventario/control_rosario_fase2.json'))['publicaciones'];urls={r['url'] for r in rs};rosario={'muestra':len(control),'detectadas':sum(c['url'] in urls for c in control),'omisiones':[c for c in control if c['url'] not in urls]}
 guardar(ROOT/'candidatas_revisadas.json',candidatas);guardar(ROOT/'control_rosario.json',rosario)
 nuevos=grupos['A_PUBLICACIONES_NUEVAS_VIGENTES']+grupos['B_VIGENTES_DESCONOCIDAS'];guardar(ROOT/'nuevas_verificadas.json',{'fecha':fecha,'oportunidades':[{k:r.get(k) for k in ('id','organismo','provincia','localidad','numero_procedimiento','objeto','fecha_publicacion','primera_deteccion','fecha_hora_limite_presentacion','fecha_limite_presentacion','condiciones_pago','modalidad_presentacion','url','enlace_pliego')} for r in nuevos]})
 for nombre,datos in [('fuentes_consultadas',observaciones),('candidatas_consultadas',candidatas)]:
  with (ROOT/(nombre+'.csv')).open('w',newline='') as out:
   campos=['id','organismo','provincia','localidad','url','estado','iniciada','publicaciones_detectadas','duracion_segundos','errores'];w=csv.DictWriter(out,fieldnames=campos);w.writeheader();w.writerows({k:json.dumps(r.get(k),ensure_ascii=False) if isinstance(r.get(k),(dict,list)) else r.get(k) for k in campos} for r in datos)
 urls_configuradas={f['url'] for f in fuentes if f.get('incorporada')}
 medido_configuradas={**snapshot,'fuentes':[f for f in fuentes if f.get('incorporada')],'observaciones':[s for s in observaciones if s['url'] in urls_configuradas],'registros':[r for r in rs if r.get('fuente') in urls_configuradas]}
 resultado={'configuradas_efectivas':len(permitidas),'fuentes_y_candidatas_identificadas_revisadas':len(fuentes),'fecha':fecha,'plan':plan,'antes':metrica(base),'despues':metrica(medido_configuradas),'antes_catalogo_recepecion_verificada_incluye_ventas':antes_comercial,'despues_compras_vigentes':comercial['vigentes_presentacion_verificada'],'categorias':resumen_diario,'nuevas_compras_vigentes':len(nuevos),'candidatas_consultadas':len(candidatas),'fuentes_incorporadas_efectivas':sum(bool(f.get('incorporada')) for f in fuentes),'primera':primera,'segunda':segunda,'cobertura':cobertura,'rosario':rosario,'protegidos_intactos':protegidos==huellas(),'ocr_nuevo':0}
 guardar(ROOT/'resultado.json',resultado);print(json.dumps({k:v for k,v in resultado.items() if k not in ('primera','segunda')},ensure_ascii=False),flush=True)
 if segunda['novedades'] or segunda['eventos_emitidos'] or not resultado['protegidos_intactos']:raise ValueError('Falló repetición o integridad')
if __name__=='__main__':main()
