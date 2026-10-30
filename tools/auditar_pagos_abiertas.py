"""Revisión focalizada y acotada de pliegos de abiertas; historial siempre de sólo lectura."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
import oportunidades as o
import pagos
from tools.comprobar_pliegos import comprobar
from tools.radar_controlado import fuentes_configuradas


def main():
    p=argparse.ArgumentParser();p.add_argument('--entrada',default='work/revision-pagos/work/cobertura');a=p.parse_args();root=Path(a.entrada)
    dbpath=root/'estado.sqlite3';antes=sha256(dbpath.read_bytes()).hexdigest();meta=json.loads((root/'ultima_ejecucion.json').read_text())
    with sqlite3.connect('file:'+str(dbpath.resolve())+'?mode=ro',uri=True) as db:rs=inc.actuales(db,meta['fecha'],meta['corrida'])
    abiertas=[r for r in rs if r.get('clasificacion_registro')=='PROCEDIMIENTO' and r.get('vigencia')=='ABIERTA']
    salida=Path('work/pagos-abiertas');salida.mkdir(parents=True,exist_ok=True)
    pendientes=[r for r in abiertas if r['pago']['estado']!='VERIFICADO'];antes_pago=pagos.resumen(abiertas)
    comprobar(pendientes,meta['fecha'],fuentes_configuradas(),total=180,salida_parcial=salida/'documentos.jsonl')
    abiertas=[o.normalizar(r,meta['fecha']) for r in abiertas]
    resultado={'corrida_origen':meta['corrida'],'fecha_evidencia_catalogo':meta['fecha'],'solo_lectura_historial':True,'hash_sqlite_antes':antes,'hash_sqlite_despues':sha256(dbpath.read_bytes()).hexdigest(),'abiertas':len(abiertas),'pago_antes':antes_pago,'pago_despues':pagos.resumen(abiertas)}
    (salida/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    (salida/'abiertas.json').write_text(json.dumps(abiertas,ensure_ascii=False,indent=2)+'\n')
    (salida/'abiertas.md').write_text(o.reporte(abiertas,meta['fecha'])+'\n')
    print('PAGOS_ABIERTAS '+json.dumps({k:v for k,v in resultado.items() if not k.startswith('pago_') or k=='pago_despues'},ensure_ascii=False))
    if resultado['hash_sqlite_antes']!=resultado['hash_sqlite_despues']:raise ValueError('Cambió el historial aislado durante la revisión')

if __name__=='__main__':main()
