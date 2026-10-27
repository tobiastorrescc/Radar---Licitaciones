import copy
from datetime import datetime
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import conectores
import extractores
import oportunidades as o
from tools import reportar_oportunidades

FECHA='2026-10-26T09:00:00-03:00'
class ComercialTests(unittest.TestCase):
    def base(self,**kw):
        return dict(titulo='Licitación Pública 4/2026 Compra de herramientas',procedimiento='licitacion publica 4/2026',numero_procedimiento='4/2026',tipo_procedimiento='licitacion publica',organismo='Municipio',provincia='Santa Fe',localidad='Rosario',url='https://oficial.gob.ar/llamado',fuente='https://oficial.gob.ar/',detalle_completo=True,**kw)
    def test_fechas(self):
        for t in ['28 de octubre del año 2026','28/10/2026','2026-10-28','28-10-2026']:
            self.assertEqual(o.fecha(t),'2026-10-28')
        self.assertIsNone(o.fecha('31/2/2026'))
        self.assertIsNone(o.fecha('28/10'))
    def test_datos_y_evidencia(self):
        r=o.normalizar(self.base(objeto='Herramientas. Presupuesto oficial ARS 1.234.567,89. Apertura 28/10/2026. Publicado el 20/10/2026. Pago contado'),FECHA)
        self.assertEqual(r['presupuesto'],{'importe':'1234567.89','moneda':'ARS'})
        self.assertEqual(r['fecha_apertura'],'2026-10-28')
        self.assertEqual(r['fecha_publicacion'],'2026-10-20')
        self.assertEqual(r['vigencia'],'ABIERTA')
        self.assertEqual(r['antiguedad_publicacion'],'HISTORICA')
        self.assertIn('fecha_apertura',r['evidencias_campos'])
        self.assertIsNone(r['estimacion_comercial'])
    def test_desconocidos_no_inferidos_del_anio(self):
        r=o.normalizar(self.base(),FECHA)
        for k in ['presupuesto','fecha_apertura','fecha_publicacion','enlace_pliego']:self.assertIsNone(r[k])
        self.assertEqual(r['vigencia'],'DESCONOCIDA')
    def test_no_moneda_inventada_ni_precio_pliego(self):
        self.assertIsNone(o.monto('Costo del pliego $15.000')[0])
        self.assertIsNone(o.monto('Presupuesto $79.500.00,00')[0])
        self.assertIsNone(o.monto('Presupuesto $83.700.000,00')[0]['moneda'])
    def test_vigencia_y_llamados(self):
        for texto,esperado in [('Apertura 25/10/2026','VENCIDA'),('Apertura 26/10/2026','DESCONOCIDA'),('Apertura 27/10/2026','ABIERTA')]:
            self.assertEqual(o.normalizar(self.base(objeto=texto),FECHA)['vigencia'],esperado)
        self.assertEqual(o.normalizar(self.base(situacion_publicada='ADJUDICADA'),FECHA)['vigencia'],'VENCIDA')
        r=o.normalizar(self.base(objeto='Segundo llamado, anterior desierta, reapertura'),FECHA)
        self.assertTrue(all(r[k] for k in ['desierta','segundo_llamado','reapertura']))
    def test_persistencia_no_reescribe_legado_ni_duplica_por_url(self):
        h={'legado':o.normalizar(self.base(),FECHA)};antes=copy.deepcopy(h)
        r=self.base();r['url']='https://oficial.gob.ar/anexo.pdf'
        self.assertEqual(o.incorporar(h,[r],FECHA),[])
        self.assertEqual(h,antes)
    def test_segundo_llamado_nuevo_no_cambio_de_estado(self):
        h={};primero=self.base();o.incorporar(h,[primero],FECHA)
        segundo={**primero,'evento_publicado':'segundo llamado'}
        self.assertEqual(len(o.incorporar(h,[segundo],FECHA)),1)
        self.assertEqual(o.incorporar(h,[{**primero,'situacion_publicada':'ADJUDICADA'}],FECHA),[])
    def test_sin_tope_incluso_vencidas(self):
        h={};items=[{**self.base(objeto='Apertura 1/1/2020'),'numero_procedimiento':f'{i}/2020'} for i in range(1600)]
        nuevos=o.incorporar(h,items,FECHA)
        self.assertEqual(len(nuevos),1600);self.assertTrue(all(r['vigencia']=='VENCIDA' for r in nuevos))
        self.assertEqual(o.incorporar(h,items,FECHA),[])
    def test_tabla_real_crespo(self):
        config=json.loads(Path('fuentes.json').read_text())['https://www.crespo.gob.ar/licitaciones-privadas-2026/']
        rs,_,_=extractores.extraer(Path('tests/fixtures/reales/fuente-038.html').read_text(),'https://www.crespo.gob.ar/licitaciones-privadas-2026/',config)
        r=o.normalizar(rs[0],FECHA)
        self.assertEqual(r['objeto'],'Adquisición de 310 m3 de hormigón elaborado H21.')
        self.assertEqual(r['presupuesto']['importe'],'83700000.00')
        self.assertEqual(r['fecha_apertura'],'2026-10-20')
        self.assertIn('Pliego',r['enlace_pliego'])
    def test_reporte_todo_con_riesgos_desconocidos(self):
        filas=[o.normalizar(self.base(objeto='Pago contado'),FECHA),o.normalizar(self.base(objeto='Apertura 1/1/2020'),FECHA)]
        texto=o.reporte(filas,FECHA)
        self.assertEqual(texto.count('| Municipio /'),2)
        self.assertIn('Condiciones de pago',texto)
        self.assertIn('Documento de respaldo',texto)
        self.assertNotIn('Rentabilidad potencial',texto)
    def test_cache_solo_texto_lectura_contenido_revalidado(self):
        with tempfile.TemporaryDirectory() as d,patch.dict('os.environ',{'RADAR_CACHE_DOCUMENTOS':d}),patch('documentos.leer',return_value='Licitación Pública 1/2026 Objeto herramientas') as leer:
            def fetch(u):return b'%PDF-documento','application/pdf',u
            cfg={'urls_inicio':['https://x.gob.ar/1.pdf'],'ocr':True}
            conectores.explorar('https://x.gob.ar/',cfg,fetch=fetch)
            conectores.explorar('https://x.gob.ar/',cfg,fetch=fetch)
            self.assertEqual(leer.call_count,1)
    def test_objeto_incompleto_desconocido(self):
        r=self.base();r['detalle_completo']=False
        self.assertIsNone(o.normalizar(r,FECHA)['objeto'])

    def test_enriquecer_ficha_y_pliego_sin_duplicar(self):
        pages={'https://x.gob.ar/':'<article><a href="/ficha">Licitación Pública 3/2026 herramientas</a></article>',
               'https://x.gob.ar/ficha':'<article><h1>Licitación Pública 3/2026 herramientas</h1><p>Apertura 28/10/2026. Presupuesto oficial ARS 500.000,00</p><a href="/pliego.pdf">Pliego</a></article>'}
        def fetch(u):return pages[u].encode(),'text/html',u
        r=conectores.explorar('https://x.gob.ar/',{'lectura_adjuntos':'necesarios','enriquecer_fichas':True},fetch=fetch)
        self.assertEqual(r['estado'],'OPERATIVA')
        self.assertEqual(len(r['oportunidades']),1)
        item=r['oportunidades'][0]
        self.assertEqual(item['enlace_pliego'],'https://x.gob.ar/pliego.pdf')
        self.assertEqual(item['fecha_apertura'],'2026-10-28')
        self.assertEqual(item['presupuesto']['importe'],'500000.00')

    def test_pdf_multillamado_no_mezcla_presupuestos(self):
        texto='Licitación Pública 1/2026 Herramientas\nPresupuesto oficial ARS 100,00. Apertura 28/10/2026\nLicitación Pública 2/2026 Cemento\nPresupuesto oficial ARS 200,00. Apertura 29/10/2026'
        with tempfile.TemporaryDirectory() as d,patch.dict('os.environ',{'RADAR_CACHE_DOCUMENTOS':d}),patch('documentos.leer',return_value=texto):
            def fetch(u):return b'%PDF-multiple','application/pdf',u
            r=conectores.explorar('https://x.gob.ar/aviso.pdf',{},fetch=fetch)
        registros={i['numero_procedimiento']:i for i in r['oportunidades']}
        self.assertEqual(registros['1/2026']['presupuesto']['importe'],'100.00')
        self.assertEqual(registros['2/2026']['presupuesto']['importe'],'200.00')
        self.assertEqual(registros['2/2026']['fecha_apertura'],'2026-10-29')

    def test_reapertura_futura_de_anterior_desierta_no_vencida(self):
        r=o.normalizar(self.base(objeto='Segundo llamado. Anterior desierta. Apertura 28/10/2026',situacion_publicada='DESIERTA'),FECHA)
        self.assertEqual(r['vigencia'],'ABIERTA')
        self.assertTrue(r['desierta'])

    def test_codigo_aeropuerto_misma_identidad_cambio_titulo_url(self):
        r=self.base()
        r['numero_procedimiento']='LPU-2026-00000003-APPSF-OD-COM-CON-AIR-ROS'
        h={};self.assertEqual(len(o.incorporar(h,[r],FECHA)),1)
        cambiado={**r,'titulo':r['titulo']+' - Anexo publicado','url':r['url']+'/anexo'}
        self.assertEqual(o.incorporar(h,[cambiado],FECHA),[])

    def test_fecha_llamese_san_nicolas_evidencia_run50(self):
        texto='Llámese a Licitación Pública para el día 26 DE DICIEMBRE DE 2018, a las 09:00 horas en la Municipalidad de San Nicolás'
        r=o.normalizar(self.base(objeto=texto),FECHA)
        self.assertEqual(r['fecha_apertura'],'2018-12-26')
        self.assertEqual(r['vigencia'],'VENCIDA')

    def test_asunto_aeropuerto_separa_navegacion_y_expediente(self):
        texto='Aeropuerto Vuelos Pasajeros Asunto Contratación de servicio de líquidos azules. Expediente N° EE-2026-004 Presupuesto Oficial: $10.000.000.- Descargas documento.pdf'
        r=o.normalizar(self.base(objeto=texto),FECHA)
        self.assertEqual(r['objeto'],'Contratación de servicio de líquidos azules.')
        self.assertEqual(r['presupuesto']['importe'],'10000000')
