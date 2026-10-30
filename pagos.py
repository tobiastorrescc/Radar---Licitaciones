"""Condiciones de pago literales con documento, cita y página; nunca filtra oportunidades."""
from hashlib import sha256
import re
import unicodedata

VERSION=13
NO_INFORMADO='Pendiente de verificar'
NUMEROS={'siete':7,'quince':15,'treinta':30,'cuarenta y cinco':45,'sesenta':60,'noventa':90,
         'cinco':5,'diez':10,'veinte':20,'veinticinco':25,'cuarenta':40,'cincuenta':50,
         'setenta':70,'ochenta':80,'cien':100,'ciento veinte':120,'ciento cincuenta':150,'ciento ochenta':180}
PALABRAS='|'.join(sorted(NUMEROS,key=len,reverse=True))
DIAS=re.compile(r'\b(?:(?P<palabra>'+PALABRAS+r')(?:\s*\((?P<duplicado>\d{1,3})\))?|(?P<numero>\d{1,3}))\s*(?:\([^)]{1,30}\)\s*)?dias\b(?:\s+(?P<unidad>habiles|corridos|calendario))?')
INICIO=re.compile(r'\b(?:(?:forma|condiciones|plazo|modalidad|terminos)(?:s)?\s+(?:y condiciones\s+)?(?:de\s+)?pago|pagos?\s*[:\-]|el pago\b|los pagos\b|se (?:abonara|pagara|cancelara)|seran? (?:abonad[oa]s?|pagad[oa]s?)|pago\s+(?:al\s+)?contado|pago\s+contra\s+)')
LIMITE=re.compile(r'\b(?:(?:plazo|lugar|forma|condiciones)\s+(?:de\s+|para\s+(?:la\s+)?)?(?:entrega|apertura|garantia|mantenimiento de oferta|recepcion definitiva)|la entrega\s+(?:se|sera|debera)|garantia de (?:oferta|contrato)|valor del pliego|costo del pliego)\b')
EXCLUIDO=re.compile(r'^(?:(?:forma|condiciones|plazo|modalidad)(?:s)?\s+(?:de\s+)?pago|el pago|pago)\s+(?:de[l]?\s+)?(?:(?:la|el|los|las)\s+)?(?:pliegos?|sellado|sellos|tasas?|garantias?|bases|arancel(?:es)?)\b')


def norm(t):
    return re.sub(r'\s+',' ',''.join(c for c in unicodedata.normalize('NFKD',str(t or '').lower()) if not unicodedata.combining(c))).strip()


