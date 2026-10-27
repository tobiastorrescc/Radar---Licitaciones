"""Padrón oficial Georef con procedencia; no equivale a cobertura de portales."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
import json
import math
from pathlib import Path
import sys
from urllib.request import urlopen
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from oportunidades import norm

URLS={k:'https://apis.datos.gob.ar/georef/api/v2.0/'+k+'.json' for k in ('municipios','gobiernos-locales')}

def distancia(a,b):
    lat1,lon1,lat2,lon2=map(math.radians,(*a,*b));dlat=lat2-lat1;dlon=lon2-lon1
    return 6371.0088*2*math.asin(min(1,math.sqrt(math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2)))

def construir(documentos,fuentes):
    salida={};rosario=(-32.9468,-60.6393)
    for recurso,datos in documentos.items():
        filas=datos.get(recurso.replace('-','_'),datos.get(recurso,[])) if isinstance(datos,dict) else datos
        if not isinstance(filas,list):continue
        for r in filas:
            prov=r.get('provincia',{});prov=prov.get('nombre') if isinstance(prov,dict) else prov
            if prov not in ('Santa Fe','Entre Ríos','Buenos Aires'):continue
            nombre=r.get('nombre');codigo=r.get('id');centro=r.get('centroide') or {}
            km=distancia(rosario,(centro['lat'],centro['lon'])) if centro.get('lat') is not None and centro.get('lon') is not None else None
            if prov=='Buenos Aires' and (km is None or km>280):continue
            if not nombre or not codigo:continue
            key=(prov,norm(nombre));item=salida.setdefault(key,{'codigo':codigo,'localidad':nombre,'provincia':prov,'tipo_gobierno':r.get('categoria') or r.get('tipo'),'recursos_oficiales':[],'centroide':centro,'distancia_geodesica_rosario_km':round(km,2) if km is not None else None,'distancia_por_ruta_km':None,'fuentes':[],'estado':'PENDIENTE_DESCUBRIMIENTO'})
            item['recursos_oficiales'].append(recurso)
    for (prov,nombre),r in salida.items():
        r['fuentes']=[f['id'] for f in fuentes if f['provincia']==prov and norm(f.get('localidad'))==nombre]
        if r['fuentes']:r['estado']='PORTAL_INVENTARIADO_NO_EQUIVALE_OPERATIVA'
    return {'fecha':datetime.now().astimezone().isoformat(),'exhaustivo':False,'advertencia':'Padrón Georef observado, no certificación de vigencia provincial ni cobertura operativa. Buenos Aires: selección geodésica <=280 km del centro de Rosario, no distancia vial. Revisar límites y altas recientes.','municipios':list(sorted(salida.values(),key=lambda x:(x['provincia'],x['localidad']))),'totales':{p:sum(r['provincia']==p for r in salida.values()) for p in ('Santa Fe','Entre Ríos','Buenos Aires')}}

def descargar(recurso_url):
    recurso,url=recurso_url
    try:
        with urlopen(url,timeout=12) as r:
            data=r.read(12_000_001)
            if len(data)>12_000_000:raise ValueError('Padron excede 12 MB')
            valor=json.loads(data)
        return recurso,valor,{'url':url,'estado':'DESCARGADO','sha256':sha256(data).hexdigest(),'bytes':len(data)}
    except Exception as e:return recurso,None,{'url':url,'estado':'PENDIENTE','error':str(e)}

def main():
    p=argparse.ArgumentParser();p.add_argument('--salida',default='work/verificacion/territorio.json');args=p.parse_args()
    documentos={};auditoria=[]
    with ThreadPoolExecutor(max_workers=2) as pool:
        for recurso,datos,estado in pool.map(descargar,URLS.items()):
            auditoria.append(estado);print('PADRON '+json.dumps(estado,ensure_ascii=False),flush=True)
            if datos is not None:documentos[recurso]=datos
    fuentes=json.loads(Path('inventario/fuentes.json').read_text())
    resultado=construir(documentos,fuentes);resultado['auditoria_descarga']=auditoria
    destino=Path(args.salida);destino.parent.mkdir(parents=True,exist_ok=True)
    destino.write_text(json.dumps(resultado,ensure_ascii=False,indent=2)+'\n')
    destino.with_name('padrones_originales.json').write_text(json.dumps(documentos,ensure_ascii=False)+'\n')
    print('PADRON_RESUMEN '+json.dumps(resultado['totales']),flush=True)

if __name__=='__main__':main()
