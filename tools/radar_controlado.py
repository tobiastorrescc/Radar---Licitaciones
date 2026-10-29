"""Piloto aislado con límites y estado incremental; no escribe producción."""
import argparse
from collections import Counter
from datetime import datetime
from hashlib import sha256
from html import escape
import json
import os
from pathlib import Path
import sys
import uuid
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import incremental as inc
import oportunidades as o
import registro_fuentes
from tools.verificar_fuentes import ejecutar,guardar
from tools import comprobar_pliegos
from tools.informe_cobertura import estado_cobertura

PROTEGIDOS=('radar_estado.json','licitaciones_nuevas.json','licitaciones_nuevas.md','auditoria_fuentes.json')

def validar_salida(path):
    p=Path(path).resolve();permitida=(Path.cwd()/'work').resolve()
    if not p.is_relative_to(permitida):raise ValueError('El piloto sólo puede escribir bajo work/; producción queda protegida')
    p.mkdir(parents=True,exist_ok=True);return p

def huellas_produccion():
    return {n:sha256(Path(n).read_bytes()).hexdigest() if Path(n).exists() else None for n in PROTEGIDOS}

def fuentes_configuradas():
    fs=[f for f in json.loads(Path('inventario/fuentes.json').read_text()) if f['incorporada']]
    urls={f['url'] for f in fs}
    fs.extend(f for u,f in registro_fuentes.cargar_auto().items() if u not in urls)
    return fs

def registros_checkpoint(informe):
    registros=[]
    for obs in informe['observaciones']:
        path=Path(obs.get('resultado_archivo',''))
        if not path.is_file():continue
        for raw in json.loads(path.read_text()).get('oportunidades',[]):
            registros.append(o.normalizar(raw,informe['actualizado']))
    return o.deduplicar(registros,informe['actualizado'])

def enlace(url,texto):
    import extractores
    u=extractores.url_publica(url or '')
    return f'<a href="{escape(u,quote=True)}" target="_blank" rel="noopener noreferrer">{escape(str(texto))}</a>' if u else escape(str(texto))

