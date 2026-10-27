"""Normalización conservadora y reporte comercial: cada dato requiere evidencia."""
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from hashlib import sha256
from zoneinfo import ZoneInfo
import re
import unicodedata

ZONA=ZoneInfo('America/Argentina/Buenos_Aires')
MESES={'enero':1,'febrero':2,'marzo':3,'abril':4,'mayo':5,'junio':6,'julio':7,'agosto':8,'septiembre':9,'setiembre':9,'octubre':10,'noviembre':11,'diciembre':12}

def norm(t):
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD',str(t or '').lower()) if not unicodedata.combining(c)).split())

def fecha(texto):
    t=norm(texto)
    m=re.search(r'\b(20\d{2})-(\d{2})-(\d{2})\b',t)
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
    def dato(campo,valor,fragmento):
        if valor is not None:
            r[campo]=valor;ev[campo]={'url':origen,'texto':fragmento}
        else:r.setdefault(campo,None)
    import extractores
    ps=extractores.procesos(r.get('procedimiento') or r.get('titulo') or '')
    dato('numero_procedimiento',r.get('numero_procedimiento') or (ps[0]['numero'] if ps else None),r.get('procedimiento'))
    if r.get('numero_procedimiento'):r['numero_procedimiento']=re.sub(r'^(\d+)[–-](20\d{2})$',r'\1/\2',r['numero_procedimiento'])
    dato('tipo_procedimiento',r.get('tipo_procedimiento') or (ps[0]['tipo'] if ps else None),r.get('procedimiento'))
    for campo,patron in [('fecha_apertura',r'(?:(?:fecha\s+(?:de\s+)?)?apertura(?:\s+(?:de\s+)?(?:ofertas|sobres))?|llamese a licitacion (?:publica|privada) para el dia)\s*[:\-]?\s*(.{0,90})'),('fecha_publicacion',r'(?:fecha\s+(?:de\s+)publicacion|publicad[oa](?:\s+el)?)\s*[:\-]?\s*(.{0,70})')]:
        dedicado=r.get(campo+'_texto')
        m=re.search(patron,t) or re.search(patron,norm(texto_titulo))
        raw=dedicado or (m[1] if m else '')
        # No tomar una fecha de otro campo cuando la etiqueta está vacía.
        raw=re.split(r'presupuesto|publicacion|apertura|adjudicacion',norm(raw))[0]
        dato(campo,fecha(raw),raw)
    if r.get('presupuesto') is None:
        valor,frag=monto('presupuesto oficial '+r['presupuesto_texto'] if r.get('presupuesto_texto') else t)
        if valor is None:valor,frag=monto(norm(texto_titulo))
        dato('presupuesto',valor,frag)
    else:r.setdefault('presupuesto',None)
    pago=re.search(r'pago (?:al )?contado|contra entrega|pago inmediato',t)
    dato('condiciones_pago',pago.group(0) if pago else None,pago.group(0) if pago else None)
    r['pago_prioritario']=bool(pago)
    r['desierta']='desiert' in t
    r['segundo_llamado']=bool(re.search(r'segund[oa] (?:llamado|convocatoria)|2(?:do|º|°) llamado|llamado 2\b',t))
    r['reapertura']='reapertura' in t
    r['llamado_especial']=bool(r.get('llamado_especial') or r['desierta'] or r['segundo_llamado'] or r['reapertura'])
    cerrada=r.get('situacion_publicada') in ('ADJUDICADA','FINALIZADA','EN_EVALUACION','DESIERTA')
    if r.get('situacion_publicada')=='DESIERTA' and (r['segundo_llamado'] or r['reapertura']):
        # Mencionar el llamado anterior desierto no prueba cierre de la reapertura.
        cerrada=False
    r['procedimiento_canonico']=procedimiento_canonico(r)
    r['convocatoria']=convocatoria(r)
    es_real=bool(r['procedimiento_canonico'] or r.get('registro_estructurado') or (ps and len(ps)==1 and re.fullmatch(r'\d{1,6}',ps[0]['numero']) and r.get('url','').lower().endswith(('.pdf','.docx'))))
    r['clasificacion_registro']='PROCEDIMIENTO' if es_real else 'CANDIDATO_NO_VERIFICADO'
    apertura=r.get('fecha_apertura')
    raw_apertura=r.get('fecha_apertura_texto') or next((re.search(patron,norm(texto))[1] for campo,patron in [('a',r'apertura(?:\s+de\s+ofertas)?\s*[:\-]?\s*(.{0,90})')] if re.search(patron,norm(texto))), '')
    hora=re.search(r'(?<!\d)([01]?\d|2[0-3])[:.]([0-5]\d)(?:\s*(?:hs|h|horas))?',raw_apertura)
    r['hora_apertura']=f'{int(hora[1]):02d}:{hora[2]}' if hora else r.get('hora_apertura')
    r['fecha_hora_apertura']=datetime.fromisoformat(apertura+'T'+r['hora_apertura']).replace(tzinfo=ZONA).isoformat() if apertura and r.get('hora_apertura') else None
    r['vigencia']='VENCIDA' if cerrada or (apertura and apertura<hoy.isoformat()) else ('ABIERTA' if apertura and apertura>hoy.isoformat() else 'DESCONOCIDA')
    if r['fecha_hora_apertura']:
        limite=datetime.fromisoformat(r['fecha_hora_apertura'])
        consulta=ahora.replace(tzinfo=ZONA) if not ahora.tzinfo else ahora
        r['vigencia']='VENCIDA' if cerrada or limite<=consulta else 'ABIERTA'
    if not es_real:r['vigencia']='DESCONOCIDA'
    r['motivo_vigencia']='SIN_PROCEDIMIENTO_VERIFICADO' if not es_real else ('SITUACION_CERRADA' if cerrada else ('APERTURA_FUTURA' if r['vigencia']=='ABIERTA' else ('APERTURA_VENCIDA' if r['vigencia']=='VENCIDA' else 'FECHA_U_HORA_INSUFICIENTE')))
    # Con día de apertura igual a hoy sin hora verificada no se asegura que siga abierta.
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
    return (not r.get('pago_prioritario',False),not r.get('llamado_especial',False),{'ABIERTA':0,'DESCONOCIDA':1,'VENCIDA':2}.get(r.get('vigencia'),1),r.get('titulo',''))

