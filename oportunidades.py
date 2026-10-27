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
    r=dict(r);texto=' '.join(dict.fromkeys(str(r.get(k) or '') for k in ('titulo','objeto','texto_documento')))
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
    for campo,patron in [('fecha_apertura',r'(?:fecha\s+(?:de\s+)?)?apertura(?:\s+(?:de\s+)?(?:ofertas|sobres))?\s*[:\-]?\s*(.{0,90})'),('fecha_publicacion',r'(?:fecha\s+(?:de\s+)publicacion|publicad[oa](?:\s+el)?)\s*[:\-]?\s*(.{0,70})')]:
        dedicado=r.get(campo+'_texto')
        m=re.search(patron,t)
        raw=dedicado or (m[1] if m else '')
        # No tomar una fecha de otro campo cuando la etiqueta está vacía.
        raw=re.split(r'presupuesto|publicacion|apertura|adjudicacion',norm(raw))[0]
        dato(campo,fecha(raw),raw)
    if r.get('presupuesto') is None:
        valor,frag=monto('presupuesto oficial '+r['presupuesto_texto'] if r.get('presupuesto_texto') else t);dato('presupuesto',valor,frag)
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
    apertura=r.get('fecha_apertura')
    r['vigencia']='VENCIDA' if cerrada or (apertura and apertura<hoy.isoformat()) else ('ABIERTA' if apertura and apertura>hoy.isoformat() else 'DESCONOCIDA')
    # Con día de apertura igual a hoy sin hora verificada no se asegura que siga abierta.
    r['antiguedad_publicacion']='HISTORICA' if (r.get('fecha_publicacion') and r['fecha_publicacion']<hoy.isoformat()) or r['vigencia']=='VENCIDA' else 'DESCONOCIDA'
    r['estimacion_comercial']=None
    r['motivo_sin_estimacion']='No hay costos propios, cantidades y precio de venta comprobables para estimar margen'
    r['evidencias_campos']=ev
    # Solo llamar pliego al enlace identificado como tal: otros adjuntos quedan en documentos.
    r['enlace_pliego']=next((d['url'] for d in r.get('documentos',[]) if 'pliego' in norm(d.get('titulo'))),None)
    for k in ('organismo','localidad','provincia','objeto','fecha_publicacion','fecha_apertura','presupuesto'):r.setdefault(k,None)
    if r.get('detalle_completo') is False:r['objeto']=None
    r['campos_desconocidos']=[k for k in ('numero_procedimiento','organismo','localidad','provincia','objeto','presupuesto','fecha_apertura','fecha_publicacion','enlace_pliego') if not r.get(k)]
    return r

def identidad(r):
    # Una URL de listado o un anexo no identifica un procedimiento. El organismo sí.
    if r.get('numero_procedimiento') and re.search(r'/20\d{2}$',r['numero_procedimiento']):
        partes=[norm(r.get(k)) for k in ('organismo','provincia','localidad','tipo_procedimiento','numero_procedimiento')]
        partes.append('' if norm(r.get('evento_publicado')) in ('','1') else norm(r.get('evento_publicado')))
    else:partes=[r.get('fuente',''),r.get('id') or r.get('url',''),norm(r.get('titulo'))]
    return sha256('|'.join(partes).encode()).hexdigest()

def prioridad(r):
    return (not r.get('pago_prioritario',False),not r.get('llamado_especial',False),{'ABIERTA':0,'DESCONOCIDA':1,'VENCIDA':2}.get(r.get('vigencia'),1),r.get('titulo',''))

def incorporar(historial,registros,ahora):
    """Índice derivado: no elimina ni reescribe entradas antiguas."""
    nuevas=[];indice={identidad(normalizar(v,ahora)):k for k,v in historial.items() if isinstance(v,dict)}
    for raw in registros:
        r=normalizar(raw,ahora);key=identidad(r)
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
        lineas += ['## '+str(r.get('titulo') or 'Procedimiento sin título'),'',f"- Organismo: {r.get('organismo') or 'desconocido'} · {r.get('localidad') or 'desconocido'} · {r.get('provincia') or 'desconocido'}",f"- Número: {r.get('numero_procedimiento') or 'desconocido'}; vigencia: {r.get('vigencia')}; publicación: {r.get('fecha_publicacion') or 'desconocido'}; apertura: {r.get('fecha_apertura') or 'desconocido'}",f"- Objeto: {r.get('objeto') or 'desconocido'}",f"- Presupuesto: {r.get('presupuesto') or 'desconocido'}; pago: {r.get('condiciones_pago') or 'desconocido'}",f"- Desierta: {r.get('desierta')}; segundo llamado: {r.get('segundo_llamado')}; reapertura: {r.get('reapertura')}",f"- [Publicación oficial]({r.get('evidencia_url') or r.get('url')}) · Pliego: {r.get('enlace_pliego') or 'desconocido'}",'- Rentabilidad potencial: desconocida; '+r.get('motivo_sin_estimacion',''), '']
    return '\n'.join(lineas)
