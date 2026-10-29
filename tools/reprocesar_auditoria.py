"""Reclasifica evidencia real guardada sin red ni cambios en SQLite/producción."""
import argparse
import json
from pathlib import Path
import sqlite3
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
import oportunidades as o
import pagos


def main():
    p=argparse.ArgumentParser();p.add_argument('--entrada',default='work/reprocesar/work/cobertura');a=p.parse_args();root=Path(a.entrada)
    meta=json.loads((root/'ultima_ejecucion.json').read_text());db=sqlite3.connect('file:'+str((root/'estado.sqlite3').resolve())+'?mode=ro',uri=True)
    try:
        if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Estado de auditoría dañado')
        registros=inc.actuales(db,meta['fecha'],meta['corrida']);cuentas={t:db.execute('SELECT COUNT(*) FROM '+t).fetchone()[0] for t in ('procedimientos','versiones','ejecuciones')}
    finally:db.close()
    salida=Path('work/reprocesado');salida.mkdir(parents=True,exist_ok=True)
    vistas=o.separar_vigencia(registros,meta['fecha']);pago=pagos.resumen(registros)
    resultado={'origen_run_id':'40952155721','fecha_observacion':meta['fecha'],'version_analizador_pago':pagos.VERSION,
        'sin_consultas_nuevas':True,'sin_escritura_sqlite':True,'cuentas_preservadas':cuentas,
        'procedimientos_unicos':len(registros),'duplicados_unificados':cuentas['procedimientos']-len(registros),
        'abiertas':len(vistas['abiertas']),'proximas_a_vencer':len(vistas['proximas_a_vencer']),
        'pagos':{k:v for k,v in pago.items() if k!='fuentes'},'clasificacion_incremental_original':meta['clasificacion']}
    (salida/'resultado.json').write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    verificados=[{k:r.get(k) for k in ('organismo','numero_procedimiento','objeto','fecha_apertura','fecha_limite_presentacion','presupuesto','pago','url','enlace_pliego')} for r in registros if r.get('pago',{}).get('estado')=='VERIFICADO']
    (salida/'pagos_verificados.json').write_text(json.dumps(verificados,ensure_ascii=False,indent=2)+'\n')
    print('REPROCESO_AUDITABLE '+json.dumps(resultado,ensure_ascii=False),flush=True)

if __name__=='__main__':main()
