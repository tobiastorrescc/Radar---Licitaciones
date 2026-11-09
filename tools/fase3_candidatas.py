"""Validar nuevas rutas del inventario ya documentadas; no altas sin prueba real."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint

def main():
 conocidas={f['url'].rstrip('/') for f in fuentes_configuradas()};sect=json.load(open('inventario/candidatas_sectoriales.json'))['candidatos'];fs=[]
 plan=json.load(open('tools/plan_fase3.json'))
 candidatas=json.load(open(plan['candidatas_extra']))['fuentes'] if plan.get('candidatas_extra') else sect[:14]
 for c in candidatas:
  if c['url'].rstrip('/') in conocidas:continue
  f={**c,'id':'fase3-'+str(len(fs)+1).zfill(3),'conector':'publicaciones','descubrir_contrataciones':True,'barrido_institucional':True,'indice_documentos':True,'priorizar_listados':True,'lectura_adjuntos':'necesarios','solo_descubrimiento':True,'ocr':False,'capturar_respuestas':True,'admitir_avisos_sin_numero':True,'conexion_timeout':4,'lectura_timeout':7}
  fs.append(f)
 root=Path('work/fase3/candidatas');root.mkdir(parents=True,exist_ok=True)
 informe=ejecutar(fs,root/'auditoria.json',concurrencia=3,por_fuente=45,total=260)
 guardar(root/'resultado.json',{'fecha':informe['actualizado'],'run':informe['github_run_id'],'fuentes':fs,'observaciones':informe['observaciones'],'registros':registros_checkpoint(informe),'segundos':informe['duracion_segundos'],'alta_automatica':False})
if __name__=='__main__':main()
