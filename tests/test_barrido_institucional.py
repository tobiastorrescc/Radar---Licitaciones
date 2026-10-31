import unittest
import conectores,extractores,oportunidades as o
from barrido_institucional import endpoints_publicados,extraer_feed,busquedas_publicadas

class BarridoInstitucional(unittest.TestCase):
    def test_endpoint_debe_estar_publicado_en_el_html(self):
        c={'endpoints_publicados':[{'url':'https://qx.com.ar/clientes/munic/boletines.php?cols=si'}]}
        self.assertFalse(endpoints_publicados('<main>Boletines</main>',c))
        self.assertEqual(len(endpoints_publicados("<script>var url='https://qx.com.ar/clientes/munic/boletines.php?cols=si'</script>",c)),1)

    def test_paginacion_ajax_oficial_post_y_final_explicito(self):
        base='https://oficial.gob.ar/';api='https://qx.com.ar/clientes/munic/boletines.php?cols=si';calls=[]
        def fetch(u,datos_post=None):
            calls.append((u,datos_post))
            if u==base:return ("<script>var url='"+api+"'</script>").encode(),'text/html',u
            n=1 if datos_post==b'limiteInfConsulta=0' else 2
            html=f'<article><h2>Licitación pública {n}/2026</h2><p>Adquisición de insumos</p></article>'
            if n==2:html+='<div id="finResultados"></div>'
            return html.encode(),'text/html',u
        r=conectores.explorar(base,{'endpoints_publicados':[{'url':api}],'dominios_documentos':['qx.com.ar'],'solo_descubrimiento':True},fetch=fetch)
        self.assertEqual(len(r['oportunidades']),2)
        self.assertEqual([x[1] for x in calls[1:]],[b'limiteInfConsulta=0',b'limiteInfConsulta=6'])

    def test_ajax_repetido_es_incompleto_no_sin_novedades(self):
        base='https://oficial.gob.ar/';api='https://qx.com.ar/clientes/munic/boletines.php?cols=si'
        def fetch(u,datos_post=None):return (("<script>var url='"+api+"'</script>") if u==base else '<p>Listado estático</p>').encode(),'text/html',u
        r=conectores.explorar(base,{'endpoints_publicados':[{'url':api}],'dominios_documentos':['qx.com.ar']},fetch=fetch)
        self.assertTrue(any('repite página' in x['error'] for x in r['errores']))
        self.assertNotEqual(r['estado'],'SIN_PUBLICACIONES')

    def test_feed_registra_sin_presupuesto_ni_documento(self):
        xml=b'<rss><channel><item><title>Licitacion publica 2/2026</title><link>https://oficial.gob.ar/aviso/</link><pubDate>Fri, 30 Oct 2026 10:00:00 -0300</pubDate><description>Adquisicion de insumos</description></item></channel></rss>'
        rs,links,n=extraer_feed(xml,'https://oficial.gob.ar/feed/',{})
        self.assertEqual(n,1);self.assertEqual(len(rs),1);self.assertEqual(rs[0]['fecha_publicacion_texto'],'2026-10-30')
        self.assertEqual(links,['https://oficial.gob.ar/aviso/']);self.assertFalse(rs[0]['documentos'])

    def test_feed_pagina_de_licitaciones_no_fecha_todos_los_adjuntos_con_fecha_antigua(self):
        xml=b'<rss><channel><item><title>Licitaciones</title><link>https://oficial.gob.ar/licitaciones/</link><pubDate>Wed, 01 Aug 2018 10:00:00 -0300</pubDate><description>&lt;p&gt;Licitacion publica 9/2026 Adquisicion de retroexcavadora&lt;/p&gt;&lt;p&gt;Licitacion publica 7/2026 Venta de lotes&lt;/p&gt;</description></item></channel></rss>'
        rs,_,_=extraer_feed(xml,'https://oficial.gob.ar/feed/',{})
        self.assertEqual(len(rs),2)
        self.assertTrue(all(not r.get('fecha_publicacion_texto') for r in rs))

    def test_formulario_get_sibom_es_enlace_de_boletin(self):
        html='<form method="get" action="/bulletins/13933"><input type="submit" value="Ver Boletin"></form><form method="post" action="/admin"></form>'
        links=extractores.DOM(html).root.enlaces('https://sibom.slyt.gba.gob.ar/cities/102')
        self.assertEqual([x['url'] for x in links],['https://sibom.slyt.gba.gob.ar/bulletins/13933'])

    def test_anio_explicito_de_2026_no_es_numero_sin_anio(self):
        self.assertEqual(extractores.procesos('Licitación Privada N°32 de 2026')[0]['numero'],'32/2026')

    def test_buscador_get_publicado_sin_formularios_login_ni_dominios_ajenos(self):
        html='<form role="search" method="get" action="https://oficial.gob.ar/"><input name="s" type="search"></form><form method="post" action="/login"><input name="q"></form><form role="search" action="https://otro.gob.ar/"><input name="s" type="search"></form>'
        urls=busquedas_publicadas(extractores.DOM(html),'https://oficial.gob.ar/')
        self.assertEqual(len(urls),5)
        self.assertIn('https://oficial.gob.ar/?s=licitacion',urls)
        self.assertTrue(all('oficial.gob.ar' in u for u in urls))

    def test_correlativo_viale_y_plazo_para_el_sin_inventar_anio(self):
        url='https://viale.gob.ar/wp-content/uploads/2026/10/2535.pdf'
        texto='COTEJO DE PRECIOS Nro.2535\nPara El : 30/10/2026 A Las 11.00 HS.\nObjeto : ADQ. DE NEUMATICOS\nMunicipio de Viale\nPresentar antes de la hora fijada por Mesa de Entradas.'
        from unittest.mock import patch
        with patch('cache_documentos.leer_texto',return_value=(texto,{})):
            r=conectores.explorar(url,{'organismo':'Municipio de Viale','provincia':'Entre Ríos','correlativos_publicados':True,'solo_descubrimiento':True},fetch=lambda u:(b'%PDF-test','application/pdf',u))
        x=o.normalizar(r['oportunidades'][0],'2026-10-31T10:00:00-03:00')
        self.assertEqual(x['numero_procedimiento'],'2535');self.assertEqual(x['vigencia'],'VENCIDA')
        self.assertEqual(x['fecha_limite_presentacion'],'2026-10-30');self.assertIsNone(x['fecha_apertura'])

