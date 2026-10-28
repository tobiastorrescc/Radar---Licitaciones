"""Estado transaccional del piloto: línea de base, versiones y novedades sin producción."""
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import oportunidades as o

VERSION=1
CAMPOS=('titulo','objeto','numero_procedimiento','tipo_procedimiento','procedimiento','organismo','localidad','provincia',
    'fecha_apertura','fecha_apertura_texto','hora_apertura','fecha_publicacion','fecha_publicacion_texto','presupuesto',
    'situacion_publicada','evento_publicado','documentos','enlace_pliego','comprobacion_pliego','evidencias_campos',
    'pago_evidencias','pago_motivo_pendiente','fuente','fuentes_observadas','url','urls_publicacion','evidencia_url',
    'detalle_completo','rango_evidencia','registro_estructurado','numero_oficial_sin_interpretar','id_origen','identidad_ambito','documentos_versiones')
SEMANTICOS=('objeto','numero_procedimiento','tipo_procedimiento','organismo','localidad','provincia','fecha_apertura',
    'hora_apertura','fecha_publicacion','presupuesto','situacion_publicada','evento_publicado')
NOVEDADES={'NUEVO_CONFIRMADO','NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA','MODIFICADO','DATOS_COMPLETADOS'}

def serializar(v):return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))

def abrir(path):
    path=Path(path)
    if path.suffix!='.sqlite3':raise ValueError('Usar un estado SQLite aislado, nunca un archivo de producción')
    path.parent.mkdir(parents=True,exist_ok=True)
    existente=path.exists() and path.stat().st_size>0
    db=sqlite3.connect(path,timeout=15)
    if existente:
        try:
            v=db.execute("SELECT valor FROM meta WHERE clave='version'").fetchone()
            if not v or int(v[0])!=VERSION:raise ValueError('Estado no compatible; no se reinicializa')
            if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise ValueError('Estado dañado')
        except Exception:
            db.close();raise
    db.execute('PRAGMA foreign_keys=ON')
    db.executescript('''
    CREATE TABLE IF NOT EXISTS meta (clave TEXT PRIMARY KEY,valor TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS ejecuciones (id TEXT PRIMARY KEY,fecha TEXT NOT NULL,resumen TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS fuentes (url TEXT PRIMARY KEY,inicio TEXT NOT NULL,base_completa INTEGER NOT NULL DEFAULT 0,ultima_completa TEXT);
    CREATE TABLE IF NOT EXISTS procedimientos (id TEXT PRIMARY KEY,primera TEXT NOT NULL,ultima TEXT NOT NULL,corrida TEXT NOT NULL,huella TEXT NOT NULL,dato TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS versiones (procedimiento TEXT NOT NULL,huella TEXT NOT NULL,fecha TEXT NOT NULL,corrida TEXT NOT NULL,dato TEXT NOT NULL,PRIMARY KEY(procedimiento,huella));
    CREATE TABLE IF NOT EXISTS eventos (corrida TEXT NOT NULL,procedimiento TEXT NOT NULL,huella TEXT NOT NULL,tipo TEXT NOT NULL,cambios TEXT NOT NULL,PRIMARY KEY(corrida,procedimiento));
    CREATE TABLE IF NOT EXISTS auditorias (corrida TEXT NOT NULL,fuente TEXT NOT NULL,dato TEXT NOT NULL,PRIMARY KEY(corrida,fuente));
    ''')
    v=db.execute("SELECT valor FROM meta WHERE clave='version'").fetchone()
    if v and int(v[0])!=VERSION:db.close();raise ValueError('Versión de estado no compatible; no se reinicializa')
    db.execute("INSERT OR IGNORE INTO meta VALUES ('version',?)",(str(VERSION),));db.commit()
    if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':db.close();raise ValueError('Estado dañado: no se borra ni reinicia')
    return db

def compacto(r):
    dato={k:r[k] for k in CAMPOS if k in r}
    hashes={d['url']:d['sha256'] for d in r.get('auditoria_documentos',[]) if d.get('estado')=='DOCUMENTO_ACCESIBLE' and d.get('sha256')}
    cp=r.get('comprobacion_pliego') or {}
    if cp.get('estado')=='DOCUMENTO_ACCESIBLE' and cp.get('sha256') and cp.get('url'):hashes[cp['url']]=cp['sha256']
    if hashes:dato['documentos_versiones']={**dato.get('documentos_versiones',{}),**hashes}
    return dato

def calidad(r):return (r.get('rango_evidencia',0),bool(r.get('detalle_completo')),bool(r.get('objeto')))

