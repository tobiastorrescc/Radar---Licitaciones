import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import subprocess
import documentos
import incremental as inc
from tools.auditar_evolucion import comparar,instantanea,ejecutar

class AuditoriaTests(unittest.TestCase):
    def test_separa_historia_de_nuevas_y_cambios_sin_omitir(self):
        a={'ids':['a'],'versiones':[['a','1']],'corrida':'ayer','fecha':'2026-10-29','fuentes':{}}
        b={**a,'ids':['a','b'],'corrida':'hoy'}
        e=[{'clasificacion_novedad':k,'id':str(i)} for i,k in enumerate(('NUEVO_CONFIRMADO','RECUPERACION_LINEA_BASE','MODIFICADO','NUEVA_DETECCION_FECHA_DESCONOCIDA'))]
        r=comparar(a,b,[],e)
        self.assertEqual(r['conteos'],{'nuevas_confirmadas':1,'detecciones_sin_fecha_suficiente':1,'recuperaciones_historicas':1,'modificaciones':1,'datos_completados':0})
        self.assertFalse(r['ids_perdidos'])
    def test_sin_corrida_nueva_no_reemite_eventos_anteriores(self):
        a={'ids':['a'],'versiones':[['a','1']],'corrida':'ayer','fuentes':{},'fecha':'2026-10-29'}
        r=comparar(a,a,[],[{'clasificacion_novedad':'NUEVO_CONFIRMADO'}])
        self.assertEqual(r['estado'],'SIN_NUEVA_EJECUCION');self.assertEqual(sum(r['conteos'].values()),0)
    def test_detecta_perdida_de_versiones_y_ids(self):
        a={'ids':['a'],'versiones':[['a','1']],'corrida':'ayer','fuentes':{},'fecha':'2026-10-29'}
        b={**a,'ids':[],'versiones':[],'corrida':'hoy'}
        r=comparar(a,b,[],[])
        self.assertEqual(r['estado'],'HISTORIAL_PERDIDO');self.assertEqual(r['ids_perdidos'],['a'])
    def test_variantes_duplicadas_con_fechas_distintas_quedan_visibles(self):
        with tempfile.TemporaryDirectory() as d:
            db=inc.abrir(Path(d)/'estado.sqlite3')
            for i,fecha in enumerate(('2026-10-05','2026-10-26')):
                r={'titulo':'Licitación Pública 8/2026','numero_procedimiento':'8/2026','organismo':'Municipalidad de Federación','provincia':'Entre Ríos','fecha_apertura':fecha,'url':'https://federacion.gob.ar/pliego.pdf','objeto':'Venta de lotes'}
                db.execute('INSERT INTO procedimientos VALUES (?,?,?,?,?,?)',(str(i),'2026-10-01','2026-10-29','hoy',str(i),json.dumps(r)))
            db.commit();rs=inc.actuales(db,'2026-10-29T12:00:00-03:00','hoy');db.close()
            self.assertEqual(len(rs),1);self.assertEqual(rs[0]['unificacion_estado'],'REQUIERE_REVISION')
            self.assertEqual(len(rs[0]['variantes_historial']),2);self.assertEqual(len(rs[0]['ids_historial']),2)

class OCRSelectivoTests(unittest.TestCase):
    def test_cupo_y_cache_por_pagina_reanuda_sin_repetir(self):
        with tempfile.TemporaryDirectory() as d:
            llamadas=[]
            def run(args,**kw):
                llamadas.append(args)
                if args[0]=='pdftotext':return subprocess.CompletedProcess(args,0,stdout=b'\f\f\f')
                if args[0]=='pdfinfo':return subprocess.CompletedProcess(args,0,stdout='Pages: 3\n')
                if args[0]=='tesseract':return subprocess.CompletedProcess(args,0,stdout='Pago contado contra entrega del material.')
                return subprocess.CompletedProcess(args,0,stdout=b'')
            with patch('cache_documentos.raiz',return_value=Path(d)),patch('documentos.subprocess.run',side_effect=run):
                _,a=documentos.ocr_selectivo(b'%PDF-fixture',1)
                self.assertFalse(a['completa']);self.assertEqual(a['paginas_ocr_nuevas'],[1])
                _,b=documentos.ocr_selectivo(b'%PDF-fixture',2)
                self.assertTrue(b['completa']);self.assertEqual(b['paginas_ocr_nuevas'],[2,3])
                _,c=documentos.ocr_selectivo(b'%PDF-fixture',2)
                self.assertEqual(c['paginas_ocr_nuevas'],[])
                self.assertEqual(sum(x[0]=='tesseract' for x in llamadas),3)

