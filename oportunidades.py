"""Normalización conservadora y reporte comercial: cada dato requiere evidencia."""
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from zoneinfo import ZoneInfo
from urllib.parse import urlsplit
import re
import unicodedata
import pagos

ZONA=ZoneInfo('America/Argentina/Buenos_Aires')
MESES={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'setiembre':9,'octubre':10,'noviembre':11,'diciembre':12}

def norm(t):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(t or '').lower()) if not unicodedata.combining(c)).split())

def fecha(texto):
    t=norm(texto)
    m=re.search(r'\b(20\d{2})-(\d{2})-(\d{2})(?=t|\b)',t)
    if m:y,mo,d=map(int,m.groups())
    else:
        m=re.search(r'\b(\d{1,2})[/.\-](\d{1,2})[/.\-](20\d{2})\b',t)
        if m:d,mo,y=map(int,m.groups())
        else:
            m=re.search(r'\b(\d{1,2})\s+(?:de\s+)?('+'|'.join(MESES)+r')\s+(?:de\s+(?:l?ano\s+)?|del\s+ano\s+)?(20\d{2})\b',t)
            if not m:return None
            d,mo,y=int(m[1]),MESES[m[2]],int(m[3])
    try:return date(y,mo,d).isoformat()
    except ValueError:return None

def monto(t):
    # Solo cifras explícitamente etiquetadas como presupuesto; no valor del pliego.
    m=re.search(r'presupuesto(?:\s+(?:oficial|estimado|total|base))?\s*[:\-]?\s*(?:(ARS|USD|U\$S|\$)\s*)?([\d][\d.,]*)',t,re.I)
    if not m:return None,None
    raw=m[2].rstrip('.,')
    if ',' in raw:
        entero,decimales=raw.split(',',1)
        if '.' in entero and not re.fullmatch(r'\d{1,3}(?:\.\d{3})+',entero):return None,None
        if not re.fullmatch(r'\d{1,2}',decimales):return None,None
        raw=entero.replace('.','')+'.'+decimales
    elif re.fullmatch(r'\d{1,3}(?:\.\d{3})+',raw):raw=raw.replace('.','')
    try:v=str(Decimal(raw))
    except InvalidOperation:return None,None
    moneda=(m[1] or '').upper()
    return {'importe':v,'moneda':'USD' if moneda in ('USD','U$S') else ('ARS' if moneda=='ARS' else None)},m.group(0)

