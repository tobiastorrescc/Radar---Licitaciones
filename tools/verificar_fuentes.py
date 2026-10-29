"""Verificación aislada, acotada y con avances persistidos; nunca escribe producción."""
import argparse
from collections import Counter, deque
from datetime import datetime
from functools import partial
import json
import math
import re
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid
from zoneinfo import ZoneInfo
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import conectores
import cache_documentos
import registro_fuentes
from urllib.parse import urlparse


def ahora():
    return datetime.now(ZoneInfo('America/Argentina/Buenos_Aires')).isoformat()


def guardar(path, data):
    path = Path(path)
    temporal = path.with_suffix(path.suffix + '.tmp')
    temporal.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporal, path)


def leer_checkpoint(path):
    try:
        return json.loads(Path(path).read_text(encoding='utf-8'))
    except FileNotFoundError:
        return {}


def worker(config, checkpoint, conexion, lectura, max_paginas):
    fuente = json.loads(Path(config).read_text(encoding='utf-8'))
    inicio = time.monotonic()
    def progreso(r):
        guardar(checkpoint, {**r, 'actualizado': ahora(), 'duracion_segundos': round(time.monotonic()-inicio, 3)})
    transporte=partial(conectores.descargar, conexion_timeout=fuente.get('conexion_timeout',conexion), lectura_timeout=fuente.get('lectura_timeout',lectura))
    def fetch(url,datos_post=None):
        es_documento=urlparse(url).path.lower().endswith(('.pdf','.docx','.zip','.jpg','.jpeg','.png','.xls','.xlsx')) or any(re.search(p,url) for p in fuente.get('patrones_documentos',[]))
        if fuente.get('capturar_respuestas') and not es_documento:
            from hashlib import sha256
            datos,tipo,final=transporte(url,datos_post=datos_post) if datos_post is not None else transporte(url)
            if 'html' in tipo.lower() or 'json' in tipo.lower():
                base=Path(checkpoint).parent/'capturas'/fuente['id'];base.mkdir(parents=True,exist_ok=True)
                nombre=sha256(url.encode()+(datos_post or b'')).hexdigest()
                (base/(nombre+'.txt')).write_bytes(datos)
                guardar(base/(nombre+'.json'),{'url':url,'final':final,'tipo':tipo,'sha256':sha256(datos).hexdigest(),'metodo':'POST' if datos_post is not None else 'GET','parametros':datos_post.decode() if datos_post else None})
            return datos,tipo,final
        if es_documento:return cache_documentos.obtener(url,transport=transporte)[:3]
        return transporte(url,datos_post=datos_post) if datos_post is not None else transporte(url)
    try:
        r = conectores.explorar(fuente['url'], fuente, max_paginas=max_paginas, progreso=progreso,
            fetch=fetch)
    except Exception as e:
        r = {**leer_checkpoint(checkpoint), 'estado': 'ERROR', 'finalizado': True,
             'errores': [{'categoria': 'INTERNO', 'tipo': type(e).__name__, 'timeout': False, 'error': str(e)}]}
    progreso({**r, 'finalizado': True})


def detener(proceso):
    """No espera hilos bloqueados. También detiene pdftotext del mismo grupo."""
    try:
        if os.name == 'posix':
            os.killpg(proceso.pid, signal.SIGKILL)
        elif proceso.poll() is None:
            proceso.kill()
    except ProcessLookupError:
        pass
    proceso.wait(timeout=2)


