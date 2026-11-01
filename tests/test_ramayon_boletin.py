import unittest
from pathlib import Path
import conectores,oportunidades as o,extractores

class RamayonBoletin(unittest.TestCase):
    def explorar(self,html):
        inicio='https://www.santafe.gov.ar/boletinoficial/'
        aviso=inicio+'ver.php?seccion=2026/2026-09-18licitaciones.html'
        paginas={inicio:'<a href="'+aviso+'">Licitaciones</a>',aviso:html}
        return conectores.explorar(inicio,{'adaptador':'boletin-sf','provincia':'Santa Fe','organismos_multiples':True,'solo_descubrimiento':True,'seguir_patrones':['ver.php.*licitaciones']},fetch=lambda u:(paginas[u].encode(),'text/html',u))
    def test_aviso_ramayon_sin_adjunto_se_descubre_por_la_seccion(self):
        html=Path('tests/fixtures/ramayon_bo_20260918.html').read_text()
        r=self.explorar(html);rs=[o.normalizar(x,'2026-11-01T08:00:00-03:00') for x in r['oportunidades']]
        x=next(x for x in rs if o.norm(x['localidad'])=='ramayon')
        self.assertEqual(x['numero_procedimiento'],'1/2026')
        # La edición está fechada; no sustituir automáticamente la primera publicación.
        self.assertIn('2026-09-18licitaciones.html',x['url'])
        self.assertIsNone(x['fecha_publicacion'])
        self.assertEqual(x['fecha_apertura'],'2026-10-08')
        self.assertEqual(x['fecha_limite_presentacion'],'2026-10-06')
        self.assertEqual(x['vigencia'],'VENCIDA')
        self.assertEqual(x['presupuesto']['importe'],'50000000')
        self.assertIn('TRACTOR',x['objeto']);self.assertFalse(x['documentos'])
        self.assertNotIn('CAMIÓN',x['objeto'])
        self.assertEqual(len(rs),2)
    def test_el_presupuesto_y_el_pliego_no_condicionan_la_deteccion(self):
        html=Path('tests/fixtures/ramayon_bo_20260918.html').read_text()
        import re
        html=re.sub(r'<p>Presupuesto Oficial:.*?</p>','',html)
        rs=self.explorar(html)['oportunidades']
        x=next(x for x in rs if o.norm(x['localidad'])=='ramayon')
        self.assertEqual(x['numero_procedimiento'],'1/2026');self.assertIsNone(x['presupuesto'])
        self.assertFalse(x['documentos'])

if __name__=='__main__':unittest.main()