def normalizar(r,ahora=None):
    ahora=ahora or datetime.now(ZONA)
    if isinstance(ahora,str):ahora=datetime.fromisoformat(ahora)
    hoy=ahora.astimezone(ZONA).date() if ahora.tzinfo else ahora.date()
    r=dict(r);texto=str(r.get('texto_documento') or r.get('objeto') or r.get('titulo') or '')
    texto_titulo=str(r.get('titulo') or '')
    t=norm(texto);ev=dict(r.get('evidencias_campos') or {})
    origen=r.get('evidencia_url') or r.get('url')
    if (urlsplit(origen or '').hostname in ('www.aguassantafesinas.com.ar','aguassantafesinas.com.ar')
        and r.get('registro_estructurado') and r.get('campos_oficiales',{}).get('localidades')==[]):
        # La sede del organismo y la oficina de apertura no acreditan el lugar
        # de la prestación. El API no publica localidades para estas fichas.
        r['localidad']=None
        ev['localidad']={'url':origen,'texto':'API: localidades=[]; localidad del procedimiento desconocida'}
    def dato(campo,valor,fragmento):
        if valor is not None:
            r[campo]=valor;ev[campo]={'url':origen,'texto':fragmento}
        else:r.setdefault(campo,None)
    import extractores
    ps=extractores.procesos(r.get('procedimiento') or r.get('titulo') or '')
    numero_rotulado=extractores.procesos(r.get('numero_procedimiento') or '')
    if len(numero_rotulado)==1:r['numero_procedimiento']=numero_rotulado[0]['numero']
    dato('numero_procedimiento',r.get('numero_procedimiento') or (ps[0]['numero'] if ps else None),r.get('procedimiento'))
    if r.get('numero_procedimiento'):r['numero_procedimiento']=re.sub(r'^(\d+)[–-](20\d{2})$',r'\1/\2',r['numero_procedimiento'])
    dato('tipo_procedimiento',r.get('tipo_procedimiento') or (ps[0]['tipo'] if ps else None),r.get('procedimiento'))
    if r.get('tipo_procedimiento')=='licitacion':
        tipos={p['tipo'] for p in extractores.procesos(texto_titulo+' '+texto) if p['numero']==r.get('numero_procedimiento') and p['tipo']!='licitacion'}
        if len(tipos)==1:
            r['tipo_procedimiento']=next(iter(tipos));ev['tipo_procedimiento']={'url':origen,'texto':'Tipo explícito del mismo número en el documento: '+r['tipo_procedimiento']}
    if re.match(r'^\s*circular\s+(?:aclaratoria|modificatoria)',norm(texto_titulo)):r['tipo_documento']='CIRCULAR_ACLARATORIA'

    for campo,patron in [('fecha_apertura',r'(?:(?:fecha\s+(?:de\s+)?)?apertura(?:\s+(?:de\s+)?(?:ofertas|sobres))?|llamese a licitacion (?:publica|privada) para el dia)\s*[:\-]?\s*(.{0,90})'),('fecha_limite_presentacion',r'(?:fecha\s+limite(?:\s+de\s+presentacion)?|limite\s+(?:de|para)\s+(?:la\s+)?(?:presentacion|recepcion)(?:\s+de\s+(?:ofertas|sobres))?|(?:presentacion|recepcion)\s+de\s+(?:ofertas|sobres)\s+hasta|presentacion\s*:\s*hasta)\s*[:\-]?\s*(.{0,90})'),('fecha_publicacion',r'(?:fecha\s+(?:de\s+)?publicacion|publicad[oa](?:\s+el)?)\s*[:\-]?\s*(.{0,70})')]:
        dedicado=r.get(campo+'_texto')
        candidatos=[dedicado] if dedicado else [m[1] for contenido in (t,norm(texto_titulo)) for m in re.finditer(r"(?="+patron+r")",contenido)]
        raw='';valor=None
        for candidato in candidatos:
            fragmento=re.split(r'presupuesto|publicacion|apertura|adjudicacion|presentacion|recepcion',norm(candidato))[0]
            f=fecha(fragmento)
            if f:
                raw=fragmento;valor=f;break
        dato(campo,valor,raw)
    if r.get('presupuesto') is None:
        valor,frag=monto('presupuesto oficial '+r['presupuesto_texto'] if r.get('presupuesto_texto') else t)
        if valor is None:valor,frag=monto(norm(texto_titulo))
        dato('presupuesto',valor,frag)
    else:r.setdefault('presupuesto',None)
    r['pago']=pagos.consolidar(r.get('pago_evidencias',[]))
    if r['pago']['estado']!='VERIFICADO' and r['pago'].get('motivo') in (None,'SIN_CLAUSULA_COMPROBADA') and r.get('pago_motivo_pendiente'):r['pago']['motivo']=r['pago_motivo_pendiente']
    r['condiciones_pago']=r['pago']['etiqueta']
    r['enlace_condiciones_pago']=r['pago']['documento_respaldo']
    r['pago_prioritario']=r['pago']['prioritario']
    r['desierta']='desiert' in t
    r['fracasada']=r.get('situacion_publicada')=='FRACASADA' or extractores.situacion(texto_titulo)=='FRACASADA'
    senales=t+' '+norm(texto_titulo)+' '+norm(r.get('evento_publicado'))
    r['segundo_llamado']=bool(re.search(r'segund[oa] (?:llamado|convocatoria)|2(?:do|º|°) llamado|llamado 2\b',senales))
    r['reapertura']='reapertura' in senales
    r['llamado_especial']=bool(r.get('llamado_especial') or r['desierta'] or r['fracasada'] or r['segundo_llamado'] or r['reapertura'])
    cerrada=r.get('situacion_publicada') in ('ADJUDICADA','FINALIZADA','EN_EVALUACION','DESIERTA','FRACASADA','SUSPENDIDA','CANCELADA')
    if r.get('situacion_publicada') in ('DESIERTA','FRACASADA') and (r['segundo_llamado'] or r['reapertura']):
        # Mencionar el llamado anterior desierto no prueba cierre de la reapertura.
        cerrada=False
    r['procedimiento_canonico']=procedimiento_canonico(r)
    r['convocatoria']=convocatoria(r)
    es_real=bool(r['procedimiento_canonico'] or r.get('registro_estructurado') or (ps and len(ps)==1 and re.fullmatch(r'\d{1,6}',ps[0]['numero']) and r.get('url','').lower().endswith(('.pdf','.docx'))))
    if (urlsplit(r.get('fuente') or r.get('evidencia_url') or '').hostname in ('www.rosario.gob.ar','rosario.gob.ar')
        and norm(r.get('objeto') or r.get('titulo')).count('publicada para apertura')>1):
        es_real=False;r['motivo_no_verificado']='CONTENEDOR_DE_MULTIPLES_PROCEDIMIENTOS'
    r['clasificacion_registro']='PROCEDIMIENTO' if es_real else 'CANDIDATO_NO_VERIFICADO'
    apertura=r.get('fecha_apertura')
    raw_apertura=r.get('fecha_apertura_texto') or ev.get('fecha_apertura',{}).get('texto') or ''
    hora=re.search(r'(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*(?:hs|h|horas))?',raw_apertura)
    r['hora_apertura']=f'{int(hora[1]):02d}:{hora[2]}' if hora else r.get('hora_apertura')
    r['fecha_hora_apertura']=datetime.fromisoformat(apertura+'T'+r['hora_apertura']).replace(tzinfo=ZONA).isoformat() if apertura and r.get('hora_apertura') else None
    r['vigencia']='VENCIDA' if cerrada or (apertura and apertura<hoy.isoformat()) else ('ABIERTA' if apertura and apertura>hoy.isoformat() else 'DESCONOCIDA')
    if r['fecha_hora_apertura']:
        limite=datetime.fromisoformat(r['fecha_hora_apertura'])
        consulta=ahora.replace(tzinfo=ZONA) if not ahora.tzinfo else ahora
        r['vigencia']='VENCIDA' if cerrada or limite<=consulta else 'ABIERTA'
    limite_presentacion=r.get('fecha_limite_presentacion')
    raw_limite=r.get('fecha_limite_presentacion_texto') or ev.get('fecha_limite_presentacion',{}).get('texto') or ''
    h_limite=re.search(r'(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*(?:hs|h|horas))?',raw_limite)
    r['hora_limite_presentacion']=f'{int(h_limite[1]):02d}:{h_limite[2]}' if h_limite else r.get('hora_limite_presentacion')
    r['fecha_hora_limite_presentacion']=datetime.fromisoformat(limite_presentacion+'T'+r['hora_limite_presentacion']).replace(tzinfo=ZONA).isoformat() if limite_presentacion and r.get('hora_limite_presentacion') else None
    if limite_presentacion:
        # Un cierre anterior a la apertura impide presentar ofertas aunque aún no se abran.
        consulta=ahora.replace(tzinfo=ZONA) if not ahora.tzinfo else ahora
        if cerrada or limite_presentacion<hoy.isoformat() or (r['fecha_hora_limite_presentacion'] and datetime.fromisoformat(r['fecha_hora_limite_presentacion'])<=consulta):r['vigencia']='VENCIDA'
        elif limite_presentacion==hoy.isoformat() and not r['hora_limite_presentacion']:r['vigencia']='DESCONOCIDA'
        elif r['vigencia']!='VENCIDA':r['vigencia']='ABIERTA'
    r['fecha_referencia_vencimiento']=limite_presentacion or apertura
    r['tipo_fecha_vencimiento']='LIMITE_PRESENTACION' if limite_presentacion else ('APERTURA_REFERENCIAL' if apertura else 'DESCONOCIDA')
    modos=[]
    if re.search(r'(?:presentacion|presentar|recepcion|remitir|enviar)\b.{0,100}\b(?:online|en linea|plataforma|portal web)',t):modos.append('ONLINE')
    if re.search(r'(?:presentacion|presentar|recepcion|remitir|enviar)\b.{0,100}\b(?:correo electronic[oa]|e-mail|email)',t):modos.append('CORREO_ELECTRONICO')
    if re.search(r'(?:presentacion|presentar|recepcion|entregar)\b.{0,100}\b(?:presencial|mesa de entradas|sobre cerrado)',t):modos.append('PRESENCIAL')
    if modos:
        r['modalidad_presentacion']=modos
        ev['modalidad_presentacion']={'url':origen,'texto':texto}
    else:r.setdefault('modalidad_presentacion',[])
    if not es_real:r['vigencia']='DESCONOCIDA'
    r['motivo_vigencia']='SIN_PROCEDIMIENTO_VERIFICADO' if not es_real else ('SITUACION_CERRADA' if cerrada else ('APERTURA_FUTURA' if r['vigencia']=='ABIERTA' else ('APERTURA_VENCIDA' if r['vigencia']=='VENCIDA' else 'FECHA_U_HORA_INSUFICIENTE')))
    if limite_presentacion and es_real and not cerrada:r['motivo_vigencia']='LIMITE_PRESENTACION_'+r['vigencia']
    # Con día de apertura igual a hoy sin hora verificada no se asegura que siga abierta.
    if r.get('fechas_apertura_contradictorias'):
        r['fecha_apertura']=None;r['hora_apertura']=None;r['fecha_hora_apertura']=None
        r['fecha_referencia_vencimiento']=r.get('fecha_limite_presentacion')
        r['tipo_fecha_vencimiento']='LIMITE_PRESENTACION' if r.get('fecha_limite_presentacion') else 'DESCONOCIDA'
        r['vigencia']='VENCIDA' if cerrada or (r.get('fecha_limite_presentacion') and r['fecha_limite_presentacion']<hoy.isoformat()) else 'DESCONOCIDA'
        r['motivo_vigencia']='FECHAS_DE_APERTURA_CONTRADICTORIAS_EN_DOCUMENTO_OFICIAL'
    r['antiguedad_publicacion']='HISTORICA' if (r.get('fecha_publicacion') and r['fecha_publicacion']<hoy.isoformat()) or r['vigencia']=='VENCIDA' else 'DESCONOCIDA'
    r['estimacion_comercial']=None
    r['motivo_sin_estimacion']='No hay costos propios, cantidades y precio de venta comprobables para estimar margen'
    r['evidencias_campos']=ev
    # Solo llamar pliego al enlace identificado como tal: otros adjuntos quedan en documentos.
    r['enlace_pliego']=r.get('enlace_pliego') if r.get('comprobacion_pliego',{}).get('estado')=='DOCUMENTO_ACCESIBLE' and r.get('enlace_pliego') in {d['url'] for d in r.get('documentos',[])} else next((d['url'] for d in r.get('documentos',[]) if 'pliego' in norm(d.get('titulo')) or 'pliego' in norm(d['url'].split('/')[-1])),None)
    for k in ('organismo','localidad','provincia','objeto','fecha_publicacion','fecha_apertura','presupuesto'):r.setdefault(k,None)
    objeto=r.get('objeto') or ''
    especifico=re.search(r'\b(?:asunto\s*:?|objeto\s*:)\s*(.+?)(?=\s+(?:expediente|presupuesto oficial|fecha (?:y hora )?de apertura|consultas|descargas)\b|$)',objeto,re.I)
    if especifico:r['objeto']=especifico[1].strip()
    if r.get('detalle_completo') is False:r['objeto']=None
    r['campos_desconocidos']=[k for k in ('numero_procedimiento','organismo','localidad','provincia','objeto','presupuesto','fecha_apertura','fecha_publicacion','enlace_pliego') if not r.get(k)]
    return r

