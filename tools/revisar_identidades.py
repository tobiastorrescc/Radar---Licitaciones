"""Lee cuatro documentos oficiales de los grupos dudosos, sin modificar historial."""
import json
from pathlib import Path
import subprocess
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cache_documentos as cache
import conectores
from hashlib import sha256

URLS=['https://www.federacion.gob.ar/sites/default/files/4-invitacion_2_1.docx','https://www.federacion.gob.ar/sites/default/files/pliego_general_y_particular_lic_publica_no_01-23.pdf','https://www.federacion.gob.ar/sites/default/files/pliego_lic_publica_no_08-2026.pdf','https://www.federacion.gob.ar/sites/default/files/condiciones_particulares_lp_18-23.pdf','https://www.federacion.gob.ar/sites/default/files/6-pliego_lic._restaurante_costanera.pdf']

def worker(url):
    b,t,u,m=cache.obtener(url)
    texto,meta=cache.leer_texto(b,t,u,ocr=False)
    return {'url':url,'url_final':u,'sha256':sha256(b).hexdigest(),'texto':texto,'cache':m['cache_estado'],'lectura':meta}

if __name__=='__main__':
    if '--worker' in sys.argv:
        try:print(json.dumps(worker(sys.argv[-1]),ensure_ascii=False))
        except Exception as e:print(json.dumps({'url':sys.argv[-1],'error':str(e)}))
    elif json.load(open('tools/plan_cobertura.json')).get('revisar_identidades'):
        salida=Path('work/identidades');salida.mkdir(parents=True,exist_ok=True);rs=[]
        for i,u in enumerate(URLS):
            try:r=json.loads(subprocess.run([sys.executable,__file__,'--worker',u],capture_output=True,text=True,check=True,timeout=30).stdout)
            except Exception as e:r={'url':u,'error':str(e)}
            rs.append(r);(salida/'documentos.json').write_text(json.dumps(rs,ensure_ascii=False,indent=2)+'\n')
            print('IDENTIDAD_DOCUMENTO '+json.dumps({k:v for k,v in r.items() if k!='texto'},ensure_ascii=False),flush=True)
