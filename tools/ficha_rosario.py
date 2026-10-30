"""Ficha oficial Drupal: no confundir expediente con número de contratación."""
import re
from datetime import datetime
from urllib.parse import urlparse
import extractores

def extraer(html,url):
    if not re.fullmatch(r'/inicio/compras-licitaciones/detalle/\d+',urlparse(url).path):return []
    dom=extractores.DOM(html);raiz=next((n for n in dom.root.iter() if n.clase('contrataciones-detalle')),None)
    if raiz is None:return []
    campos={};nodos={}
    for fila in raiz.iter():
        if not fila.clase('govuk-summary-list__row'):continue
        k=next((n for n in fila.iter() if n.tag=='dt'),None);v=next((n for n in fila.iter() if n.tag=='dd'),None)
        if k and v:campos[extractores.norm(k.text)]=v.text;nodos[extractores.norm(k.text)]=v
    numero=next((v for k,v in campos.items() if k.startswith('n') and 'de contratacion' in k),None);tipo=campos.get('tipo de contratacion');obj=campos.get('objeto')
    ps=extractores.procesos((tipo or '')+' '+(numero or ''))
    if not ps or not obj:return []
    p=ps[0];id=urlparse(url).path.rsplit('/',1)[-1]
    docs=[]
    for k,n in nodos.items():
        if 'adjunto' not in k and 'pliego' not in k:continue
        for l in n.enlaces(url):
            u=l['url']
            # Únicamente endpoint de lectura efectivamente enlazado por la ficha.
            if re.fullmatch(r'https://apimgw\.rosario\.gob\.ar/licitaciones-api/v1/licitaciones/'+id+r'/documentos/\d+',u):docs.append({'url':u,'titulo':l['texto']})
    r={'url':url,'id_origen':id,'identidad_ambito':'ficha-rosario-'+id,'titulo':tipo+' '+numero+' '+obj,'objeto':obj,'numero_procedimiento':numero,'tipo_procedimiento':p['tipo'],'procedimiento':p['procedimiento'],'expediente':campos.get('expediente'),'documentos':docs,'detalle_completo':True,'registro_estructurado':True,'fecha_apertura_texto':campos.get('fecha de apertura'),'presupuesto_texto':campos.get('presupuesto oficial'),'situacion_publicada':extractores.situacion(campos.get('estado','')),'campos_oficiales':campos,'rango_evidencia':3,'evidencias_campos':{}}
    for k,campo in [('fecha de publicacion','fecha_publicacion')]:
        if campos.get(k):
            try:r[campo]=datetime.strptime(campos[k].strip(),'%d/%m/%Y').date().isoformat();r['evidencias_campos'][campo]={'url':url,'texto':k+': '+campos[k]}
            except ValueError:pass
    return [r]
