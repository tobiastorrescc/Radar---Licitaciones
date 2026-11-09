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

class Diario(unittest.TestCase):
 def test_urgencias_no_inventan_hora_de_cierre(self):
  from informe_descubrimiento import urgencia
  base={'titulo':'Concurso de precios 1/2026 compra de insumos','objeto':'Compra de insumos','fecha_limite_presentacion':'2026-11-10','fecha_apertura':'2026-11-10'}
  self.assertEqual(urgencia(base,'2026-11-09T09:00:00-03:00'),'HORA_LIMITE_PENDIENTE')
  self.assertEqual(urgencia({**base,'fecha_limite_presentacion_texto':'2026-11-10T08:00:00-03:00'},'2026-11-09T09:00:00-03:00'),'MENOS_24H')
 def test_venta_no_se_cuenta_como_suministro(self):
  from fuentes_fase4 import naturaleza_convocatoria
  self.assertEqual(naturaleza_convocatoria({'objeto':'Licitación 5/2026 venta de tractor municipal'}),'VENTA_BIENES_PUBLICOS')
  self.assertEqual(naturaleza_convocatoria({'objeto':'Adquisición de tractor. Venta de pliegos en oficina.'}),'COMPRA_O_SERVICIO')

class Navegacion(unittest.TestCase):
 def test_menu_licitaciones_no_se_trata_como_ficha_individual(self):
  import conectores
  root='https://comuna.gob.ar/'
  paginas={root:'<a href="/compras">Licitaciones</a>',root+'compras':'<a href="/aviso">Licitación Pública 1/2026</a>',root+'aviso':'<article><h1>Licitación Pública 1/2026 compra de insumos</h1><p>Presentación de ofertas hasta el 20 de noviembre de 2026 a las 10:30 horas.</p></article>'}
  visitadas=[]
  def fetch(u):visitadas.append(u);return paginas[u].encode(),'text/html',u
  r=conectores.explorar(root,{'noticias_comunales':True,'descubrir_contrataciones':True,'solo_descubrimiento':True},fetch=fetch)
  self.assertIn(root+'aviso',visitadas);self.assertTrue(any(presentacion(x,'2026-11-09T09:00:00-03:00')['presentacion_verificada'] for x in r['oportunidades']))
 def test_encabezado_pdf_sin_objeto_no_valida_fuente(self):
  from tools.descubrir_fuentes import objeto_comprobado
  self.assertFalse(objeto_comprobado({'objeto':'LICITACION PUBLICA 01-2026.pdf Descarga Detalles'}))
  self.assertTrue(objeto_comprobado({'objeto':'Licitación 1/2026 suministro de equipos'}))

class Categorias(unittest.TestCase):
 def test_primera_deteccion_no_es_publicacion_reciente_ni_recuperacion_conocida(self):
  from informe_descubrimiento import clasificar
  r=o.normalizar({'id':'nuevo','organismo':'Comuna A','titulo':'Concurso de precios 1/2026 compra de insumos','objeto':'Compra de insumos','fecha_publicacion_texto':'2026-10-01','fecha_limite_presentacion_texto':'2026-11-20T10:00:00-03:00','observada_esta_corrida':True},'2026-11-09T09:00:00-03:00')
  e={**r,'clasificacion_novedad':'RECUPERACION_LINEA_BASE'}
  gs=clasificar([r],[e],'2026-11-09T09:00:00-03:00',{})
  self.assertEqual(len(gs['B_VIGENTES_DESCONOCIDAS']),1);self.assertFalse(gs['A_PUBLICACIONES_NUEVAS_VIGENTES'])
  gs=clasificar([r],[e],'2026-11-09T09:00:00-03:00',{},['nuevo']);self.assertFalse(gs['B_VIGENTES_DESCONOCIDAS'])
 def test_informe_comercial_separa_venta_y_conserva_compra(self):
  import tempfile,json
  from pathlib import Path
  from calidad_comercial import escribir
  base={'organismo':'Comuna A','titulo':'Licitación Pública 1/2026','fecha_limite_presentacion_texto':'2026-11-20T10:00:00-03:00'}
  rs=[o.normalizar({**base,'objeto':obj,'url':'https://comuna.gob.ar/'+str(i)},'2026-11-09T09:00:00-03:00') for i,obj in enumerate(['Adquisición de tractor','Venta de tractor municipal'])]
  with tempfile.TemporaryDirectory() as d:
   self.assertEqual(escribir(rs,'2026-11-09T09:00:00-03:00',d)['vigentes_presentacion_verificada'],1)
   self.assertEqual(json.loads(Path(d,'ventas_municipales.json').read_text())['total'],1)

class IdentidadEditorial(unittest.TestCase):
 def test_historia_municipal_con_mencion_a_concurso_no_es_convocatoria(self):
  from descubrimiento_noticias import noticia
  html='<article><h1>Acebal, nuestro lugar en el mundo</h1><p>La escuela convoca a concurso. La comuna realizó la compra de materiales.</p></article>'
  self.assertEqual(noticia(extractores.DOM(html),'https://acebal.gob.ar/acebal/'),[])

class Cobertura(unittest.TestCase):
 def test_localidad_sin_codigo_no_inventa_identificador_oficial(self):
  from cobertura_territorial import generar
  import tempfile,csv
  from pathlib import Path
  with tempfile.TemporaryDirectory() as d:
   r=generar([],[],[],'2026-11-09T09:00:00-03:00',d,{'municipios':[{'provincia':'Santa Fe','localidad':'Prueba'}]})
   self.assertEqual(r['Santa Fe']['localidades_identificadas'],1)
   self.assertEqual(next(csv.DictReader(Path(d,'cobertura_territorial.csv').open()))['codigo_padron'],'')
