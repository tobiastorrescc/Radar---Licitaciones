"""Inspección de rutas públicas publicadas, sin credenciales ni controles desactivados."""
import sys,json,re
from pathlib import Path
from urllib.parse import urljoin
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import conectores,extractores
from tools.verificar_fuentes import guardar
from hashlib import sha256
root=Path('work/fase6/inspeccion');root.mkdir(parents=True,exist_ok=True)
urls=['https://www.mtotoras.gob.ar/index-BPyaO9iV.js','https://sigloservicios.com/PublicDoc/PublicDoc.aspx?3,7=']
for i,u in enumerate(urls):
 try:
  b,t,f=conectores.descargar(u,conexion_timeout=4,lectura_timeout=8);(root/(str(i)+'.txt')).write_bytes(b)
  guardar(root/(str(i)+'.json'),{'url':u,'final':f,'tipo':t,'bytes':len(b),'sha256':sha256(b).hexdigest(),'estado':'DESCARGADO'})
 except Exception as e:guardar(root/(str(i)+'.json'),{'url':u,'estado':'ERROR','tipo':type(e).__name__,'error':str(e)[:300]})
