"""Inspección acotada de scripts públicos observados, sin inventar endpoints ni ejecutarlos."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
from urllib.parse import urljoin,urlparse
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
import extractores
from tools.verificar_fuentes import ejecutar,guardar

def candidatos(html,url):
    dom=extractores.DOM(html);host=lambda u:(urlparse(u).hostname or '').removeprefix('www.')
    encontrados=[]
    for n in dom.root.iter():
        if n.tag=='script' and n.attrs.get('src'):
            destino=extractores.url_publica(n.attrs['src'],url)
            if destino and host(destino)==host(url) and not re.search(r'jquery|bootstrap|gtag|recaptcha|fontawesome',destino,re.I):encontrados.append(destino)
    return sorted(set(encontrados),key=lambda u:(not bool(re.search(r'licit|compra|main|app',u,re.I)),u))

def worker(url,salida):
    datos,tipo,final=conectores.descargar(url,conexion_timeout=5,lectura_timeout=5)
    if (urlparse(final).hostname or '').removeprefix('www.')!=(urlparse(url).hostname or '').removeprefix('www.'):raise ValueError('Asset redirige a otro dominio')
    root=Path(salida).parent;archivo=root/(sha256(url.encode()).hexdigest()+'.js')
    archivo.write_bytes(datos)
    texto=datos.decode('utf-8',errors='replace')
    endpoints=sorted(set(re.findall(r'''(?:fetch|axios\.(?:get|post))\(\s*['"]([^'"]+)''',texto)))
    guardar(salida,{'estado':'OPERATIVA','finalizado':True,'paginas_correctas':1,'oportunidades':[],'url':url,'sha256':sha256(datos).hexdigest(),'archivo':str(archivo),'endpoints_observados':endpoints,'advertencia':'Asset público; no prueba funcionamiento de una fuente de licitaciones'})

def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--salida');args=p.parse_args()
    if args.worker:worker(args.worker,args.salida);return
    fs={f['id']:f for f in json.loads(Path('inventario/fuentes.json').read_text()) if f.get('investigar_scripts')}
    jobs={}
    for meta in Path('work/verificacion').glob('**/capturas/*/*.json'):
        if meta.parent.name not in fs:continue
        r=json.loads(meta.read_text());txt=meta.with_suffix('.txt')
        if not txt.is_file():continue
        for url in candidatos(txt.read_text(errors='replace'),r['final'])[:4]:jobs[url]={'id':sha256(url.encode()).hexdigest()[:16],'url':url,'incorporada':True}
    informe=ejecutar(list(jobs.values()),'work/verificacion/scripts/verificacion_assets.json',concurrencia=4,por_fuente=12,total=45,comando=lambda f,path:[sys.executable,__file__,'--worker',f['url'],'--salida',str(path)],emitir=lambda m:print('ASSET '+m,flush=True))
    print('SCRIPTS_RESUMEN '+json.dumps(informe['resumen']),flush=True)
    for obs in informe['observaciones']:
        ruta=Path(obs.get('resultado_archivo',''))
        if ruta.is_file():
            r=json.loads(ruta.read_text());print('SCRIPT_OBSERVADO '+json.dumps({k:r.get(k) for k in ('url','archivo','sha256','endpoints_observados','estado')},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
