"""Descarga externa opcional e importación genérica de HTML, CSV y PDF oficiales."""
import argparse,json,sys
from datetime import datetime
from hashlib import sha256
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import archivos_oficiales as a,conectores,oportunidades as o
from tools.verificar_fuentes import guardar


def capturar(fuente,url,destino):
    _,url=a.configuracion({'fuente_id':fuente,'url_oficial':url})
    datos,tipo,final,status=conectores.descargar(url,conexion_timeout=8,lectura_timeout=12,devolver_estado=True)
    tipo=tipo.split(';')[0]
    if tipo not in ('text/html','text/csv','application/pdf'):raise ValueError('Formato oficial no admitido: '+tipo)
    a.configuracion({'fuente_id':fuente,'url_oficial':final})
    root=Path(destino);root.mkdir(parents=True,exist_ok=True);digest=sha256(datos).hexdigest()
    archivo=digest+{'text/html':'.html','text/csv':'.csv','application/pdf':'.pdf'}[tipo]
    (root/archivo).write_bytes(datos)
    entrada={'fuente_id':fuente,'url_oficial':final,'archivo':archivo,'tipo':tipo,'sha256':digest,'capturado_en':datetime.now(o.ZONA).isoformat(),'recibo':{'metodo':'HTTP_OFICIAL','codigo_http':status,'url_final':final,'sha256':digest}}
    guardar(root/(digest+'.json'),entrada)
    return root/(digest+'.json')


def main():
    p=argparse.ArgumentParser();p.add_argument('--worker');p.add_argument('--checkpoint');p.add_argument('--fuente');p.add_argument('--url');p.add_argument('--bandeja',default='entradas_oficiales');p.add_argument('--salida',default='work/importados');d=p.parse_args()
    if d.worker:
        try:
            path=Path(d.worker);entrada=json.loads(path.read_text());rs,errors=a.leer(entrada,path.parent)
            guardar(d.checkpoint,{'archivo_clave':a.clave(entrada),'archivo_sha256':entrada['sha256'],'archivo_entrada':str(path),'estado':'PARCIAL' if errors else 'OPERATIVA','finalizado':True,'paginas_correctas':1,'oportunidades':rs,'errores':errors,'limites':[],'fase':'EXTRACCION'})
        except Exception as e:guardar(d.checkpoint,{'estado':'ERROR_IMPORTACION','finalizado':True,'paginas_correctas':0,'oportunidades':[],'errores':[conectores.clasificar_error(e,'EXTRACCION')],'limites':[]})
    elif d.url:
        if not d.fuente:p.error('--url necesita --fuente')
        print(capturar(d.fuente,d.url,d.bandeja))
    else:
        rs,informe=a.importar(d.salida,d.bandeja)
        print(json.dumps({'archivos':len(informe['observaciones']),'convocatorias':len(rs),'errores':sum(x['estado']!='OPERATIVA' for x in informe['observaciones'])},ensure_ascii=False))

if __name__=='__main__':main()
