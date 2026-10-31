import unittest
from unittest.mock import patch
import conectores, extractores

class BarridoDescubrimiento(unittest.TestCase):
    def test_aviso_sin_numero_pliego_o_presupuesto(self):
        html='<main><article>Se solicitan cotizaciones para la provisión de caños para desagües.</article></main>'
        rs,_,_=extractores.extraer(html,'https://oficial.gob.ar/compras/',{'admitir_avisos_sin_numero':True})
        self.assertEqual(len(rs),1)
        self.assertTrue(rs[0]['aviso_oficial_sin_numero'])
        self.assertFalse(rs[0]['documentos'])

    def test_no_confundir_registro_proveedores(self):
        html='<main><article>Solicitud de cotización para provisión: normativa del registro de proveedores.</article></main>'
        rs,_,_=extractores.extraer(html,'https://oficial.gob.ar/',{'admitir_avisos_sin_numero':True})
        self.assertFalse(rs)

    def test_sigue_boletines_oficiales_plural(self):
        calls=[]
        def fetch(url):
            calls.append(url)
            html='<main><a href="/boletines/">Boletines oficiales</a></main>' if len(calls)==1 else '<main>Archivo municipal</main>'
            return html.encode(),'text/html',url
        conectores.explorar('https://oficial.gob.ar/',{'descubrir_contrataciones':True,'descubrir_menu':True,'solo_descubrimiento':True},fetch=fetch)
        self.assertIn('https://oficial.gob.ar/boletines/',calls)

if __name__=='__main__':unittest.main()
