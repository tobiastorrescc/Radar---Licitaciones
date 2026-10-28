import unittest
import extractores
import oportunidades as o
from pathlib import Path
URL='https://villaelisa.gov.ar/transparencia/licitaciones/concursos-de-precios/'
# Estructura mínima sintética basada en las columnas de la sección oficial.
def fila(n,objeto):
 return f'<div class="et_pb_row"><div><h6>N°</h6><p>{n}</p></div><div><h6>DECRETO DE APERTURA</h6><a href="decreto{n.replace("/","-")}.pdf">DECRETO N° 006/26</a></div><div><h6>PLIEGO</h6><a href="pliego{n.replace("/","-")}.pdf">VER PLIEGO</a></div><div><h6>CONCEPTO</h6><p>{objeto}</p></div></div>'
class VillaElisaTests(unittest.TestCase):
 def extraer(self,html):
  rs,_,_=extractores.extraer(html,URL,{'adaptador':'villa-elisa'});return [o.normalizar(r) for r in rs]
 def test_filas_concepto_y_documentos_no_se_mezclan(self):
  rs=self.extraer('<main><h1>Concursos de precios</h1>'+fila('Concurso de precios N° 001/26','Hormigón elaborado')+fila('Concurso de precios N° 002/26','Broza grillada')+'</main>')
  self.assertEqual(len(rs),2);self.assertEqual([r['objeto'] for r in rs],['Hormigón elaborado','Broza grillada']);self.assertEqual([r['numero_procedimiento'] for r in rs],['1/2026','2/2026']);self.assertNotEqual(rs[0]['documentos'],rs[1]['documentos'])
  self.assertIsNone(rs[0]['fecha_publicacion']);self.assertIsNone(rs[0]['fecha_apertura']);self.assertIsNone(rs[0]['presupuesto'])
 def test_privadas_numero_sin_modalidad_en_columna(self):
  r,=self.extraer('<main><h1>Licitaciones Privadas</h1>'+fila('001/25','Combustible')+'</main>')
  self.assertEqual(r['procedimiento_canonico'],'licitacion privada 1/2025');self.assertEqual(r['objeto'],'Combustible')
 def test_pagina_general_no_se_convierte_en_procedimiento(self):
  self.assertEqual(self.extraer('<h1>Licitaciones Públicas, Privadas y Concursos de Precios</h1><p>Teléfono 03447 480139</p>'),[])
 def test_noticia_de_segundo_llamado_conserva_extraccion_y_fechas_separadas(self):
  html='<main><article><h1>Segundo llamado para adquirir un vehículo</h1><p>Licitación Pública N° 004/26 (Segundo llamado). Objeto: adquisición de vehículo. Fecha de apertura: 05/11/2026 10:00 hs.</p><time class="published" datetime="2026-10-20">20 octubre</time></article></main>'
  r,=self.extraer(html)
  self.assertEqual(r['numero_procedimiento'],'4/2026');self.assertTrue(r['segundo_llamado'])
  self.assertEqual(r['fecha_apertura'],'2026-11-05');self.assertEqual(r['fecha_publicacion'],'2026-10-20')
  self.assertEqual(r['convocatoria'],'2')
 def test_url_compartida_decreto_no_se_presenta_como_pliego(self):
  html='<h1>Concursos de precios</h1>'+fila('1/26','Hormigón')
  html=html.replace('pliego1-26.pdf','decreto1-26.pdf');r,=self.extraer(html)
  self.assertEqual(len(r['documentos']),1);self.assertIsNone(r['enlace_pliego'])
 def test_grilla_real123_separa_datos_y_pliegos_por_fila(self):
  html=(Path(__file__).parent/'fixtures/villaelisa/concursos.html').read_text()
  rs=self.extraer(html)
  self.assertEqual(len(rs),2)
  self.assertEqual(rs[0]['objeto'],'ADQUISICIÓN DE HORMIGÓN ELABORADO H21')
  self.assertEqual(rs[1]['objeto'],'ADQUISICIÓN DE 2000 M3 DE BROZA GRILLADA')
  self.assertIn('001-26',rs[0]['enlace_pliego']);self.assertIn('002-26',rs[1]['enlace_pliego'])
  self.assertTrue(all('CONCEPTO' not in r['objeto'] for r in rs))
 def test_privada_real123_numero_sin_rotulo_modalidad(self):
  html=(Path(__file__).parent/'fixtures/villaelisa/privadas.html').read_text()
  r,=self.extraer(html)
  self.assertEqual(r['tipo_procedimiento'],'licitacion privada')
  self.assertEqual(r['numero_procedimiento'],'1/2026')
  self.assertNotIn('DECRETO',r['objeto'])
 def test_portada_real_no_se_clasifica_como_procedimiento(self):
  html='<h1>Somos elisenses</h1><div>Licitación Pública N° 004/26 (Segundo llamado) <a href="/segundo-llamado-a-licitacion-publica/">LICITACIÓN</a></div><footer>Teléfonos</footer>'
  rs,links,_=extractores.extraer(html,'https://villaelisa.gov.ar/',{'adaptador':'villa-elisa'})
  self.assertEqual(rs,[]);self.assertEqual(len(links),1)
 def test_grilla_sin_concepto_no_se_declara_completa(self):
  html=(Path(__file__).parent/'fixtures/villaelisa/privadas.html').read_text()
  # Quitar sólo el dato de concepto de la fila real, conservando sus etiquetas.
  dom=extractores.DOM(html)
  objeto=next(n.text for n in dom.root.iter() if n.clase('dvmd_tm_tdata') and n.clase('dvmd_tm_col_4'))
  from html import unescape
  html=unescape(html).replace(objeto,'')
  r,=self.extraer(html)
  self.assertIsNone(r['objeto']);self.assertFalse(r['detalle_completo'])
