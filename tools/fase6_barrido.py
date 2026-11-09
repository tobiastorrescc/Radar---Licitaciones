"""Primero inventario y 20 exploraciones reales, usando lectores existentes."""
import json,sys,os
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.fase6_inventario import generar
from tools.verificar_fuentes import ejecutar,guardar
from tools.descubrir_fuentes import aceptacion,objeto_comprobado
from calidad_comercial import presentacion
from tools.radar_controlado import huellas_produccion

def main():
 plan=json.load(open(os.environ.get('FASE6_PLAN','tools/plan_fase6.json')));lote=next(l for l in json.load(open('inventario/fase6_lotes.json'))['lotes'] if l['id']==plan['lote']);todas=lote['localidades'];cs=[c for c in todas if not plan.get('ids') or c['id'] in plan['ids']];root=Path('work/fase6')/('lote-'+lote['id']);root.mkdir(parents=True,exist_ok=True);antes=huellas_produccion();generar(root/'inventario_antes.json')
 assert len(todas)==20 and len({(c['provincia'],c['localidad']) for c in todas})==20
 entradas=root/'entradas';entradas.mkdir(exist_ok=True)
 for c in cs:guardar(entradas/(c['id']+'.json'),c)
 inf=ejecutar(cs,root/'auditoria.json',concurrencia=plan['concurrencia'],por_fuente=plan['por_fuente_segundos'],total=plan['total_segundos'],comando=lambda f,s:[sys.executable,'tools/descubrir_fuentes.py','--worker',str(entradas/(f['id']+'.json')),'--salida',str(s)])
 resultados=[];altas=[];rs=[]
 for s in inf['observaciones']:
  c=next(c for c in cs if c['id']==s['id']);p=Path(s.get('resultado_archivo',''));r=json.load(open(p)) if p.is_file() else {};v=r.get('validacion') or aceptacion(r,r.get('identidad') or {});ident=r.get('identidad') or v.get('identidad') or {};items=r.get('oportunidades',[]);rs+=items
  caps=list(p.parent.glob('capturas/'+c['id']+'/*.json')) if p.is_file() else [];urls=list(dict.fromkeys(json.load(open(x))['url'] for x in caps));secciones=[u for u in urls if any(t in u.lower() for t in ('licit','compra','contrata','concurso','presupuesto','noticia','novedad','decreto','resolucion','ordenanza','boletin','transparen'))]
  efectiva=bool(s.get('iniciada') and s.get('paginas_correctas',0)>1 and secciones)
  resultados.append({**c,'resultado':s,'identidad':ident,'validacion':v,'urls_revisadas':urls,'secciones_revisadas':secciones,'revision_efectiva':efectiva,'oportunidades_recuperadas':len(items),'recepcion_vigente_comprobada':sum(presentacion(x,inf['actualizado'])['presentacion_verificada'] for x in items)})
  if v.get('estado')=='VALIDADA':altas.append({'id':'auto-'+c['id'],'url':c['url'],'config':r['config'],'validacion':v})
 auto_path=Path('inventario/fuentes_auto.json');auto=json.load(open(auto_path));auto['fuentes']=[f for f in auto['fuentes'] if not (f['id'].startswith('auto-fase6-') and f.get('validacion',{}).get('ejemplos') and not any(objeto_comprobado(x) for x in f['validacion']['ejemplos']))];existentes={f['url'] for f in auto['fuentes']};incorporadas=[f for f in altas if f['url'] not in existentes];auto['fuentes']+=incorporadas;guardar(auto_path,auto)
 resumen={'fecha':inf['actualizado'],'lote':lote['id'],'github_run_id':os.environ.get('GITHUB_RUN_ID'),'programadas':len(cs),'intentadas':sum(bool(s.get('iniciada')) for s in inf['observaciones']),'revision_efectiva':sum(r['revision_efectiva'] for r in resultados),'lote_completo':all(r['revision_efectiva'] for r in resultados),'altas_validadas':len(incorporadas),'estados':dict(Counter(s['estado'] for s in inf['observaciones'])),'duracion_segundos':inf['duracion_segundos'],'produccion_intacta':antes==huellas_produccion()}
 guardar(root/'resultados.json',{'resumen':resumen,'localidades':resultados});guardar(root/'registros.json',{'fecha':inf['actualizado'],'oportunidades':rs});guardar(root/'altas.json',{'fuentes':incorporadas});
 avance_path=Path('inventario/fase6_avance.json');avance=json.load(open(avance_path)) if avance_path.exists() else {'schema_version':1,'lotes':{}}
 anteriores={r['id']:r for r in avance['lotes'].get(lote['id'],{}).get('localidades',[])}
 for r in resultados:
  fila={k:r[k] for k in ('id','localidad','provincia','revision_efectiva','urls_revisadas','secciones_revisadas','identidad','oportunidades_recuperadas','recepcion_vigente_comprobada')}
  fila['ultima_revision']=inf['actualizado'];fila['revision_efectiva_previa']=anteriores.get(r['id'],{}).get('revision_efectiva',False);anteriores[r['id']]=fila
 resumen_lote={**resumen,'programadas':len(todas),'intentadas_ultima_ejecucion':len(cs),'revision_efectiva':sum(x['revision_efectiva'] or x.get('revision_efectiva_previa',False) for x in anteriores.values()),'localidades':list(anteriores.values())}
 resumen_lote['lote_completo']=len(anteriores)==len(todas) and resumen_lote['revision_efectiva']==len(todas)
 avance['lotes'][lote['id']]=resumen_lote;guardar(avance_path,avance)
 print(json.dumps(resumen,ensure_ascii=False),flush=True)
 if not resumen['produccion_intacta']:raise ValueError('Producción modificada')
if __name__=='__main__':main()