def prioridad(r):
    p=r.get('pago',{})
    grupo=pagos.grupo_comercial(p)
    presupuesto=r.get('presupuesto') if isinstance(r.get('presupuesto'),dict) else {}
    try:importe=Decimal(presupuesto.get('importe') or '0')
    except (InvalidOperation,AttributeError):importe=Decimal(0)
    # Monedas diferentes se agrupan; no se convierten ni se estima rentabilidad.
    return (grupo,not r.get('llamado_especial',False),not bool(presupuesto),presupuesto.get('moneda') or '',-importe,
            r.get('fecha_hora_limite_presentacion') or r.get('fecha_limite_presentacion') or r.get('fecha_hora_apertura') or r.get('fecha_apertura') or '9999',r.get('titulo',''))


def incorporar(historial,registros,ahora,desde=None):
    """Índice derivado: no elimina ni reescribe entradas antiguas."""
    nuevas=[];indice={identidad(normalizar(v,ahora)):k for k,v in historial.items() if isinstance(v,dict)}
    for raw in deduplicar(registros,ahora):
        r=normalizar(raw,ahora);key=identidad(r)
        if r.get('clasificacion_registro')!='PROCEDIMIENTO':continue
        viejo=indice.get(key)
        if viejo is None:
            # Compatibilidad con IDs previos y URL de ficha, sin colisionar listados.
            viejo=next((k for k in (r.get('id'),r.get('url')) if k in historial and norm(historial[k].get('titulo'))==norm(r.get('titulo'))),None)
        if viejo is None:
            r.update(primera_deteccion=ahora,ultima_deteccion=ahora,novedad='NUEVA_DETECCION')
            publicada=r.get('fecha_publicacion');hoy=fecha(str(ahora));inicio=fecha(str(desde)) if desde else None
            r['clasificacion_novedad']=('PUBLICACION_NUEVA_COMPROBADA' if publicada and inicio and inicio<publicada<=hoy else 'PUBLICACION_EN_DIA_DE_CORRIDA_ANTERIOR' if publicada and inicio and publicada==inicio else 'PUBLICACION_HISTORICA_RECUPERADA' if publicada and publicada<hoy else 'FECHA_PUBLICACION_DESCONOCIDA' if not publicada else 'PUBLICACION_CONOCIDA_SIN_VENTANA_PREVIA')
            historial[key]=r;indice[key]=key;nuevas.append(r)
        # Datos enriquecidos se reportan aparte: el registro legado permanece idéntico.
    return sorted(nuevas,key=prioridad)

