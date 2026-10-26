"""Inspección de evidencia de un run anterior y captura pública, sin tocar producción."""
import argparse
import base64
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores


def main():
    p=argparse.ArgumentParser()
    p.add_argument('--auditoria',default='work/auditoria35')
    p.add_argument('--worker')
    args=p.parse_args()
    if args.worker:
        f=json.loads(args.worker)
        try:
            raw,tipo,final=conectores.descargar(f['url'],conexion_timeout=5,lectura_timeout=8)
            raw=__import__('re').sub(rb'data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+',b'data:image/omitida',raw)
            truncada=len(raw)>2_000_000
            print('MUESTRA_JSON '+json.dumps({'id':f['id'],'url':f['url'],'final':final,'tipo':tipo,
                'truncada':truncada,'gzip_b64':base64.b64encode(gzip.compress(raw[:2_000_000])).decode()}))
        except Exception as e:
            print('MUESTRA_JSON '+json.dumps({'id':f['id'],'url':f['url'],'error':str(e),'tipo_error':type(e).__name__}))
        return
    raiz=Path(args.auditoria)
    informes=list(raiz.rglob('verificacion.json'))
    if informes:
        informe=json.loads(informes[0].read_text())
        print('BASE_RESUMEN '+json.dumps(informe['resumen']))
        for r in informe['observaciones']:
            ejemplos=[]
            for e in r.get('errores',[]):
                if not any(x['tipo']==e['tipo'] and x['error']==e['error'] for x in ejemplos): ejemplos.append(e)
            nombre=Path(r.get('resultado_archivo','')).name
            candidatos=[x for x in raiz.rglob(nombre) if x.is_file()] if nombre else []
            completo=json.loads(candidatos[0].read_text()) if candidatos else {}
            print('BASE_FUENTE '+json.dumps({**r,'errores':ejemplos,'muestras_publicaciones':completo.get('oportunidades',[])[:3]},ensure_ascii=False))
    else:
        raise RuntimeError('No se encontró la auditoría original')
    fuentes=[f for f in json.loads(Path('inventario/fuentes.json').read_text()) if f['incorporada']]
    fuentes += json.loads(Path('tools/objetivos_conectores.json').read_text())
    def capturar(f):
        try:
            r=subprocess.run([sys.executable,__file__,'--worker',json.dumps(f)],capture_output=True,text=True,timeout=20)
            return r.stdout or 'MUESTRA_JSON '+json.dumps({'id':f['id'],'error':r.stderr[-1000:]})
        except subprocess.TimeoutExpired:
            return 'MUESTRA_JSON '+json.dumps({'id':f['id'],'error':'Captura excedió 20s'})
    with ThreadPoolExecutor(max_workers=4) as pool:
        for r in as_completed([pool.submit(capturar,f) for f in fuentes]): print(r.result(),flush=True)

if __name__=='__main__':main()