def consolidar(anterior,nuevo):
    """Un fallo/dato desconocido no borra información previamente comprobada."""
    if not anterior:return compacto(nuevo)
    salida=dict(anterior);entrada=compacto(nuevo)
    versiones_nuevas=entrada.get('documentos_versiones',{})
    cambiados={u for u,h in versiones_nuevas.items() if u in anterior.get('documentos_versiones',{}) and anterior['documentos_versiones'][u]!=h}
    mejor=calidad(nuevo)>=calidad(anterior)
    for k,v in entrada.items():
        if v is None or v=='' or v==[]:continue
        if k=='rango_evidencia':salida[k]=max(anterior.get(k,0),v);continue
        if k=='detalle_completo':salida[k]=bool(anterior.get(k) or v);continue
        if k in ('objeto','presupuesto','fecha_apertura','fecha_publicacion','hora_apertura') and salida.get(k) and not mejor:continue
        if k in ('fecha_apertura_texto','fecha_publicacion_texto') and salida.get(k) and not mejor:continue
        if k=='comprobacion_pliego' and v.get('estado')!='DOCUMENTO_ACCESIBLE':continue
        if k=='documentos_versiones':salida[k]={**anterior.get(k,{}),**v};continue
        if k=='pago_evidencias':
            import pagos
            salida[k]=pagos.unir_evidencias(anterior.get(k),v);continue
        if k=='documentos':
            salida[k]=list({d['url']:d for d in anterior.get(k,[])+v}.values());continue
        if k in ('fuentes_observadas','urls_publicacion'):
            salida[k]=sorted(set(anterior.get(k,[])+v));continue
        salida[k]=v
    if cambiados:
        import pagos
        anteriores=[e for e in anterior.get('pago_evidencias',[]) if e.get('url_documento') not in cambiados]
        salida['pago_evidencias']=pagos.unir_evidencias(anteriores,entrada.get('pago_evidencias',[]))
        if not salida['pago_evidencias']:salida['pago_motivo_pendiente']='DOCUMENTO_CAMBIADO_SIN_CLAUSULA_COMPROBADA'
    return salida

def contenido(r):
    """No incluye vigencia calculada, clocks, orden de enlaces ni errores de red."""
    n=o.normalizar(r)
    pago=n['pago']
    docs=sorted({d['url'] for d in r.get('documentos',[])})
    campos={k:r.get(k) for k in SEMANTICOS}
    if campos.get('objeto'):campos['objeto']=' '.join(campos['objeto'].split())
    return {**campos,'documentos':docs,'documentos_versiones':r.get('documentos_versiones',{}),
        'pago':{'estado':pago.get('estado'),'clasificacion':pago.get('clasificacion'),'plazos_dias':sorted(pago.get('plazos_dias') or []),
            'hitos_inicio':sorted(pago.get('hitos_inicio') or []),'documentos':sorted(pago.get('documentos_respaldo') or [])}}

def huella(r):return sha256(serializar(contenido(r)).encode()).hexdigest()

def fuentes_de(r):return sorted({u for u in [r.get('fuente'),*r.get('fuentes_observadas',[])] if u})

def tipo_nuevo(r,previas,fecha):
    disponibles=[previas[u] for u in fuentes_de(r) if u in previas and previas[u]['base_completa']]
    if not disponibles:return 'RECUPERACION_LINEA_BASE'
    publicada=r.get('fecha_publicacion')
    corte=min(o.fecha(f['ultima_completa']) for f in disponibles if f['ultima_completa'])
    if not publicada:
        import re
        anios=re.findall(r'20\d{2}',r.get('numero_procedimiento') or '')
        return 'HISTORICA_ANIO_PROCEDIMIENTO' if anios and max(anios)<corte[:4] else 'NUEVA_DETECCION_FECHA_DESCONOCIDA'
    hoy=datetime.fromisoformat(fecha).astimezone(o.ZONA).date().isoformat()
    if corte<publicada<=hoy:return 'NUEVO_CONFIRMADO'
    if publicada==corte:return 'NUEVA_DETECCION_MISMO_DIA'
    if publicada<corte:return 'HISTORICA_RECUPERADA'
    return 'FECHA_PUBLICACION_PENDIENTE'

