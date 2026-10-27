"""Overlay de fuentes autodescubiertas; nunca sustituye configuración existente."""
import json
from pathlib import Path
import extractores

def cargar_auto(path='inventario/fuentes_auto.json'):
    p=Path(path)
    if not p.exists():return {}
    datos=json.loads(p.read_text())
    if datos.get('schema_version')!=1:raise ValueError('Registro automático no reconocido')
    fuentes={}
    for f in datos.get('fuentes',[]):
        prueba=f.get('validacion',{})
        url=extractores.url_publica(f.get('url',''))
        if not url or prueba.get('estado')!='VALIDADA' or not prueba.get('identidad_verificada') or not prueba.get('procedimientos_con_objeto',0):
            raise ValueError('Una fuente automática carece de evidencia verificable')
        fuentes[url]={**f['config'],'id':f['id'],'url':url,'incorporada':True,'validacion':prueba}
    return fuentes

def combinar(configuradas,automaticas):
    return {**automaticas,**configuradas}
