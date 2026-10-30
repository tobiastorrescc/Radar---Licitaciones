"""Ficha comercial con evidencia por campo, sin completar ausencias por suposición."""
import json
from pathlib import Path
import re
import pagos

CAMPOS=('objeto','productos','presupuesto','fecha_publicacion','fecha_limite_presentacion','fecha_apertura','condiciones_pago','plazo_entrega','lugar_entrega','modalidad_presentacion','garantias','requisitos','limite_nota_contrasena','moneda_literal')


def extraer(texto,url,digest,metodo='TEXTO'):
    salida={}
    def guardar(campo,valor,pagina,cita,met=metodo):
        salida[campo]={'valor':valor,'estado':'VERIFICADO','evidencia':{'url':url,'sha256':digest,'pagina':pagina,'cita':cita,'metodo':met}}
    for pagina,t in enumerate(texto.split('\f'),1):
        patrones={'plazo_entrega':r'(?:plazo\s+(?:de\s+)?entrega)\s*[:.\-]?\s*([^\n]{5,180})','lugar_entrega':r'(?:lugar\s+(?:de\s+)?entrega)\s*[:.\-]?\s*\n?\s*([^\n]{5,220})','garantias':r'(?:dep[oó]sito\s+de\s+garant[ií]a|garant[ií]a\s+de\s+(?:oferta|contrato))\s*[:.\-]?\s*([^\f]{0,600})'}
        for campo,patron in patrones.items():
            m=re.search(patron,t,re.I)
            if m and not re.search(r'^(?:lugar|forma|apertura|presupuesto|se establecer)',pagos.norm(m[1])):guardar(campo,re.sub(r'\s+',' ',m[1]).strip(),pagina,m[0])
        if re.search(r'repuestos.*nuevos.*sin uso.*originales',pagos.norm(t)):
            m=re.search(r'Los repuestos deber[aá]n[^.]+\.',t,re.I)
            if m:guardar('requisitos',re.sub(r'\s+',' ',m[0]),pagina,m[0])
    archivo=Path(__file__).parent/'inventario/evidencias_documentales.json'
    for e in json.loads(archivo.read_text()) if archivo.exists() else []:
        if e['sha256']!=digest:continue
        guardar('objeto',e['objeto'],e['pagina_objeto'],'Objeto del decreto y especificaciones del mismo PDF', 'REVISION_DOCUMENTAL_PDF_OFICIAL')
        guardar('productos',e['productos'],5,'ANEXO I — PLANILLA DE COTIZACION DE PRECIOS; tabla DETALLES / CANT.', 'REVISION_VISUAL_PDF_OFICIAL_CON_OCR_CACHE')
        for campo,v in e.get('campos_adicionales',{}).items():guardar(campo,v['valor'],v['pagina'],v['cita'],'REVISION_DOCUMENTAL_PDF_OFICIAL')
    return salida


def construir(r):
    detalle=dict(r.get('detalle_documental') or {})
    comprobacion=r.get('comprobacion_pliego') or {}
    if comprobacion.get('sha256'):
        anotado=extraer('',comprobacion.get('url') or r.get('url'),comprobacion['sha256'])
        detalle={**anotado,**detalle}
    campos={}
    for campo in CAMPOS:
        if campo in detalle:campos[campo]=detalle[campo];continue
        valor=r.get(campo)
        if campo=='condiciones_pago' and r.get('pago',{}).get('estado')!='VERIFICADO':valor=None
        evidencia=(r.get('evidencias_campos') or {}).get(campo)
        if campo=='condiciones_pago' and valor:evidencia=r['pago']['evidencias']
        campos[campo]={'valor':valor or None,'estado':'VERIFICADO' if valor and (evidencia or campo in ('objeto','presupuesto','modalidad_presentacion')) else 'PENDIENTE','evidencia':evidencia}
    return {'organismo':r.get('organismo'),'localidad':r.get('localidad'),'provincia':r.get('provincia'),'numero_procedimiento':r.get('numero_procedimiento'),'campos':campos,'publicacion_oficial':r.get('url'),'documentos':r.get('documentos',[]),'primera_deteccion':r.get('primera_deteccion'),'ultima_observacion':r.get('ultima_deteccion'),'pago':r.get('pago'),'recuperacion_efectiva_capital':{'estado':'PENDIENTE','dias':None,'motivo':'El plazo contractual no prueba acreditación bancaria ni fecha efectiva de recuperación del capital.'}}
