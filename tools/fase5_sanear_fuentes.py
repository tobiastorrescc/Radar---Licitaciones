"""Cuarentena de altas no respaldadas por convocatorias, conservando su auditoría."""
import json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import guardar

def main():
 controles=json.load(open('tools/fase5_control_fuentes.json'))['cuarentena'];motivos={r['url']:r['motivo'] for r in controles};p=Path('inventario/fuentes_auto.json');d=json.load(open(p));retiradas=[f['url'] for f in d['fuentes'] if f['url'] in motivos];d['fuentes']=[f for f in d['fuentes'] if f['url'] not in motivos];guardar(p,d)
 p=Path('inventario/descubrimiento_estado.json');d=json.load(open(p))
 for c in d['candidatos'].values():
  if c['url'] in motivos:c['validacion']={**c.get('validacion',{}),'estado':'PENDIENTE','motivo':motivos[c['url']]}
 guardar(p,d);print(json.dumps({'altas_retiradas':retiradas,'registros_historicos_eliminados':0},ensure_ascii=False))
if __name__=='__main__':main()
