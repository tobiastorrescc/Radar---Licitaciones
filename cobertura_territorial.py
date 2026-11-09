"""Inventario auditable: identificar localidades no equivale a revisar convocatorias."""
import csv,json
from pathlib import Path
import oportunidades as o
from calidad_comercial import presentacion
from descubrimiento_territorial import alcance_ba

def generar(fuentes,observaciones,registros,fecha,destino,padron=None):
 padron=padron or json.load(open('inventario/territorio.json'));byurl={s['url']:s for s in observaciones};rows=[]
 for m in padron['municipios']:
  fs=[f for f in fuentes if o.norm(f.get('localidad'))==o.norm(m['localidad']) and f.get('provincia')==m['provincia']]
  alcance=alcance_ba(m,padron)
  if not fs:fs=[{}]
  for f in fs:
   s=byurl.get(f.get('url'),{});rs=[r for r in registros if r.get('fuente')==f.get('url')];ident=f.get('validacion',{}).get('identidad_verificada') or f.get('evidencia_verificacion')
   rows.append({'provincia':m['provincia'],'departamento_o_partido':m.get('departamento') or m.get('partido') or 'Pendiente de padrón departamental','localidad':m['localidad'],'codigo_padron':m.get('codigo'),'organismo':f.get('organismo') or 'Pendiente de identificar','sitio_oficial':f.get('url') or '', 'fuente_contrataciones':f.get('url') or '', 'localidad_identificada':True,'fuente_localizada':bool(f.get('url')),'fuente_validada':bool(ident),'fuente_incorporada':bool(f.get('incorporada')),'fuente_revisada':bool(s.get('iniciada')),'estado_extraccion':s.get('estado') or 'NO_REVISADA','ultima_revision':s.get('inicio') or '', 'convocatorias_vigentes':sum(presentacion(r,fecha)['presentacion_verificada'] for r in rs),'alcance_geografico_verificado':alcance['verificado']})
 root=Path(destino);root.mkdir(parents=True,exist_ok=True)
 with (root/'cobertura_territorial.csv').open('w',newline='') as out:
  w=csv.DictWriter(out,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 resumen={p:{'localidades_identificadas':len({(r['provincia'],r['localidad']) for r in rows if r['provincia']==p}),'con_fuente':len({(r['provincia'],r['localidad']) for r in rows if r['provincia']==p and r['fuente_localizada']}),'revisadas':len({(r['provincia'],r['localidad']) for r in rows if r['provincia']==p and r['fuente_revisada']})} for p in ['Santa Fe','Entre Ríos','Buenos Aires']}
 (root/'cobertura_territorial_resumen.json').write_text(json.dumps({'fecha':fecha,'jurisdicciones':resumen,'cobertura_exhaustiva':False,'advertencia':'Buenos Aires incluye identificadas pendientes de distancia vial; el departamento se deja pendiente cuando el padrón no lo publica. Las fuentes sectoriales se informan además en la auditoría por organismo.'},ensure_ascii=False,indent=2)+'\n');return resumen