def generar_informe(db,resumen,registros,fuentes,destino):
    fecha=resumen['fecha'];corrida=resumen['corrida'];destino=Path(destino)
    actuales=inc.actuales(db,fecha,corrida);eventos=inc.eventos(db,corrida,fecha)
    actuales_por_id={r['id']:r for r in actuales}
    for e in eventos:actuales_por_id[e['id']]['clasificacion_novedad']=e['clasificacion_novedad']
    vistas=o.guardar_vistas(actuales,fecha,destino)
    for nombre,datos in [('catalogo_completo',actuales),('eventos',eventos),('observadas',registros)]:
        guardar(destino/(nombre+'.json'),{'fecha':fecha,'total':len(datos),'oportunidades':datos})
        (destino/(nombre+'.md')).write_text(o.reporte(datos,fecha),encoding='utf-8')
    resumen={**resumen,'abiertas':len(vistas['abiertas']),'proximas_a_vencer':len(vistas['proximas_a_vencer']),
        'no_observadas_en_corrida':sum(not r['observada_esta_corrida'] for r in actuales),'cobertura_estricta':dict(Counter(f['estado_cobertura'] for f in fuentes))}
    guardar(destino/'resumen.json',resumen)
    lineas=['# Radar diario controlado', '',f"Fecha: {fecha}. Estado: **{resumen['estado']}**. {resumen['mensaje']}.",'',
        f"Historial: {resumen['total_historial']}; novedades y cambios: {resumen['novedades']}; abiertas: {resumen['abiertas']}; próximas a vencer: {resumen['proximas_a_vencer']}.",'',
        'La primera corrida es línea de base sin alertas de novedades. Fecha de detección no equivale a fecha de publicación. Una fuente con incidencias no permite afirmar ausencia de novedades. Se conserva todo el historial, incluso registros no recuperados en esta consulta.','',
        '[Consulta completa y búsqueda: index.html](index.html) · [Catálogo completo](catalogo_completo.md) · [Abiertas](oportunidades_abiertas.md) · [Próximas a vencer](oportunidades_proximas_a_vencer.md)','',
        '| Fuente | Estado de consulta | Cobertura estricta | Publicaciones |','|---|---|---|---:|']
    lineas.extend(f"| {f['url']} | {f['estado']} | {f['estado_cobertura']} | {f.get('publicaciones_detectadas',0)} |" for f in fuentes)
    for tipo in sorted({e['clasificacion_novedad'] for e in eventos}):
        if tipo=='LINEA_BASE':continue # Todas las filas están en el catálogo, sin alertar miles de antiguas.
        lineas+=['',f'## {tipo}','',o.reporte([r for r in eventos if r['clasificacion_novedad']==tipo],fecha)]
    (destino/'reporte_diario.md').write_text('\n'.join(lineas)+'\n',encoding='utf-8')
    filas=[]
    for r in actuales:
        nombre=(r.get('organismo') or 'Organismo desconocido')+' / '+(r.get('numero_procedimiento') or r.get('numero_oficial_sin_interpretar') or 'Número desconocido')
        flags=', '.join(k for k in ('desierta','segundo_llamado','reapertura') if r.get(k))
        valores=[enlace(r.get('evidencia_url') or r.get('url'),nombre),escape(r.get('objeto') or 'Objeto desconocido'),
            escape(r.get('clasificacion_novedad') or 'Ya registrada'),escape(r['vigencia']),escape(r.get('fecha_publicacion') or 'Desconocida'),
            escape(r.get('fecha_hora_apertura') or r.get('fecha_apertura') or 'Desconocida'),escape(r['condiciones_pago']),
            enlace(r.get('enlace_condiciones_pago'),'Respaldo') if r.get('enlace_condiciones_pago') else 'No comprobado',
            enlace(r.get('enlace_pliego'),'Pliego') if r.get('enlace_pliego') else 'No identificado',escape(flags),
            'Observada' if r['observada_esta_corrida'] else 'No confirmada en esta corrida']
        filas.append('<tr>'+''.join('<td>'+v+'</td>' for v in valores)+'</tr>')
    titulos=['Organismo / procedimiento','Objeto','Detección','Vigencia','Publicación','Apertura','Pago','Documento de pago','Pliego','Señales','Última consulta']
    html='<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Radar controlado</title><style>body{font:16px system-ui;margin:2rem;color:#172b4d}table{border-collapse:collapse;width:100%}td,th{border:1px solid #ccd;padding:.5rem;text-align:left;vertical-align:top}th{background:#edf3fa;position:sticky;top:0}input{font:inherit;padding:.6rem;width:min(90%,50rem)}td:nth-child(2){min-width:20rem;white-space:pre-wrap}a{color:#1254ad}</style>'
    html+=f'<h1>Radar controlado</h1><p>{escape(fecha)} · {escape(resumen["estado"])} · {escape(resumen["mensaje"])}</p><p>{resumen["total_historial"]} registros, {resumen["novedades"]} novedades/cambios, {resumen["abiertas"]} abiertas y {resumen["proximas_a_vencer"]} próximas a vencer. Sin filtros comerciales ni límite de cantidad.</p><p>Los registros no observados hoy se conservan; su vigencia calculada requiere confirmar nuevamente la fuente.</p><input id="buscar" aria-label="Buscar" placeholder="Buscar organismo, objeto, pago o estado"><p><a href="reporte_diario.md">Informe diario</a> · <a href="eventos.json">Eventos JSON</a> · <a href="catalogo_completo.json">Catálogo JSON</a></p><div style="overflow:auto"><table><thead><tr>'+''.join('<th>'+t+'</th>' for t in titulos)+'</tr></thead><tbody>'+''.join(filas)+'</tbody></table></div>'
    html+='<script>document.getElementById("buscar").addEventListener("input",function(){const q=this.value.toLocaleLowerCase();document.querySelectorAll("tbody tr").forEach(r=>r.hidden=!r.textContent.toLocaleLowerCase().includes(q));});</script></html>'
    (destino/'index.html').write_text(html,encoding='utf-8')
    return resumen

