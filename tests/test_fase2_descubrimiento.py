import unittest
from urllib.error import HTTPError
import conectores

class RecuperacionPaginacion(unittest.TestCase):
 def test_pagina_transitoria_se_reintenta_despues_y_no_se_pierde_aviso(self):
  u='https://prueba.gob.ar/compras/';calls=[]
  def fetch(url):
   calls.append(url)
   if 'page=2' in url:
    if calls.count(url)==1:raise TimeoutError('Lectura agotada')
    return b'<article><h2>Concurso de Precios 2/2026</h2><p>Objeto: Provisi\xc3\xb3n de ca\xc3\xb1os.</p></article>','text/html',url
   return b'<article><h2>Concurso de Precios 1/2026</h2><p>Objeto: Arena.</p></article><a rel="next" href="?page=2">Siguiente</a>','text/html',url
  config={'solo_descubrimiento':True,'reintentar_listados_diferidos':1}
  r=conectores.explorar(u,config,fetch=fetch);self.assertEqual(len(r['oportunidades']),2);self.assertEqual(sum('page=2' in x for x in calls),2)
  self.assertTrue(any(x.get('acceso_recuperado') for x in r['errores']))
 def test_403_y_fallo_persistente_no_generan_bucle(self):
  for status in (403,503):
   calls=[]
   def fetch(url):calls.append(url);raise HTTPError(url,status,'fallo',{},None)
   r=conectores.explorar('https://prueba.gob.ar/compras/',{'reintentar_listados_diferidos':1},fetch=fetch)
   self.assertEqual(len(calls),1 if status==403 else 2);self.assertEqual(r['estado'],'BLOQUEADA');self.assertFalse(r['oportunidades'])
if __name__=='__main__':unittest.main()
