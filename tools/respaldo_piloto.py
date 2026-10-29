"""Respaldo incremental verificable del piloto, independiente de la caducidad de Actions."""
import argparse
import gzip
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import sys
import tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
from tools.radar_controlado import validar_salida,sellar_estado

TABLAS={'meta':('clave',),'ejecuciones':('id',),'fuentes':('url',),'procedimientos':('id',),
        'versiones':('procedimiento','huella'),'eventos':('corrida','procedimiento'),'auditorias':('corrida','fuente')}
INDICE='indice.json'

def canon(x):return json.dumps(x,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(x):return sha256(canon(x).encode()).hexdigest()
def guardar(p,d):
    p=Path(p);p.parent.mkdir(parents=True,exist_ok=True)
    tmp=p.with_suffix(p.suffix+'.tmp');tmp.write_text(canon(d)+'\n');os.replace(tmp,p)

def directorio(p):
    p=Path(p).resolve();root=Path.cwd().resolve()
    if not any(p.is_relative_to(root/x) for x in ('piloto_respaldo','work')):raise ValueError('Destino de respaldo fuera del piloto')
    p.mkdir(parents=True,exist_ok=True);return p

def filas(db,t):
    cols=[r[1] for r in db.execute('PRAGMA table_info('+t+')')]
    return [dict(zip(cols,row)) for row in db.execute('SELECT * FROM '+t+' ORDER BY '+','.join(TABLAS[t]))]

def estado(db):
    datos={t:filas(db,t) for t in TABLAS}
    return datos,{t:len(r) for t,r in datos.items()},digest(datos)

def indice(p):
    q=p/INDICE
    if not q.exists():return {'schema_version':1,'segmentos':[],'corridas':[]}
    d=json.loads(q.read_text())
    if d.get('schema_version')!=1:raise ValueError('Índice incompatible; no se reinicia')
    return d

def leer_cadena(p,d):
    previo=None
    for n,s in enumerate(d['segmentos']):
        if not re.fullmatch(r'[0-9]{6}-[a-f0-9]{64}\.json\.gz',s['archivo']):raise ValueError('Nombre de segmento inválido')
        raw=(p/s['archivo']).read_bytes()
        if sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Segmento alterado')
        if len(raw)>50*1024*1024:raise ValueError('Segmento excesivo')
        with gzip.open(p/s['archivo'],'rb') as stream:
            descomprimido=stream.read(256*1024*1024+1)
        if len(descomprimido)>256*1024*1024:raise ValueError('Respaldo descomprimido excesivo')
        datos=json.loads(descomprimido)
        if datos['anterior']!=previo or datos['secuencia']!=n or datos['schema_version']!=inc.VERSION:raise ValueError('Cadena incompleta o incompatible')
        if set(datos['filas'])!=set(TABLAS):raise ValueError('Tablas inesperadas')
        previo=s['sha256'];yield datos

def aplicar(db,datos):
    with db:
        for t,rs in datos['filas'].items():
            columnas=[r[1] for r in db.execute('PRAGMA table_info('+t+')')]
            for r in rs:
                if set(r)!=set(columnas):raise ValueError('Columnas incompatibles')
                valores=[r[c] for c in columnas]
                if t in ('versiones','eventos','auditorias','ejecuciones'):
                    existente=db.execute('SELECT * FROM '+t+' WHERE '+' AND '.join(k+'=?' for k in TABLAS[t]),[r[k] for k in TABLAS[t]]).fetchone()
                    if existente and list(existente)!=valores:raise ValueError('Un respaldo intenta reescribir historia inmutable')
                db.execute('INSERT OR REPLACE INTO '+t+' VALUES ('+','.join('?' for _ in columnas)+')',valores)
        _,cuentas,firma=estado(db)
        if cuentas!=datos['cuentas'] or firma!=datos['contenido_sha256']:raise ValueError('Estado restaurado no coincide con el respaldo')

def restaurar(carpeta,salida):
    p=directorio(carpeta);salida=validar_salida(salida);d=indice(p)
    if not d['segmentos']:return False
    destino=salida/'estado.sqlite3'
    if destino.exists():raise ValueError('No sobrescribir un estado existente al restaurar')
    temporal=salida/'restauracion.sqlite3'
    if temporal.exists():raise ValueError('Hay una restauración previa sin resolver')
    db=inc.abrir(temporal)
    try:
        for datos in leer_cadena(p,d):aplicar(db,datos)
        ids=[r[0] for r in db.execute('SELECT id FROM ejecuciones ORDER BY id')]
        if ids!=d['corridas']:raise ValueError('Faltan ejecuciones del índice')
    except BaseException:
        db.close();temporal.unlink(missing_ok=True);raise
    db.close();os.replace(temporal,destino);sellar_estado(salida);return True

def exportar(salida,carpeta):
    salida=validar_salida(salida);p=directorio(carpeta);d=indice(p)
    previo=canon(d)
    if not (salida/'estado.sqlite3').is_file():raise ValueError('Falta estado; no crear respaldo vacío')
    db=inc.abrir(salida/'estado.sqlite3')
    try:datos,cuentas,firma=estado(db)
    finally:db.close()
    previas=set(d['corridas']);ids=sorted(r['id'] for r in datos['ejecuciones'])
    if not previas<=set(ids):raise ValueError('El estado perdió ejecuciones respaldadas')
    if d['segmentos']:
        # Comprobar la cadena antes de añadir, también si el último segmento desapareció.
        for _ in leer_cadena(p,d):pass
    if set(ids)==previas:
        if d['segmentos'] and d['segmentos'][-1]['contenido_sha256']!=firma:raise ValueError('Estado cambiado sin una nueva ejecución')
        return d
    delta={t:[r for r in rs if t in ('meta','fuentes') or (r.get('id') if t=='ejecuciones' else r.get('corrida')) not in previas] for t,rs in datos.items()}
    segmento={'schema_version':inc.VERSION,'secuencia':len(d['segmentos']),
        'anterior':d['segmentos'][-1]['sha256'] if d['segmentos'] else None,
        'filas':delta,'cuentas':cuentas,'contenido_sha256':firma}
    raw=gzip.compress(canon(segmento).encode(),mtime=0)
    if len(raw)>50*1024*1024:raise ValueError('Segmento excesivo')
    h=sha256(raw).hexdigest();nombre=f'{len(d["segmentos"]):06d}-{h}.json.gz'
    (p/nombre).write_bytes(raw)
    d['segmentos'].append({'archivo':nombre,'sha256':h,'contenido_sha256':firma,'cuentas':cuentas})
    d['corridas']=ids;guardar(p/INDICE,d)
    try:
        with tempfile.TemporaryDirectory(dir=Path.cwd()/'work',prefix='verificar-respaldo-') as tmp:
            restaurar(p,tmp)
    except BaseException:
        guardar(p/INDICE,json.loads(previo));(p/nombre).unlink(missing_ok=True);raise
    return d

def continuidad(salida,fase):
    salida=validar_salida(salida);p=salida/'continuidad_antes.json';db=inc.abrir(salida/'estado.sqlite3') if (salida/'estado.sqlite3').exists() else None
    try:
        datos=estado(db)[0] if db else {t:[] for t in TABLAS}
        ids={r['id'] for r in datos['procedimientos']}
        versiones={r['procedimiento']+'|'+r['huella']:digest(r) for r in datos['versiones']}
        if fase=='antes':guardar(p,{'ids':sorted(ids),'versiones':versiones,'corridas':[r['id'] for r in datos['ejecuciones']]});return
        anterior=json.loads(p.read_text());corridas={r['id'] for r in datos['ejecuciones']}-set(anterior['corridas'])
        repetidas=[r for r in datos['eventos'] if r['corrida'] in corridas and r['procedimiento'] in anterior['ids'] and r['tipo'].startswith(('NUEVO_','NUEVA_DETECCION'))]
        correcta=set(anterior['ids'])<=ids and not repetidas and all(versiones.get(k)==v for k,v in anterior['versiones'].items()) and bool(corridas)
        resumen={'correcta':correcta,'procedimientos_anteriores':len(anterior['ids']),'procedimientos_actuales':len(ids),
            'versiones_anteriores':len(anterior['versiones']),'versiones_actuales':len(versiones),'repetidas_como_nuevas':len(repetidas),'corridas_nuevas':sorted(corridas),
            'clasificaciones':dict(__import__('collections').Counter(r['tipo'] for r in datos['eventos'] if r['corrida'] in corridas))}
        guardar(salida/'continuidad.json',resumen);print('CONTINUIDAD '+canon(resumen),flush=True)
        if not correcta:raise ValueError('Falló la continuidad del historial')
    finally:
        if db:db.close()

def main():
    a=argparse.ArgumentParser();a.add_argument('accion',choices=['exportar','restaurar','antes','despues']);a.add_argument('--salida',default='work/controlado');a.add_argument('--respaldo',required=True);args=a.parse_args()
    if args.accion=='exportar':print('RESPALDO '+canon(exportar(args.salida,args.respaldo)['segmentos'][-1]))
    elif args.accion=='restaurar':print('RESTAURADO '+str(restaurar(args.respaldo,args.salida)))
    else:continuidad(args.salida,args.accion)
if __name__=='__main__':main()
