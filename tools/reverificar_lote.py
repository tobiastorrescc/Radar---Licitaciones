"""Regresión real por IDs explícitos; no consulta ni modifica un historial."""
from collections import Counter
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import registros_checkpoint
from tools.informe_cobertura import estado_cobertura


def main():
    ids=set(json.load(open('tools/plan_cobertura.json')).get('reverificar_ids',[]))
    if not ids:return
    fs=[f for f in json.load(open('inventario/fuentes.json')) if f['id'] in ids]
    if {f['id'] for f in fs}!=ids:raise ValueError('ID de fuente no configurada')
    root=Path('work/reverificacion');root.mkdir(parents=True,exist_ok=True)
    informe=ejecutar(fs,root/'verificacion.json',concurrencia=2,por_fuente=75,total=150)
    rs=registros_checkpoint(informe);observaciones=[]
    for f in informe['observaciones']:
        filas=[r for r in rs if r.get('fuente')==f['url']]
        observaciones.append({**f,'estado_cobertura':estado_cobertura(f,filas)})
    guardar(root/'resultado.json',{'fuentes':observaciones,'registros':rs,'estados':dict(Counter(f['estado_cobertura'] for f in observaciones))})
    print('REVERIFICACION '+json.dumps({'fuentes':len(fs),'estados':dict(Counter(f['estado_cobertura'] for f in observaciones)),'registros':len(rs)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
