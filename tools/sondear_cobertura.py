"""Captura oficial para reparar conectores. No promueve fuentes ni toca historiales."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import sys
import subprocess
from urllib.error import HTTPError
from urllib.parse import urlsplit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
import extractores
from tools.verificar_fuentes import ejecutar,guardar


def worker(entrada,salida):
    f=json.loads(Path(entrada).read_text());u=f['url']
    root=Path(salida).parent/'capturas';root.mkdir(exist_ok=True)
    nombre=sha256(u.encode()).hexdigest();archivo=root/(nombre+'.bin')
    if f.get('transporte')=='curl':
        # Diagnóstico público: CA/TLS y proxy heredados, sin cookies ni evasión.
        opciones_tls=['--tls-max','1.2'] if f.get('tls_max')=='1.2' else []
        r=subprocess.run(['curl',*opciones_tls,'--silent','--show-error','--location','--max-redirs','3',
            '--proto','=https','--proto-redir','=https','--connect-timeout','8','--max-time','24',
            '--max-filesize','12000000','--user-agent','RadarLicitaciones/2.0',
            '--output',str(archivo),'--write-out','%{http_code}\n%{content_type}\n%{url_effective}',u],
            capture_output=True,text=True,timeout=27)
        if r.returncode:raise OSError('curl '+str(r.returncode)+': '+r.stderr.strip())
        estado,tipo,final=r.stdout.split('\n',2)
        if int(estado)>=400:raise HTTPError(u,int(estado),'Respuesta HTTP en diagnóstico público',{},None)
        datos=archivo.read_bytes()
    else:
        conexion=max(1,min(12,int(f.get('conexion_timeout',5))));lectura=max(1,min(20,int(f.get('lectura_timeout',8))))
        datos,tipo,final=conectores.descargar(u,conexion_timeout=conexion,lectura_timeout=lectura,datos_post=f.get('datos_post','').encode() if 'datos_post' in f else None,headers_extra={'Content-Type':f.get('content_type','application/json')} if 'datos_post' in f else None)
        archivo.write_bytes(datos)
    if conectores._host(final)!=conectores._host(u):raise ValueError('Redirección a otro dominio: requiere contraste')
    dom=extractores.DOM(conectores.decodificar_html(datos,tipo))
    enlaces=[{k:l[k] for k in ('url','texto')} for l in dom.root.enlaces(final)
        if re.search(r'licit|compra|contrata|cotiza|concurso|boletin|proveedor',l['url']+' '+l['texto'],re.I)]
    guardar(salida,{'estado':'OPERATIVA','finalizado':True,'paginas_correctas':1,'oportunidades':[],
        'url':u,'final':final,'transporte':f.get('transporte','urllib'),'metodo':'POST' if 'datos_post' in f else 'GET','parametros':f.get('datos_post'),'tipo':tipo,'sha256':sha256(datos).hexdigest(),'archivo':str(root/(nombre+'.bin')),
        'enlaces':enlaces,'aviso':'Captura de investigación; no prueba extracción de procedimientos'})


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--salida',default='work/sondeo');a=p.parse_args()
    if a.worker:
        try:worker(a.worker,a.salida)
        except Exception as e:
            f=json.loads(Path(a.worker).read_text())
            guardar(a.salida,{'estado':'BLOQUEADA','finalizado':True,'url':f['url'],'paginas_correctas':0,'oportunidades':[],'errores':[conectores.clasificar_error(e,'DESCARGA')]})
        return
    root=Path(a.salida);root.mkdir(parents=True,exist_ok=True)
    fs=json.loads(Path('inventario/fuentes.json').read_text())
    urls={}
    for f in fs:
        u=f['url'];s=urlsplit(u);base=s.scheme+'://'+s.netloc+'/'
        if f.get('incorporada'):urls.setdefault(base,{'url':base,'organismo':f['organismo']})
    plan=json.loads(Path('tools/plan_cobertura.json').read_text())
    if plan.get('urls_sondeo'):
        urls={u:{'url':u} for u in plan['urls_sondeo']}
    for peticion in plan.get('peticiones',[]):urls[peticion['url']]=peticion
    entradas=root/'entradas';entradas.mkdir(exist_ok=True)
    fuentes=[]
    for n,f in enumerate(urls.values()):
        f={**f,'id':'sondeo-'+str(n)};guardar(entradas/(f['id']+'.json'),f);fuentes.append(f)
    informe=ejecutar(fuentes,root/'sondeo.json',concurrencia=4,por_fuente=35,total=240,
        comando=lambda f,path:[sys.executable,__file__,'--worker',str(entradas/(f['id']+'.json')),'--salida',str(path)])
    hallazgos=[]
    for obs in informe['observaciones']:
        path=Path(obs.get('resultado_archivo',''))
        if path.is_file():hallazgos.append(json.loads(path.read_text()))
    guardar(root/'hallazgos.json',hallazgos)

if __name__=='__main__':main()
