import unittest
from pathlib import Path
import extractores
from tools.descubrir_fuentes import verificar_identidad,objeto_comprobado
class EvidenciaReal(unittest.TestCase):
 def test_pagina_de_busqueda_no_es_convocatoria(self):
  html=Path('tests/fixtures/fase6/busqueda-sauce.html').read_text()
  rs=extractores.extraer(html,'https://sanjeronimodelsauce.gob.ar/?s=licitacion',{'noticias_comunales':True,'admitir_avisos_sin_numero':True})[0]
  self.assertFalse(any((r.get('objeto') or '').startswith('Resultados de búsqueda') for r in rs))
  self.assertFalse(objeto_comprobado({'objeto':'Resultados de búsqueda para: licitacion'}))
 def test_identidad_san_jose_no_exige_que_el_nombre_sea_un_prefijo(self):
  c={'tipo':'TERRITORIAL','provincia':'Santa Fe','localidad':'San José de la Esquina','organismo':'Municipalidad de San José de la Esquina'}
  self.assertTrue(verificar_identidad(Path('tests/fixtures/fase6/san-jose.html').read_text(),'https://munisje.gob.ar/ciudad/',c)['verificada'])
 def test_totoras_no_se_valida_si_html_solo_carga_javascript(self):
  c={'tipo':'TERRITORIAL','provincia':'Santa Fe','localidad':'Totoras','organismo':'Municipalidad de Totoras'}
  r=verificar_identidad(Path('tests/fixtures/fase6/totoras.html').read_text(),'https://www.mtotoras.gob.ar/',c)
  self.assertFalse(r['verificada']);self.assertFalse(r['jurisdiccion_publicada'])
