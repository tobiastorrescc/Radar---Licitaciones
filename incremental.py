"""Estado transaccional del piloto: línea de base, versiones y novedades sin producción."""
from collections import Counter
from datetime import datetime
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import re
from urllib.parse import urlsplit
import oportunidades as o

VERSION=1
CAMPOS=('tipo_documento','detalle_documental','titulo','objeto','numero_procedimiento','tipo_procedimiento','procedimiento','organismo','localidad','provincia',
    'fecha_apertura','fecha_apertura_texto','hora_apertura','fecha_publicacion','fecha_publicacion_texto','presupuesto',
    'situacion_publicada','evento_publicado','documentos','enlace_pliego','comprobacion_pliego','evidencias_campos',
    'pago_evidencias','pago_motivo_pendiente','fuente','fuentes_observadas','url','urls_publicacion','evidencia_url',
    'texto_listado','detalle_completo','rango_evidencia','registro_estructurado','numero_oficial_sin_interpretar','id_origen','identidad_ambito','documentos_versiones','campos_oficiales','numero_convocatoria','fecha_limite_presentacion','fecha_limite_presentacion_texto','hora_limite_presentacion','modalidad_presentacion')
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
        if salida.get('detalle_documental'):salida['detalle_documental']=dict(salida['detalle_documental'])
        for campo,v in list(salida.get('detalle_documental',{}).items()):
            ev=v.get('evidencia',{});url=ev.get('url')
            if url in cambiados and ev.get('sha256')!=versiones_nuevas[url]:
                salida['detalle_documental'][campo]={**v,'valor':None,'valor_anterior':v.get('valor'),'estado':'PENDIENTE','motivo':'DOCUMENTO_CAMBIADO_REQUIERE_REVALIDACION'}
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
    if campos.get('objeto'):
        texto=campos['objeto']
        host=(urlsplit(r.get('evidencia_url') or r.get('url') or '').hostname or '').removeprefix('www.')
        # Contadores observados en #107. La evidencia original se conserva;
        # sólo se excluyen de la comparación estas etiquetas del sitio.
        if host=='timbues.gob.ar':texto=re.sub(r'\b[\d.]+\s+vistas\b','',texto,flags=re.I)
        if host=='armstrong.gov.ar':texto=re.sub(r'\bDescargas\s+\d+\s+(?=Licencia\b)','',texto,flags=re.I)
        campos['objeto']=' '.join(texto.split())
    for k in ('fecha_limite_presentacion','hora_limite_presentacion','modalidad_presentacion','detalle_documental'):
        if r.get(k):campos[k]=r[k]
    if r.get('detalle_documental'):
        # Transporte/caché no son modificaciones de la convocatoria.
        campos['detalle_documental']={k:{'valor':v.get('valor'),'estado':v.get('estado'),'evidencia':{c:v.get('evidencia',{}).get(c) for c in ('url','sha256','pagina','cita')}} for k,v in r['detalle_documental'].items()}
    return {**campos,'documentos':docs,'documentos_versiones':r.get('documentos_versiones',{}),
        'pago':{'estado':pago.get('estado'),'clasificacion':pago.get('clasificacion'),'plazos_dias':sorted(pago.get('plazos_dias') or []),
            'hitos_inicio':sorted(pago.get('hitos_inicio') or []),'documentos':sorted(pago.get('documentos_respaldo') or [])}}

def huella(r):return sha256(serializar(contenido(r)).encode()).hexdigest()

def fuentes_de(r):return sorted({u for u in [r.get('fuente'),*r.get('fuentes_observadas',[])] if u})