def registrar(db,registros,informe):
    corrida=informe['ejecucion_id'];fecha=informe['actualizado']
    repetida=db.execute('SELECT resumen FROM ejecuciones WHERE id=?',(corrida,)).fetchone()
    if repetida:return {**json.loads(repetida[0]),'reprocesamiento':True,'eventos_emitidos':0,'novedades':0}
    previas={r[0]:{'inicio':r[1],'base_completa':bool(r[2]),'ultima_completa':r[3]} for r in db.execute('SELECT * FROM fuentes')}
    primera=db.execute('SELECT COUNT(*) FROM ejecuciones').fetchone()[0]==0
    dedup=o.deduplicar(registros,fecha);tipos=Counter();candidatos=0
    with db:
        for r in dedup:
            if r.get('clasificacion_registro')!='PROCEDIMIENTO':candidatos+=1;continue
            clave=o.identidad(r)
            viejo=db.execute('SELECT dato,huella FROM procedimientos WHERE id=?',(clave,)).fetchone()
            anterior=json.loads(viejo[0]) if viejo else None
            dato=consolidar(anterior,r);firma=huella(dato);cambios=[]
            if not viejo:tipo='LINEA_BASE' if primera else tipo_nuevo(r,previas,fecha)
            elif firma!=viejo[1]:
                a=contenido(anterior);b=contenido(dato)
                cambios=[k for k in b if a.get(k)!=b[k]]
                def completado(k):
                    if k=='documentos_versiones':return all(b[k].get(u)==v for u,v in a.get(k,{}).items())
                    if k=='pago':return a[k].get('estado')!='VERIFICADO' and b[k].get('estado')=='VERIFICADO'
                    return a.get(k) in (None,'',[],{})
                tipo='DATOS_COMPLETADOS' if all(completado(k) for k in cambios) else 'MODIFICADO'
            else:tipo='SIN_CAMBIOS'
            tipos[tipo]+=1
            db.execute('INSERT INTO procedimientos VALUES (?,?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET ultima=excluded.ultima,corrida=excluded.corrida,huella=excluded.huella,dato=excluded.dato',
                (clave,fecha,fecha,corrida,firma,serializar(dato)))
            if tipo!='SIN_CAMBIOS':
                db.execute('INSERT OR IGNORE INTO versiones VALUES (?,?,?,?,?)',(clave,firma,fecha,corrida,serializar(dato)))
                db.execute('INSERT INTO eventos VALUES (?,?,?,?,?)',(corrida,clave,firma,tipo,serializar(cambios)))
        estados=Counter()
        for obs in informe['observaciones']:
            url=obs['url'];estado=obs['estado'];estados[estado]+=1
            completa=obs.get('estado_cobertura',estado) in ('OPERATIVA','SIN_PUBLICACIONES','SIN_PUBLICACIONES_CONFIRMADO') and not obs.get('errores') and not obs.get('limites')
            db.execute('INSERT OR IGNORE INTO fuentes VALUES (?,?,0,NULL)',(url,fecha))
            if completa:db.execute('UPDATE fuentes SET base_completa=1,ultima_completa=? WHERE url=?',(fecha,url))
            db.execute('INSERT INTO auditorias VALUES (?,?,?)',(corrida,url,serializar(obs)))
        total=db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0]
        pendientes=sum(s not in ('OPERATIVA','SIN_PUBLICACIONES') for s in (f['estado'] for f in informe['observaciones']))
        incompleta=informe['estado_ejecucion']!='COMPLETADA' or informe['resumen']['finalizadas']!=informe['resumen']['configuradas'] or informe['resumen'].get('fuentes_error_interno',0)>0
        resumen={'corrida':corrida,'fecha':fecha,'primera_ejecucion':primera,'estado':'INCOMPLETA' if incompleta else 'COMPLETA_CON_INCIDENCIAS' if pendientes else 'COMPLETA',
            'observadas':len(dedup),'candidatos_sin_confirmar':candidatos,'clasificacion':dict(tipos),'novedades':sum(tipos[t] for t in NOVEDADES),
            'eventos_emitidos':sum(v for k,v in tipos.items() if k!='SIN_CAMBIOS'),'total_historial':total,'fuentes':dict(estados),
            'mensaje':'LINEA_BASE_SIN_ALERTAS' if primera else 'CON_NOVEDADES' if any(tipos[t] for t in NOVEDADES) else 'SIN_NOVEDADES_CONFIRMADAS_CON_INCIDENCIAS' if pendientes or incompleta else 'SIN_NOVEDADES_CONSULTA_COMPLETA'}
        db.execute('INSERT INTO ejecuciones VALUES (?,?,?)',(corrida,fecha,serializar(resumen)))
    return resumen

def actuales(db,fecha,corrida):
    salida=[]
    for clave,primera,ultima,vista,dato in db.execute('SELECT id,primera,ultima,corrida,dato FROM procedimientos'):
        r=o.normalizar(json.loads(dato),fecha)
        r.update(id=clave,primera_deteccion=primera,ultima_deteccion=ultima,observada_esta_corrida=vista==corrida)
        salida.append(r)
    return sorted(salida,key=o.prioridad)

def eventos(db,corrida,fecha):
    salida=[]
    for clave,tipo,cambios,dato in db.execute('SELECT e.procedimiento,e.tipo,e.cambios,v.dato FROM eventos e JOIN versiones v ON v.procedimiento=e.procedimiento AND v.huella=e.huella WHERE e.corrida=?',(corrida,)):
        r=o.normalizar(json.loads(dato),fecha);r.update(id=clave,clasificacion_novedad=tipo,campos_modificados=json.loads(cambios));salida.append(r)
    return sorted(salida,key=o.prioridad)
