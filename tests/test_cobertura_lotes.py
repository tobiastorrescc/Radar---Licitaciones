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
