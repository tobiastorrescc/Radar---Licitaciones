"""Vías oficiales acotadas e importador existente; sin repetir bloqueos ni TLS inseguro."""
import sys,json,time,os,re
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores,extractores,archivos_oficiales as a,oportunidades as o
from fuentes_criticas import ediciones_santafe,enlaces_csv,gestiones_csv
from tools.verificar_fuentes import guardar
from tools.importar_oficiales import registrar_archivo
from datetime import datetime

def main():
 root=Path('work/fase3/criticas');root.mkdir(parents=True,exist_ok=True);audit=[];registros=[];inicio=time.monotonic()
 fs={f['id']:f for f in json.load(open('inventario/fuentes.json'))}
 rutas=[('fuente-003','https://epe.santafe.gov.ar/app2/aperturas'),('fuente-087','https://www.santafe.gob.ar/gestionesdecompras/site/index.php'),('fuente-060',ediciones_santafe('https://www.santafe.gov.ar/boletinoficial/',0)[0])]
 for id,url in rutas:
  start=time.monotonic();s={'fuente':id,'url':url,'estado':'INACCESIBLE','convocatorias':0,'exportaciones_observadas':[]}
  try:
   b,t,u,status=conectores.descargar(url,conexion_timeout=4,lectura_timeout=7,devolver_estado=True)
   s.update(http=status,bytes=len(b),tipo=t,sha256=__import__('hashlib').sha256(b).hexdigest())
   html=conectores.decodificar_html(b,t);rs,ls,dom=extractores.extraer(html,u,fs[id]);s['estado']='PARCIAL' if not rs else 'REVISADA_CON_RESULTADOS'
   if id=='fuente-087':
    urls=enlaces_csv(dom,u)
    # Sólo literales publicados por la interfaz, no nombres de endpoints supuestos.
    for x in re.finditer(r'''(?:window\.open|location\.href\s*=)\s*\(?\s*['"]([^'"\s]+\.csv(?:\?[^'"]*)?)['"]''',html):
     from urllib.parse import urljoin,urlsplit
     v=urljoin(u,x[1])
     if urlsplit(v).hostname==urlsplit(u).hostname:urls.append(v)
    s['exportaciones_observadas']=sorted(set(urls))
    for csvurl in s['exportaciones_observadas'][:2]:
     try:
      bb,tt,uu,ss=conectores.descargar(csvurl,conexion_timeout=4,lectura_timeout=8,devolver_estado=True)
      rr,er=gestiones_csv(bb,uu,fs[id]['url']);rs+=rr
      # Bandeja de trabajo aislada, recibo HTTP con fecha y huella del archivo.
      import hashlib
      h=hashlib.sha256(bb).hexdigest();p=root/(h+'.csv');p.write_bytes(bb)
      m=registrar_archivo(id,uu,p,root/'bandeja',datetime.now(o.ZONA).isoformat());d=json.load(open(m));d['recibo']={'metodo':'HTTP_OFICIAL','codigo_http':ss,'url_final':uu,'sha256':h};guardar(m,d)
     except Exception as e:s.setdefault('errores_exportacion',[]).append(str(e))
   if rs:
    s['estado']='REVISADA_CON_RESULTADOS';registros +=[o.normalizar({**{k:fs[id].get(k) for k in ('organismo','localidad','provincia')},**r,'fuente':fs[id]['url']},datetime.now(o.ZONA)) for r in rs]
   s['convocatorias']=len(rs)
   (root/(id+'.html')).write_bytes(b)
  except Exception as e:s['error']=conectores.clasificar_error(e,'DESCARGA')
  s['segundos']=round(time.monotonic()-start,3);audit.append(s);guardar(root/'resultado.json',{'fecha':datetime.now(o.ZONA).isoformat(),'run':os.environ.get('GITHUB_RUN_ID'),'fuentes':audit,'registros':registros,'segundos':round(time.monotonic()-inicio,3),'alternativa':'Importador CSV/HTML/PDF oficial; nunca falla=sin novedades','tls_verificado':True,'ocr_nuevo':0});print(json.dumps(s,ensure_ascii=False),flush=True)
 # Bandeja del usuario: el código ya valida dominio, huella, fecha y procedencia.
 rs,im=a.importar(root/'importacion','entradas_oficiales',total=45)
 guardar(root/'archivos_aportados.json',{'registros':rs,'auditoria':im})
if __name__=='__main__':main()
