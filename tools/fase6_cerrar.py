"""Cierre reproducible del lote territorial sobre copias; no altera producción."""
import sys,json,csv,os
from pathlib import Path
from hashlib import sha256
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc,conectores,extractores
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.respaldo_piloto import restaurar
from tools.fase2_cerrar import huellas
from calidad_comercial import escribir,presentacion
ROOT=Path('work/fase6-cierre')

def inspeccionar():
 # URLs publicadas y comprobadas previamente en navegación independiente.
 urls=['https://totoras.gob.ar/','https://totoras.gob.ar/municipio/','https://totoras.gob.ar/autoridades/','https://www.comunasangregorio.gob.ar/pages/actos.php','https://www.comunasangregorio.gob.ar/pages/tesoreria.php']
 out=[]
 for i,u in enumerate(urls):
  try:
   b,t,f=conectores.descargar(u,conexion_timeout=4,lectura_timeout=8);p=ROOT/'rutas'/str(i);p.parent.mkdir(parents=True,exist_ok=True);p.with_suffix('.html').write_bytes(b)
   registros=extractores.extraer(b.decode('utf-8',errors='replace'),f,{'noticias_comunales':True,'admitir_avisos_sin_numero':True})[0]
   out.append({'url':u,'url_final':f,'estado':'REVISADA','bytes':len(b),'tipo':t,'sha256':sha256(b).hexdigest(),'convocatorias_extraidas':len(registros),'cobertura_compras':'PENDIENTE: no se acredita ausencia de convocatorias por estas páginas'})
  except Exception as e:out.append({'url':u,'estado':'ERROR_ACCESO','error':type(e).__name__+': '+str(e)[:250]})
 guardar(ROOT/'rutas.json',out)
 return out

