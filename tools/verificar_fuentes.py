"""Consulta todas las fuentes incorporadas sin tocar historial ni resultados de producción.
Ejecutar desde la raíz: python tools/verificar_fuentes.py
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
import json
import sys
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conectores


def main():
    fuentes=json.loads(Path('inventario/fuentes.json').read_text())
    def verificar(f):
        r=conectores.explorar(f['url'],f)
        return {'id':f['id'],'url':f['url'],'estado':r['estado'],
                'publicaciones_detectadas':len(r['oportunidades']),
                'paginas_correctas':r['paginas_correctas'],'paginas_visitadas':r['paginas_visitadas'],
                'limites':r['limites'],'errores':r['errores']}
    with ThreadPoolExecutor(max_workers=4) as pool:
        observaciones=list(pool.map(verificar,[f for f in fuentes if f['incorporada']]))
    fecha=datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).isoformat()
    Path('inventario/verificacion.json').write_text(json.dumps({'fecha':fecha,'metodo':'conector HTTP del executor',
        'observaciones':observaciones},ensure_ascii=False,indent=2)+'\n')
    print('Consultadas:',len(observaciones),'Con publicaciones:',sum(r['publicaciones_detectadas']>0 for r in observaciones))
    return 2 if any(r['estado'] in ('BLOQUEADA','PENDIENTE','PARCIAL') for r in observaciones) else 0

if __name__=='__main__':
    raise SystemExit(main())
