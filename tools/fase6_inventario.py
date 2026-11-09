"""Inventario anterior al barrido: no modifica fuentes, lectores ni historial."""
import sys,csv,json
from pathlib import Path
from datetime import datetime
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import oportunidades as o
from tools.radar_controlado import fuentes_configuradas
from descubrimiento_territorial import alcance_ba

def generar(destino='inventario/fase6_cobertura.json'):
 padron=json.load(open('inventario/territorio.json'));fs=fuentes_configuradas();prev=list(csv.DictReader(open('informes/2026-11-09-fase5/cobertura_territorial.csv')));lotes=json.load(open('inventario/fase6_lotes.json'))['lotes'];plan={(c['provincia'],o.norm(c['localidad'])):c for l in lotes for c in l['localidades']};rows=[]
 for m in padron['municipios']:
  k=(m['provincia'],o.norm(m['localidad']));ss=[f for f in fs if f.get('provincia')==k[0] and o.norm(f.get('localidad'))==k[1]];urls={s['url'] for s in ss};revisadas=[r for r in prev if r['provincia']==k[0] and o.norm(r['localidad'])==k[1] and r['fuente_contrataciones'] in urls and r['fuente_incorporada']=='True'];op=[r for r in revisadas if r['fuente_revisada']=='True' and r['estado_extraccion'] in ('OPERATIVA','SIN_PUBLICACIONES')];par=[r for r in revisadas if r['estado_extraccion'] in ('PARCIAL','TIEMPO_FUENTE')];bloq=[r for r in revisadas if r['estado_extraccion'] in ('BLOQUEADA','ERROR_ACCESO')]
  estado='CUBIERTA_OPERATIVA' if op else 'CUBIERTA_PARCIAL' if par else 'FUENTE_INACCESIBLE' if bloq else 'SIN_REVISION_PREVIA_COMPROBADA' if ss or k in plan else 'SIN_FUENTE_LOCALIZADA'
  c=plan.get(k,{})
  rows.append({'provincia':k[0],'departamento_o_partido':m.get('departamento') or m.get('partido') or (m['localidad'] if k[0]=='Buenos Aires' else None),'departamento_propuesto_lote':c.get('departamento'),'localidad':m['localidad'],'organismo':[s['organismo'] for s in ss] or ([c['organismo']] if c else []),'url_oficial':[s['url'] for s in ss] or ([c['url']] if c else []),'url_contrataciones':[s['url'] for s in ss],'estado_cobertura':estado,'ultima_revision':max((r.get('ultima_revision') or '' for r in revisadas),default=None),'evidencia_extraccion':'informes/2026-11-09-fase5/cobertura_territorial.csv' if revisadas else None,'oportunidades_vigentes_ultima_muestra':sum(int(r['convocatorias_vigentes'] or 0) for r in revisadas),'alcance_geografico':alcance_ba(m,padron),'lote':next((l['id'] for l in lotes if any(x['provincia']==k[0] and o.norm(x['localidad'])==k[1] for x in l['localidades'])),None)})
 for c in plan.values():
  if any(r['provincia']==c['provincia'] and o.norm(r['localidad'])==o.norm(c['localidad']) for r in rows):continue
  raise ValueError('Localidad no encontrada en padrón: '+c['localidad'])
 for l in lotes:
  for c in l['localidades']:
   r=next(r for r in rows if r['provincia']==c['provincia'] and o.norm(r['localidad'])==o.norm(c['localidad']))
   if r['estado_cobertura']=='CUBIERTA_OPERATIVA':raise ValueError('No repetir localidad operativa: '+c['localidad'])
 p=Path(destino);p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps({'fecha':datetime.now(o.ZONA).isoformat(),'schema_version':1,'referencia':'5ebae02','cobertura_exhaustiva':False,'localidades':rows,'departamentos_pendientes_de_completar':True},ensure_ascii=False,indent=2)+'\n')
 return rows
if __name__=='__main__':
 rs=generar();from collections import Counter
 print(json.dumps({'localidades':len(rs),'estados':dict(Counter(r['estado_cobertura'] for r in rs)),'lote01':sum(r['lote']=='01' for r in rs)},ensure_ascii=False))
