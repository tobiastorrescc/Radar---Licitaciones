import unittest
import conectores,extractores,oportunidades as o
from barrido_institucional import endpoints_publicados,extraer_feed

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

    def test_formulario_get_sibom_es_enlace_de_boletin(self):
        html='<form method="get" action="/bulletins/13933"><input type="submit" value="Ver Boletin"></form><form method="post" action="/admin"></form>'
        links=extractores.DOM(html).root.enlaces('https://sibom.slyt.gba.gob.ar/cities/102')
        self.assertEqual([x['url'] for x in links],['https://sibom.slyt.gba.gob.ar/bulletins/13933'])

    def test_anio_explicito_de_2026_no_es_numero_sin_anio(self):
        self.assertEqual(extractores.procesos('Licitación Privada N°32 de 2026')[0]['numero'],'32/2026')

    def test_correlativo_viale_y_plazo_para_el_sin_inventar_anio(self):
        url='https://viale.gob.ar/wp-content/uploads/2026/10/2535.pdf'
        texto='COTEJO DE PRECIOS Nro.2535\nPara El : 30/10/2026 A Las 11.00 HS.\nObjeto : ADQ. DE NEUMATICOS\nMunicipio de Viale\nPresentar antes de la hora fijada por Mesa de Entradas.'
        from unittest.mock import patch
        with patch('cache_documentos.leer_texto',return_value=(texto,{})):
            r=conectores.explorar(url,{'organismo':'Municipio de Viale','provincia':'Entre Ríos','correlativos_publicados':True,'solo_descubrimiento':True},fetch=lambda u:(b'%PDF-test','application/pdf',u))
        x=o.normalizar(r['oportunidades'][0],'2026-10-31T10:00:00-03:00')
        self.assertEqual(x['numero_procedimiento'],'2535');self.assertEqual(x['vigencia'],'VENCIDA')
        self.assertEqual(x['fecha_limite_presentacion'],'2026-10-30');self.assertIsNone(x['fecha_apertura'])

if __name__=='__main__':unittest.main()
