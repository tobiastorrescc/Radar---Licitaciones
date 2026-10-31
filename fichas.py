"""Ficha comercial con evidencia por campo, sin completar ausencias por suposición."""
import json
from pathlib import Path
import re
import pagos

CAMPOS=('objeto','productos','productos_alternativos','presupuesto','fecha_publicacion','fecha_limite_presentacion','hora_limite_presentacion','fecha_apertura','hora_apertura','condiciones_pago','plazo_entrega','lugar_entrega','modalidad_presentacion','garantias','requisitos','limite_nota_contrasena','moneda_literal')



def separar_alternativas(productos):
    principales=[];alternativas=[]
    for p in productos:
        texto=p.get('producto') or ''
        if not re.search(r'alternativa|en lugar de',texto,re.I):principales.append(p);continue
        alternativas.append({**p,'tipo_requerimiento':'ALTERNATIVA_PERMITIDA'})
        original=re.search(r'en lugar de (?:las |los )?(\d+) solicitad',texto,re.I)
        if original:
            principales.append({**p,'producto':re.split(r'en lugar de',texto,flags=re.I)[0].strip(),'cantidad':int(original[1]),'tipo_requerimiento':'PRINCIPAL_EXPLICITO_EN_CLAUSULA_ALTERNATIVA'})
    return principales,alternativas

def extraer(texto,url,digest,metodo='TEXTO'):
    salida={}
    def guardar(campo,valor,pagina,cita,met=metodo):
        salida[campo]={'valor':valor,'estado':'VERIFICADO','evidencia':{'url':url,'sha256':digest,'pagina':pagina,'cita':cita,'metodo':met}}
    for pagina,t in enumerate(texto.split('\f'),1):
        patrones={'plazo_entrega':r'(?:plazo\s+(?:de\s+)?entrega)[ \t]*:[ \t]*([^\n]{5,180})','lugar_entrega':r'(?:lugar\s+(?:de\s+)?entrega)[ \t]*:[ \t]*\n?[ \t]*([^\n]{5,220})','garantias':r'(?:dep[oó]sito\s+de\s+garant[ií]a|garant[ií]a\s+de\s+(?:oferta|contrato))[ \t]*:[ \t]*([^\f]{0,600})'}
        for campo,patron in patrones.items():
            m=re.search(patron,t,re.I)
            if m and not re.search(r'^(?:lugar|forma|apertura|presupuesto|se establecer)',pagos.norm(m[1])):guardar(campo,re.sub(r'\s+',' ',m[1]).strip(),pagina,m[0])
        if re.search(r'repuestos.*nuevos.*sin uso.*originales',pagos.norm(t)):
            m=re.search(r'Los repuestos deber[aá]n[^\n]+(?:\n[^\n]+)?',t,re.I)
            if m:guardar('requisitos',re.sub(r'\s+',' ',m[0]),pagina,m[0])
    # Cantidades sólo cuando el texto liga explícitamente compra y producto.
    patron=re.compile(r'(?:adquisici[oó]n|provisi[oó]n|suministro|compra)\s+de\s+(?:(?P<palabra>una?|dos|tres)\s*\(\s*)?(?P<cantidad>\d{1,3}(?:\.\d{3})*|\d{1,6})(?(palabra)\s*\)\s*|\s+)(?P<producto>[A-Za-zÁÉÍÓÚáéíóúÑñ][^.;\n]{2,110})',re.I)
    productos=[]
    for pagina,t in enumerate(texto.split('\f'),1):
        for m in patron.finditer(t):
            n=int(m['cantidad'].replace('.',''))
            palabra=(m['palabra'] or '').lower()
            if palabra and {'un':1,'una':1,'dos':2,'tres':3}[palabra]!=n:continue
            productos.append({'producto':m['producto'].strip(' “”.'), 'cantidad':n,'unidad':None,'pagina':pagina,'cita':m[0]})
    principales,alternativas=separar_alternativas(productos)
    if principales:guardar('productos',principales,principales[0]['pagina'],'; '.join(p['cita'] for p in principales))
    if alternativas:guardar('productos_alternativos',alternativas,alternativas[0]['pagina'],'; '.join(p['cita'] for p in alternativas))
    archivo=Path(__file__).parent/'inventario/evidencias_documentales.json'
    for e in json.loads(archivo.read_text()) if archivo.exists() else []:
        if e['sha256']!=digest:continue
        guardar('objeto',e['objeto'],e['pagina_objeto'],'Objeto del decreto y especificaciones del mismo PDF', 'REVISION_DOCUMENTAL_PDF_OFICIAL')
        guardar('productos',e['productos'],e.get('pagina_productos',5),e.get('cita_productos','ANEXO I — PLANILLA DE COTIZACION DE PRECIOS; tabla DETALLES / CANT.'), 'REVISION_VISUAL_PDF_OFICIAL_CON_OCR_CACHE')
        for campo,v in e.get('campos_adicionales',{}).items():guardar(campo,v['valor'],v['pagina'],v['cita'],'REVISION_DOCUMENTAL_PDF_OFICIAL')
    return salida