def reporte(registros,fecha_reporte):
    def celda(texto):return str(texto or '').replace('|','/').replace('\n',' ')
    def presupuesto(valor):
        if isinstance(valor,dict):return str(valor.get('importe') or 'desconocido')+' '+(valor.get('moneda') or '(moneda no informada)')
        return valor or 'desconocido'
    lineas=['# Oportunidades detectadas — '+fecha_reporte,'',
        'Primera detección no significa publicación reciente. Se incluyen todas las novedades válidas, también vencidas y de vigencia desconocida. Orden: anticipos; contado/contra entrega; plazos comprobados de 5, 10, 15, 30, 60 y más días; señales de desiertas, segundos llamados y reaperturas; presupuesto por moneda; límite de presentación o apertura referencial. Sin filtros comerciales ni límite de cantidad. Pendiente de verificar indica investigación documental pendiente; no es una evaluación de rentabilidad.','',
        '| Organismo / procedimiento | Localidad / provincia | Objeto | Presupuesto oficial | Vigencia / apertura | Fecha de publicación | Límite de presentación | Presentación | Pliego | Condiciones de pago | Documento de respaldo | Señales | Publicación oficial | Novedad |',
        '|---|---|---|---|---|---|---|---|---|---|---|---|---|---|']
    ordenadas=sorted(registros,key=prioridad)
    for r in ordenadas:
        url=r.get('enlace_condiciones_pago');enlaces=r.get('pago',{}).get('documentos_respaldo') or ([url] if url else [])
        respaldo=' '.join(f'[Documento {i}]({u})' for i,u in enumerate(enlaces,1)) if enlaces else 'No comprobado'
        flags=', '.join(nombre for clave,nombre in [('desierta','Desierta'),('fracasada','Fracasada'),('segundo_llamado','Segundo llamado'),('reapertura','Reapertura')] if r.get(clave)) or '—'
        fuente=r.get('evidencia_url') or r.get('url')
        lineas.append('| '+ ' | '.join([celda((r.get('organismo') or 'desconocido')+' / '+(r.get('numero_procedimiento') or 'sin número')),celda((r.get('localidad') or 'desconocida')+' / '+(r.get('provincia') or 'desconocida')),celda(r.get('objeto') or r.get('titulo')),celda(presupuesto(r.get('presupuesto'))),celda((r.get('estado_vigencia') or r.get('vigencia') or 'DESCONOCIDA')+' / '+(r.get('fecha_hora_apertura') or r.get('fecha_apertura') or 'desconocida')),celda(r.get('fecha_publicacion') or 'desconocida'),celda(r.get('fecha_hora_limite_presentacion') or r.get('fecha_limite_presentacion') or 'desconocido'),celda(', '.join(r.get('modalidad_presentacion') or []) or 'No informada'),f"[Pliego]({r['enlace_pliego']})" if r.get('enlace_pliego') else 'No identificado',celda(r.get('condiciones_pago') or pagos.NO_INFORMADO),respaldo,flags,f'[Oficial]({fuente})',celda(r.get('clasificacion_novedad') or 'Sin comparación con corrida anterior')])+' |')
    lineas+=['','## Evidencia de las condiciones de pago','']
    for r in ordenadas:
        p=r.get('pago',{})
        if not p.get('evidencias'):continue
        lineas+=['### '+celda(r.get('titulo') or r.get('numero_procedimiento')),'',p.get('etiqueta',pagos.NO_INFORMADO),'']
        for e in p['evidencias']:
            pagina=' · página '+str(e['pagina']) if e.get('pagina') else ''
            lineas+=[f"- [Documento]({e['url_documento']}){pagina}: {celda(e['cita'])}",'']
            if e.get('definicion_contado'):
                d=e['definicion_contado'];lineas += [f"- Definición expresa del mismo documento, página {d.get('pagina') or 'no indicada'}: {celda(d['cita'])}",'']
    return '\n'.join(lineas)