def resumen(observaciones):
    terminadas = [r for r in observaciones if r['estado'] not in ('NO_INICIADA', 'EN_CURSO')]
    intentadas = [r for r in observaciones if r['iniciada']]
    exitosas = [r for r in terminadas if r['estado'] in ('OPERATIVA','SIN_PUBLICACIONES')]
    fallidas = [r for r in terminadas if r['iniciada'] and r['estado'] not in ('OPERATIVA','SIN_PUBLICACIONES')]
    errores = Counter(e['categoria'] for r in intentadas for e in r.get('errores', []))
    return {'configuradas': len(observaciones), 'consultadas': len(intentadas),
        'finalizadas': sum(r['iniciada'] for r in terminadas), 'funcionaron': len(exitosas),
        'parciales_con_publicaciones': sum(r.get('publicaciones_detectadas',0)>0 and r['estado']!='OPERATIVA' for r in terminadas),
        'sin_publicaciones_confirmado': sum(r['estado']=='SIN_PUBLICACIONES' for r in terminadas),
        'con_publicaciones': sum(r.get('publicaciones_detectadas', 0) > 0 for r in intentadas),
        'con_respuesta_procesada': sum(r.get('paginas_correctas', 0) > 0 for r in intentadas),
        'fallaron': len(fallidas), 'no_iniciadas': len(observaciones)-len(intentadas),
        'fuentes_error_red': sum(any(e['categoria']=='RED' for e in r.get('errores', [])) for r in fallidas),
        'fuentes_error_extraccion': sum(any(e['categoria']=='EXTRACCION' for e in r.get('errores', [])) for r in fallidas),
        'fuentes_acceso_restringido': sum(any(e['categoria']=='ACCESO' for e in r.get('errores', [])) for r in fallidas),
        'fuentes_error_interno': sum(any(e['categoria']=='INTERNO' for e in r.get('errores', [])) for r in fallidas),
        'fuentes_timeout': sum(any(e.get('timeout') for e in r.get('errores', [])) for r in fallidas),
        'fuentes_presupuesto_o_cancelacion': sum(any(e['categoria']=='PRESUPUESTO' for e in r.get('errores', [])) for r in fallidas),
        'errores_por_categoria': dict(errores)}