def _ejecutar_corrida(raiz,*,total=600,documentos=120,informe_previo=None):
    raiz=validar_salida(raiz);antes=huellas_produccion();config=fuentes_configuradas()
    carpeta=raiz/'ejecuciones'/(datetime.now(o.ZONA).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]);carpeta.mkdir(parents=True)
    informe=informe_previo or ejecutar(config,carpeta/'verificacion.json',concurrencia=4,conexion=5,lectura=10,por_fuente=60,total=total)
    registros=registros_checkpoint(informe)
    comprobar_pliegos.comprobar(registros,informe['actualizado'],config,total=documentos,salida_parcial=carpeta/'documentos_parciales.jsonl')
    registros=[o.normalizar(r,informe['actualizado']) for r in registros]
    fuentes=[]
    for obs in informe['observaciones']:
        filas=[r for r in registros if obs['url'] in inc.fuentes_de(r)]
        fuentes.append({**obs,'estado_cobertura':estado_cobertura(obs,filas)})
    informe={**informe,'observaciones':fuentes}
    guardar(carpeta/'auditoria_fuentes.json',{'fuentes':fuentes})
    db=inc.abrir(raiz/'estado.sqlite3')
    try:
        resumen=inc.registrar(db,registros,informe)
        resumen.update(fuentes_configuradas=informe['resumen']['configuradas'],fuentes_consultadas=informe['resumen']['consultadas'],fuentes_finalizadas=informe['resumen']['finalizadas'])
        resumen=generar_informe(db,resumen,registros,fuentes,carpeta)
        guardar(raiz/'ultima_ejecucion.json',{'directorio':str(carpeta.relative_to(raiz)),**resumen})
    finally:db.close()
    despues=huellas_produccion()
    guardar(carpeta/'integridad_produccion.json',{'antes':antes,'despues':despues,'intacto':antes==despues})
    if antes!=despues:raise RuntimeError('Cambió producción durante el piloto')
    sellar_estado(raiz)
    portada=f'<!doctype html><html lang="es"><meta charset="utf-8"><title>Piloto del radar</title><h1>Piloto del radar</h1><p>{escape(resumen["estado"])} · {escape(resumen["fecha"])}</p><p><a href="{escape(str(carpeta.relative_to(raiz)),quote=True)}/index.html">Abrir último informe completo</a></p><p>Entorno controlado. No es producción.</p></html>'
    (raiz/'index.html').write_text(portada,encoding='utf-8')
    print('CONTROLADO_RESUMEN '+json.dumps(resumen,ensure_ascii=False),flush=True)
    return resumen,carpeta,informe,registros

def ejecutar_corrida(raiz,**kwargs):
    raiz=validar_salida(raiz);antes=huellas_produccion()
    guardar(raiz/'progreso_actual.json',{'estado':'EN_CURSO','fecha':datetime.now(o.ZONA).isoformat()})
    try:
        resultado=_ejecutar_corrida(raiz,**kwargs)
        guardar(raiz/'progreso_actual.json',{'estado':resultado[0]['estado'],'corrida':resultado[0]['corrida'],'fecha':resultado[0]['fecha']})
        return resultado
    except BaseException as e:
        guardar(raiz/'progreso_actual.json',{'estado':'INCOMPLETA','fecha':datetime.now(o.ZONA).isoformat(),'error':str(e)})
        (raiz/'index.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><h1>Ejecución incompleta</h1><p>'+escape(str(e))+'</p><p>El estado anterior se conserva. Revisar checkpoints y auditoría; no se presume ausencia de novedades.</p></html>',encoding='utf-8')
        raise
    finally:
        despues=huellas_produccion()
        guardar(raiz/'integridad_produccion.json',{'antes':antes,'despues':despues,'intacto':antes==despues})
        if antes!=despues:raise RuntimeError('Producción cambió durante una ejecución controlada')

