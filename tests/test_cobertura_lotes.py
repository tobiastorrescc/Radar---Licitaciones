import json
from pathlib import Path
import unittest
import extractores
from tools.padron_territorial import construir,distancia
class CoberturaTests(unittest.TestCase):
    def test_conserva_base_36(self):
        fs=json.loads(Path('inventario/fuentes.json').read_text())
        base=json.loads(Path('inventario/base_36.json').read_text())['ids']
        self.assertEqual(len(base),36)
        self.assertTrue(set(base)<={f['id'] for f in fs if f['incorporada']})
    def test_secciones_no_mezclan_aperturas_adjuntos_o_modalidades(self):
        html='<main><h3>LICITACIÓN PRIVADA Nº 8/2026</h3><p>Objeto: Adquisición de una contadora de billetes</p><p>Fecha de apertura: 17 de noviembre de 2026</p><a href="uno.pdf">Pliego</a><h3>SOLICITUD DE COTIZACIÓN Nº 8/2026</h3><p>Objeto: Alquiler de inmueble</p><p>Apertura: 7 de julio de 2026</p><a href="dos.pdf">Pliego</a></main>'
        rs,_,_=extractores.extraer(html,'https://organismo.gob.ar/lista',{'adaptador':'encabezados'})
        self.assertEqual(len(rs),2);self.assertIn('billetes',rs[0]['objeto']);self.assertNotIn('inmueble',rs[0]['titulo']);self.assertEqual(rs[0]['documentos'][0]['url'],'https://organismo.gob.ar/uno.pdf')
    def test_colon_errata_y_imagen_sin_inventar_objeto(self):
        html='<h3>Licitacioón Pública N° 10/2026</h3><p>Fecha de publicación: viernes 25/09/2026</p><a href="aviso.jpg"><img src="aviso.jpg"></a>'
        rs,_,_=extractores.extraer(html,'https://oficial.gob.ar/',{'adaptador':'colon-pba','documentos_imagen':True})
        self.assertEqual(len(rs),1);self.assertEqual(rs[0]['numero_procedimiento'],'10/2026');self.assertFalse(rs[0]['detalle_completo']);self.assertEqual(rs[0]['fecha_publicacion_texto'],'25/09/2026')
    def test_padron_incluye_comunas_pequenas_y_radio_no_es_ruta(self):
        docs={'municipios':[{'id':'820001','nombre':'Comuna Pequeña','provincia':{'nombre':'Santa Fe'},'centroide':{'lat':-32,'lon':-61}},{'id':'060001','nombre':'Cercano','provincia':{'nombre':'Buenos Aires'},'centroide':{'lat':-33,'lon':-60}},{'id':'060002','nombre':'Lejano','provincia':{'nombre':'Buenos Aires'},'centroide':{'lat':-39,'lon':-62}}]}
        r=construir(docs,[]);self.assertEqual(len(r['municipios']),2);self.assertFalse(r['exhaustivo']);self.assertIsNone(r['municipios'][0]['distancia_por_ruta_km']);self.assertAlmostEqual(distancia((-32,-60),(-32,-60)),0)

    def test_boletin_atribuye_organismos_y_deduplica_portal_original(self):
        import oportunidades as o
        html='<p>COMUNA DE AREQUITO</p><p>LICITACIÓN PÚBLICA Nº 4/2026</p><p>Objeto: adquisición de pala cargadora. Apertura: 04/06/2026.</p><p>MUNICIPALIDAD DE ROSARIO</p><p>CONCURSO DE PRECIOS Nº 4/2026</p><p>Objeto: compra de materiales</p>'
        rs,_,_=extractores.extraer(html,'https://www.santafe.gov.ar/boletinoficial/ver.php?seccion=2026/2026-05-04licitaciones.html',{'adaptador':'boletin-sf'})
        self.assertEqual(len(rs),2);self.assertEqual(rs[0]['organismo'],'Comuna De Arequito');self.assertEqual(rs[0]['localidad'],'Arequito');self.assertNotIn('materiales',rs[0]['objeto'])
        r=o.normalizar(rs[0]);portal={**r,'url':'https://comunaarequito.gob.ar/otro','fuente':'https://comunaarequito.gob.ar/licitaciones/'}
        self.assertEqual(o.identidad(r),o.identidad(portal))
    def test_colon_provincias_distintas_no_son_duplicados(self):
        import oportunidades as o
        r={'organismo':'Municipalidad de Colón','numero_procedimiento':'1/2026','tipo_procedimiento':'licitacion publica'}
        self.assertNotEqual(o.identidad({**r,'provincia':'Entre Ríos'}),o.identidad({**r,'provincia':'Buenos Aires'}))

    def test_boletin_pdf_distingue_dos_organismos_con_igual_numero(self):
        from extractores_lotes import boletin_texto
        rs=boletin_texto('MUNICIPALIDAD DE VICTORIA\nLICITACION PUBLICA Nº 1/2026\nObjeto: cemento asfáltico.\nMUNICIPALIDAD DE DIAMANTE\nLICITACION PUBLICA Nº 1/2026\nObjeto: compra de hormigón.','https://www.entrerios.gov.ar/boletin/ejemplo.pdf',{'provincia':'Entre Ríos'})
        self.assertEqual(len(rs),2);self.assertEqual(rs[0]['provincia'],'Entre Ríos');self.assertNotEqual(rs[0]['organismo'],rs[1]['organismo'])
    def test_fracasada_se_conserva_y_se_destaca(self):
        import oportunidades as o
        r=o.normalizar({'titulo':'Licitación pública 1/2026 fracasada','url':'https://oficial.gob.ar/a','situacion_publicada':extractores.situacion('DECLARADA FRACASADA')})
        self.assertTrue(r['fracasada']);self.assertTrue(r['llamado_especial']);self.assertEqual(r['vigencia'],'VENCIDA');self.assertIn('Fracasada',o.reporte([r],'2026-10-27'))

    def test_http_o_candidatos_no_demuestran_fuente_operativa(self):
        from tools.informe_cobertura import estado_cobertura
        self.assertEqual(estado_cobertura({'estado':'OPERATIVA'},[]),'PENDIENTE')
        self.assertEqual(estado_cobertura({'estado':'OPERATIVA'},[{'clasificacion_registro':'CANDIDATO_NO_VERIFICADO','objeto':'General'}]),'PENDIENTE')
        self.assertEqual(estado_cobertura({'estado':'SIN_PUBLICACIONES'},[]),'SIN_PUBLICACIONES_CONFIRMADO')
        self.assertEqual(estado_cobertura({'estado':'PARCIAL'},[{'clasificacion_registro':'PROCEDIMIENTO','objeto':'Hormigón','detalle_completo':True}]),'PARCIAL')

    def test_inspector_solo_sigue_scripts_publicados_del_mismo_origen(self):
        from tools.inspeccionar_portales import candidatos
        html='<script src="/js/licitaciones.js"></script><script src="https://otro.gob.ar/api.js"></script><script src="/jquery.js"></script>'
        self.assertEqual(candidatos(html,'https://oficial.gob.ar/'),['https://oficial.gob.ar/js/licitaciones.js'])

    def test_regresion_real_iafas_objeto_fecha_y_descargas_sin_extension(self):
        import oportunidades as o
        html=Path('tests/fixtures/reales/cobertura77/fuente-057.html').read_text()
        rs,_,_=extractores.extraer(html,'https://www.iafas.gov.ar/proveedores/licitaciones/',{'adaptador':'encabezados','patrones_documentos':[r'/descargas/\d+$']})
        self.assertEqual(len(rs),2);self.assertIn('billetes',rs[0]['objeto']);self.assertEqual(len(rs[0]['documentos']),2)
        self.assertEqual(o.normalizar(rs[0])['fecha_apertura'],'2026-11-17');self.assertNotIn('conexión corporativa',rs[0]['objeto'])
    def test_regresion_real_colon_imagen_y_fecha_publicacion(self):
        html=Path('tests/fixtures/reales/cobertura77/fuente-059.html').read_text()
        rs,_,_=extractores.extraer(html,'https://www.municipalidadcolonpba.gob.ar/licitaciones.php',{'adaptador':'colon-pba','documentos_imagen':True})
        self.assertEqual(rs[0]['numero_procedimiento'],'11/2026');self.assertTrue(rs[0]['documentos'][0]['url'].endswith('licitacion_11-2026.jpg'));self.assertEqual(rs[0]['fecha_publicacion_texto'],'19/10/2026');self.assertFalse(rs[0]['detalle_completo'])
    def test_vgg_endpoint_se_deriva_del_html_oficial(self):
        from extractores_lotes import endpoints_vgg,extraer_vgg
        url='https://vggmunicipalidad.gov.ar/licitaciones/'
        html=Path('tests/fixtures/reales/cobertura77/fuente-016.html').read_text()
        urls=endpoints_vgg(extractores.DOM(html),html,url)
        self.assertEqual(len(urls),7);self.assertIn('https://vggmunicipalidad.gov.ar/scripts/licitaciones/licitaciones-registros.php?anio=2026&tipo=apertura',urls)
        rs=extraer_vgg(json.dumps([{'objeto':'Adquisición de hormigón','apertura_raw':'2026-11-02','archivo_url':'/pliego.pdf','presupuesto':10000}]),urls[0])
        self.assertEqual(rs[0]['objeto'],'Adquisición de hormigón');self.assertIsNone(rs[0]['numero_procedimiento']);self.assertTrue(rs[0]['registro_estructurado'])
        with self.assertRaises(ValueError):extraer_vgg('{}',urls[0])
    def test_429_pospone_recorrido_sin_perder_publicaciones(self):
        import conectores
        from urllib.error import HTTPError
        calls=[]
        def fetch(url):
            calls.append(url)
            if url!='https://oficial.gob.ar/':raise HTTPError(url,429,'Too Many Requests',{},None)
            return b'<article><a href="a">Licitacion publica 1/2026 hormigon</a></article><article><a href="b">Licitacion publica 2/2026 materiales</a></article>','text/html',url
        r=conectores.explorar('https://oficial.gob.ar/',{'organismo':'Municipalidad','provincia':'Santa Fe','enriquecer_fichas':True},fetch=fetch)
        self.assertEqual(len(calls),2);self.assertEqual(len(r['oportunidades']),2);self.assertIn('HTTP_429_REINTENTO_POSPUESTO',r['limites']);self.assertEqual(r['estado'],'PARCIAL')
    def test_descubre_seccion_oficial_sin_salir_de_dominio(self):
        import conectores
        paginas={'https://oficial.gob.ar/':'<nav><a href="/compras">Compras y licitaciones</a><a href="https://otro.gob.ar/compras">Compras</a></nav><main>Municipalidad</main>','https://oficial.gob.ar/compras':'<article><h2>Licitación pública 7/2026</h2><p>Objeto: adquisición de hormigón. Apertura: 02/11/2026</p></article>'}
        visitas=[]
        def fetch(url):visitas.append(url);return paginas[url].encode(),'text/html',url
        r=conectores.explorar('https://oficial.gob.ar/',{'organismo':'Municipalidad','provincia':'Santa Fe','descubrir_menu':True,'descubrir_contrataciones':True},fetch=fetch)
        self.assertEqual(r['estado'],'OPERATIVA');self.assertEqual(visitas,['https://oficial.gob.ar/','https://oficial.gob.ar/compras'])

    def test_pdf_seguido_desde_listado_con_contexto_no_falla_por_dict(self):
        import conectores
        from unittest.mock import patch
        def fetch(url):
            if url=='https://oficial.gob.ar/':return b'<a href="download.php">Descargar</a>','text/html',url
            return b'%PDF-datos','application/pdf',url
        with patch('cache_documentos.leer_texto',return_value=('Licitacion publica 8/2026 adquisicion de tapas y listones de nichos',{})):
            r=conectores.explorar('https://oficial.gob.ar/',{'organismo':'Municipio','seguir_patrones':['download.php']},fetch=fetch)
        self.assertEqual(r['estado'],'OPERATIVA');self.assertEqual(len(r['oportunidades']),1);self.assertFalse(r['errores'])

    def test_condicional_fracasada_no_cierra_convocatoria(self):
        import oportunidades as o
        titulo='Licitación Pública 7/2026 Apertura: 02/11/2026. Si resultare fracasada se hará otro llamado.'
        r=o.normalizar({'titulo':titulo,'url':'https://oficial.gob.ar/','situacion_publicada':extractores.situacion(titulo)},'2026-10-27T10:00:00-03:00')
        self.assertFalse(r['fracasada']);self.assertEqual(r['vigencia'],'ABIERTA')

    def test_vgg_real_numero_presupuesto_y_raiz_de_enlace(self):
        from extractores_lotes import extraer_vgg
        import oportunidades as o
        api='https://vggmunicipalidad.gov.ar/scripts/licitaciones/licitaciones-registros.php?anio=2026&tipo=apertura'
        r=extraer_vgg(Path('tests/fixtures/reales/cobertura77/vgg-apertura81.json').read_text(),api)[0]
        self.assertEqual(r['numero_procedimiento'],'26/2026');self.assertEqual(r['presupuesto']['importe'],'84389000');self.assertIsNone(r['presupuesto']['moneda'])
        self.assertEqual(r['documentos'][0]['url'],'https://vggmunicipalidad.gov.ar/galeria/licitaciones/17924075412049.pdf')
        self.assertEqual(o.normalizar(r)['fecha_apertura'],'2026-10-30')