def procedimiento_canonico(r):
    """Conserva la serie administrativa del código; resuelve abreviaturas con evidencia."""
    tipos={'LPU':'licitacion publica','LPR':'licitacion privada','CPRV':'concurso privado de precios','CD':'contratacion directa'}
    patron=r'\b(LPU|LPR|CPRV|CD)[-\s]+(20\d{2})-(\d{1,8})(?:-[A-Za-z][A-Za-z0-9]*)*\b'
    def codigos(texto):
        texto=re.sub(r'\s*-\s*','-',str(texto or ''))
        return list(re.finditer(patron,texto,re.I))
    def clave(m):
        original=m.group().upper();sufijo=original.split('-',3)[3] if len(original.split('-',3))>3 else ''
        return tipos[m[1].upper()]+' '+m[1].upper()+'-'+m[2]+'-'+str(int(m[3]))+('-'+sufijo if sufijo else '')
    numero=str(r.get('numero_procedimiento') or r.get('procedimiento') or '')
    originales=codigos(numero)
    if originales and len(originales[0].group().split('-'))>3:return clave(originales[0])
    corto=re.fullmatch(r'(LPU|LPR|CPRV|CD)\s+n[º°o.]*\s*(\d+)',numero,re.I)
    prefijo=originales[0][1].upper() if originales else (corto[1].upper() if corto else None)
    serial=int(originales[0][3]) if originales else (int(corto[2]) if corto else None)
    anio=originales[0][2] if originales else None
    tipo=norm(r.get('tipo_procedimiento'))
    anual=re.fullmatch(r'\s*0*(\d+)\s*[/–-]\s*(\d{2}|20\d{2})\s*',numero)
    if anual and not prefijo:
        serial=int(anual[1]);anio=str(int(anual[2])+2000 if int(anual[2])<70 else int(anual[2]))
        prefijo=next((p for p,t in tipos.items() if t==tipo),None)
    candidatos={}
    if prefijo and serial is not None:
        textos=[r.get('campos_oficiales',{}).get('numero'),r.get('url')]
        textos += [str(d.get('titulo') or '')+' '+d['url'] for d in r.get('documentos',[])]
        for texto in textos:
            for m in codigos(texto):
                if m[1].upper()==prefijo and int(m[3])==serial and (not anio or m[2]==anio) and len(m.group().split('-'))>3:candidatos[clave(m)]=m
        if len(candidatos)==1:return next(iter(candidatos))
    if originales:return clave(originales[0])
    if not anual:
        from urllib.parse import urlsplit
        # Numeración pública correlativa de ASSA; la convocatoria se vincula al UUID publicado.
        host_api=urlsplit(r.get('evidencia_url') or '').hostname
        if host_api in ('www.aguassantafesinas.com.ar','aguassantafesinas.com.ar') and r.get('registro_estructurado') and re.fullmatch(r'[a-f0-9]{32}',str(r.get('id_origen') or '')) and re.fullmatch(r'\d+',numero):
            return tipo+' ASSA-'+numero
        # Numeración propia de EPE, acreditada por ficha con objeto dedicado.
        # No relajar la detección de teléfonos/números sueltos en otros portales.
        host=urlsplit(r.get('evidencia_url') or '').hostname
        if (host in ('www.epe.santafe.gov.ar','epe.santafe.gov.ar')
                and r.get('registro_estructurado') and re.fullmatch(r'\d{10}',numero)
                and tipo in ('licitacion publica','licitacion privada','concurso privado','compra menor','compra directa','contratacion directa')):
            return tipo+' '+numero
        return None
    if not tipo:
        import extractores
        ps=extractores.procesos(r.get('procedimiento') or r.get('titulo') or '')
        tipo=ps[0]['tipo'] if ps else ''
    return tipo+' '+str(int(anual[1]))+'/'+str(anio)


