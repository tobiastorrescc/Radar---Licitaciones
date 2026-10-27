"""Condiciones de pago literales con documento, cita y página; nunca filtra oportunidades."""
from hashlib import sha256
import re
import unicodedata

VERSION=1
NO_INFORMADO='Pago no informado'
NUMEROS={'siete':7,'quince':15,'treinta':30,'cuarenta y cinco':45,'sesenta':60,'noventa':90,
         'cinco':5,'diez':10,'veinte':20,'veinticinco':25,'cuarenta':40,'cincuenta':50,
         'setenta':70,'ochenta':80,'cien':100,'ciento veinte':120,'ciento cincuenta':150,'ciento ochenta':180}
PALABRAS='|'.join(sorted(NUMEROS,key=len,reverse=True))
DIAS=re.compile(r'\b(?:(?P<palabra>'+PALABRAS+r')(?:\s*\((?P<duplicado>\d{1,3})\))?|(?P<numero>\d{1,3}))\s*(?:\([^)]{1,30}\)\s*)?dias\b(?:\s+(?P<unidad>habiles|corridos|calendario))?')
INICIO=re.compile(r'\b(?:(?:forma|condiciones|plazo|modalidad|terminos)(?:s)?\s+(?:y condiciones\s+)?(?:de\s+)?pago|pagos?\s*[:\-]|el pago\b|los pagos\b|se (?:abonara|pagara|cancelara)|seran? (?:abonad[oa]s?|pagad[oa]s?)|pago\s+(?:al\s+)?contado|pago\s+contra\s+)')
LIMITE=re.compile(r'\b(?:(?:plazo|lugar|forma|condiciones)\s+(?:de\s+)?(?:entrega|apertura|garantia|mantenimiento de oferta)|la entrega\s+(?:se|sera|debera)|garantia de (?:oferta|contrato)|valor del pliego|costo del pliego)\b')
EXCLUIDO=re.compile(r'^(?:(?:forma|condiciones|plazo|modalidad)(?:s)?\s+(?:de\s+)?pago|el pago|pago)\s+(?:de[l]?\s+)?(?:pliego|sellado|sellos|tasa|garantia|bases)\b')


def norm(t):
    return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFKD',str(t or '').lower()) if not unicodedata.combining(c))).strip()