class CapturaBinaria(unittest.TestCase):
    def test_pdf_se_conserva_sin_interpretarlo_como_html(self):
        from tools.sondear_cobertura import worker
        from unittest.mock import patch
        from tempfile import TemporaryDirectory
        from pathlib import Path
        import json
        with TemporaryDirectory() as tmp:
            entrada=Path(tmp)/'entrada.json';salida=Path(tmp)/'salida.json'
            entrada.write_text(json.dumps({'url':'https://oficial.gob.ar/aviso.pdf'}))
            with patch('conectores.descargar',return_value=(b'%PDF-1.4\nbinario','application/pdf','https://oficial.gob.ar/aviso.pdf')),patch('extractores.DOM',side_effect=AssertionError('PDF no es HTML')):
                worker(entrada,salida)
            r=json.loads(salida.read_text());self.assertEqual(r['paginas_correctas'],1);self.assertEqual(r['enlaces'],[])
            self.assertEqual(Path(r['archivo']).read_bytes(),b'%PDF-1.4\nbinario')

class BoletinER(unittest.TestCase):
    def test_rutas_segun_cliente_oficial_y_orden_reciente(self):
        from barrido_institucional import ediciones_entre_rios
        import json
        r=ediciones_entre_rios(json.dumps([{'nro':'28448','fecha':'2026-10-30'},{'nro':'28336','fecha':'2026-05-18'}]))
        self.assertEqual(r,[('https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/30-10-26.pdf','2026-10-30')])

    def test_avisos_sin_pliego_ni_presupuesto_y_frontera_por_id(self):
        from barrido_institucional import boletin_entre_rios
        t='LICITACIONES\nMUNICIPALIDAD DE SEGUI\nLicitación Pública 9/2026\nObjeto: Adquisición de retroexcavadora. Apertura: 03/11/2026 a las 10:00\nID:1234 - F.C.\nCOMUNA COLONIA CRESPO\nLicitación Pública 1/2026\nObjeto: Compra de materiales. Apertura: 02/06/2026\nID:1235 - F.C.\nCONCURSOS Y QUIEBRAS\nMUNICIPALIDAD DE OTRA\nLicitación Pública 1/2026\n'
        rs=boletin_entre_rios(t,'https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/30-10-26.pdf')
        self.assertEqual(len(rs),2)
        self.assertEqual(o.normalizar(rs[0],'2026-10-31T12:00:00Z')['vigencia'],'ABIERTA')
        self.assertEqual(o.normalizar(rs[1],'2026-10-31T12:00:00Z')['vigencia'],'VENCIDA')
        self.assertIsNone(rs[0].get('fecha_publicacion_texto'))

    def test_enersa_numeracion_literal_sin_repetir_citas(self):
        from barrido_institucional import boletin_entre_rios
        t='CONCURSOS\nEnersa (Energía de Entre Ríos S.A.)\nConcursos de Precios Módulo A\nN.º 2026-0841: Servicio de mantenimiento. Presentación de ofertas hasta 03/11/2026. Expediente 2026-0841.\nN.º 2026-0862: Adquisición de cable. Presentación de ofertas hasta 04/11/2026.\nID:30159 - F.C.\nDESIGNACIÓN DE AUTORIDADES\n'
        rs=boletin_entre_rios(t,'https://www.entrerios.gov.ar/boletin/calendario/Boletin/2026/Octubre/30-10-26.pdf')
        self.assertEqual(len(rs),2)
        self.assertNotEqual(o.identidad(rs[0]),o.identidad(rs[1]))
        self.assertIn('ENERSA-2026-0841',o.procedimiento_canonico(rs[0]))