def incorporar(historial,registros,ahora):
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
            historial[key]=r;indice[key]=key;nuevas.append(r)
        # Datos enriquecidos se reportan aparte: el registro legado permanece idéntico.
    return sorted(nuevas,key=prioridad)

def reporte(registros,fecha_reporte):
    lineas=['# Oportunidades detectadas — '+fecha_reporte,'','Novedad significa primera detección en el historial; puede ser una publicación histórica. Datos ausentes: desconocido. Orden orientativo por pago explícito, llamados especiales y vigencia; no predice rentabilidad.','']
    for r in sorted(registros,key=prioridad):
        lineas += ['## '+str(r.get('titulo') or 'Procedimiento sin título'),'',f"- Organismo: {r.get('organismo') or 'desconocido'} · {r.get('localidad') or 'desconocido'} · {r.get('provincia') or 'desconocido'}",f"- Número: {r.get('numero_procedimiento') or 'desconocido'}; vigencia: {r.get('vigencia')}; publicación: {r.get('fecha_publicacion') or 'desconocido'}; apertura: {r.get('fecha_apertura') or 'desconocido'}",f"- Objeto: {r.get('objeto') or 'desconocido'}",f"- Presupuesto: {r.get('presupuesto') or 'desconocido'}; pago: {r.get('condiciones_pago') or 'desconocido'}",f"- Desierta: {r.get('desierta')}; segundo llamado: {r.get('segundo_llamado')}; reapertura: {r.get('reapertura')}",f"- [Publicación oficial]({r.get('evidencia_url') or r.get('url')}) · Pliego: {r.get('enlace_pliego') or 'desconocido'} · Comprobación: {r.get('comprobacion_pliego',{}).get('estado','NO_COMPROBADO')}",'- Rentabilidad potencial: desconocida; '+r.get('motivo_sin_estimacion',''), '']
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
    if not anual:return None
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
    if re.search(r'segund[oa]|2(?:do|º|°|o) llamado',t):return '2'
    if re.search(r'tercer|3(?:er|º|°|o) llamado',t):return '3'
    if 'reapertura' in t:return 'reapertura'
    if norm(r.get('evento_publicado')).isdigit():return str(int(norm(r['evento_publicado'])))
    return '1'


def identidad(r):
    proc=procedimiento_canonico(r)
    org=norm(r.get('organismo'))
    if proc:
        partes=[org or r.get('fuente',''),proc,convocatoria(r),r.get('identidad_ambito','')]
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
    for k,v in otro.items():
        if salida.get(k) is None or salida.get(k)=='' or salida.get(k)==[]:salida[k]=v
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
    abiertas=sorted([r for r in registros if r.get('vigencia')=='ABIERTA' and r.get('clasificacion_registro')=='PROCEDIMIENTO'],key=lambda r:(r['fecha_apertura'],r.get('hora_apertura') or '',r.get('titulo') or ''))
    proximas=[r for r in abiertas if 0<=(date.fromisoformat(r['fecha_apertura'])-hoy).days<=dias]
    return {'abiertas':abiertas,'proximas_a_vencer':proximas,'dias_proximas':dias,'criterio':'Apertura futura comprobada; próximas: hasta 7 días calendario inclusive. Sin hora, el día de apertura queda desconocido.'}


def guardar_vistas(registros,ahora,directorio,prefijo='oportunidades'):
    import json
    from pathlib import Path
    d=Path(directorio);d.mkdir(parents=True,exist_ok=True)
    vistas=separar_vigencia(registros,ahora)
    for nombre in ('abiertas','proximas_a_vencer'):
        (d/f'{prefijo}_{nombre}.json').write_text(json.dumps({'fecha':ahora,'criterio':vistas['criterio'],'total':len(vistas[nombre]),'oportunidades':vistas[nombre]},ensure_ascii=False,indent=2),encoding='utf-8')
        (d/f'{prefijo}_{nombre}.md').write_text(reporte(vistas[nombre],ahora),encoding='utf-8')
    return vistas