def main():
 ROOT.mkdir(parents=True,exist_ok=True);protegidos=huellas();plan=json.load(open('tools/plan_fase6_cierre.json'));fuentes=[{**f,'solo_descubrimiento':True,'ocr':False,'capturar_respuestas':True} for f in fuentes_configuradas() if f['id'] in plan['fuentes']]
 assert {f['id'] for f in fuentes}==set(plan['fuentes'])
 informe=ejecutar(fuentes,ROOT/'auditoria.json',concurrencia=3,por_fuente=plan['por_fuente_segundos'],total=plan['total_segundos']);fecha=informe['actualizado'];actuales=registros_checkpoint(informe);rutas=inspeccionar();previos=[];resultados=[]
 for run in plan['runs']:
  p=ROOT/'capturas'/str(run)/'work/fase6/lote-01';d=json.load(open(p/'registros.json'));previos+=d['oportunidades'];resultados+=json.load(open(p/'resultados.json'))['localidades']
 rs=o.deduplicar([o.normalizar(r,fecha) for r in previos]+actuales,fecha)
 # Conservar toda la evidencia de las dos exploraciones, incluso las parciales.
 guardar(ROOT/'observadas.json',{'fecha':fecha,'registros':rs,'fuentes':fuentes,'observaciones':informe['observaciones']})
 copia=ROOT/'historial-aislado';restaurar('piloto_respaldo/diario',copia);db=inc.abrir(copia/'estado.sqlite3');antes=db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0]
 base={'ejecucion_id':'fase6-'+plan['revision'],'actualizado':fecha,'estado_ejecucion':'COMPLETADA','observaciones':informe['observaciones'],'resumen':{'configuradas':len(fuentes),'consultadas':len(fuentes),'finalizadas':len(fuentes)}}
 uno=inc.registrar(db,rs,base);dos=inc.registrar(db,rs,{**base,'ejecucion_id':base['ejecucion_id']+'-repeticion'});db.close()
 comercio=escribir(rs,fecha,ROOT/'comercial',fuentes=informe['observaciones'])
 control=json.load(open('inventario/control_rosario_fase2.json'))['publicaciones'];urls={r['url'] for r in actuales};rosario={'muestra':len(control),'detectadas':sum(c['url'] in urls for c in control),'omisiones':[c for c in control if c['url'] not in urls]};guardar(ROOT/'control_rosario.json',rosario)
 # Una muestra del lote es independiente del catálogo completo: no sumar sus
 # parciales a los 101 estados previos como si se hubieran vuelto a consultar.
 guardados=json.load(open('inventario/fase6_avance.json'));lote=guardados['lotes']['01'];filas=[]
 for c in json.load(open('inventario/fase6_lotes.json'))['lotes'][0]['localidades']:
  intentos=[r for r in resultados if r['id']==c['id']];last=intentos[-1];obs=last['resultado'];revisada=any(r['revision_efectiva'] for r in intentos)
  if c['localidad']=='San Gregorio':revisada=all(any(u['url'].endswith('/pages/'+s+'.php') and u['estado']=='REVISADA' for u in rutas) for s in ['actos','tesoreria']) or revisada
  if c['localidad']=='Totoras':revisada=sum(u['estado']=='REVISADA' for u in rutas if 'totoras.gob.ar' in u['url'])>=2
  incorporada=next((f for f in fuentes if f['id']=='auto-'+c['id']),None);aud=next((s for s in informe['observaciones'] if incorporada and s['id']==incorporada['id']),None)
  filas.append({'provincia':c['provincia'],'departamento_propuesto':c.get('departamento'),'localidad':c['localidad'],'organismo':c['organismo'],'url_oficial':('https://totoras.gob.ar/' if c['localidad']=='Totoras' else c['url']),'revision_mas_alla_de_portada':revisada,'cobertura_exhaustiva_comprobada':False,'identidad_verificada':last['identidad'].get('verificada',False),'incorporada':bool(incorporada),'estado_extraccion':aud['estado'] if aud else obs['estado'],'publicaciones_extraidas':aud.get('publicaciones_detectadas',0) if aud else obs.get('publicaciones_detectadas',0),'convocatorias_vigentes_verificadas':0,'ultima_revision':fecha,'evidencia':','.join(str(run) for run in plan['runs'] if any(r['id']==c['id'] for r in json.load(open(ROOT/'capturas'/str(run)/'work/fase6/lote-01/resultados.json'))['localidades']))})
 with (ROOT/'lote01.csv').open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=list(filas[0]));w.writeheader();w.writerows(filas)
 campos=['organismo','localidad','provincia','numero_procedimiento','objeto','fecha_publicacion','fecha_apertura','fecha_limite_presentacion','condiciones_pago','url','estado_comercial']
 with (ROOT/'pendientes.csv').open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=campos);w.writeheader()
  for r in rs:
   p=presentacion(r,fecha)
   if p['estado_comercial'].startswith('PENDIENTE'):w.writerow({**{k:r.get(k) or 'Pendiente de verificar' for k in campos},'estado_comercial':p['estado_comercial']})
 nuevas=[r for r in rs if r.get('fuente')!='https://www.rosario.gob.ar/inicio/compras-y-licitaciones' and presentacion(r,fecha)['presentacion_verificada']]
 resumen={'fecha':fecha,'github_run_id':os.environ.get('GITHUB_RUN_ID'),'fuentes_configuradas_antes':101,'fuentes_configuradas_despues':len(fuentes_configuradas()),'fuentes_del_catalogo_consultadas_en_cierre':len(fuentes),'estados_consulta_catalogo':{f['id']:f['estado'] for f in informe['observaciones']},'publicaciones_consulta_catalogo':{f['id']:f.get('publicaciones_detectadas',0) for f in informe['observaciones']},'localidades_intentadas':20,'localidades_con_revision_mas_alla_portada':sum(f['revision_mas_alla_de_portada'] for f in filas),'auditoria_exhaustiva_del_lote_completada':False,'registros_brutos_territoriales':len(previos),'registros_unicos_territoriales':len(o.deduplicar([o.normalizar(r,fecha) for r in previos],fecha)),'comercial_muestra_incluye_rosario':comercio,'compras_vigentes_ineditas_del_lote':len(nuevas),'publicaciones_nuevas_confirmadas_del_lote':0,'fuentes_nuevas_incorporadas':sum(f['incorporada'] for f in filas),'primera':uno,'segunda':dos,'historial_copia_inicial':antes,'rosario':rosario,'protegidos_intactos':protegidos==huellas(),'ocr_nuevo':0,'segundos_barrido_final':informe['duracion_segundos'],'advertencia':'El número de registros territoriales incluye históricos, anexos, adjudicaciones y avisos sin vigencia comprobada. No equivale a oportunidades comerciales; el lote mantiene limitaciones y no acredita cobertura exhaustiva.'}
 guardar(ROOT/'resultado.json',resumen);print(json.dumps(resumen,ensure_ascii=False),flush=True)
 if dos['novedades'] or dos['eventos_emitidos'] or not resumen['protegidos_intactos'] or rosario['detectadas']!=53:raise ValueError('Falló repetición, integridad o control Rosario')
if __name__=='__main__':main()
