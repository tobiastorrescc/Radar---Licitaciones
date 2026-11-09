import unittest
from presentacion_documental import clausula
from tools.fase3_revalidar import elegir
from calidad_comercial import presentacion
import oportunidades as o

class RecepcionDocumental(unittest.TestCase):
 def test_apertura_y_direccion_no_prueban_recepcion(self):
  self.assertEqual({},clausula('Apertura 11/11/2026 11:00. Recepción de ofertas: San Luis 2020.',{},'https://oficial'))
 def test_clausula_mismo_dia_y_hora(self):
  r={'fecha_hora_apertura':'2026-11-11T11:00:00-03:00'}
  d=clausula('Recepción de ofertas: hasta el día y hora de apertura.',r,'https://oficial','abc')
  self.assertEqual(d['fecha_limite_presentacion_texto'],r['fecha_hora_apertura'])
  self.assertEqual(d['evidencia_recepcion']['sha256'],'abc')
 def test_minutos_antes(self):
  d=clausula('Presentación de ofertas hasta 30 minutos antes de la apertura.',{'fecha_hora_apertura':'2026-11-11T11:00:00-03:00'},'https://oficial')
  self.assertIn('10:30:00',d['fecha_limite_presentacion_texto'])
 def test_limite_explicito_y_fecha_consultas_distinta(self):
  d=clausula('Recepción de ofertas hasta el 12/11/2026 a las 09:30 hs. Consultas: 15/11/2026',{},'https://oficial')
  self.assertEqual(d['fecha_limite_presentacion_texto'],'2026-11-12T09:30:00-03:00')
 def test_distinguir_procedimientos_mismo_numero(self):
  c={'numero_procedimiento':'1/2026','objeto':'Compra de combustible para ambulancias'}
  a={'numero_procedimiento':'1/2026','objeto':'Compra de combustible para ambulancias'}
  b={'numero_procedimiento':'1/2026','objeto':'Construcción de puente peatonal'}
  self.assertIs(elegir(c,[b,a]),a)
  self.assertIsNone(elegir(c,[a,a]))
 def test_evidencia_vencida_no_comercial(self):
  r=o.normalizar({'titulo':'Concurso de precios 1/2026 Combustible','url':'https://oficial','fecha_limite_presentacion_texto':'2026-11-09T08:00:00-03:00'},'2026-11-09T09:00:00-03:00')
  self.assertFalse(presentacion(r,'2026-11-09T09:00:00-03:00')['presentacion_verificada'])
if __name__=='__main__':unittest.main()

class SantaAnaReal(unittest.TestCase):
 def test_separa_seis_llamados_y_no_asume_en_curso_como_vigente(self):
  from pathlib import Path
  import extractores
  html=Path('tests/fixtures/fase3_santaana.html').read_text()
  rs=extractores.extraer(html,'https://www.santaana.gob.ar/home/licitaciones/',{'adaptador':'santaana'})[0]
  self.assertEqual(len(rs),6)
  r=o.normalizar(rs[0],'2026-11-09T09:00:00-03:00')
  self.assertEqual(r['fecha_apertura'],'2026-11-06')
  self.assertEqual(r['numero_procedimiento'],'6/2026')
  self.assertEqual(r['vigencia'],'VENCIDA')
  self.assertIn('Pavimento Urbano',r['objeto'])
  self.assertFalse(presentacion(r,'2026-11-09T09:00:00-03:00')['presentacion_verificada'])

class TrazabilidadRegresion(unittest.TestCase):
 def test_fecha_con_puntos_no_se_convierte_en_hora(self):
  r=clausula('Recepción de ofertas hasta el 12.11.2026 a las 09.30 hs.',{},'https://oficial')
  self.assertEqual(r['fecha_limite_presentacion_texto'],'2026-11-12T09:30:00-03:00')
 def test_errores_de_cache_siguen_siendo_red(self):
  from tools.fase3_revalidar import error_documentado,ErrorObtencion
  self.assertEqual(error_documentado(ErrorObtencion('timed out'))['categoria'],'RED')
  self.assertEqual(error_documentado(ValueError('PDF no reconocido'))['categoria'],'EXTRACCION')
 def test_ficha_sin_organismo_no_borra_identidad(self):
  from unittest.mock import patch
  from tools.fase3_revalidar import worker
  from pathlib import Path
  import tempfile,json
  c={'organismo':'Municipalidad de Rosario','localidad':'Rosario','provincia':'Santa Fe','fuente':'https://www.rosario.gob.ar/inicio/compras-y-licitaciones','url':'https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/12345','caso_id':'prueba','objeto':'Compra de combustible','numero_procedimiento':'1/2026'}
  raw={'organismo':None,'localidad':None,'provincia':None,'url':c['url'],'titulo':'Compra ágil 1/2026 Compra de combustible','objeto':c['objeto'],'numero_procedimiento':'1/2026','tipo_procedimiento':'compra agil','registro_estructurado':True}
  import extractores
  with tempfile.TemporaryDirectory() as tmp,patch('tools.fase3_revalidar.obtener',return_value=(b'<main>Compra de combustible</main>',{'tipo':'text/html','url':c['url'],'sha256':'abc'})),patch('tools.fase3_revalidar.extractores.extraer',return_value=([raw],[],extractores.DOM('<main>Compra de combustible</main>'))):
   p=Path(tmp)/'r.json';worker(c,p);r=json.load(open(p))['oportunidades'][0]
   self.assertEqual(r['organismo'],c['organismo']);self.assertEqual(r['provincia'],'Santa Fe')