def tipo_nuevo(r,previas,fecha):
    disponibles=[previas[u] for u in fuentes_de(r) if u in previas and previas[u]['base_completa']]
    publicada=r.get('fecha_publicacion')
    hoy=datetime.fromisoformat(fecha).astimezone(o.ZONA).date().isoformat()
    if not disponibles:
        inicios=[o.fecha(previas[u]['inicio']) for u in fuentes_de(r) if u in previas]
        if publicada and inicios and min(inicios)<publicada<=hoy:return 'NUEVO_CONFIRMADO'
        if not publicada:
            anios=re.findall(r'20\d{2}',r.get('numero_procedimiento') or '')
            historica=(anios and max(anios)<hoy[:4]) or (r.get('fecha_apertura') and r['fecha_apertura']<hoy) or r.get('situacion_publicada') in ('ADJUDICADA','FINALIZADA','DESIERTA','FRACASADA')
            if not historica:return 'NUEVA_DETECCION_FECHA_DESCONOCIDA'
        return 'RECUPERACION_LINEA_BASE'
    corte=min(o.fecha(f['ultima_completa']) for f in disponibles if f['ultima_completa'])
    if not publicada:
        anios=re.findall(r'20\d{2}',r.get('numero_procedimiento') or '')
        return 'HISTORICA_ANIO_PROCEDIMIENTO' if anios and max(anios)<corte[:4] else 'NUEVA_DETECCION_FECHA_DESCONOCIDA'
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
    # Índice derivado bajo el analizador actual: corregir identidad no crea una
    # novedad ni reescribe IDs/versiones ya persistidas.
    identidades_anteriores={}
    for antigua,dato in db.execute('SELECT id,dato FROM procedimientos ORDER BY primera,id'):
        identidades_anteriores.setdefault(o.identidad(json.loads(dato)),antigua)
    dedup=o.deduplicar(registros,fecha);tipos=Counter();candidatos=0
    with db:
        for r in dedup:
            if r.get('clasificacion_registro')!='PROCEDIMIENTO':candidatos+=1;continue
            identidad_actual=o.identidad(r)
            clave=identidades_anteriores.get(identidad_actual,identidad_actual)
            if clave==identidad_actual and r.get('identidad_ambito','').startswith('ficha-rosario-'):
                legado=identidades_anteriores.get(o.identidad({**r,'identidad_ambito':''}))
                if legado:
                    viejo_dato=db.execute('SELECT dato FROM procedimientos WHERE id=?',(legado,)).fetchone()
                    previo=json.loads(viejo_dato[0]) if viejo_dato else {}
                    if r.get('texto_listado') and o.norm(r['texto_listado']) in {o.norm(previo.get('objeto')),o.norm(previo.get('titulo'))}:clave=legado
            viejo=db.execute('SELECT dato,huella FROM procedimientos WHERE id=?',(clave,)).fetchone()
            identidades_anteriores[identidad_actual]=clave
            anterior=json.loads(viejo[0]) if viejo else None
            dato=consolidar(anterior,r);firma=huella(dato);cambios=[]
            if not viejo:tipo='LINEA_BASE' if primera else tipo_nuevo(r,previas,fecha)
            elif firma!=viejo[1]:
                a=contenido(anterior);b=contenido(dato)
                cambios=[k for k in b if a.get(k)!=b[k]]
                def completado(k):
                    if k=='objeto' and calidad(dato)>calidad(anterior):return True
                    if k=='documentos_versiones':return all(b[k].get(u)==v for u,v in a.get(k,{}).items())
                    if k=='pago':return a[k].get('estado')!='VERIFICADO' and b[k].get('estado')=='VERIFICADO'
                    return a.get(k) in (None,'',[],{})
                tipo=('DATOS_COMPLETADOS' if all(completado(k) for k in cambios) else 'MODIFICADO') if cambios else 'SIN_CAMBIOS'
                if not cambios:firma=viejo[1]
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
    # Vista derivada: conserva cada fila/versión histórica en SQLite, pero informa
    # una sola oportunidad por organismo, procedimiento y convocatoria actuales.
    grupos={}
    for clave,primera,ultima,vista,dato in db.execute('SELECT id,primera,ultima,corrida,dato FROM procedimientos ORDER BY primera,id'):
        r=o.normalizar(json.loads(dato),fecha)
        r.update(id=clave,primera_deteccion=primera,ultima_deteccion=ultima,observada_esta_corrida=vista==corrida,ids_historial=[clave])
        variante={k:r.get(k) for k in ('id','numero_procedimiento','objeto','fecha_apertura','fecha_limite_presentacion','evento_publicado','numero_convocatoria','url','documentos')}
        r['variantes_historial']=[variante]
        identidad=o.identidad(r);anterior=grupos.get(identidad)
        if anterior:
            unido=o.fusionar(anterior,r,fecha)
            unido.update(id=anterior['id'],ids_historial=sorted(set(anterior['ids_historial']+[clave])),
                primera_deteccion=min(anterior['primera_deteccion'],primera),ultima_deteccion=max(anterior['ultima_deteccion'],ultima),
                observada_esta_corrida=anterior['observada_esta_corrida'] or r['observada_esta_corrida'])
            unido['variantes_historial']=anterior['variantes_historial']+[variante]
            fechas={v['fecha_apertura'] for v in unido['variantes_historial'] if v.get('fecha_apertura')}
            eventos={o.norm(v.get('evento_publicado')) for v in unido['variantes_historial']}
            unido['unificacion_estado']='REQUIERE_REVISION' if len(fechas)>1 or ('nuevo llamado' in eventos and len(eventos)>1) else 'MISMO_PROCEDIMIENTO_VARIANTES_CONSERVADAS'
            r=unido
        grupos[identidad]=r
    revisiones=Path(__file__).parent/'inventario/revisiones_identidad.json'
    revisiones=json.loads(revisiones.read_text()) if revisiones.exists() else []
    for r in grupos.values():
        for revision in revisiones:
            if set(r['ids_historial'])!=set(revision['ids_historial']):continue
            if r.get('organismo')!=revision['organismo'] or r.get('numero_procedimiento')!=revision['numero_procedimiento']:continue
            esperados={d['url']:d['sha256'] for d in revision['evidencias']}
            if any(u in esperados and esperados[u]!=h for u,h in r.get('documentos_versiones',{}).items()):continue
            r['revision_unificacion']=revision;r['unificacion_estado']=revision['estado']
            if revision.get('fecha_apertura'):
                cambio={k:revision[k] for k in ('fecha_apertura','hora_apertura','fecha_limite_presentacion','hora_limite_presentacion') if revision.get(k)}
                cambio['fecha_apertura_texto']=revision['fecha_apertura']+' '+revision['hora_apertura']
                cambio['fecha_limite_presentacion_texto']=revision['fecha_limite_presentacion']+' '+revision['hora_limite_presentacion']
                r.update(cambio);r.update(o.normalizar(r,fecha))
            if revision.get('fechas_apertura_contradictorias'):
                r['fecha_apertura']=None;r['hora_apertura']=None;r['fecha_hora_apertura']=None
                r['fechas_apertura_contradictorias']=revision['fechas_apertura_contradictorias']
                if r['vigencia']=='ABIERTA':r['vigencia']='DESCONOCIDA'
                r['motivo_vigencia']='FECHAS_DE_APERTURA_CONTRADICTORIAS_EN_DOCUMENTO_OFICIAL'
        r['estado_vigencia']=('ABIERTA_OBSERVADA_EN_CORRIDA' if r['observada_esta_corrida'] else 'ABIERTA_CALCULADA_SIN_REVALIDACION') if r['vigencia']=='ABIERTA' else r['vigencia']
    return sorted(grupos.values(),key=o.prioridad)


def eventos(db,corrida,fecha):
    salida=[]
    for clave,tipo,cambios,dato in db.execute('SELECT e.procedimiento,e.tipo,e.cambios,v.dato FROM eventos e JOIN versiones v ON v.procedimiento=e.procedimiento AND v.huella=e.huella WHERE e.corrida=?',(corrida,)):
        r=o.normalizar(json.loads(dato),fecha)
        observacion=db.execute('SELECT primera,ultima FROM procedimientos WHERE id=?',(clave,)).fetchone()
        r.update(id=clave,clasificacion_novedad=tipo,campos_modificados=json.loads(cambios),primera_deteccion=observacion[0] if observacion else None,ultima_deteccion=observacion[1] if observacion else None)
        r['etiqueta_novedad']='Primera detección, fecha pendiente' if tipo=='NUEVA_DETECCION_FECHA_DESCONOCIDA' else tipo
        salida.append(r)
    return sorted(salida,key=o.prioridad)
