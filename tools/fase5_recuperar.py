"""Contraste dirigido: conservar presupuesto anterior y lectores probados."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.radar_controlado import fuentes_configuradas,registros_checkpoint
from tools.verificar_fuentes import ejecutar,guardar
p=json.load(open('tools/plan_fase5_recuperacion.json'));fs=[{**f,'capturar_respuestas':True,'solo_descubrimiento':True,'ocr':False,'admitir_avisos_sin_numero':True} for f in fuentes_configuradas() if f['id'] in p['ids']];root=Path('work/fase5/recuperacion');root.mkdir(parents=True,exist_ok=True)
informe=ejecutar(fs,root/'verificacion.json',concurrencia=3,por_fuente=55,total=240)
guardar(root/'resultado.json',{'fecha':informe['actualizado'],'fuentes':fs,'observaciones':informe['observaciones'],'registros':registros_checkpoint(informe)})