def clasificar(cita,permitir_definicion=False):
    t=norm(cita)
    t=re.split(r'en el caso de que se hubiera efectuado la adjudicacion en moneda extranjera',t)[0]
    if EXCLUIDO.search(t) or re.search(r'pago (?:al |de )?contado (?:de[l]?|por (?:la )?(?:compra|adquisicion) de[l]?) (?:los )?pliegos?',t):return None
    if re.search(r'forma de pago determinada por .*pliego de condiciones particulares',t):return None
    if not permitir_definicion and (re.search(r'^pago (?:al )?contado se entendera',t) or re.search(r'forma de pago (?:determinada|establecida|fijada|indicada) en (?:el )?pliego',t)):return None
    # Las negaciones y remisiones no se transforman en una condición positiva.
    if re.search(r'no se (?:admite|admitira|acepta|aceptara|efectuara|realizara)\b',t):return None
    if re.search(r'(?:segun|conforme a) (?:lo )?(?:establecido|indicado|dispuesto) en (?:el )?pliego',t) and not DIAS.search(t) and not re.search(r'contra entrega|contado',t):return None
    # Comprobantes fiscales/laborales exigidos al oferente no son su cobro.
    if re.search(r'^(?:el pago|los pagos) (?:de |del )?(?:las? |los? )?(?:declaraciones juradas|suss|aportes|contribuciones|seguros?|impuestos?)\b',t):return None
    plazos=[];unidades=[]
    cantidad=re.compile(r'cantidad\s*:\s*(?:(?P<palabra>'+PALABRAS+r')(?:\s*\((?P<duplicado>\d{1,3})\))?|(?P<numero>\d{1,3}))\s*unidad de tiempo\s*:\s*dias(?:\s+(?P<unidad>habiles|corridos|calendario))?')
    for m in list(DIAS.finditer(t))+list(cantidad.finditer(t)):
        n=int(m['numero'] or m['duplicado'] or NUMEROS[m['palabra']])
        # Emisión de factura, entrega y garantía no son plazos de pago.
        previo=t[max(0,m.start()-120):m.start()]
        if re.search(r'(?:factura.{0,45}(?:emitida|emitirse)|emision de factura|plazo de entrega|garantia).{0,45}$',previo):continue
        if m['palabra'] and m['duplicado'] and NUMEROS[m['palabra']]!=int(m['duplicado']):return None
        if n not in plazos:plazos.append(n)
        u=m['unidad'] or 'no indicada'
        if u not in unidades:unidades.append(u)
    if len(unidades)>1 and 'no indicada' in unidades:unidades.remove('no indicada')
    presentacion_factura=bool(re.search(r'contra (?:presentacion|entrega)(?: de)? (?:(?:la|las|su|sus) )?facturas?|presentacion de (?:(?:la|las|su|sus) )?facturas?|presentada (?:(?:la|las|su|sus) )?facturas?',t))
    recepcion_factura=bool(re.search(r'recepcion de (?:(?:la|las|su|sus) )?facturas?|recibida (?:(?:la|las|su|sus) )?facturas?|ingreso de (?:(?:la|las|su|sus) )?facturas?',t))
    fecha_factura=bool(re.search(r'(?:fecha|emision) (?:de )?(?:(?:la|las|su|sus) )?facturas?',t))
    contra_factura=bool(re.search(r'contra (?:(?:la|las|su|sus) )?facturas?',t))
    conformidad_generica=bool(re.search(r'previa conformidad|despues de (?:la )?conformidad',t))
    factura_conformada=bool(re.search(r'factura\s+(?:debidamente\s+)?conformada|conformidad de (?:(?:la|las|su|sus) )?facturas?',t))
    factura=presentacion_factura or recepcion_factura or fecha_factura or contra_factura or factura_conformada
    conformidad=bool(re.search(r'previa entrega y aceptacion|conformidad (?:de (?:la )?)?(?:recepcion|prestacion|servicio)|recepcion (?:definitiva|conforme)(?! de (?:(?:la|las|su|sus) )?facturas?)|conformada (?:la )?(?:recepcion|prestacion)',t))
    contra_entrega=bool(re.search(r'contra\s+entrega\b(?!\s+(?:de\s+)?(?:la\s+)?(?:factura|comprobante))',t))
    contado=bool(re.search(r'\b(?:al |de )?contado\b|pago inmediato',t))
    hitos=[]
    if re.search(r'tramites administrativos',t):hitos.append('TRAMITES_ADMINISTRATIVOS')
    if re.search(r'presentacion por parte del adjudicatario de la pertinente factura',t):presentacion_factura=True;factura=True
    if re.search(r'recepcion de (?:la )?(?:correspondiente )?documentacion',t):hitos.append('RECEPCION_DOCUMENTACION_CORRESPONDIENTE')
    if re.search(r'certificacion definitiva',t):hitos.append('CERTIFICACION_DEFINITIVA')
    if re.search(r'presentacion de (?:la )?facturacion',t):hitos.append('PRESENTACION_FACTURACION')
    if presentacion_factura:hitos.append('PRESENTACION_FACTURA')
    if recepcion_factura:hitos.append('RECEPCION_FACTURA')
    if fecha_factura:hitos.append('FECHA_O_EMISION_FACTURA')
    if contra_factura:hitos.append('FACTURA_REQUERIDA')
    if factura_conformada:hitos.append('CONFORMIDAD_FACTURA')
    if conformidad:hitos.append('CONFORMIDAD_RECEPCION')
    elif conformidad_generica and not factura_conformada:hitos.append('CONFORMIDAD_NO_ESPECIFICADA')
    if contra_entrega or re.search(r'desde (?:la )?entrega|de entregad|posteriores a (?:la )?fecha de entrega',t):hitos.append('ENTREGA')
    anticipo=bool(re.search(r'\b(?:anticipo(?:s)?|pago anticipado)\b',t))
    parcial=bool(re.search(r'pagos? parciales|certificados mensuales|por certificacion|en cuotas|mensual a mes vencido|liquidaciones parciales',t))
    aprobacion=bool(re.search(r'(?:aprobacion|autorizacion) (?:administrativa|del pago|de la factura)|acto administrativo',t))
    if aprobacion:hitos.append('APROBACION_ADMINISTRATIVA')
    if not(plazos or contado or contra_entrega or factura or conformidad or anticipo or parcial or aprobacion):return None
    condicion=re.search(r'(?:podra|podran|si (?:el|la)|en (?:el )?caso (?:de|del)|cuando la municipalidad requiera)\b',t)
    compromiso_previo=bool(condicion and DIAS.search(t[:condicion.start()]) and re.search(r'\b(?:abonara|pagara|sera abonado|se efectuara)\b',t[:condicion.start()]))
    if not permitir_definicion and condicion and not compromiso_previo and not re.search(r'se (?:acepta|admite)n?.*(?:o |alternativ)',t):return None
    opciones=bool(re.search(r'\b(?:o (?:a |al |contra )|alternativas? de pago|opciones de pago)',t) or re.search(r'(?:pago podra hacerse|pagos? podran? (?:hacerse|realizarse)).{0,60}(?:semanal|quincenal|mensual)',t))
    mixto=bool(re.search(r'anticipo|saldo|\d+\s*%|por ciento|cuotas|parciales|certificados mensuales',t)) and (len(plazos)>1 or contado or contra_entrega or 'saldo' in t or bool(re.search(r'anticipo.{0,30}\b(?:[1-9]|[1-9]\d)\s*(?:%|por ciento)',t)))
    if opciones:categoria='OPCIONES_PUBLICADAS'
    elif mixto:categoria='MIXTO'
    elif plazos:categoria='PLAZO_'+str(plazos[0])+'_DIAS' if len(plazos)==1 and plazos[0] in (5,7,10,15,30,45,60,90) else 'OTRO_PLAZO'
    elif anticipo:categoria='ANTICIPO'
    elif parcial:categoria='PAGOS_PARCIALES'
    elif contado:categoria='CONTADO'
    elif contra_entrega:categoria='CONTRA_ENTREGA'
    elif conformidad:categoria='DESPUES_CONFORMIDAD_RECEPCION'
    elif factura_conformada:categoria='CONTRA_FACTURA_CONFORMADA'
    elif presentacion_factura:categoria='CONTRA_PRESENTACION_FACTURA'
    elif recepcion_factura:categoria='DESPUES_RECEPCION_FACTURA'
    elif contra_factura:categoria='CONTRA_FACTURA'
    elif aprobacion:categoria='DESPUES_APROBACION_ADMINISTRATIVA'
    else:return None
    direccion='OFERTANTE_AL_ORGANISMO' if re.search(r'(?:adjudicatario|concesionario|oferente) (?:debera |debe |se obliga a )?(?:abonar|pagar)|canon (?:a cargo|que abonara) (?:del )?(?:adjudicatario|concesionario)',t) else ('ORGANISMO_AL_PROVEEDOR' if re.search(r'(?:municipalidad|municipio|organismo|contratante) (?:debera |debe )?(?:abonar|pagar)|pago al (?:proveedor|adjudicatario)',t) else 'NO_ESPECIFICADA')
    if categoria=='CONTADO':etiqueta='Pago contado contra entrega' if contra_entrega else 'Pago contado'
    elif categoria=='CONTRA_ENTREGA':etiqueta='Pago contra entrega'
    elif categoria=='CONTRA_PRESENTACION_FACTURA':etiqueta='Contra presentación de factura; plazo no indicado'
    elif categoria=='CONTRA_FACTURA_CONFORMADA':etiqueta='Contra factura conformada; plazo no indicado'
    elif categoria=='DESPUES_RECEPCION_FACTURA':etiqueta='Después de recepción de factura; plazo no indicado'
    elif categoria=='CONTRA_FACTURA':etiqueta='Contra factura; plazo no indicado'
    elif categoria=='DESPUES_CONFORMIDAD_RECEPCION':etiqueta='Después de entrega y aceptación' if 'previa entrega y aceptacion' in t else 'Después de conformidad de recepción'
    elif categoria=='ANTICIPO':etiqueta='Anticipo publicado; ver cláusula'
    elif categoria=='PAGOS_PARCIALES':etiqueta='Pagos parciales; plazo no indicado'
    elif categoria=='DESPUES_APROBACION_ADMINISTRATIVA':etiqueta='Después de aprobación administrativa; plazo no indicado'
    elif categoria in ('MIXTO','OPCIONES_PUBLICADAS'):etiqueta='Pago mixto' if categoria=='MIXTO' else 'Opciones de pago publicadas'
    else:etiqueta='/'.join(str(n) for n in plazos)+' días'+(' '+unidades[0] if len(unidades)==1 and unidades[0]!='no indicada' else '')
    if categoria=='DESPUES_CONFORMIDAD_RECEPCION':
        if presentacion_factura:etiqueta+=' y presentación de factura'
        if 'TRAMITES_ADMINISTRATIVOS' in hitos:etiqueta+='; exige trámites administrativos'
        etiqueta+='; plazo no indicado'
    if not plazos and categoria in ('CONTADO','CONTRA_ENTREGA'):
        if conformidad:etiqueta+='; exige conformidad de recepción'
        elif factura_conformada:etiqueta+=' contra factura conformada'
        elif presentacion_factura:etiqueta+=' contra presentación de factura'
        elif recepcion_factura:etiqueta+=' después de recepción de factura'
    if plazos:
        if 'RECEPCION_DOCUMENTACION_CORRESPONDIENTE' in hitos:etiqueta+=' desde recepción de la documentación correspondiente'
        if conformidad:etiqueta+=' después de conformidad de recepción'
        elif factura_conformada:etiqueta+=' desde factura conformada'
        elif presentacion_factura:etiqueta+=(' desde entrega y presentación de factura' if 'ENTREGA' in hitos else ' desde presentación de factura')
        elif recepcion_factura:etiqueta+=' desde recepción de factura'
        elif fecha_factura:etiqueta+=' desde fecha/emisión de factura'
        elif 'ENTREGA' in hitos:etiqueta+=' desde entrega'
        if aprobacion:etiqueta+='; requiere aprobación administrativa'
    if 'CONFORMIDAD_NO_ESPECIFICADA' in hitos:etiqueta+='; exige conformidad no especificada'
    if re.search(r'mensualmente.*(?:vencido|mes vencido)|a mes vencido',t):etiqueta+='; mensual a mes vencido'
    if direccion=='OFERTANTE_AL_ORGANISMO':etiqueta+=' (a cargo del adjudicatario)'
    return {'categoria':categoria,'etiqueta':etiqueta,'plazos_dias':plazos,'unidades_dias':unidades,'hitos_inicio':hitos,
            'direccion':direccion,'contado_mencionado':contado,'contra_entrega_mencionado':contra_entrega,
            'prioritario':categoria in ('ANTICIPO','CONTADO','CONTRA_ENTREGA') and direccion!='OFERTANTE_AL_ORGANISMO',
            'pagos_parciales':parcial,'anticipo_publicado':anticipo,'facturacion_parcial':bool(re.search(r'facturaci[oó]n parcial|liquidaciones parciales|certificados parciales|por mes vencido|periodo vencido',t)),'acreditacion_inmediata_comprobada':False}


