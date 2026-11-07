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
 def test_ultima_pagina_oficial_recupera_38723_y_38741(self):
  from pathlib import Path
  origen='https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones?recomendada=apertura'
  ultima='https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones?page=3&recomendada=apertura&tipoRecomendada=5';calls=[]
  html=Path('tests/fixtures/fase2_rosario_ultima_20261107.html').read_bytes()
  def fetch(url):
   calls.append(url)
   if url==origen:return ('<a rel="next" href="'+ultima+'">Siguiente</a>').encode(),'text/html',url
   if calls.count(url)==1:raise TimeoutError('Fallo transitorio reproducido del run real')
   return html,'text/html',url
  r=conectores.explorar(origen,{'adaptador':'rosario','reintentar_listados_diferidos':1,'solo_descubrimiento':True},fetch=fetch)
  self.assertTrue({'38723','38741'}<={x['url'].rsplit('/',1)[-1] for x in r['oportunidades']})
 def test_tarjetas_dpv_extraen_numero_y_fecha_sin_descargar_pdf(self):
  import extractores
  from pathlib import Path
  html=Path('tests/fixtures/fase2_dpv_tarjeta.html').read_text()
  rs,_,_=extractores.extraer(html,'https://aplicaciones.vialidadentrerios.gob.ar/contrataciones-licitaciones',{'adaptador':'dpver-tarjetas'})
  self.assertEqual(len(rs),1);self.assertEqual(rs[0]['numero_procedimiento'],'86');self.assertEqual(rs[0]['fecha_apertura_texto'],'05/11/2026 10:00');self.assertIn('/533/adjunto',rs[0]['url'])
if __name__=='__main__':unittest.main()
