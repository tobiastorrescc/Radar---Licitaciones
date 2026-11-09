"""Descubrimiento prioritario con persistencia existente y presupuesto independiente."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.descubrir_fuentes import ejecutar_descubrimiento
from tools.verificar_fuentes import guardar

def main():
 p=json.load(open('tools/plan_fase4.json'));semillas=json.load(open('tools/fase4_semillas.json'))['candidatos']
 r=ejecutar_descubrimiento('work/fase4/descubrimiento',total=p['descubrimiento_segundos'],busquedas=p['busquedas'],candidatos=p['candidatas_por_lote'],revisar_pendientes=True,priorizar_urls=p.get('priorizar_urls') or [c['url'] for c in semillas])
 guardar('work/fase4/descubrimiento/plan_aplicado.json',p)
if __name__=='__main__':main()
