import json
from pathlib import Path
import unittest
import conectores as c
import extractores

class AccesoCodificacionTests(unittest.TestCase):
 def test_href_real_utf8_no_corrompido_por_byte_latin1_en_otro_bloque(self):
  f=Path('tests/fixtures/villaguay/codificacion-mixta.hex')
  html=c.decodificar_html(bytes.fromhex(f.read_text()),'text/html; charset=UTF-8')
  links=extractores.DOM(html).root.enlaces('https://villaguay.gob.ar/boletindigital/licitaciones-2026/')
  self.assertTrue(any('Lic.P%C3%BAblicas-2026.pdf' in l['url'] for l in links));self.assertNotIn('PÃºblicas',html)
 def test_respeta_charset_latin1_declarado(self):
  self.assertEqual(c.decodificar_html('Licitación'.encode('latin1'),'text/html; charset=iso-8859-1'),'Licitación')
 def test_desafio_http200_es_bloqueo_no_extraccion_o_vacio(self):
  html='<title>One moment, please...</title>Please wait while your request is being verified. Sin licitaciones vigentes'
  r=c.explorar('https://ejemplo.gob.ar',{},fetch=lambda u:(html.encode(),'text/html',u))
  self.assertEqual(r['estado'],'BLOQUEADA');self.assertEqual(r['errores'][0]['categoria'],'ACCESO');self.assertEqual(r['paginas_correctas'],0);self.assertEqual(r['oportunidades'],[])
 def test_mencion_en_documento_no_bloquea(self):
  c.comprobar_acceso('<title>Licitaciones</title>El servicio comprueba request is being verified')
 def test_publicaciones_ya_recuperadas_se_conservan_ante_bloqueo_adjunto(self):
  fuente='https://ejemplo.gob.ar/'
  html='<article><a href="/desafio">Licitacion Publica 1/2026 Objeto: Hormigon</a></article>'
  def fetch(u):return ((html if u==fuente else '<title>Just a moment...</title>Enable JavaScript and cookies').encode(),'text/html',u)
  r=c.explorar(fuente,{'enriquecer_fichas':True},fetch=fetch)
  self.assertTrue(r['oportunidades']);self.assertEqual(r['estado'],'PARCIAL')
