"""Disparador externo acotado. Sin --ejecutar no consulta red ni requiere secretos."""
import argparse
from datetime import datetime, timedelta
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import tempfile
import time
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPRedirectHandler
from zoneinfo import ZoneInfo

REPO='tobiastorrescc/Radar---Licitaciones'
RAMA='mejora/radar-auditable'
WORKFLOW='radar-diario.yml'
ZONA='America/Argentina/Buenos_Aires'

class SinRedireccion(HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):
        return None # Nunca entregar el token a un destino redirigido.

class API:
    def __init__(self,token):self.token=token
    def __call__(self,ruta,datos=None):
        req=Request('https://api.github.com/repos/'+REPO+'/'+ruta,
            data=json.dumps(datos).encode() if datos is not None else None,
            headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github+json',
                     'X-GitHub-Api-Version':'2022-11-28','User-Agent':'radar-piloto-externo','Content-Type':'application/json'})
        try:
            with build_opener(SinRedireccion()).open(req,timeout=20) as r:
                contenido=r.read(2_000_001)
                if len(contenido)>2_000_000:raise RuntimeError('Respuesta API demasiado grande')
                return json.loads(contenido) if contenido else {}
        except HTTPError as e:
            raise RuntimeError(f'GitHub HTTP {e.code}; revisar permisos, caducidad o límite API') from None


def plan(ahora):
    fecha=ahora.astimezone(ZoneInfo(ZONA)).date().isoformat()
    clave=sha256(('piloto-diario:'+fecha).encode()).hexdigest()[:40]
    return {'fecha_argentina':fecha,'zona':ZONA,'hora':'08:00','ref':RAMA,
        'inputs':{'modo':'controlado','canal':'piloto','inicializar':'false',
                  'clave_validacion':clave,'paso_validacion':'programado'},
        'titulo':f'Radar controlado {clave} programado'}


def guardar(path,dato):
    path=Path(path)
    with tempfile.NamedTemporaryFile(mode='w',dir=path.parent,delete=False) as f:
        json.dump(dato,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno());temporal=f.name
    os.replace(temporal,path)
    fd=os.open(path.parent,os.O_RDONLY)
    try:os.fsync(fd)
    finally:os.close(fd)


def ejecuciones(api,ahora):
    lista=[]
    desde=(ahora-timedelta(days=2)).date().isoformat()
    for pagina in range(1,6):
        d=api(f'actions/workflows/{WORKFLOW}/runs?branch=mejora%2Fradar-auditable&created=%3E%3D{desde}&per_page=100&page={pagina}')
        filas=d['workflow_runs'];lista.extend(filas)
        if len(filas)<100:return lista
    raise RuntimeError('Listado de ejecuciones truncado; revisar antes de disparar')


def ejecutar(api,carpeta,ahora,*,pausa=time.sleep,reloj=time.monotonic,plazo=3000):
    carpeta=Path(carpeta);carpeta.mkdir(parents=True,exist_ok=True)
    with (carpeta/'programador.lock').open('a') as lock:
        try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:raise RuntimeError('Ya hay un disparador local activo') from None
        p=plan(ahora);path=carpeta/(p['fecha_argentina']+'.json')
        anterior=json.loads(path.read_text()) if path.exists() else None
        if anterior and anterior['estado']=='EXITO':return anterior
        # Confirma acceso y que la cadena diaria existe; no crea una línea de base vacía.
        flujo=api(f'actions/workflows/{WORKFLOW}')
        if flujo['state']!='active':raise RuntimeError('Workflow deshabilitado')
        api('contents/piloto_respaldo/diario/indice.json?ref=mejora%2Fradar-auditable')
        runs=ejecuciones(api,ahora)
        candidatos=[r for r in runs if r.get('display_title')==p['titulo'] and r.get('event')=='workflow_dispatch' and r.get('head_branch')==RAMA]
        if len(candidatos)>1:raise RuntimeError('Disparadores duplicados para la fecha; intervención requerida')
        run=candidatos[0] if candidatos else None
        if not run:
            if anterior:raise RuntimeError('Disparo previo sin confirmar; no se repite automáticamente')
            if any(r['status']!='completed' and r.get('head_branch')==RAMA for r in runs):
                raise RuntimeError('Hay otra ejecución del radar en esta rama; no se dispara otra')
            print('Solicitar piloto '+p['fecha_argentina']+' en '+RAMA,flush=True)
            guardar(path,{**p,'estado':'PENDIENTE_CONFIRMACION'})
            # Si POST fue aceptado pero su respuesta se perdió, conservar journal y reconciliar; nunca reintentar POST.
            api(f'actions/workflows/{WORKFLOW}/dispatches',{'ref':RAMA,'inputs':p['inputs']})
        inicio=reloj()
        while reloj()-inicio<plazo:
            if run:
                if not anterior or anterior.get('run_id')!=run['id']:
                    print('Supervisar '+run['html_url'],flush=True)
                    anterior={'run_id':run['id']}
                estado={**p,'estado':'EN_CURSO','run_id':run['id'],'url':run['html_url']}
                if run['status']=='completed':
                    estado.update(estado='EXITO' if run['conclusion']=='success' else 'FALLO',conclusion=run['conclusion'])
                    guardar(path,estado)
                    if estado['estado']!='EXITO':raise RuntimeError('Falló el piloto: '+run['html_url'])
                    return estado
                guardar(path,estado)
            pausa(15)
            if run:run=api('actions/runs/'+str(run['id']))
            else:
                encontrados=[r for r in ejecuciones(api,ahora) if r.get('display_title')==p['titulo'] and r.get('event')=='workflow_dispatch' and r.get('head_branch')==RAMA]
                if len(encontrados)>1:raise RuntimeError('Disparadores duplicados; revisión requerida')
                run=encontrados[0] if encontrados else None
        raise RuntimeError('Plazo total agotado: resultado incompleto. Consultar journal/Actions; no se redispara')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--ejecutar',action='store_true')
    p.add_argument('--config',type=Path,default=Path('despliegue/piloto.json'))
    p.add_argument('--estado',type=Path,default=Path('/var/lib/radar-piloto'))
    args=p.parse_args();config=json.loads(args.config.read_text())
    if not args.ejecutar:
        print(json.dumps({'modo':'SIMULACION_SIN_RED','habilitado':config['habilitado'],**plan(datetime.now(ZoneInfo(ZONA)))},indent=2));return
    if config.get('habilitado') is not True:raise SystemExit('Programador desactivado: requiere autorización y habilitado=true')
    cred=os.environ.get('CREDENTIALS_DIRECTORY')
    if not cred:raise SystemExit('Falta credencial de systemd; no se acepta token por argumento')
    token=(Path(cred)/'github-token').read_text().strip()
    if not token:raise SystemExit('Token vacío')
    try:print(json.dumps(ejecutar(API(token),args.estado,datetime.now(ZoneInfo(ZONA))),ensure_ascii=False))
    except (RuntimeError,OSError,ValueError,KeyError) as e:raise SystemExit(str(e)) from None

if __name__=='__main__':main()
