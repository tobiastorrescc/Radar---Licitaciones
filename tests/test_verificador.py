"""Simula bloqueos en procesos reales; no depende de portales externos."""
import contextlib
import io
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError, URLError
from http.client import HTTPConnection, HTTPSConnection
import conectores as c
from tools import verificar_fuentes as v


class VerificadorTests(unittest.TestCase):
    def fuente(self, numero, **extras):
        return {'id':str(numero),'url':f'https://example.org/{numero}',**extras}

    def comando(self, fuente, checkpoint):
        """Worker sintético que guarda las mismas fases que el conector."""
        tipo=fuente.get('fixture','ok')
        cantidad=fuente.get('cantidad',1)
        data={'fase':'DESCARGA','paginas_visitadas':1,'paginas_correctas':0,
              'errores':[],'limites':[],'oportunidades':[],'finalizado':False}
        if tipo in ('ok','parcial','extraccion'):
            data.update(fase='EXTRACCION',paginas_correctas=1)
        if tipo in ('ok','parcial'):
            data['oportunidades']=[{'id':str(n),'titulo':f'Compra menor {n}/2026','url':fuente['url']} for n in range(cantidad)]
        if fuente.get('objeto_nulo'):
            for item in data['oportunidades']:item['objeto']=None
        if tipo=='red':
            data.update(estado='BLOQUEADA',finalizado=True,
                errores=[{'categoria':'RED','tipo':'URLError','error':'bloqueo','timeout':False}])
        if tipo=='extraccion':
            data.update(estado='PENDIENTE',finalizado=True,
                errores=[{'categoria':'EXTRACCION','tipo':'ValueError','error':'PDF ilegible','timeout':False}])
        if tipo=='ok':
            data.update(estado='OPERATIVA',finalizado=True)
        codigo='import json,os,time,sys\nfrom pathlib import Path\np=Path(sys.argv[1])\n'
        codigo+='d=json.loads(sys.argv[2])\nt=p.with_suffix(".tmp")\nt.write_text(json.dumps(d))\nos.replace(t,p)\n'
        if tipo in ('lento','parcial','terco'):
            if tipo=='terco': codigo+='import signal\nsignal.signal(signal.SIGTERM,signal.SIG_IGN)\n'
            codigo+='time.sleep(60)\n'
        if tipo=='crash': codigo+='sys.exit(7)\n'
        return [sys.executable,'-u','-c',codigo,str(checkpoint),json.dumps(data)]

    def ejecutar(self, fuentes, **opciones):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.salida=Path(self.temp.name)/'verificacion.json'
        self.logs=[]
        return v.ejecutar(fuentes,self.salida,concurrencia=opciones.pop('concurrencia',2),
            por_fuente=opciones.pop('por_fuente',0.6),total=opciones.pop('total',4),
            intervalo=0.1,comando=self.comando,emitir=self.logs.append,**opciones)

    def test_objeto_desconocido_no_interrumpe_supervisor(self):
        r=self.ejecutar([self.fuente(1,objeto_nulo=True),self.fuente(2)])
        self.assertEqual(r['estado_ejecucion'],'COMPLETADA')
        self.assertEqual(r['resumen']['finalizadas'],2)
        self.assertTrue(any('RESUMEN' in linea for linea in self.logs))
        guardado=json.loads(self.salida.read_text())
        self.assertEqual(guardado['resumen']['consultadas'],2)

    def test_portal_bloqueado_no_frena_otros_y_clasifica(self):
        r=self.ejecutar([self.fuente(1,fixture='red'),self.fuente(2),self.fuente(3,fixture='extraccion')])
        self.assertEqual(r['resumen']['consultadas'],3)
        self.assertEqual(r['resumen']['funcionaron'],1)
        self.assertEqual(r['resumen']['fallaron'],2)
        self.assertEqual(r['resumen']['fuentes_error_red'],1)
        self.assertEqual(r['resumen']['fuentes_error_extraccion'],1)
        self.assertTrue(any('CONSULTANDO' in s for s in self.logs))
        self.assertTrue(any('segundos' in s and 'FIN' in s for s in self.logs))

    def test_timeout_duro_no_espera_worker_terco(self):
        inicio=time.monotonic()
        r=self.ejecutar([self.fuente(1,fixture='terco'),self.fuente(2)])
        self.assertLess(time.monotonic()-inicio,3)
        self.assertEqual(r['observaciones'][0]['estado'],'TIEMPO_FUENTE')
        self.assertEqual(r['resumen']['fuentes_timeout'],1)
        self.assertTrue(any('PROGRESO' in s for s in self.logs))
        self.assertEqual(r['resumen']['funcionaron'],1)
        self.assertEqual(r['resumen']['fuentes_error_red'],1)

    def test_preserva_todas_publicaciones_ante_timeout(self):
        r=self.ejecutar([self.fuente(1,fixture='parcial',cantidad=500)])
        f=r['observaciones'][0]
        self.assertEqual(f['estado'],'TIEMPO_FUENTE')
        self.assertEqual(f['publicaciones_detectadas'],500)
        self.assertEqual(len(json.loads(Path(f['resultado_archivo']).read_text())['oportunidades']),500)
        self.assertEqual(r['resumen']['fuentes_error_extraccion'],1)

    def test_plazo_total_marca_no_iniciadas_y_preserva_rapida(self):
        inicio=time.monotonic()
        r=self.ejecutar([self.fuente(1),self.fuente(2,fixture='lento'),self.fuente(3)],
                        concurrencia=1,por_fuente=10,total=0.7)
        self.assertLess(time.monotonic()-inicio,3)
        self.assertEqual(r['estado_ejecucion'],'TIEMPO_TOTAL')
        self.assertEqual(r['resumen']['funcionaron'],1)
        self.assertEqual(r['resumen']['no_iniciadas'],1)
        self.assertEqual(r['observaciones'][1]['estado'],'TIEMPO_TOTAL')
        self.assertEqual(r['observaciones'][2]['estado'],'NO_INICIADA')
        self.assertEqual(r['resumen']['fuentes_presupuesto_o_cancelacion'],1)

    def test_concurrencia_limitada_y_efectiva(self):
        inicio=time.monotonic()
        r=self.ejecutar([self.fuente(n,fixture='lento') for n in range(4)],concurrencia=2,por_fuente=0.5)
        self.assertLess(time.monotonic()-inicio,2.5)
        activos=0;maximos=0
        for s in self.logs:
            if ' CONSULTANDO ' in s: activos+=1;maximos=max(maximos,activos)
            if ' FIN ' in s: activos-=1
            self.assertLessEqual(activos,2)
        self.assertEqual(maximos,2)
        self.assertEqual(r['resumen']['finalizadas'],4)

    def test_crash_worker_no_frena_y_error_interno(self):
        r=self.ejecutar([self.fuente(1,fixture='crash'),self.fuente(2)])
        self.assertEqual(r['resumen']['fuentes_error_interno'],1)
        self.assertEqual(r['resumen']['funcionaron'],1)

    def test_guarda_antes_de_terminar_y_sin_resultados_antiguos(self):
        lecturas=[]
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        salida=Path(self.temp.name)/'verificacion.json'
        salida.write_text('{"ejecucion_id":"antigua"}')
        def observar(log):
            if 'PROGRESO' in log:
                lecturas.append(json.loads(salida.read_text()))
        r=v.ejecutar([self.fuente(1,fixture='lento')],salida,por_fuente=0.5,total=2,
                    intervalo=0.05,comando=self.comando,emitir=observar)
        self.assertTrue(lecturas)
        self.assertTrue(all(l['ejecucion_id']!='antigua' for l in lecturas))
        self.assertTrue(any(l['estado_ejecucion']=='EN_CURSO' for l in lecturas))
        carpeta=Path(r['observaciones'][0]['resultado_archivo']).parent
        self.assertTrue((carpeta/'auditoria.jsonl').exists())
        self.assertEqual(json.loads((carpeta/'resumen.json').read_text())['estado_ejecucion'],'COMPLETADA')

    @unittest.skipUnless(os.name=='posix','Señales POSIX')
    def test_cancelacion_preserva_parciales_y_termina_hijos(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        salida=Path(self.temp.name)/'verificacion.json'
        anterior=signal.getsignal(signal.SIGTERM)
        def cancelar(log):
            if 'PROGRESO' in log: os.kill(os.getpid(),signal.SIGTERM)
        r=v.ejecutar([self.fuente(1,fixture='parcial'),self.fuente(2)],salida,concurrencia=1,
                    total=4,por_fuente=3,intervalo=0.1,comando=self.comando,emitir=cancelar)
        self.assertEqual(r['estado_ejecucion'],'CANCELADA')
        self.assertEqual(r['observaciones'][0]['estado'],'CANCELADA')
        self.assertEqual(r['resumen']['no_iniciadas'],1)
        self.assertEqual(signal.getsignal(signal.SIGTERM),anterior)

    def test_no_escribe_historial_de_produccion(self):
        r=self.ejecutar([self.fuente(1)])
        for nombre in ('radar_estado.json','licitaciones_nuevas.json','auditoria_fuentes.json'):
            archivo=Path(self.temp.name)/nombre;archivo.write_text('historial anterior')
            with self.assertRaises(ValueError):
                v.ejecutar([],archivo,emitir=lambda x:None)
            self.assertEqual(archivo.read_text(),'historial anterior')

    def test_valida_presupuestos(self):
        with tempfile.TemporaryDirectory() as d:
            for opciones in [{'total':0},{'lectura':float('nan')},{'concurrencia':20},{'por_fuente':-1}]:
                with self.assertRaises(ValueError):
                    v.ejecutar([],Path(d)/'resultado.json',**opciones)

    def test_worker_real_finaliza_y_clasifica(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fuente.json';cp=Path(d)/'checkpoint.json'
            path.write_text(json.dumps(self.fuente(1)))
            with patch.object(c,'descargar',side_effect=URLError('bloqueo')):
                v.worker(path,cp,0.1,0.2,2)
            data=json.loads(cp.read_text())
            self.assertTrue(data['finalizado'])
            self.assertEqual(data['estado'],'BLOQUEADA')
            self.assertEqual(data['errores'][0]['categoria'],'RED')

    def test_timeout_conexion_y_lectura_separados(self):
        for cls,base in [(c._HTTPAcotada,HTTPConnection),(c._HTTPSAcotada,HTTPSConnection)]:
            conn=cls('example.org',timeout=0.15,lectura_timeout=0.25)
            conn.sock=Mock()
            with patch.object(base,'connect'):
                conn.connect()
            self.assertEqual(conn.timeout,0.15)
            conn.sock.settimeout.assert_called_once_with(0.25)
        with patch.object(c,'build_opener') as build:
            opener=build.return_value
            response=opener.open.return_value.__enter__.return_value
            response.read.return_value=b'<html></html>'
            response.headers.get.return_value='text/html'
            response.geturl.return_value='https://example.org/'
            c.descargar('https://example.org/',conexion_timeout=0.15,lectura_timeout=0.25)
            self.assertEqual(opener.open.call_args.kwargs['timeout'],0.15)
            self.assertEqual(build.call_args.args[0].lectura_timeout,0.25)
            self.assertEqual(build.call_args.args[1].lectura_timeout,0.25)

    def test_error_red_y_error_pdf_diferenciados(self):
        for e in [URLError('DNS'),HTTPError('u',403,'bloqueado',{},None),TimeoutError('lento')]:
            self.assertEqual(c.clasificar_error(e,'DESCARGA')['categoria'],'RED')
        self.assertTrue(c.clasificar_error(URLError(TimeoutError('lectura')),'DESCARGA')['timeout'])
        self.assertEqual(c.clasificar_error(ValueError('PDF'),'EXTRACCION')['categoria'],'EXTRACCION')

    def test_checkpoint_conector_sobrevive_error_y_preserva_publicaciones(self):
        eventos=[]
        def fetch(url):
            if url.endswith('/2'): raise URLError('error')
            return (b'<li>Compra menor 8/2026 papel</li><a rel="next" href="/2">2</a>', 'text/html',url)
        r=c.explorar('https://example.org/',{},fetch=fetch,progreso=eventos.append)
        self.assertEqual(r['estado'],'PARCIAL')
        self.assertEqual(len(eventos[-1]['oportunidades']),1)
        self.assertEqual(eventos[-1]['errores'][0]['categoria'],'RED')
        self.assertIn('DESCARGA',{e['fase'] for e in eventos})
        self.assertIn('EXTRACCION',{e['fase'] for e in eventos})

    def test_http_real_rapido_lento_bloqueado_y_extraccion(self):
        # Se ejecuta en Actions; el executor puede prohibir incluso sockets locales.
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        import threading
        class Portal(BaseHTTPRequestHandler):
            def log_message(self, *args): pass
            def do_GET(self):
                try:
                    if self.path == '/bloqueado':
                        self.send_error(403); return
                    if self.path == '/lento': time.sleep(0.5)
                    body=(b'<li>Compra menor 8/2026 papel</li>' if self.path=='/ok' else b'<html>Cargando</html>')
                    self.send_response(200)
                    self.send_header('Content-Type','text/html')
                    self.send_header('Content-Length',str(len(body)))
                    self.end_headers();self.wfile.write(body)
                except (BrokenPipeError,ConnectionResetError): pass
        try:
            server=ThreadingHTTPServer(('127.0.0.1',0),Portal)
        except PermissionError:
            self.skipTest('El executor prohíbe sockets locales; casos HTTP reales se ejecutan en Actions')
        hilo=threading.Thread(target=lambda:server.serve_forever(poll_interval=0.05),daemon=True)
        hilo.start()
        try:
            with tempfile.TemporaryDirectory() as d, patch.dict(os.environ,{'no_proxy':'127.0.0.1','NO_PROXY':'127.0.0.1'}):
                base='http://127.0.0.1:'+str(server.server_port)
                fuentes=[{'id':str(i),'url':base+p} for i,p in enumerate(['/ok','/lento','/bloqueado','/vacio'])]
                r=v.ejecutar(fuentes,Path(d)/'verificacion.json',conexion=0.2,lectura=0.1,
                    por_fuente=3,total=8,concurrencia=4,emitir=lambda x:None)
                self.assertEqual(r['resumen']['funcionaron'],1)
                self.assertEqual(r['resumen']['fuentes_error_red'],2)
                self.assertEqual(r['resumen']['fuentes_error_extraccion'],1)
                self.assertEqual(r['resumen']['fuentes_timeout'],1)
                datos={o['id']:o for o in r['observaciones']}
                self.assertEqual(datos['2']['errores'][0]['http_status'],403)
        finally:
            server.shutdown();server.server_close();hilo.join(timeout=2)


if __name__=='__main__': unittest.main()