class CorrespondenciaComplementaria(unittest.TestCase):
    def test_mismo_numero_con_otro_objeto_no_es_antecedente(self):
        base={'id':'base','organismo':'Ministerio de Planeamiento','provincia':'Entre Ríos','numero_procedimiento':'12/2026','tipo_procedimiento':'licitacion publica','fecha_apertura':'2026-11-25','objeto':'Cambio de tanques cubierta accesibilidad y refacción en baños Escuela Luis Agote','identidad_ambito':'departamento-arquitectura','numero_convocatoria':'2'}
        aviso={**base,'id':None,'es_fuente_complementaria':True,'numero_convocatoria':None,'identidad_ambito':None,'objeto':'Provisión de materiales y mano de obra: cambio de tanques cubierta accesibilidad refacción baños Escuela Luis Agote'}
        self.assertEqual(o.antecedente_complementario(aviso,[base])['id'],'base')
        distinto={**aviso,'objeto':'Adquisición de combustible para maquinaria vial y camiones'}
        self.assertIsNone(o.antecedente_complementario(distinto,[base]))
        self.assertIsNone(o.antecedente_complementario(aviso,[base,{**base,'id':'otro','identidad_ambito':'otro-departamento'}]))

class PliegoSegui(unittest.TestCase):
    def test_clausula_condicional_desierto_no_cierra_convocatoria(self):
        from pathlib import Path
        from unittest.mock import patch
        texto=Path('tests/fixtures/segui_09_2026.txt').read_text()
        url='https://www.segui.gob.ar/sitio/wp-content/uploads/2025/01/MUNICIPALIDAD-DE-SEGUI-Pliegos-Lic-Publica-09-2026-1.pdf'
        with patch('cache_documentos.leer_texto',return_value=(texto,{})):
            r=conectores.explorar(url,{'organismo':'Municipalidad de Seguí','provincia':'Entre Ríos','solo_descubrimiento':True},fetch=lambda u:(b'%PDF-test','application/pdf',u))
        rs=[o.normalizar(x,'2026-10-31T15:00:00-03:00') for x in r['oportunidades']]
        self.assertEqual(len(rs),1)
        self.assertEqual(rs[0]['numero_procedimiento'],'9/2026')
        self.assertEqual(rs[0]['vigencia'],'ABIERTA')
        self.assertFalse(rs[0]['desierta'])
        self.assertEqual(rs[0]['fecha_apertura'],'2026-11-03')
        self.assertIsNone(rs[0]['fecha_publicacion'])

    def test_ley_contabilidad_y_calle_publica_no_son_procedimientos(self):
        from unittest.mock import patch
        texto='LICITACIÓN PÚBLICA 3/2026\nObjeto: Adquisición de materiales. Apertura: 03/11/2026.\nLa Ley de Contabilidad Pública Nº 5140 y sus decretos.\nSobre calle Pública Nº 26 por doce millones.'
        url='https://oficial.gob.ar/3-2026.pdf'
        with patch('cache_documentos.leer_texto',return_value=(texto,{})):
            r=conectores.explorar(url,{'solo_descubrimiento':True},fetch=lambda u:(b'%PDF-test','application/pdf',u))
        self.assertEqual([x['numero_procedimiento'] for x in r['oportunidades']],['3/2026'])

if __name__=='__main__':unittest.main()
