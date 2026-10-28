import json
from pathlib import Path
import unittest
import conectores
import extractores
import oportunidades

BASE='https://www.generalramirez.gob.ar/licitaciones-y-concursos/'
FIXTURES=Path(__file__).parent/'fixtures'/'ramirez'

class RamirezTests(unittest.TestCase):
    def extraer(self,texto,url=BASE+'licitaciones-publicas/'):
        rs,_,_=extractores.extraer(texto,url,{'adaptador':'ramirez'})
        return [oportunidades.normalizar(r) for r in rs]

    def test_captura_real_presupuesto_no_confunde_ofertas_ni_publicacion(self):
        r,=self.extraer((FIXTURES/'publicas.html').read_text())
        self.assertEqual(r['numero_procedimiento'],'1/2026')
        self.assertEqual(r['presupuesto']['importe'],'56960000.00')
        self.assertEqual(r['fecha_apertura'],'2026-09-11')
        self.assertIsNone(r['fecha_publicacion'])
        self.assertIsNone(r['situacion_publicada'])
        self.assertIn('1300 M3 BROZA',r['objeto'])
        self.assertTrue(r['detalle_completo'])
        self.assertIsNone(r['enlace_pliego']) # Decreto no se presenta como pliego.
        self.assertEqual(r['condiciones_pago'],'Pago no informado')

    def test_captura_real_privada_y_adjudicacion_explicita(self):
        r,=self.extraer((FIXTURES/'privadas.html').read_text(),BASE+'licitaciones-privadas/')
        self.assertEqual(r['tipo_procedimiento'],'licitacion privada')
        self.assertEqual(r['numero_procedimiento'],'7/2026')
        self.assertEqual(r['situacion_publicada'],'ADJUDICADA')
        self.assertEqual(r['presupuesto']['importe'],'28860000.00')
        self.assertEqual(len(r['documentos']),2)

    def test_historico_mismo_procedimiento_no_crea_duplicado(self):
        texto=(FIXTURES/'publicas.html').read_text()
        actual,=self.extraer(texto)
        historico,=self.extraer(texto.replace('<h1>Licitaciones públicas</h1>',
            '<h1>2026 – Municipalidad de General Ramírez</h1><h2>Histórico: Licitaciones publicas</h2>'),
            'https://www.generalramirez.gob.ar/licitaciones-publicas/2026/')
        self.assertEqual(oportunidades.identidad(actual),oportunidades.identidad(historico))

    def test_multiples_fichas_concursos_sin_mezclar_datos(self):
        texto=(FIXTURES/'publicas.html').read_text().replace('Licitaciones públicas','Concursos de Precios')
        ficha=texto[texto.index('<div class="ficha-listado">'):texto.index('<div class="filtrosListados">')]
        texto=texto.replace('<div class="filtrosListados">',ficha.replace('<span>01</span>','<span>02</span>').replace('56.960.000,00','1.000,00')+'<div class="filtrosListados">')
        rs=self.extraer(texto,BASE+'concursos/')
        self.assertEqual(len(rs),2)
        self.assertEqual([r['tipo_procedimiento'] for r in rs],['concurso de precios']*2)
        self.assertEqual([r['presupuesto']['importe'] for r in rs],['56960000.00','1000.00'])

    def test_pagina_general_y_telefonos_no_son_procedimientos(self):
        self.assertEqual(self.extraer('<main><h1>Licitaciones y Concursos</h1><h2>0343/2026</h2><p>Teléfono compras</p></main>'),[])

    def test_conector_sigue_solo_enlaces_publicados_y_no_pide_documento_innecesario(self):
        config=json.loads(Path('fuentes.json').read_text())[BASE]
        pedidos=[]
        def transportar(url):
            pedidos.append(url)
            if url==BASE:
                html='<main><a href="licitaciones-publicas/">Licitaciones públicas</a><a href="concursos/">Concursos</a></main>'
            elif url==BASE+'licitaciones-publicas/':html=(FIXTURES/'publicas.html').read_text().split('<div class="filtrosListados">')[0]+'</main>'
            elif url==BASE+'concursos/':html=(FIXTURES/'privadas.html').read_text().replace('Licitaciones privadas','Concursos de Precios').split('<div class="filtrosListados">')[0]+'</main>'
            else:raise AssertionError('URL no publicada o descarga innecesaria: '+url)
            return html.encode(),'text/html',url
        r=conectores.explorar(BASE,config,fetch=transportar)
        self.assertEqual(r['estado'],'OPERATIVA')
        self.assertEqual(len(r['oportunidades']),2)
        self.assertEqual(len(pedidos),3)