def extraer(texto,url,hash_documento=None,pdf=False,metodo='TEXTO'):
    resultados=[];vistos=set();articulo_vigente=None
    for pagina,contenido in enumerate(texto.split('\f'),1):
        # Conserva párrafos para no mezclar entrega, garantías y pago de suministros.
        bloques=re.split(r'\n\s*\n',contenido)
        for indice,bloque in enumerate(bloques):
            original=re.sub(r'\s+',' ',bloque).strip();t=norm(original)
            matches=list(INICIO.finditer(t))
            fuertes=[m for m in matches if re.match(r'formas?|condiciones|plazo|modalidad|terminos',m.group()) and re.match(r'\s*(?::|[.\-]|$)',t[m.end():])]
            for m in matches:
                if fuertes and m not in fuertes:continue
                previo=t[max(0,m.start()-180):m.start()]
                if re.search(r'oferente[^.!?]{0,100}(?:consignar|indicar|proponer)[^.!?]{0,80}$',previo):continue
                if re.search(r'(?:oferta|cotizacion|precios)\s+(?:por|para|de)\s*$',previo):continue
                if re.search(r'no se (?:admite|admitira|acepta|aceptara|efectuara|realizara)[^.!?]{0,50}$',previo):continue
                if re.search(r'(?:precio|valor|costo|compra|adquisicion) de[l]? pliego[^.!?]{0,40}$',previo):continue
                siguiente=next((f.start() for f in fuertes if f.start()>m.start()),len(original))
                fragmento=original[m.start():siguiente]
                # Un encabezado aislado puede tener su cláusula en los párrafos siguientes.
                if len(fragmento)<80:
                    siguientes=[]
                    for otro in bloques[indice+1:indice+4]:
                        if LIMITE.match(norm(otro)) or (INICIO.match(norm(otro)) and clasificar(fragmento+' '+' '.join(siguientes)) is not None):break
                        siguientes.append(re.sub(r'\s+',' ',otro).strip())
                    fragmento+=' '+' '.join(siguientes)
                limite=LIMITE.search(norm(fragmento),10)
                articulo=re.search(r'\b(?:articulo|art\.)\s*\d+',norm(fragmento))
                if articulo and (not limite or articulo.start()<limite.start()):limite=articulo
                if limite:fragmento=fragmento[:limite.start()]
                # Una ventana no debe alcanzar otras secciones si el PDF perdió separadores.
                fragmento=fragmento[:1800].strip()
                clasificacion=clasificar(fragmento)
                if clasificacion is None:continue
                clave=(norm(fragmento),pagina)
                if clave in vistos:continue
                vistos.add(clave)
                prefijo=norm(contenido[:max(0,contenido.find(bloque))]+' '+original[:m.start()])
                arts=re.findall(r'\b(?:articulo|art\.)\s*(\d+)',prefijo)
                clausula='Articulo '+(arts[-1] if arts else articulo_vigente) if arts or articulo_vigente else None
                resultados.append({**clasificacion,'clausula':clausula,'cita':fragmento,'url_documento':url,'sha256':hash_documento,
                    'pagina':pagina if pdf else None,'metodo_extraccion':metodo,'version_analizador':VERSION})
        arts=re.findall(r'\b(?:articulo|art\.)\s*(\d+)',norm(contenido))
        if arts:articulo_vigente=arts[-1]
    # Una definición de contado sólo se aplica si el mismo documento selecciona contado.
    definiciones=[]
    for pagina,contenido in enumerate(texto.split('\f'),1):
        for m in re.finditer(r'(?:Por\s+)?pago\s+(?:al\s+)?Contado\s+se\s+entender[áa][^.]*\.?',contenido,re.I):
            cita=re.sub(r'\s+',' ',m.group()).strip()
            d=clasificar(cita,permitir_definicion=True)
            if d and d['plazos_dias']:definiciones.append((d,{'cita':cita,'pagina':pagina if pdf else None,'url_documento':url,'sha256':hash_documento}))
    for e in resultados:
        if e['categoria']=='CONTADO' and definiciones:
            if len({(tuple(d['plazos_dias']),tuple(d['hitos_inicio']),tuple(d['unidades_dias'])) for d,_ in definiciones})==1:
                d,ref=definiciones[0]
                e.update({k:v for k,v in d.items()});e['definicion_contado']=ref
            else:e['categoria']='CONDICION_AMBIGUA';e['prioritario']=False
    return resultados