class PagosCompatiblesTests(unittest.TestCase):
    def test_contado_contra_entrega_no_se_contradice_con_su_repeticion(self):
        import pagos
        e=pagos.extraer('Forma de pago: Contado contra entrega.\n\nEl pago se efectuará contra entrega del producto.','https://oficial.gob.ar/pliego.pdf','hash')
        r=pagos.consolidar(e)
        self.assertEqual(r['estado'],'VERIFICADO');self.assertEqual(r['clasificacion'],'CONTADO')
        self.assertIn('contra entrega',r['etiqueta'])
    def test_documentos_distintos_con_condiciones_distintas_no_se_presumen_compatibles(self):
        import pagos
        a=pagos.extraer('Forma de pago: Contado contra entrega.','https://oficial.gob.ar/a.pdf','a')
        b=pagos.extraer('Forma de pago: contra entrega.','https://oficial.gob.ar/b.pdf','b')
        self.assertEqual(pagos.consolidar(a+b)['estado'],'PENDIENTE')

class AccesoTests(unittest.TestCase):
    def test_no_confunde_timeout_tls_y_500_con_restriccion(self):
        import conectores as c
        for e,causa in [({'http_status':500},'ERROR_SERVIDOR_TEMPORAL'),({'timeout':True},'TIEMPO_ESPERA'),({'error':'certificate verify failed'},'ERROR_CERTIFICADO_TLS')]:
            r=c.diagnostico_error(e);self.assertEqual(r['causa'],causa);self.assertFalse(r['restriccion_acceso_comprobada'])
        self.assertTrue(c.diagnostico_error({'http_status':403})['restriccion_acceso_comprobada'])

class DocumentoOCRTests(unittest.TestCase):
    def test_cita_en_ocr_parcial_no_se_declara_verificada(self):
        from tools import comprobar_pliegos as c
        url='https://oficial.gob.ar/pliego.pdf'
        with patch.object(c.cache_documentos,'obtener',return_value=(b'%PDF-test','application/pdf',url,{'cache_estado':'CACHE_RECIENTE'})),patch.object(c.cache_documentos,'leer_texto',side_effect=ValueError('PDF sin texto')),patch.object(c.documentos,'ocr_selectivo',return_value=('Forma de pago: contado contra entrega.',{'completa':False,'paginas_pendientes':[2]})):
            r=c.worker(url,opciones={'ocr_selectivo':True})
            self.assertEqual(r['pagos'],[]);self.assertTrue(r['pagos_pendientes_revision']);self.assertTrue(r['lectura_pendiente'])
    def test_worker_sin_cupo_no_dispara_ocr(self):
        from tools import comprobar_pliegos as c
        url='https://oficial.gob.ar/pliego.pdf'
        with patch.object(c.cache_documentos,'obtener',return_value=(b'%PDF-test','application/pdf',url,{'cache_estado':'CACHE_RECIENTE'})),patch.object(c.cache_documentos,'leer_texto',side_effect=ValueError('PDF sin texto')),patch.object(c.documentos,'ocr_selectivo') as lector:
            r=c.worker(url);lector.assert_not_called();self.assertIn('lectura_pendiente',r)

    def test_ocr_completo_cacheado_se_reutiliza_sin_nuevo_cupo(self):
        from tools import comprobar_pliegos as c
        url='https://oficial.gob.ar/pliego.pdf'
        with patch.object(c.cache_documentos,'obtener',return_value=(b'%PDF-test','application/pdf',url,{'cache_estado':'CACHE_RECIENTE'})),patch.object(c.cache_documentos,'leer_texto',side_effect=ValueError('PDF sin texto')),patch.object(c.documentos,'ocr_en_cache',return_value=('Forma de pago: contado contra entrega.',{'completa':True,'paginas_ocr_nuevas':[]})),patch.object(c.documentos,'ocr_selectivo') as lector:
            r=c.worker(url);lector.assert_not_called();self.assertTrue(r['pagos']);self.assertFalse(r.get('lectura_pendiente'));self.assertEqual(r['ocr_selectivo']['paginas_ocr_nuevas'],[])
