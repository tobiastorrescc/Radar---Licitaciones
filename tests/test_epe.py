from html import escape
import json
from pathlib import Path
import unittest
import extractores
import oportunidades as o

URL='https://www.epe.santafe.gov.ar/app2/aperturas'

class EPETests(unittest.TestCase):
    def setUp(self):
        self.rs=json.loads((Path(__file__).parent/'fixtures'/'epe107.json').read_text())['registros']

    def extraer(self,registro,url=URL):
        # Estructura sintética mínima; textos y números recuperados en #107.
        html='<main><h1>Listado de Aperturas</h1><article>'+escape(registro['titulo'])+'<button>'+escape(registro['objeto'])+'</button></article></main>'
        filas,_,_=extractores.extraer(html,url,{'adaptador':'epe'})
        return [o.normalizar({**r,'organismo':'EPE','provincia':'Santa Fe','fuente':URL}) for r in filas]

    def test_numero_propio_presupuesto_apertura_sin_inventar_publicacion(self):
        for fila in self.rs:
            r,=self.extraer(fila)
            self.assertEqual(r['clasificacion_registro'],'PROCEDIMIENTO')
            self.assertEqual(r['numero_procedimiento'],fila['numero_procedimiento'])
            self.assertEqual(r['procedimiento_canonico'],fila['procedimiento'])
            self.assertEqual(r['objeto'],fila['objeto'])
            self.assertIsNotNone(r['fecha_apertura'])
            self.assertIsNone(r['fecha_publicacion'])
            self.assertIsNotNone(r['presupuesto'])

    def test_etiqueta_hoy_o_cambio_de_url_no_crea_otro_procedimiento(self):
        fila=self.rs[0]
        a,=self.extraer(fila)
        b,=self.extraer({**fila,'titulo':fila['titulo'].replace('Hoy','Queda 1 día')},URL+'?otra=1')
        self.assertEqual(o.identidad(a),o.identidad(b))
        self.assertEqual(len(o.deduplicar([a,b],'2026-10-28T10:00:00-03:00')),1)

    def test_no_habilita_telefonos_ni_otros_organismos(self):
        r,=self.extraer(self.rs[0],'https://otro.gob.ar/listado')
        self.assertEqual(r['clasificacion_registro'],'CANDIDATO_NO_VERIFICADO')
        r={**self.rs[0],'registro_estructurado':False}
        self.assertIsNone(o.procedimiento_canonico(r))

    def test_sin_objeto_dedicado_no_declara_ficha_verificada(self):
        html='<article>Concurso Privado Nº 7040004980 Teléfono de compras</article>'
        rs,_,_=extractores.extraer(html,URL,{'adaptador':'epe'})
        self.assertTrue(all(o.normalizar(r)['clasificacion_registro']=='CANDIDATO_NO_VERIFICADO' for r in rs))
