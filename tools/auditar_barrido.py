"""Barrido territorial verificable: captura avisos sin esperar análisis documental."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import registros_checkpoint
import oportunidades as o


def main():
    parametros=json.load(open('tools/plan_cobertura.json'));manifest=Path(parametros.get('barrido_manifest','inventario/barrido20.json'))
    if manifest.parent!=Path('inventario') or manifest.suffix!='.json':raise ValueError('Manifiesto fuera del inventario')
    plan=json.load(open(manifest));config={f['id']:f for f in json.load(open('inventario/fuentes.json'))};fs=[]
    lote=json.load(open('tools/plan_cobertura.json')).get('barrido_ids',[])
    for entrada in plan['fuentes']:
        if lote and entrada['id'] not in lote:continue
        f={**config[entrada['id']],**entrada} if entrada['id'] in config else entrada
        fs.append({**f,'capturar_respuestas':True,'solo_descubrimiento':True,'ocr':False,'admitir_avisos_sin_numero':True,'conexion_timeout':f.get('conexion_timeout',3),'lectura_timeout':f.get('lectura_timeout',5)})
    root=Path('work/barrido');root.mkdir(parents=True,exist_ok=True)
    informe=ejecutar(fs,root/'verificacion.json',concurrencia=4,por_fuente=min(90,max(15,int(parametros.get('barrido_por_fuente',65)))),total=480)
    rs=registros_checkpoint(informe);validos=[r for r in rs if r.get('clasificacion_registro')=='PROCEDIMIENTO']
    guardar(root/'resultado.json',{'fecha':informe['actualizado'],'run':informe['github_run_id'],'fuentes':fs,'observaciones':informe['observaciones'],'registros':rs,'validos':len(validos),'por_fuente':dict(Counter(r['fuente'] for r in validos)),'descubrimiento_independiente':True,'ocr_nuevo':0})
    print('BARRIDO_REAL '+json.dumps({'fuentes':len(fs),'procedimientos':len(validos),'estados':dict(Counter(f['estado'] for f in informe['observaciones']))},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
