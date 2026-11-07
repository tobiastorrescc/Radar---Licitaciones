"""Barrido territorial aislado por lotes, sin enriquecimiento ni escrituras de estado."""
import argparse,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.verificar_fuentes import ejecutar,guardar

def main():
 p=argparse.ArgumentParser();p.add_argument('--lote',type=int,required=True);a=p.parse_args();plan=json.load(open('tools/plan_fase2.json'))
 fs=[] if plan.get('solo_candidatas') else fuentes_configuradas();ids=plan.get('ids',[])
 if ids:fs=[f for f in fs if f['id'] in ids]
 if plan.get('candidatas'):fs+=json.load(open(plan['candidatas']))['fuentes']
 if len({f['id'] for f in fs})!=len(fs):raise ValueError('IDs repetidos')
 n=int(plan.get('lotes',4))
 if not 1<=n<=8 or not 0<=a.lote<n:raise ValueError('Lote inválido')
 fs=[{**f,'capturar_respuestas':True,'solo_descubrimiento':True,'ocr':False,'admitir_avisos_sin_numero':True,'conexion_timeout':5,'lectura_timeout':8} for i,f in enumerate(fs) if i%n==a.lote]
 root=Path('work/fase2')/('lote-'+str(a.lote));root.mkdir(parents=True,exist_ok=True)
 informe=ejecutar(fs,root/'verificacion.json',concurrencia=4,por_fuente=55,total=480)
 rs=registros_checkpoint(informe)
 guardar(root/'resultado.json',{'fecha':informe['actualizado'],'run':informe['github_run_id'],'revision':informe.get('revision'),'fuentes':fs,'observaciones':informe['observaciones'],'registros':rs,'resumen':informe['resumen'],'segundos':informe['duracion_segundos'],'descubrimiento_independiente':True,'ocr_nuevo':0})
 print('FASE2_BARRIDO '+json.dumps({'lote':a.lote,'registros':len(rs),**informe['resumen']},ensure_ascii=False),flush=True)
if __name__=='__main__':main()