def convocatoria(r):
    # Desierta/adjudicada son situaciones, no números de convocatoria.
    explicita=r.get('numero_convocatoria')
    if explicita is not None:return str(explicita)
    t=norm(r.get('evento_publicado'))+' '+norm(r.get('titulo'))
    m=re.search(r'(?:llamado|convocatoria)\s*(\d+)\b',t)
    if m:return str(int(m[1]))
    if re.search(r'\bsegund[oa] (?:llamado|convocatoria)\b|2(?:do|º|°|o) llamado',t):return '2'
    if re.search(r'\btercer(?:o|a)? (?:llamado|convocatoria)\b|3(?:er|º|°|o) llamado',t):return '3'
    if 'reapertura' in t:return 'reapertura'
    if norm(r.get('evento_publicado')).isdigit():return str(int(norm(r['evento_publicado'])))
    return '1'


def identidad(r):
    proc=procedimiento_canonico(r)
    org=norm(r.get('organismo'))
    if proc:
        partes=[norm(r.get('provincia')),org or r.get('fuente',''),proc,convocatoria(r),r.get('identidad_ambito','')]
    elif r.get('registro_estructurado') and r.get('numero_oficial_sin_interpretar') and r.get('evidencia_url'):
        # Dos accesos al mismo registro API: igualdad literal comprobada sin inventar número.
        partes=[norm(r.get('provincia')),org,r['evidencia_url'],str(r['numero_oficial_sin_interpretar']),norm(r.get('titulo')),convocatoria(r)]
    else:
        partes=[r.get('fuente',''),r.get('id') or r.get('url',''),norm(r.get('titulo'))]
    return sha256('|'.join(partes).encode()).hexdigest()


