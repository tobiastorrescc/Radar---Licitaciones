"""Publicar inventario con estados observados, sin confundir exploración y cobertura."""
import sys,json,csv
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
ROOT=Path('informes/2026-11-09-fase6')
def main():
 ROOT.mkdir(parents=True,exist_ok=True);p=json.load(open('inventario/fase6_cobertura.json'));filas=p['localidades'];av=json.load(open('inventario/fase6_avance.json'))['lotes']['01'];by={(r['provincia'],r['localidad']):r for r in av['localidades']}
 for r in filas:
  a=by.get((r['provincia'],r['localidad']))
  if a:
   r.update({'ultima_revision':a.get('ultima_revision') or av['fecha'],'evidencia_extraccion':'https://github.com/tobiastorrescc/Radar---Licitaciones/actions/runs/42679698776','estado_cobertura':'EXPLORADA_PARCIALMENTE_NO_INCORPORADA','url_contrataciones':a['secciones_revisadas'],'oportunidades_vigentes_ultima_muestra':0})
   if r['localidad'] in ['Sastre y Ortiz','General Galarza']:r['estado_cobertura']='INCORPORADA_EXTRACCION_HISTORICA_COMPROBADA'
   if r['localidad']=='Totoras':r['url_oficial']=['https://totoras.gob.ar/','https://www.mtotoras.gob.ar/'];r['estado_cobertura']='PENDIENTE_CONTRASTE_SITIO_INSTITUCIONAL'
 def csvout(nombre,rows,campos):
  with (ROOT/nombre).open('w',newline='') as out:
   w=csv.DictWriter(out,fieldnames=campos);w.writeheader();w.writerows({k:json.dumps(r[k],ensure_ascii=False) if isinstance(r[k],(dict,list)) else r[k] for k in campos} for r in rows)
 csvout('cobertura_territorial.csv',filas,list(filas[0]));pend=[r for r in filas if r['estado_cobertura'] not in ['CUBIERTA_OPERATIVA','INCORPORADA_EXTRACCION_HISTORICA_COMPROBADA']];csvout('localidades_pendientes.csv',pend,['provincia','departamento_o_partido','localidad','estado_cobertura','url_oficial','lote'])
 print(json.dumps({'identificadas':len(filas),'pendientes_cobertura_operativa':len(pend),'advertencia':'Departamento oficial pendiente donde no consta; BA por radio geodésico, distancia vial pendiente. No acredita cobertura exhaustiva.'}))
if __name__=='__main__':main()
