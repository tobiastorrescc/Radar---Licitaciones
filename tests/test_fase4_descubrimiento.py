import unittest
from descubrimiento_territorial import departamentos,resultado_pertinente,alcance_ba,ventanas
from tools.descubrir_fuentes import plan_busquedas
class DescubrimientoFase4(unittest.TestCase):
 def test_no_validar_otro_municipio_por_resultado_generico(self):
  q={'tipo':'TERRITORIAL','localidad':'Bombal','provincia':'Santa Fe'}
  self.assertFalse(resultado_pertinente({'titulo':'Registro Civil Entre Ríos'},q))
  self.assertTrue(resultado_pertinente({'titulo':'Comuna de Bombal - concursos'},q))
 def test_menu_oficial_no_requiere_repetir_localidad_en_enlace(self):
  self.assertTrue(resultado_pertinente({'titulo':'Compras'},{'tipo':'TERRITORIAL','localidad':'Bombal','metodo':'ENLACES_OFICIALES'}))
 def test_19_departamentos_son_consultas_no_fuentes_inventadas(self):
  ds=departamentos();self.assertEqual(len(ds),19);self.assertEqual(len({d['clave'] for d in ds}),19);self.assertTrue(all('url' not in d for d in ds))
 def test_rotacion_2_sf_1_er_1_ba_y_persistencia(self):
  qs=[{'clave':str(i),'provincia':p} for i,p in enumerate(['Santa Fe']*4+['Entre Ríos']*2+['Buenos Aires']*2)]
  r=plan_busquedas(qs,{},4);self.assertEqual([q['provincia'] for q in r],['Santa Fe','Santa Fe','Entre Ríos','Buenos Aires'])
  st={'busquedas':{q['clave']:'2026-11-09' for q in r}}
  self.assertTrue(not any(q in r for q in plan_busquedas(qs,st,4)))
 def test_ba_geodesica_no_sustituye_distancia_vial(self):
  p={'municipios':[{'provincia':'Buenos Aires','localidad':'Localidad lejana','centroide':{'lat':-34,'lon':-60},'distancia_geodesica_rosario_km':250}]}
  self.assertFalse(alcance_ba({'provincia':'Buenos Aires','localidad':'Localidad lejana'},p)['verificado'])
  self.assertTrue(alcance_ba({'provincia':'Buenos Aires','localidad':'Ramallo'})['verificado'])
 def test_publicacion_desconocida_y_fecha_sin_hora(self):
  self.assertFalse(ventanas(None,'2026-11-09T10:00:00-03:00')['72h'])
  r=ventanas('2026-11-08','2026-11-09T10:00:00-03:00');self.assertFalse(r['24h']);self.assertTrue(r['posible_24h']);self.assertEqual(r['precision'],'DIA_CALENDARIO_SIN_HORA')
  self.assertFalse(ventanas('2026-11-10','2026-11-09T10:00:00-03:00')['72h'])
if __name__=='__main__':unittest.main()

class CasosRealesFase4(unittest.TestCase):
 def test_ceres_054_sin_palabra_licitacion_no_se_omite(self):
  from pathlib import Path
  import extractores
  html=Path('tests/fixtures/fase4_ceres_054.html').read_text()
  r=extractores.extraer(html,'https://ceres.gob.ar/compras/',{'adaptador':'ceres'})[0]
  self.assertTrue(any(x['numero_procedimiento']=='54/2026' for x in r))
  self.assertIn('VENTA-3-LOTES',r[0]['documentos'][0]['url'])
 def test_identidad_es_distinta_del_alcance_vial(self):
  from tools.descubrir_fuentes import verificar_identidad,aceptacion
  c={'tipo':'TERRITORIAL','organismo':'Municipalidad de Campana','localidad':'Campana','provincia':'Buenos Aires'}
  v=verificar_identidad('<title>Municipalidad de Campana</title><p>Buenos Aires</p>','https://campana.gob.ar/',c)
  self.assertTrue(v['verificada']);self.assertFalse(v['ubicacion']['verificado'])
  self.assertEqual(aceptacion({'estado':'OPERATIVA','oportunidades':[]},v)['estado'],'PENDIENTE')
 def test_larroque_titulo_y_nombre_publicado_no_solo_dominio(self):
  from tools.descubrir_fuentes import verificar_identidad
  c={'tipo':'TERRITORIAL','organismo':'Municipalidad de Larroque','localidad':'Larroque','provincia':'Entre Ríos'}
  self.assertTrue(verificar_identidad('<title>Larroque :: Gobierno Abierto</title><footer>Municipalidad de Larroque. Entre Ríos</footer>','https://larroque.gob.ar/',c)['verificada'])

class NoticiasNoSonPortales(unittest.TestCase):
 def test_felicitaciones_titan_no_reingresa_como_fuente(self):
  from tools.descubrir_fuentes import seleccionar_validaciones
  c={'id':'falso','tipo':'TERRITORIAL','localidad':'Arrecifes','provincia':'Buenos Aires','url':'https://arrecifes.gob.ar/felicitaciones-titan/'}
  self.assertEqual(seleccionar_validaciones([c],set(),{},10,True),[])

class ComunaSinNumero(unittest.TestCase):
 def test_cajas_de_maria_teresa_no_necesita_numero_ni_pliego(self):
  from pathlib import Path
  import extractores,oportunidades as o
  from calidad_comercial import presentacion
  url='https://mariateresa.gob.ar/index.php?idp=859&pagina=detalle'
  r,=extractores.extraer(Path('tests/fixtures/fase4_mariateresa_cajas.html').read_text(),url,{'adaptador':'comuna-cms'})[0]
  n=o.normalizar(r,'2026-11-09T10:00:00-03:00');self.assertIsNone(n['numero_procedimiento']);self.assertEqual(n['fecha_publicacion'],'2026-10-26');self.assertIn('200',n['objeto']);self.assertTrue(presentacion(n,'2026-11-09T10:00:00-03:00')['presentacion_verificada']);self.assertFalse(presentacion(n,'2026-11-10T11:01:00-03:00')['presentacion_verificada'])