def desconocido(motivo='SIN_CLAUSULA_COMPROBADA'):
    return {'estado':'PENDIENTE','clasificacion':'NO_INFORMADO','etiqueta':NO_INFORMADO,'plazos_dias':[],
            'hitos_inicio':[],'documento_respaldo':None,'documentos_respaldo':[],'evidencias':[],'prioritario':False,'motivo':motivo}


def consolidar(evidencias):
    # Revisar las citas guardadas sin descargar otra vez el pliego. No modificar
    # evidencias/versiones persistidas; la clasificación vigente es una vista derivada.
    genericos={(e.get('url_documento'),e.get('sha256')) for e in evidencias if re.search(r'oferente.*consignar.*pagos parciales',norm(e.get('cita')))}
    revisadas=[]
    for original in evidencias:
        e=dict(original)
        if e.get('categoria')=='PAGOS_PARCIALES' and re.search(r'en (?:el )?caso (?:de|del)\b',norm(e.get('cita'))) and clasificar(e.get('cita')) is None:continue
        if (e.get('url_documento'),e.get('sha256')) in genericos and e.get('categoria')=='PAGOS_PARCIALES' and (re.search(r'oferente.*consignar',norm(e.get('cita'))) or norm(e.get('cita')).startswith('pago: - pago total')):continue
        if e.get('version_analizador') in (5,6,7,8,9,10,11) and not e.get('definicion_contado'):
            actual=clasificar(e.get('cita'))
            if actual is None:continue
            e.update(actual);e['reclasificada_desde_version']=e['version_analizador'];e['version_analizador']=VERSION
        revisadas.append(e)
    evidencias=revisadas
    articulos={}
    for e in evidencias:
        if e.get('clausula'):articulos.setdefault((e.get('url_documento'),e.get('sha256'),e['clausula']),[]).append(e)
    for grupo in articulos.values():
        paginas={e.get('pagina') for e in grupo if e.get('pagina') is not None}
        plazos=[e for e in grupo if e.get('plazos_dias') and e.get('hitos_inicio')==['RECEPCION_DOCUMENTACION_CORRESPONDIENTE']]
        condiciones=[e for e in grupo if not e.get('plazos_dias') and e.get('categoria') in ('DESPUES_CONFORMIDAD_RECEPCION','PAGOS_PARCIALES')]
        if not paginas or max(paginas)-min(paginas)>1 or not plazos or not condiciones:continue
        if len({(tuple(e['plazos_dias']),tuple(e.get('unidades_dias',[]))) for e in plazos})!=1:continue
        if len(plazos)+len(condiciones)!=len(grupo):continue
        direcciones={e.get('direccion') for e in grupo}-{None,'NO_ESPECIFICADA'}
        if len(direcciones)>1:continue
        e=dict(plazos[0]);e['condiciones_previas']=sorted({h for c in condiciones for h in c.get('hitos_inicio',[])})
        e['evidencias_condiciones_previas']=[{k:c.get(k) for k in ('pagina','clausula','cita','url_documento','sha256')} for c in condiciones]
        e['pagos_parciales']=any(c.get('pagos_parciales') for c in condiciones)
        if direcciones:e['direccion']=next(iter(direcciones))
        e['etiqueta']+='; exige entrega aceptada, factura y trámites administrativos'
        if any('mensual a mes vencido' in norm(c.get('cita')) for c in condiciones):e['etiqueta']+='; mensual a mes vencido'
        evidencias=[v for v in evidencias if v not in grupo]+[e]
    grupos={}
    for e in evidencias:grupos.setdefault((e.get('url_documento'),e.get('sha256'),e.get('pagina')),[]).append(e)
    for grupo in grupos.values():
        con_plazo=[e for e in grupo if len(e.get('plazos_dias',[]))==1 and e.get('categoria') not in ('MIXTO','OPCIONES_PUBLICADAS')]
        sin_plazo=[e for e in grupo if not e.get('plazos_dias') and e.get('categoria')=='DESPUES_CONFORMIDAD_RECEPCION']
        if not con_plazo or not sin_plazo or len({tuple(e['plazos_dias']) for e in con_plazo})!=1:continue
        # No combinar factura a 30 días con recepción a 30 días: ambos hitos deben ser compatibles.
        hitos=[set(e.get('hitos_inicio',[])) for e in con_plazo]
        if any(h-{'CONFORMIDAD_RECEPCION','CONFORMIDAD_FACTURA'} for h in hitos):continue
        unidades={u for e in con_plazo for u in e.get('unidades_dias',[]) if u!='no indicada'}
        if len(unidades)>1:continue
        principal=max(con_plazo,key=lambda e:(len(e.get('hitos_inicio',[])),e.get('unidades_dias')!=['no indicada']))
        cita=' '.join(dict.fromkeys(e['cita'] for e in grupo))
        fusion=clasificar(cita)
        if fusion and len(fusion['plazos_dias'])==1:
            nuevo={**principal,**fusion,'cita':cita,'citas_complementarias':[e['cita'] for e in grupo],'version_analizador':VERSION}
            evidencias=[e for e in evidencias if e not in grupo]+[nuevo]
    if any(e.get('categoria')=='CONDICION_AMBIGUA' for e in evidencias):
        r=desconocido('DEFINICION_CONTADO_AMBIGUA');r['evidencias']=evidencias;return r
    unicas={}
    for e in evidencias:
        if not e.get('url_documento') or not e.get('cita') or not e.get('sha256'):continue
        llave=(e['categoria'],tuple(e['plazos_dias']),tuple(e['hitos_inicio']),tuple(e.get('unidades_dias',[])),e['direccion'])
        unicas.setdefault(llave,[]).append(e)
    if not unicas:return desconocido()
    todos=[e for lista in unicas.values() for e in lista]
    if len(unicas)>1:
        # Una omisión no contradice un dato explícito: admite sólo ampliaciones
        # compatibles de la misma categoría/plazo, sin mezclar hitos distintos.
        # Contado contra entrega y su repetición abreviada son compatibles sólo
        # cuando el MISMO documento dice expresamente ambas condiciones.
        documentos_explicitos={(e['url_documento'],e['sha256']) for e in todos if e['categoria']=='CONTADO' and e.get('contra_entrega_mencionado') and not e['plazos_dias']}
        compatibles=bool(documentos_explicitos) and all(e['categoria'] in ('CONTADO','CONTRA_ENTREGA') and not e['plazos_dias'] and (e['url_documento'],e['sha256']) in documentos_explicitos for e in todos)
        bases={(('CONTADO' if compatibles else e['categoria']),tuple(e['plazos_dias'])) for e in todos}
        unidades={u for e in todos for u in e.get('unidades_dias',[]) if u!='no indicada'}
        direcciones={e['direccion'] for e in todos if e['direccion']!='NO_ESPECIFICADA'}
        hitos=[set(e['hitos_inicio']) for e in todos]
        mayor=max(hitos,key=len)
        if len(bases)==1 and len(unidades)<=1 and len(direcciones)<=1 and all(h<=mayor for h in hitos):
            principal=max(todos,key=lambda e:(e['categoria']=='CONTADO' if compatibles else False,len(e['hitos_inicio']),e.get('unidades_dias')!=['no indicada'],e['direccion']!='NO_ESPECIFICADA'))
            e=dict(principal)
            if unidades:e['unidades_dias']=sorted(unidades)
            if direcciones:e['direccion']=next(iter(direcciones))
            if unidades and e['plazos_dias'] and not re.search(r'dias (?:habiles|corridos|calendario)',norm(e['etiqueta'])):e['etiqueta']=e['etiqueta'].replace('días','días '+next(iter(unidades)).replace('habiles','hábiles'),1)
            if e['direccion']=='OFERTANTE_AL_ORGANISMO' and 'a cargo del adjudicatario' not in e['etiqueta']:e['etiqueta']+=' (a cargo del adjudicatario)'
            e['prioritario']=e['categoria'] in ('CONTADO','CONTRA_ENTREGA') and e['direccion']!='OFERTANTE_AL_ORGANISMO'
            unicas={next(iter(unicas)):[e]}
        else:
            r=desconocido('CONDICIONES_DIFERENTES_REQUIEREN_REVISION');r['evidencias']=todos;return r
    e=next(iter(unicas.values()))[0]
    return {'estado':'VERIFICADO','clasificacion':e['categoria'],'etiqueta':e['etiqueta'],'plazos_dias':e['plazos_dias'],
            'hitos_inicio':e['hitos_inicio'],'unidades_dias':e['unidades_dias'],'direccion':e['direccion'],
            'documento_respaldo':e['url_documento'],'documentos_respaldo':list(dict.fromkeys(e['url_documento'] for e in todos)),'evidencias':todos,'prioritario':e['prioritario'],'motivo':None}


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


def grupo_comercial(pago):
    if pago.get('estado')!='VERIFICADO' or pago.get('direccion')=='OFERTANTE_AL_ORGANISMO':return 8
    categoria=pago.get('clasificacion')
    if categoria=='ANTICIPO':return 0
    if categoria in ('CONTADO','CONTRA_ENTREGA'):return 1
    if categoria in ('MIXTO','OPCIONES_PUBLICADAS'):return 8
    dias=max(pago.get('plazos_dias') or [999])
    return 2 if dias<=5 else 3 if dias<=10 else 4 if dias<=15 else 5 if dias<=30 else 6 if dias<=60 else 7 if dias<999 else 8


def requiere_investigacion(pago):
    if pago.get('estado')!='VERIFICADO':return True
    if pago.get('clasificacion') in ('MIXTO','OPCIONES_PUBLICADAS'):return True
    if pago.get('plazos_dias'):return not bool(pago.get('hitos_inicio'))
    return pago.get('clasificacion') not in ('CONTADO','CONTRA_ENTREGA','ANTICIPO')
