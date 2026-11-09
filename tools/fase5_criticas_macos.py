"""Contraste legítimo desde otra red estándar de Actions, con TLS verificado."""
import json,sys,subprocess,tempfile,argparse
from pathlib import Path
from urllib.error import HTTPError,URLError
from hashlib import sha256
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores
from tools.verificar_fuentes import ejecutar,guardar
from tools.radar_controlado import fuentes_configuradas

def main():
 p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--checkpoint');a=p.parse_args();fs=[f for f in fuentes_configuradas() if f['id'] in ('fuente-003','fuente-060','fuente-087')];root=Path('work/fase5/criticas');root.mkdir(parents=True,exist_ok=True)
 if a.worker:
  f=next(f for f in fs if f['id']==a.worker);cfg={**f,'ocr':False,'solo_descubrimiento':True,'lectura_adjuntos':'necesarios'};cfg['urls_inicio']=list(dict.fromkeys([f['url']]+f.get('urls_inicio',[])))
  def fetch(url,datos_post=None):
   with tempfile.TemporaryDirectory() as tmp:
    body=Path(tmp)/'body';cmd=['/usr/bin/curl','--silent','--show-error','--location','--connect-timeout','4','--max-time','12','--max-filesize','12000000','--output',str(body),'--write-out','%{http_code}\n%{content_type}\n%{url_effective}']
    if datos_post is not None:cmd+=['--data-binary',datos_post.decode()]
    cmd+=[url];r=subprocess.run(cmd,capture_output=True,timeout=14);lines=r.stdout.decode(errors='replace').splitlines();status=int(lines[0]) if lines and lines[0].isdigit() else None;contenido=body.read_bytes() if body.exists() else b''
    guardar(root/(sha256(url.encode()).hexdigest()+'.json'),{'url':url,'http_status':status,'bytes':len(contenido),'sha256':sha256(contenido).hexdigest(),'tipo':lines[1] if len(lines)>1 else None,'curl_returncode':r.returncode,'error':r.stderr.decode(errors='replace')[:500],'tls_verificado':True})
    if r.returncode:raise URLError('curl macOS '+str(r.returncode)+': '+r.stderr.decode(errors='replace')[:300])
    if status is None or status>=400:raise HTTPError(url,status or 0,'Respuesta oficial no satisfactoria',{},None)
    return contenido,lines[1],lines[2]
  def progreso(r):guardar(a.checkpoint,{**r,'config':cfg,'finalizado':False})
  r=conectores.explorar(f['url'],cfg,fetch=fetch,progreso=progreso);guardar(a.checkpoint,{**r,'config':cfg,'finalizado':True});return
 informe=ejecutar(fs,root/'auditoria.json',concurrencia=3,por_fuente=45,total=60,comando=lambda f,s:[sys.executable,__file__,'--worker',f['id'],'--checkpoint',str(s)])
 from tools.radar_controlado import registros_checkpoint
 guardar(root/'resultado.json',{'fecha':informe['actualizado'],'fuentes':fs,'observaciones':informe['observaciones'],'registros':registros_checkpoint(informe),'metodo':'macOS estándar de GitHub Actions; curl nativo y certificados verificados'})
if __name__=='__main__':main()