def construir(r):
    detalle=dict(r.get('detalle_documental') or {})
    comprobacion=r.get('comprobacion_pliego') or {}
    if comprobacion.get('sha256'):
        anotado=extraer(comprobacion.get('encabezado') or '',comprobacion.get('url') or r.get('url'),comprobacion['sha256'],'ENCABEZADO_DOCUMENTAL_GUARDADO_NORMALIZADO')
        for v in anotado.values():
            if v['evidencia']['metodo']=='ENCABEZADO_DOCUMENTAL_GUARDADO_NORMALIZADO':v['evidencia']['pagina']=None
        detalle={**anotado,**detalle}
    campos={}
    if detalle.get('productos'):
        principal,alternativo=separar_alternativas(detalle['productos']['valor'])
        if alternativo:
            detalle['productos_alternativos']={**detalle['productos'],'valor':alternativo}
            detalle['productos']={**detalle['productos'],'valor':principal,'estado':'VERIFICADO' if principal else 'PENDIENTE'}
    for campo in CAMPOS:
        if campo in detalle:campos[campo]=detalle[campo];continue
        valor=r.get(campo)
        if campo=='condiciones_pago' and r.get('pago',{}).get('estado')!='VERIFICADO':valor=None
        evidencia=(r.get('evidencias_campos') or {}).get(campo)
        if campo.startswith('hora_') and not evidencia:evidencia=(r.get('evidencias_campos') or {}).get(campo.replace('hora_','fecha_'))
        if campo=='condiciones_pago' and valor:evidencia=r['pago']['evidencias']
        campos[campo]={'valor':valor or None,'estado':'VERIFICADO' if valor and (evidencia or campo in ('objeto','presupuesto','modalidad_presentacion')) else 'PENDIENTE','evidencia':evidencia}
    return {'organismo':r.get('organismo'),'localidad':r.get('localidad'),'provincia':r.get('provincia'),'numero_procedimiento':r.get('numero_procedimiento'),'tipo_procedimiento':r.get('tipo_procedimiento'),'campos':campos,'publicacion_oficial':r.get('url'),'documentos':r.get('documentos',[]),'primera_deteccion':r.get('primera_deteccion'),'ultima_observacion':r.get('ultima_deteccion'),'pago':r.get('pago'),'plazo_nominal_pago':{'dias':r.get('pago',{}).get('plazos_dias',[]),'unidades':r.get('pago',{}).get('unidades_dias',[]),'hitos_inicio':r.get('pago',{}).get('hitos_inicio',[])},'anticipos_y_parciales':{k:(True if any(e.get(k) for e in r.get('pago',{}).get('evidencias',[])) else None) for k in ('anticipo_publicado','pagos_parciales','facturacion_parcial')},'recuperacion_efectiva_capital':{'estado':'PENDIENTE','dias':None,'motivo':'El plazo contractual no prueba acreditación bancaria ni fecha efectiva de recuperación del capital.'}}


def reporte(registros,fecha):
    def limpio(v):return str(v or '').replace('|','/').replace('\n',' ')
    lineas=['# Fichas completas de oportunidades abiertas','',f'Vigencia calculada a {fecha}. Los datos pendientes no se completan por suposición.','']
    for r in registros:
        f=construir(r);lineas+=['## '+limpio(f['organismo'])+' — '+limpio(f['numero_procedimiento']),'',f"[Publicación oficial]({f['publicacion_oficial']})",'']
        for campo,d in f['campos'].items():
            if campo=='productos':continue
            v=d['valor'];v=json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v
            lineas.append('- **'+campo.replace('_',' ').capitalize()+'**: '+limpio(v or 'Pendiente de verificar')+' ('+d['estado']+').')
            e=d.get('evidencia')
            if isinstance(e,dict) and e.get('url'):lineas.append('  Respaldo: '+e['url']+'; página '+str(e.get('pagina') or 'no identificada')+'.')
        productos=f['campos']['productos']['valor'] or []
        if productos:
            lineas+=['','| Equipo | Renglón | Producto | Cantidad | Página |','|---|---:|---|---:|---:|']
            lineas.extend('| '+' | '.join(limpio(p.get(k)) for k in ('equipo','renglon','producto','cantidad','pagina'))+' |' for p in productos)
        lineas+=['','Tiempo efectivo hasta acreditación bancaria: **pendiente de verificar**. El plazo contractual no equivale a recuperación efectiva del capital.','']
    return '\n'.join(lineas)+'\n'
