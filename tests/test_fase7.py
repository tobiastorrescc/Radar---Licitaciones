import unittest,json
from pathlib import Path
import extractores,oportunidades as o
from calidad_comercial import presentacion
class RosarioReal(unittest.TestCase):
 def test_ficha_38659_cambio_de_estado_no_es_oportunidad_abierta(self):
  u='https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38659';html=Path('tests/fixtures/fase7/rosario-38659.html').read_text();rs=extractores.extraer(html,u,{'adaptador':'rosario'})[0];self.assertEqual(len(rs),1)
  r=o.normalizar(rs[0],'2026-11-10T00:00:00-03:00');self.assertEqual(r['numero_procedimiento'],'63/2026');self.assertEqual(r['situacion_publicada'],'EN_EVALUACION');self.assertFalse(presentacion(r,'2026-11-10T00:00:00-03:00')['presentacion_verificada'])
 def test_grid_publicado_de_hughes_conserva_objeto_y_enlace(self):
  from fuentes_fase7 import siglo
  rs,n=siglo(Path('tests/fixtures/fase7/hughes-grid.html').read_text(),'https://sigloservicios.com/PublicDoc/PublicDoc.aspx?3,7=');self.assertEqual(n,10);self.assertTrue(any('3000 LTS.' in r['objeto'] for r in rs));self.assertTrue(all(r['url'].startswith('https://sigloservicios.com/PublicDoc/PublicTempStorage/') for r in rs))
class ControlCompleto(unittest.TestCase):
 def test_53_referencias_con_capturas_oficiales_de_actions(self):
  import gzip,base64
  d=json.loads(gzip.decompress(base64.b64decode(Path('tests/fixtures/fase7/rosario_53_real.json.gz.b64').read_text())))
  urls=set()
  for u,html in d['paginas'].items():urls.update(r['url'] for r in extractores.extraer(html,u,{'adaptador':'rosario'})[0])
  control=json.loads(Path('inventario/control_rosario_fase2.json').read_text())['publicaciones'];self.assertEqual(sum(c['url'] in urls for c in control),53)
 def test_prioridad_no_penaliza_datos_desconocidos(self):
  from descubrimiento_rapido import puntuar
  p=puntuar({'seccion_compras':True,'accesible':True});self.assertEqual(p['puntos'],5);self.assertIn('publicacion_ultimos_7_dias',p['desconocidos']);self.assertNotIn('publicacion_ultimos_7_dias',[r['criterio'] for r in p['razones']])
 def test_descubrimiento_no_consulta_fichas_ni_pierde_su_cola(self):
  import conectores,gzip,base64
  d=json.loads(gzip.decompress(base64.b64decode(Path('tests/fixtures/fase7/rosario_53_real.json.gz.b64').read_text())));u=next(u for u in d['paginas'] if 'recomendada=apertura' in u)
  html=d['paginas'][u];llamadas=[]
  def fetch(url):
   llamadas.append(url)
   if '/detalle/' in url:self.fail('La fase de descubrimiento no debe esperar fichas')
   return html.encode(),'text/html',url
  r=conectores.explorar(u,{'adaptador':'rosario','descubrimiento_prioritario':True,'requerir_ficha':True,'urls_inicio':[u]},fetch=fetch,max_paginas=1)
  self.assertTrue(r['oportunidades']);self.assertTrue(r['enriquecimiento_pendiente']);self.assertFalse(any('/detalle/' in x for x in llamadas))
 def test_indice_de_salto_precede_a_pdf_individual(self):
  from descubrimiento_rapido import elegir_seccion
  r=json.loads(Path('tests/fixtures/fase7/salto-enlaces.json').read_text());self.assertEqual(elegir_seccion(r),'https://saltogrande.gob.ar/contrataciones/')
 def test_san_salvador_objeto_fecha_y_drive_de_publicacion_real(self):
  html=Path('tests/fixtures/fase7/san-salvador-29.html').read_text();u='https://sansalvadorer.gob.ar/llamado-a-concurso-de-precios-n-29-2026/'
  rs=extractores.extraer(html,u,{'noticias_comunales':True})[0];self.assertEqual(len(rs),1);self.assertIn('200 cargas',rs[0]['objeto']);r=o.normalizar(rs[0],'2026-11-10T00:00:00-03:00');self.assertEqual(r['fecha_publicacion'],'2026-11-05');self.assertTrue(any('drive.google.com' in d['url'] for d in rs[0]['documentos']))
 def test_llamado_sin_objeto_no_valida_fuente(self):
  from tools.descubrir_fuentes import objeto_comprobado
  self.assertFalse(objeto_comprobado({'objeto':'Llamado a Concurso de Precios N° 29-2026'}))
