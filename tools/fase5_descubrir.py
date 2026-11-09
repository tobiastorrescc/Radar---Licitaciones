"""Lote territorial verificable: no toca la programación ni el historial del piloto."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.descubrir_fuentes import ejecutar_descubrimiento
from tools.verificar_fuentes import guardar

def main():
 p=json.load(open('tools/plan_fase5.json'));ss=json.load(open('tools/fase5_semillas.json'))['candidatos']
 r=ejecutar_descubrimiento('work/fase5/descubrimiento',total=p['descubrimiento_segundos'],busquedas=p['busquedas'],candidatos=p['candidatas_por_lote'],revisar_pendientes=True,priorizar_urls=[c['url'] for c in ss])
 guardar('work/fase5/descubrimiento/plan_aplicado.json',p)
if __name__=='__main__':main()
