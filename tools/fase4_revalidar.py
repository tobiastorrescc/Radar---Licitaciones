"""Cola secundaria separada: un deadline no reduce la búsqueda territorial."""
import json,csv,sys,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import ejecutar,guardar

def main():
 p=json.load(open('tools/plan_fase4.json'));ids={c['caso_id'] for c in csv.DictReader(open('informes/2026-11-09-fase3/119_pendientes.csv'))};cs=[c for c in json.load(open('inventario/revalidacion_fase3.json'))['casos'] if c['caso_id'] in ids]
 cs.sort(key=lambda c:(c.get('fecha_limite_presentacion') or c.get('fecha_apertura') or '9999',not bool(c.get('documentos') or c.get('enlace_pliego')),c['caso_id']))
 if not p.get('revalidar',True):
  guardar('work/fase4/revalidacion/resultado.json',{'cola':len(cs),'consultadas':0,'estado':'DIFERIDA_PARA_PRIORIZAR_DESCUBRIMIENTO','presupuesto_independiente':True});return
 fs=[{'id':c['caso_id'],'url':c['url']} for c in cs];root=Path('work/fase4/revalidacion');root.mkdir(parents=True,exist_ok=True)
 informe=ejecutar(fs,root/'auditoria.json',concurrencia=2,por_fuente=25,total=p['revalidacion_segundos'],comando=lambda f,s:[sys.executable,'tools/fase3_revalidar.py','--worker',f['id'],'--checkpoint',str(s)])
 guardar(root/'resultado.json',{'fecha':informe['actualizado'],'cola':len(cs),'consultadas':sum(x['iniciada'] for x in informe['observaciones']),'observaciones':informe['observaciones'],'segundos':informe['duracion_segundos'],'presupuesto_independiente':True})
if __name__=='__main__':main()
