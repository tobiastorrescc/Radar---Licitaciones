import unittest
from pathlib import Path
import extractores,oportunidades as o

class MinplanAvisos(unittest.TestCase):
    def test_aviso_sin_numero_con_fecha_y_objeto_no_exige_pdf(self):
        html=Path('tests/fixtures/rosario_issue10/minplan-tarjetas.html').read_text()
        rs,_,_=extractores.extraer(html,'https://www.entrerios.gov.ar/minplan/licitaciones',{'adaptador':'minplan'})
        self.assertEqual(len(rs),8)
        xs=[o.normalizar(r,'2026-11-05T08:00:00-03:00') for r in rs]
        abiertos=[x for x in xs if x['vigencia']=='ABIERTA'];self.assertEqual(len(abiertos),3)
        la_paz=next(x for x in abiertos if 'Primera Junta' in x['objeto'])
        self.assertIsNone(la_paz['numero_procedimiento']);self.assertEqual(la_paz['tipo_procedimiento'],'cotejo de precios')
        self.assertEqual(la_paz['localidad'],'La Paz');self.assertEqual(la_paz['fecha_apertura'],'2026-11-11')
        self.assertEqual(la_paz['presupuesto']['importe'],'42218380.22');self.assertIsNone(la_paz['fecha_publicacion'])
        self.assertNotIn('cisterna',la_paz['objeto']);self.assertTrue(la_paz['documentos'])
        otro=next(x for x in abiertos if 'cisterna' in x['objeto']);self.assertEqual(otro['fecha_apertura'],'2026-11-12')
        self.assertEqual(otro['presupuesto']['importe'],'64650283.02')
        iapv=next(x for x in abiertos if x['numero_procedimiento']=='1/2026')
        self.assertIn('IAPV',iapv['organismo']);self.assertIsNone(iapv['presupuesto']) # Dos presupuestos publicados, no reducirlos a uno.

if __name__=='__main__':unittest.main()
