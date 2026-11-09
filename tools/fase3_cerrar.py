"""Cierre Fase 3: catálogo observado, 119 controles y dos pasadas de copia aislada."""
import sys,json,csv
from pathlib import Path
from collections import Counter
from datetime import datetime
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o,incremental as inc
from calidad_comercial import presentacion,escribir
from tools.radar_controlado import fuentes_configuradas
from tools.verificar_fuentes import guardar
from tools.fase2_cerrar import huellas,metrica
from tools.reprocesar_lote_capturado import cerrar_barrido

ROOT=Path('work/fase3-cierre')
def archivos(run,patron):return sorted((ROOT/'capturas'/str(run)).rglob(patron))
def main():
 plan=json.load(open('tools/plan_fase3_cierre.json'));h=huellas();observaciones=[];rs=[];fs=[];fechas=[]
 for p in archivos(plan['barrido'],'lote-*/resultado.json'):
  d=json.load(open(p));fs+=d['fuentes'];observaciones+=d['observaciones'];rs+=d['registros'];fechas.append(d['fecha'])
 if len({f['id'] for f in fs})!=93:raise ValueError('No se consultaron las 93 fuentes de partida')
 reval=Path('work/fase3/revalidacion/resultado.json');v=json.load(open(reval));fechas.append(v['fecha'])
 if len(v['casos'])!=119:raise ValueError('Faltan controles individuales')
 fecha=max(fechas);base={'fecha':fecha,'fuentes':fs,'observaciones':observaciones,'registros':o.deduplicar(rs,fecha)};guardar(ROOT/'antes.json',base)
 casos=[];actuales=[]
 for caso in v['casos']:
  r=caso['resultado'];estado='INCIERTA';evidencia=None
  if r:
   r=o.normalizar(r,fecha);r.update(presentacion(r,fecha));actuales.append(r)
   if r['presentacion_verificada']:estado='VIGENTE_CONFIRMADA'
   elif r['vigencia']=='VENCIDA':estado='VENCIDA_O_CERRADA_REVISADA'
   evidencia=r.get('evidencia_recepcion')
  casos.append({**caso,'resultado':r,'estado_revalidacion':estado,'evidencia_recepcion':evidencia})
 guardar(ROOT/'revalidacion_119.json',{'fecha':fecha,'casos':casos,'resumen':dict(Counter(c['estado_revalidacion'] for c in casos))})
 # Sólo se ingieren fuentes del catálogo, no todas las candidatas de diagnóstico.
 incorporadas={f['id']:f for f in fuentes_configuradas()};candidatas=None
 for run in [plan['candidatas']]+plan.get('extras',[]):
  paths=[p for p in archivos(run,'resultado.json') if p.parent.name=='candidatas']
  if not paths:continue
  candidatas=json.load(open(paths[0]))
  for old,new in (plan.get('altas',{}) if run==plan.get('altas_run') else {}).items():
   cf=next(f for f in candidatas['fuentes'] if f['id']==old)
   if new not in incorporadas or cf['url']!=incorporadas[new]['url']:raise ValueError('Alta no comprobada contra configuración')
   ob=next(s for s in candidatas['observaciones'] if s['id']==old)
   if not ob.get('publicaciones_detectadas'):raise ValueError('No se promueve fuente sin extracción real')
   fs.append(incorporadas[new]);observaciones.append({**ob,'id':new});actuales +=[r for r in candidatas['registros'] if r.get('fuente')==cf['url']]
  guardar(ROOT/('candidatas-'+str(run)+'.json'),candidatas)
 registros=o.deduplicar(rs+actuales,fecha);despues={'fecha':fecha,'fuentes':fs,'observaciones':observaciones,'registros':registros};guardar(ROOT/'despues.json',despues)
 guardar(ROOT/'captura-consolidada.json',despues)
 cerrar_barrido([str(ROOT/'captura-consolidada.json')],str(ROOT/'historial-aislado'))
 cierre=json.load(open(ROOT/'historial-aislado'/'resultado.json'));guardar(ROOT/'continuidad.json',cierre)
 carpeta=sorted((ROOT/'historial-aislado'/'piloto'/'ejecuciones').glob('*'))[0]
 eventos=json.load(open(carpeta/'eventos.json'))['oportunidades']
 nuevas=[r for r in eventos if r.get('clasificacion_novedad')=='NUEVO_CONFIRMADO' and presentacion(r,fecha)['presentacion_verificada']]
 guardar(ROOT/'nuevas-vigentes.json',{'fecha':fecha,'total':len(nuevas),'oportunidades':nuevas})
 # Recuperadas = antes no tenía recepción comprobada, ahora sí. No equivale a nuevas publicaciones.
 prev={o.identidad(r):r for r in base['registros']};recuperadas=[r for r in registros if presentacion(r,fecha)['presentacion_verificada'] and (o.identidad(r) not in prev or not presentacion(prev[o.identidad(r)],fecha)['presentacion_verificada'])]
 guardar(ROOT/'recuperadas-vigentes.json',{'fecha':fecha,'total':len(recuperadas),'oportunidades':recuperadas})
 escribir(registros,fecha,ROOT/'comercial',fuentes=observaciones)
 manual=json.load(open('inventario/control_rosario_fase2.json'))['publicaciones'];urls={r['url'] for r in registros};control=[{**c,'detectada':c['url'] in urls,'alcance':'Muestra oficial fija del 7/11; no prueba publicación nueva ni cobertura territorial global'} for c in manual]
 guardar(ROOT/'contraste_manual.json',{'fecha':fecha,'casos':control,'detectadas':sum(c['detectada'] for c in control),'muestra':len(control)})
 resumen={'fecha':fecha,'runs':plan,'antes':metrica(base),'despues':metrica(despues),'pendientes_119':dict(Counter(c['estado_revalidacion'] for c in casos)),'recuperadas_vigentes':len(recuperadas),'publicaciones_nuevas_vigentes':len(nuevas),'eventos_primera':cierre['primera']['clasificacion'],'segunda_novedades':cierre['segunda']['novedades'],'segunda_eventos':cierre['segunda']['eventos_emitidos'],'repeticion_correcta':cierre['repeticion_correcta'],'protegidos_intactos':h==huellas(),'ocr_nuevo':0}
 guardar(ROOT/'resultado.json',resumen);print(json.dumps(resumen,ensure_ascii=False),flush=True)
 if not resumen['repeticion_correcta'] or not resumen['protegidos_intactos']:raise ValueError('Falló integridad o deduplicación')
if __name__=='__main__':main()
