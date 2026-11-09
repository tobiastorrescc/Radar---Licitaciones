"""Revisar catálogo vigente en lotes acotados, sin enriquecimiento ni producción."""
import sys,json,argparse
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.verificar_fuentes import ejecutar,guardar

def main():
 p=argparse.ArgumentParser();p.add_argument('--lote',type=int,required=True);a=p.parse_args();plan=json.load(open('tools/plan_fase5.json'));fs=fuentes_configuradas();root=Path('work/fase5')/('lote-'+str(a.lote));root.mkdir(parents=True,exist_ok=True)
 fs=[{**f,'noticias_comunales':bool(f.get('noticias_comunales') or f.get('barrido_institucional')),'capturar_respuestas':True,'solo_descubrimiento':True,'ocr':False,'admitir_avisos_sin_numero':True} for i,f in enumerate(fs) if i%4==a.lote]
 informe=ejecutar(fs,root/'verificacion.json',concurrencia=4,por_fuente=45,total=plan['barrido_segundos'])
 guardar(root/'resultado.json',{'fecha':informe['actualizado'],'fuentes':fs,'observaciones':informe['observaciones'],'registros':registros_checkpoint(informe)})
if __name__=='__main__':main()