def clasificar(cita):
    t=norm(cita)
    if EXCLUIDO.search(t) or re.search(r'pago (?:al |de )?contado (?:de[l]?|por (?:la )?(?:compra|adquisicion) de[l]?) (?:los )?pliegos?',t):return None
    # Las negaciones y remisiones no se transforman en una condición positiva.
    if re.search(r'no se (?:admite|admitira|acepta|aceptara|efectuara|realizara)\b',t):return None
    if re.search(r'(?:segun|conforme a) (?:lo )?(?:establecido|indicado|dispuesto) en (?:el )?pliego',t) and not DIAS.search(t) and not re.search(r'contra entrega|contado',t):return None
    plazos=[];unidades=[]
    for m in DIAS.finditer(t):
        n=int(m['numero'] or m['duplicado'] or NUMEROS[m['palabra']])
        if m['palabra'] and m['duplicado'] and NUMEROS[m['palabra']]!=int(m['duplicado']):return None
        if n not in plazos:plazos.append(n)
        u=m['unidad'] or 'no indicada'
        if u not in unidades:unidades.append(u)
    factura=bool(re.search(r'contra (?:presentacion|entrega)(?: de)? (?:la )?factura|(?:presentacion|recepcion|recibida|fecha|ingreso|entrega) de (?:la )?factura|(?:presentada|recibida) (?:la )?factura|factura (?:respectiva|correspondiente|conformada)',t))
    conformidad=bool(re.search(r'conformidad (?:de (?:la )?)?(?:recepcion|prestacion|servicio)|recepcion (?:definitiva|conforme)|conformada (?:la )?(?:recepcion|prestacion)',t))
    factura_conformada=bool(re.search(r'factura\s+(?:debidamente\s+)?conformada|conformidad de (?:la )?factura',t))
    contra_entrega=bool(re.search(r'contra\s+entrega\b(?!\s+(?:de\s+)?(?:la\s+)?(?:factura|comprobante))',t))
    contado=bool(re.search(r'\b(?:al |de )?contado\b|pago inmediato',t))
    hitos=[]
    if factura:hitos.append('PRESENTACION_O_RECEPCION_FACTURA')
    if factura_conformada:hitos.append('CONFORMIDAD_FACTURA')
    if conformidad:hitos.append('CONFORMIDAD_RECEPCION')
    if contra_entrega or re.search(r'desde (?:la )?entrega|de entregad',t):hitos.append('ENTREGA')
    if not(plazos or contado or contra_entrega or factura or conformidad):return None
    if re.search(r'(?:podra|podran|si (?:el|la)|en caso de)\b',t) and not re.search(r'se (?:acepta|admite)n?.*(?:o |alternativ)',t):return None
    opciones=bool(re.search(r'\b(?:o (?:a |al |contra )|alternativas? de pago|opciones de pago)',t))
    mixto=bool(re.search(r'anticipo|saldo|\d+\s*%|por ciento|cuotas|parciales|certificados mensuales',t)) and (len(plazos)>1 or contado or contra_entrega or 'saldo' in t or 'anticipo' in t)
    if opciones:categoria='OPCIONES_PUBLICADAS'
    elif mixto:categoria='MIXTO'
    elif plazos:categoria='PLAZO_'+str(plazos[0])+'_DIAS' if len(plazos)==1 and plazos[0] in (7,15,30,45,60,90) else 'OTRO_PLAZO'
    elif contado:categoria='CONTADO'
    elif contra_entrega:categoria='CONTRA_ENTREGA'
    elif conformidad:categoria='DESPUES_CONFORMIDAD_RECEPCION'
    elif factura:categoria='CONTRA_PRESENTACION_FACTURA'
    else:return None
    direccion='OFERTANTE_AL_ORGANISMO' if re.search(r'(?:adjudicatario|concesionario|oferente) (?:debera |debe |se obliga a )?(?:abonar|pagar)|pago (?:del |de un )?canon',t) else 'ORGANISMO_AL_PROVEEDOR'
    if categoria=='CONTADO':etiqueta='Pago contado'
    elif categoria=='CONTRA_ENTREGA':etiqueta='Pago contra entrega'
    elif categoria=='CONTRA_PRESENTACION_FACTURA':etiqueta='Contra presentación de factura; plazo no indicado'
    elif categoria=='DESPUES_CONFORMIDAD_RECEPCION':etiqueta='Después de conformidad de recepción; plazo no indicado'
    elif categoria in ('MIXTO','OPCIONES_PUBLICADAS'):etiqueta='Pago mixto' if categoria=='MIXTO' else 'Opciones de pago publicadas'
    else:etiqueta='/'.join(str(n) for n in plazos)+' días'+(' '+unidades[0] if len(unidades)==1 and unidades[0]!='no indicada' else '')
    if plazos:
        if conformidad:etiqueta+=' después de conformidad de recepción'
        elif factura_conformada:etiqueta+=' desde factura conformada'
        elif factura:etiqueta+=' desde presentación/recepción de factura'
        elif 'ENTREGA' in hitos:etiqueta+=' desde entrega'
    if direccion=='OFERTANTE_AL_ORGANISMO':etiqueta+=' (a cargo del adjudicatario)'
    return {'categoria':categoria,'etiqueta':etiqueta,'plazos_dias':plazos,'unidades_dias':unidades,'hitos_inicio':hitos,
            'direccion':direccion,'contado_mencionado':contado,'contra_entrega_mencionado':contra_entrega,
            'prioritario':categoria in ('CONTADO','CONTRA_ENTREGA') and direccion=='ORGANISMO_AL_PROVEEDOR'}