def fusionar(a,b,ahora=None):
    """Completa campos, une evidencia; nunca selecciona una ficha por longitud de título."""
    if not a:return normalizar(b,ahora)
    a=normalizar(a,ahora);b=normalizar(b,ahora)
    calidad=lambda r:(r.get('rango_evidencia',0),-len(r.get('campos_desconocidos',[])),bool(r.get('texto_documento')),bool(r.get('detalle_completo')))
    principal,otro=(b,a) if calidad(b)>calidad(a) else (a,b)
    salida=dict(principal)
    if principal.get('tipo_documento')=='CIRCULAR_ACLARATORIA' and otro.get('tipo_documento')!='CIRCULAR_ACLARATORIA' and otro.get('objeto'):
        salida['objeto']=otro['objeto'];salida['titulo']=otro.get('titulo') or salida.get('titulo');salida['tipo_documento']='CONVOCATORIA_CON_CIRCULARES'
    for k,v in otro.items():
        if salida.get(k) is None or salida.get(k)=='' or salida.get(k)==[]:salida[k]=v
    salida['pago_evidencias']=pagos.unir_evidencias(a.get('pago_evidencias'),b.get('pago_evidencias'))
    salida['documentos']=list({d['url']:d for d in a.get('documentos',[])+b.get('documentos',[])}.values())
    salida['fuentes_observadas']=sorted({u for r in (a,b) for u in r.get('fuentes_observadas',[])+[r.get('fuente')] if u})
    salida['urls_publicacion']=sorted({u for r in (a,b) for u in r.get('urls_publicacion',[])+[r.get('url'),r.get('evidencia_url')] if u})
    salida['evidencias_campos']={**otro.get('evidencias_campos',{}),**principal.get('evidencias_campos',{})}
    salida['detalle_completo']=bool(a.get('detalle_completo') or b.get('detalle_completo'))
    salida['clasificacion_registro']='PROCEDIMIENTO' if 'PROCEDIMIENTO' in (a.get('clasificacion_registro'),b.get('clasificacion_registro')) else principal.get('clasificacion_registro')
    return normalizar(salida,ahora)


