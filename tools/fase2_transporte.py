"""Comprobar alternativas de transporte estándar; nunca omitir certificados."""
import json,subprocess,time,ssl,sys
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from tools.verificar_fuentes import guardar
from hashlib import sha256
import conectores,extractores

def main():
 if not json.load(open('tools/plan_fase2.json')).get('diagnosticar_criticas'):return
 root=Path('work/fase2/transporte');root.mkdir(parents=True,exist_ok=True)
 rutas=[('epe','https://epe.santafe.gov.ar/app2/aperturas','TLS12'),('epe','https://www.epe.santafe.gov.ar/app2/aperturas','TLS12'),('epe','http://epe.santafe.gov.ar/app2/aperturas','NORMAL'),('gestiones','https://www.santafe.gob.ar/gestionesdecompras/site/index.php','TLS12'),('gestiones','https://www.santafe.gov.ar/gestionesdecompras/site/','TLS12'),('boletin','https://www.santafe.gob.ar/boletinoficial/ver.php?seccion=2026%2F2026-11-06licitaciones.html','TLS12'),('boletin','https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026%2F2026-11-06licitaciones.html','NORMAL'),('boletin','https://www.santafe.gob.ar/boletinoficial/verPdf.php?archivo=recursos%2Fboletines%2Fpdf%2F2026%2F11%2FBO06112026.pdf','NORMAL')]
 fs=json.load(open('inventario/fuentes.json'));configs={f.get('adaptador'):f for f in fs if f.get('adaptador') in ('epe','gestiones-sf','boletin-sf')}
 def probar(x):
  i,(org,url,modo)=x;path=root/(str(i)+'.bin');start=time.monotonic();cmd=['curl','--location','--silent','--show-error','--connect-timeout','6','--max-time','22','--max-filesize','12000000','--output',str(path),'--write-out','%{http_code}\n%{content_type}\n%{size_download}\n%{ssl_verify_result}\n%{http_version}\n%{url_effective}',url]
  if modo=='TLS12':cmd[1:1]=['--tlsv1.2','--tls-max','1.2','--http1.1']
  r=subprocess.run(cmd,capture_output=True,text=True,timeout=27);v=r.stdout.splitlines();data=path.read_bytes() if path.exists() else b'';registro={'organismo':org,'url':url,'modo':modo,'segundos':round(time.monotonic()-start,3),'curl_exit':r.returncode,'codigo_http':v[0] if v else None,'tipo':v[1] if len(v)>1 else None,'tamano':len(data),'certificado_resultado':v[3] if len(v)>3 else None,'http_version':v[4] if len(v)>4 else None,'final':v[5] if len(v)>5 else None,'error':r.stderr[-1200:],'sha256':sha256(data).hexdigest() if data else None,'convocatorias':0}
  if not r.returncode and v[0]=='200':
   try:
    config=configs[{'epe':'epe','gestiones':'gestiones-sf','boletin':'boletin-sf'}[org]]
    if 'html' in registro['tipo']:rs=extractores.extraer(conectores.decodificar_html(data,registro['tipo']),registro['final'],{**config,'admitir_avisos_sin_numero':True})[0]
    else:rs=[]
    registro['convocatorias']=len(rs);guardar(root/(str(i)+'-registros.json'),rs)
   except Exception as e:registro['error_extraccion']=str(e)
  guardar(root/(str(i)+'.json'),registro);print('TRANSPORTE '+json.dumps(registro,ensure_ascii=False),flush=True);return registro
 resultados=[]
 with ThreadPoolExecutor(max_workers=2) as pool:
  for f in as_completed([pool.submit(probar,x) for x in enumerate(rutas)]):resultados.append(f.result());guardar(root/'resultado.json',{'openssl':ssl.OPENSSL_VERSION,'certificados_desactivados':False,'rutas':resultados})
if __name__=='__main__':main()