def sellar_estado(raiz):
    raiz=validar_salida(raiz);path=raiz/'estado.sqlite3'
    if not path.exists():return
    db=inc.abrir(path)
    try:
        total=db.execute('SELECT COUNT(*) FROM procedimientos').fetchone()[0]
        corridas=db.execute('SELECT COUNT(*) FROM ejecuciones').fetchone()[0]
    finally:db.close()
    guardar(raiz/'estado_manifest.json',{'schema_version':inc.VERSION,'sha256':sha256(path.read_bytes()).hexdigest(),
        'procedimientos':total,'corridas':corridas,'github_run_id':os.environ.get('GITHUB_RUN_ID'),'revision':os.environ.get('GITHUB_SHA')})

def comprobar_estado(raiz):
    raiz=validar_salida(raiz);meta=json.loads((raiz/'estado_manifest.json').read_text())
    path=raiz/'estado.sqlite3'
    if meta.get('schema_version')!=inc.VERSION or sha256(path.read_bytes()).hexdigest()!=meta.get('sha256'):raise ValueError('El estado restaurado no supera su integridad; no se inicia una base vacía')
    db=inc.abrir(path);db.close()

def prueba_doble(raiz,total=600,documentos=120):
    raiz=validar_salida(raiz)
    if (raiz/'estado.sqlite3').exists():raise ValueError('La prueba doble requiere un directorio nuevo; no se borra un historial existente')
    primero,dir1,_,_=ejecutar_corrida(raiz,total=total,documentos=documentos)
    db=inc.abrir(raiz/'estado.sqlite3');ids1={r[0] for r in db.execute('SELECT id FROM procedimientos')};db.close()
    segundo,dir2,informe,registros=ejecutar_corrida(raiz,total=total,documentos=documentos)
    db=inc.abrir(raiz/'estado.sqlite3')
    try:
        eventos=inc.eventos(db,segundo['corrida'],segundo['fecha'])
        repetidas=[e['id'] for e in eventos if e['id'] in ids1 and e['clasificacion_novedad'] in ('NUEVO_CONFIRMADO','NUEVA_DETECCION_FECHA_DESCONOCIDA','NUEVA_DETECCION_MISMO_DIA')]
        replay=inc.registrar(db,registros,{**informe,'ejecucion_id':informe['ejecucion_id']+'-replay-estable'})
    finally:db.close()
    sellar_estado(raiz)
    r={'primera':primero,'segunda':segundo,'repetidas_como_nuevas':len(repetidas),'replay_sin_red':replay,
        'correcta':primero['novedades']==0 and primero['total_historial']>0 and primero['estado']!='INCOMPLETA' and segundo['estado']!='INCOMPLETA' and not repetidas and replay['novedades']==0 and replay['clasificacion'].get('MODIFICADO',0)==0 and replay['clasificacion'].get('DATOS_COMPLETADOS',0)==0}
    guardar(raiz/'prueba_doble.json',r)
    print('PRUEBA_DOBLE '+json.dumps(r,ensure_ascii=False),flush=True)
    if not r['correcta']:raise RuntimeError('Falló la verificación incremental')
    return r

def main():
    p=argparse.ArgumentParser();p.add_argument('--salida',default='work/controlado');p.add_argument('--doble',action='store_true');p.add_argument('--total',type=float,default=600);p.add_argument('--documentos',type=float,default=120);p.add_argument('--inicializar',action='store_true');p.add_argument('--comprobar-estado',action='store_true');p.add_argument('--sellar-estado',action='store_true');a=p.parse_args()
    if a.comprobar_estado:comprobar_estado(a.salida);return
    if a.sellar_estado:sellar_estado(a.salida);return
    if not 1<=a.total<=600 or not 1<=a.documentos<=180:p.error('Límites fuera de rango')
    if a.doble:prueba_doble(a.salida,a.total,a.documentos)
    else:
        raiz=validar_salida(a.salida)
        if not (raiz/'estado.sqlite3').exists() and not a.inicializar:p.error('Falta estado previo: restaurarlo o solicitar explícitamente una primera línea de base con --inicializar')
        resumen,_,_,_=ejecutar_corrida(raiz,total=a.total,documentos=a.documentos)
        if resumen['estado']=='INCOMPLETA':raise SystemExit(2)

if __name__=='__main__':main()