def ejecutar(fuentes, salida, *, concurrencia=4, conexion=5, lectura=10,
             por_fuente=60, total=600, max_paginas=1000, intervalo=1,
             comando=None, emitir=None):
    """Supervisor de procesos; comando/emitir permiten probar aislamiento real.

    El deadline incluye el arranque del worker. Al agotarse termina los procesos,
    conserva sus checkpoints y marca los pendientes como NO_INICIADA.
    """
    if not 1 <= concurrencia <= 8:
        raise ValueError('La concurrencia debe estar entre 1 y 8')
    if any(not math.isfinite(v) or v <= 0 for v in (conexion, lectura, por_fuente, total, intervalo)):
        raise ValueError('Los tiempos deben ser positivos y finitos')
    if max_paginas < 1:
        raise ValueError('max_paginas debe ser positivo')
    if len({f['id'] for f in fuentes}) != len(fuentes):
        raise ValueError('IDs de fuente duplicados')
    # Ruta de salida fija al área de auditoría; no permite sobrescribir datos de producción.
    salida = Path(salida).resolve()
    protegidos = {'radar_estado.json','licitaciones_nuevas.json','auditoria_fuentes.json'}
    if salida.name in protegidos:
        raise ValueError('La verificación no puede escribir un archivo de producción')
    salida.parent.mkdir(parents=True, exist_ok=True)
    ejecucion = datetime.now().strftime('%Y%m%dT%H%M%S') + '-' + uuid.uuid4().hex[:8]
    directorio = salida.parent / (salida.stem + '_ejecuciones') / ejecucion
    directorio.mkdir(parents=True)
    inicio = time.monotonic()
    fecha = ahora()
    observaciones = [{'id': f['id'], 'url': f['url'], 'estado': 'NO_INICIADA', 'iniciada': False,
                     'publicaciones_detectadas': 0, 'paginas_correctas': 0, 'errores': [],
                     'duracion_segundos': 0, 'limites': []} for f in fuentes]
    pendientes = deque(zip(fuentes, observaciones))
    activos = {}
    cancelada = []
    terminal = 'COMPLETADA'
    emitir = emitir or (lambda mensaje: print(mensaje, flush=True))
    def evento(mensaje, **datos):
        entrada = {'fecha': ahora(), 'mensaje': mensaje, **datos}
        with (directorio/'auditoria.jsonl').open('a', encoding='utf-8') as out:
            out.write(json.dumps(entrada, ensure_ascii=False)+'\n')
            out.flush()
        emitir(f"{entrada['fecha']} {mensaje}" + (' '+json.dumps(datos,ensure_ascii=False) if datos else ''))
    def persistir():
        informe = {'schema_version': 2, 'ejecucion_id': ejecucion, 'github_run_id': os.environ.get('GITHUB_RUN_ID'),
                   'revision': os.environ.get('GITHUB_SHA'), 'fecha': fecha, 'actualizado': ahora(),
                   'estado_ejecucion': terminal if not activos and not pendientes else 'EN_CURSO',
                   'metodo': 'conector HTTP en procesos aislados; sin historial de producción',
                   'duracion_segundos': round(time.monotonic()-inicio,3),
                   'limites': {'conexion_segundos': conexion, 'lectura_segundos': lectura,
                              'fuente_segundos': por_fuente, 'total_segundos': total,
                              'concurrencia': concurrencia, 'max_paginas': max_paginas},
                   'resumen': resumen(observaciones), 'observaciones': observaciones}
        guardar(salida, informe)
        guardar(directorio/'resumen.json', informe)
        return informe
    def cargar_avance(info):
        avance = leer_checkpoint(info['checkpoint'])
        if not avance:
            return
        r = info['registro']
        r.update({k:avance[k] for k in ('paginas_correctas','paginas_visitadas','errores','limites',
                 'fase','url_actual','documentos_leidos','alcance','documentos_pendientes','evidencias_listado_vacio') if k in avance})
        r['publicaciones_detectadas'] = len(avance.get('oportunidades', []))
        r['duracion_segundos'] = round(time.monotonic()-info['inicio'],3)
    def finalizar(info, motivo=None):
        r = info['registro']
        cargar_avance(info)
        avance = leer_checkpoint(info['checkpoint'])
        if motivo:
            fase = r.get('fase')
            categoria = ('RED' if fase == 'DESCARGA' else 'EXTRACCION' if fase == 'EXTRACCION' else 'PRESUPUESTO') if motivo == 'TIEMPO_FUENTE' else 'PRESUPUESTO'
            r['estado'] = motivo
            r['errores'].append({'categoria': categoria, 'tipo': motivo, 'timeout': motivo.startswith('TIEMPO'),
                                 'error': 'Plazo agotado; se conserva lo extraído', 'fase': fase})
        elif not avance.get('finalizado') or 'estado' not in avance or info['proceso'].returncode != 0:
            r['estado'] = 'ERROR'
            r['errores'].append({'categoria':'INTERNO','tipo':'WorkerError','timeout':False,
                'error':f"Worker terminó sin resultado válido (salida {info['proceso'].returncode})"})
        else:
            r['estado'] = avance['estado']
        r['duracion_segundos'] = round(time.monotonic()-info['inicio'],3)
        # Consolida el resultado parcial incluso si el worker fue cortado.
        guardar(info['checkpoint'], {**avance, **r, 'finalizado':True,
                'oportunidades':avance.get('oportunidades',[])})
        info['stderr'].close()
        evento('FIN', id=r['id'], url=r['url'], estado=r['estado'], segundos=r['duracion_segundos'],
               publicaciones=r['publicaciones_detectadas'], errores=dict(Counter(e['categoria'] for e in r['errores'])),
               muestras_errores=list({(e['tipo'],e['error']):{'tipo':e['tipo'],'error':e['error'],'url':e.get('url')} for e in r['errores']}.values())[:5],
               muestra_publicaciones=[{'titulo':str(p.get('titulo') or '')[:300],'objeto':str(p.get('objeto') or '')[:300],'url':p.get('url')} for p in avance.get('oportunidades',[])[:2]])
    def cancelar(signum, frame):
        cancelada.append(signum)
    anteriores = {}
    for sig in (signal.SIGINT, signal.SIGTERM):
        anteriores[sig] = signal.signal(sig, cancelar)
    try:
        evento('INICIO_VERIFICACION', fuentes=len(fuentes), concurrencia=concurrencia,
               fuente_segundos=por_fuente, total_segundos=total)
        persistir()  # Sustituye enseguida cualquier observación antigua.
        proximo_log = inicio
        while pendientes or activos:
            momento = time.monotonic()
            if cancelada or momento-inicio >= total:
                terminal = 'CANCELADA' if cancelada else 'TIEMPO_TOTAL'
                break
            while pendientes and len(activos)<concurrencia:
                if time.monotonic()-inicio >= total or cancelada:
                    break
                f, r = pendientes.popleft()
                archivo = directorio/f"{observaciones.index(r):04d}.json"
                config = archivo.with_suffix('.fuente.json')
                guardar(config, f)
                args = comando(f, archivo) if comando else [sys.executable, '-u', str(Path(__file__).resolve()),
                    '--worker', str(config), '--checkpoint', str(archivo), '--conexion', str(conexion),
                    '--lectura', str(lectura), '--max-paginas', str(max_paginas)]
                r.update(iniciada=True, estado='EN_CURSO', inicio=ahora(), resultado_archivo=str(archivo))
                stderr = archivo.with_suffix('.stderr.log').open('w', encoding='utf-8')
                evento('CONSULTANDO', id=r['id'], url=r['url'])
                try:
                    proceso = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=stderr,
                                               start_new_session=os.name=='posix')
                except OSError as e:
                    stderr.close()
                    r.update(estado='ERROR', errores=[{'categoria':'INTERNO','tipo':type(e).__name__,
                                                       'timeout':False,'error':str(e)}])
                    evento('FIN', id=r['id'], url=r['url'], estado='ERROR', error=str(e))
                    persistir()
                    continue
                activos[proceso.pid] = {'proceso':proceso,'inicio':time.monotonic(),
                                       'registro':r,'checkpoint':archivo,'stderr':stderr}
                persistir()
            for pid, info in list(activos.items()):
                cargar_avance(info)
                proceso = info['proceso']
                if proceso.poll() is not None:
                    # Reap y elimina también descendientes que haya dejado el worker.
                    detener(proceso)
                    finalizar(info)
                    del activos[pid]
                    persistir()
                elif time.monotonic()-info['inicio'] >= por_fuente:
                    detener(proceso)
                    finalizar(info, 'TIEMPO_FUENTE')
                    del activos[pid]
                    persistir()
            if time.monotonic() >= proximo_log:
                for info in activos.values():
                    r=info['registro']
                    evento('PROGRESO', id=r['id'], url=r['url'], segundos=r['duracion_segundos'],
                           fase=r.get('fase','ARRANQUE'), pagina=r.get('url_actual'),
                           publicaciones=r['publicaciones_detectadas'])
                persistir()
                proximo_log=time.monotonic()+intervalo
            if activos:
                time.sleep(min(0.05, max(0, total-(time.monotonic()-inicio))))
    finally:
        for info in activos.values():
            detener(info['proceso'])
            finalizar(info, 'CANCELADA' if cancelada else 'TIEMPO_TOTAL')
        activos.clear()
        for _, r in pendientes:
            r['motivo_no_iniciada'] = terminal
        pendientes.clear()
        informe = persistir()
        evento('RESUMEN', **informe['resumen'], segundos=informe['duracion_segundos'], estado=terminal)
        for sig, handler in anteriores.items():
            signal.signal(sig, handler)
    return informe


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--inventario',default='inventario/fuentes.json')
    parser.add_argument('--salida',default='inventario/verificacion.json')
    parser.add_argument('--concurrencia',type=int,default=4)
    parser.add_argument('--conexion',type=float,default=5)
    parser.add_argument('--lectura',type=float,default=10)
    parser.add_argument('--por-fuente',type=float,default=60)
    parser.add_argument('--total',type=float,default=600)
    parser.add_argument('--max-paginas',type=int,default=1000)
    parser.add_argument('--intervalo',type=float,default=5)
    parser.add_argument('--worker',help=argparse.SUPPRESS)
    parser.add_argument('--checkpoint',help=argparse.SUPPRESS)
    args=parser.parse_args()
    if args.worker:
        worker(args.worker,args.checkpoint,args.conexion,args.lectura,args.max_paginas)
        return 0
    fuentes=json.loads(Path(args.inventario).read_text(encoding='utf-8'))
    urls={f['url'] for f in fuentes}
    fuentes.extend(f for u,f in registro_fuentes.cargar_auto().items() if u not in urls)
    r=ejecutar([f for f in fuentes if f['incorporada']],args.salida,
        concurrencia=args.concurrencia,conexion=args.conexion,lectura=args.lectura,
        por_fuente=args.por_fuente,total=args.total,max_paginas=args.max_paginas,intervalo=args.intervalo)
    return 0 if r['estado_ejecucion']=='COMPLETADA' and r['resumen']['fallaron']==0 else 2


if __name__=='__main__':
    raise SystemExit(main())
