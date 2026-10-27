"""Diagnóstico reproducible de las abiertas de #54; nunca escribe producción."""
import base64
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
import extractores


def main():
    p=next(Path('work/base54').rglob('oportunidades_normalizadas.json'))
    datos=json.loads(p.read_text())['oportunidades']
    abiertas=[r for r in datos if r['vigencia']=='ABIERTA']
    for r in abiertas:print('BASE54_ABIERTA '+json.dumps(r,ensure_ascii=False),flush=True)
    urls=list(dict.fromkeys([u for r in abiertas for u in [r.get('url'),r.get('evidencia_url')] if u]))
    inicio='https://aeropuertorosario.com/institucional/licitaciones/'
    raw,tipo,final=conectores.descargar(inicio)
    dom=extractores.DOM(conectores.decodificar_html(raw,tipo))
    urls.extend(l['url'] for l in dom.root.enlaces(final) if 'lpr-2026-00000002' in l['url'].lower())
    def capturar(url):
        try:
            raw,tipo,final=conectores.descargar(url,conexion_timeout=5,lectura_timeout=10)
            if raw.startswith(b'%PDF-'):raw=__import__('documentos').leer(raw,tipo,url,ocr=True).encode();tipo='text/plain; documento PDF extraído'
            return {'url':url,'final':final,'tipo':tipo,'gzip_b64':base64.b64encode(gzip.compress(raw)).decode()}
        except Exception as e:return {'url':url,'error':str(e)}
    with ThreadPoolExecutor(max_workers=4) as pool:
        for r in pool.map(capturar,dict.fromkeys(urls)):print('REVISION54_MUESTRA '+json.dumps(r),flush=True)

if __name__=='__main__':main()