def extraer(texto,url,hash_documento=None,pdf=False,metodo='TEXTO'):
    resultados=[];vistos=set()
    for pagina,contenido in enumerate(texto.split('\f'),1):
        # Conserva párrafos para no mezclar entrega, garantías y pago de suministros.
        bloques=re.split(r'\n\s*\n',contenido)
        for indice,bloque in enumerate(bloques):
            original=re.sub(r'\s+',' ',bloque).strip();t=norm(original)
            for m in INICIO.finditer(t):
                previo=t[max(0,m.start()-90):m.start()]
                if re.search(r'no se (?:admite|admitira|acepta|aceptara|efectuara|realizara)[^.!?]{0,50}$',previo):continue
                if re.search(r'(?:precio|valor|costo|compra|adquisicion) de[l]? pliego[^.!?]{0,40}$',previo):continue
                fragmento=original[m.start():]
                # Un encabezado aislado puede tener su cláusula en los párrafos siguientes.
                if len(fragmento)<80:
                    siguientes=[]
                    for otro in bloques[indice+1:indice+4]:
                        if LIMITE.match(norm(otro)):break
                        siguientes.append(re.sub(r'\s+',' ',otro).strip())
                    fragmento+=' '+' '.join(siguientes)
                limite=LIMITE.search(norm(fragmento),10)
                if limite:fragmento=fragmento[:limite.start()]
                # Una ventana no debe alcanzar otras secciones si el PDF perdió separadores.
                fragmento=fragmento[:1800].strip()
                clasificacion=clasificar(fragmento)
                if clasificacion is None:continue
                clave=(norm(fragmento),pagina)
                if clave in vistos:continue
                vistos.add(clave)
                resultados.append({**clasificacion,'cita':fragmento,'url_documento':url,'sha256':hash_documento,
                    'pagina':pagina if pdf else None,'metodo_extraccion':metodo,'version_analizador':VERSION})
    return resultados


def desconocido(motivo='SIN_CLAUSULA_COMPROBADA'):
    return {'estado':'PENDIENTE','clasificacion':'NO_INFORMADO','etiqueta':NO_INFORMADO,'plazos_dias':[],
            'hitos_inicio':[],'documento_respaldo':None,'evidencias':[],'prioritario':False,'motivo':motivo}


def consolidar(evidencias):
    unicas={}
    for e in evidencias:
        if not e.get('url_documento') or not e.get('cita') or not e.get('sha256'):continue
        llave=(e['categoria'],tuple(e['plazos_dias']),tuple(e['hitos_inicio']),tuple(e.get('unidades_dias',[])),e['direccion'])
        unicas.setdefault(llave,[]).append(e)
    if not unicas:return desconocido()
    todos=[e for lista in unicas.values() for e in lista]
    if len(unicas)>1:
        # No presuponer qué documento prevalece o qué alternativa eligió el comprador.
        r=desconocido('CONDICIONES_DIFERENTES_REQUIEREN_REVISION');r['evidencias']=todos;return r
    e=todos[0]
    return {'estado':'VERIFICADO','clasificacion':e['categoria'],'etiqueta':e['etiqueta'],'plazos_dias':e['plazos_dias'],
            'hitos_inicio':e['hitos_inicio'],'unidades_dias':e['unidades_dias'],'direccion':e['direccion'],
            'documento_respaldo':e['url_documento'],'evidencias':todos,'prioritario':e['prioritario'],'motivo':None}


def unir_evidencias(*grupos):
    resultado={}
    for grupo in grupos:
        for e in grupo or []:
            resultado[(e.get('url_documento'),e.get('sha256'),e.get('pagina'),e.get('cita'))]=e
    return list(resultado.values())


def resumen(registros):
    from collections import Counter
    validos=[r for r in registros if r.get('clasificacion_registro')=='PROCEDIMIENTO']
    estados=Counter(r.get('pago',{}).get('estado','PENDIENTE') for r in validos)
    categorias=Counter(r.get('pago',{}).get('clasificacion','NO_INFORMADO') for r in validos)
    fuentes={}
    for r in validos:
        f=fuentes.setdefault(r.get('fuente'),{'verificadas':0,'pendientes':0,'motivos':Counter()})
        if r.get('pago',{}).get('estado')=='VERIFICADO':f['verificadas']+=1
        else:f['pendientes']+=1;f['motivos'][r.get('pago',{}).get('motivo') or 'SIN_CLAUSULA_COMPROBADA']+=1
    return {'procedimientos':len(validos),'verificadas':estados['VERIFICADO'],'pendientes':len(validos)-estados['VERIFICADO'],
            'clasificaciones':dict(categorias),'fuentes':fuentes}