def deduplicar(registros,ahora):
    salida={}
    for r in registros:
        r=normalizar(r,ahora);k=identidad(r)
        salida[k]=fusionar(salida.get(k),r,ahora)
    return list(salida.values())


def separar_vigencia(registros,ahora,dias=7):
    if isinstance(ahora,str):ahora=datetime.fromisoformat(ahora)
    hoy=ahora.astimezone(ZONA).date() if ahora.tzinfo else ahora.date()
    abiertas=sorted([r for r in registros if r.get('vigencia')=='ABIERTA' and r.get('clasificacion_registro')=='PROCEDIMIENTO'],key=lambda r:(r.get('fecha_referencia_vencimiento') or r.get('fecha_apertura') or '9999',r.get('titulo') or ''))
    proximas=[r for r in abiertas if 0<=(date.fromisoformat(r.get('fecha_referencia_vencimiento') or r['fecha_apertura'])-hoy).days<=dias]
    return {'abiertas':abiertas,'proximas_a_vencer':proximas,'dias_proximas':dias,'criterio':'Límite de presentación explícito; en su ausencia apertura referencial. Próximas: hasta 7 días calendario inclusive. Sin hora, el día de apertura queda desconocido.'}


def guardar_vistas(registros,ahora,directorio,prefijo='oportunidades'):
    import json
    from pathlib import Path
    d=Path(directorio);d.mkdir(parents=True,exist_ok=True)
    vistas=separar_vigencia(registros,ahora)
    for nombre in ('abiertas','proximas_a_vencer'):
        (d/f'{prefijo}_{nombre}.json').write_text(json.dumps({'fecha':ahora,'criterio':vistas['criterio'],'total':len(vistas[nombre]),'oportunidades':vistas[nombre]},ensure_ascii=False,indent=2),encoding='utf-8')
        (d/f'{prefijo}_{nombre}.md').write_text(reporte(vistas[nombre],ahora),encoding='utf-8')
    return vistas
