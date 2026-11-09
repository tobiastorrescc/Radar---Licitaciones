import unittest
import extractores,oportunidades as o
from calidad_comercial import presentacion

class Noticias(unittest.TestCase):
 def aviso(self,titulo='Solicitud de presupuestos para compra de insumos',extra=''):
  return '<article><h1>'+titulo+'</h1><time class="published" datetime="2026-11-09T08:00:00-03:00"></time><p>La Comuna solicita presupuestos para compra de insumos. Presentación de ofertas hasta el 20 de noviembre de 2026 a las 10:30 horas. En sobre cerrado.</p>'+extra+'</article>'
 def test_aviso_sin_numero_monto_ni_pliego(self):
  r,=extractores.extraer(self.aviso(),'https://comuna.gob.ar/noticias/compra',{'noticias_comunales':True})[0]
  r=o.normalizar(r,'2026-11-09T09:00:00-03:00');self.assertIsNone(r['numero_procedimiento']);self.assertEqual(r['fecha_publicacion'],'2026-11-09');self.assertTrue(presentacion(r,'2026-11-09T09:00:00-03:00')['presentacion_verificada'])
 def test_concurso_de_empleo_no_es_compra(self):
  from descubrimiento_noticias import noticia
  self.assertEqual(noticia(extractores.DOM(self.aviso('Llamado a concurso para personal administrativo')),'https://comuna.gob.ar/empleo'),[])
 def test_no_concatenar_varias_noticias(self):
  from descubrimiento_noticias import noticia
  self.assertEqual(noticia(extractores.DOM(self.aviso()+self.aviso()),'https://comuna.gob.ar/noticias'),[])
 def test_seguimiento_no_es_publicacion(self):
  from descubrimiento_territorial import ventanas
  self.assertTrue(ventanas('2026-11-04','2026-11-09T09:00:00-03:00')['168h']);self.assertFalse(ventanas(None,'2026-11-09T09:00:00-03:00')['168h'])
