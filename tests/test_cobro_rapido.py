import unittest
from tools.revisar_cobro_rapido import rapido

class CobroRapido(unittest.TestCase):
    def test_solo_evidencia_y_hasta_quince(self):
        self.assertTrue(rapido({'pago':{'estado':'VERIFICADO','clasificacion':'CONTRA_ENTREGA'}}))
        self.assertTrue(rapido({'pago':{'estado':'VERIFICADO','plazos_dias':[15]}}))
        self.assertFalse(rapido({'pago':{'estado':'PENDIENTE','clasificacion':'CONTADO'}}))
        self.assertFalse(rapido({'pago':{'estado':'VERIFICADO','plazos_dias':[5,30]}}))
        self.assertFalse(rapido({'pago':{'estado':'VERIFICADO','plazos_dias':[]}}))

    def test_no_confundir_direccion_ni_opciones(self):
        self.assertFalse(rapido({'pago':{'estado':'VERIFICADO','clasificacion':'CONTADO','direccion':'OFERTANTE_AL_ORGANISMO'}}))
        self.assertFalse(rapido({'pago':{'estado':'VERIFICADO','clasificacion':'OPCIONES_PUBLICADAS','plazos_dias':[5]}}))

    def test_plazo_firme_no_desaparece_por_retenciones_eventuales(self):
        import pagos
        c='FORMA DE PAGO: La Municipalidad de La Paz abonará el importe dentro de los 10 (diez) días hábiles posteriores a la fecha de entrega del bien y presentación de la factura. También podrán realizarse pagos parciales en caso de certificaciones parciales. La Municipalidad podrá retener las deudas por tasas.'
        e=pagos.clasificar(c)
        self.assertEqual(e['plazos_dias'],[10])
        self.assertEqual(e['unidades_dias'],['habiles'])
        self.assertIn('ENTREGA',e['hitos_inicio'])
        self.assertIn('PRESENTACION_FACTURA',e['hitos_inicio'])
        self.assertTrue(e['pagos_parciales'])

    def test_calendario_alternativo_no_promete_cobro_a_diez(self):
        import pagos
        e=pagos.clasificar('FORMA DE PAGO: La Municipalidad abonará dentro de los 10 días desde entrega. En el caso de servicios, el pago podrá hacerse en forma semanal, quincenal o mensual contra presentación de factura.')
        self.assertEqual(e['categoria'],'OPCIONES_PUBLICADAS')

    def test_ficha_rosario_numero_no_es_expediente(self):
        from pathlib import Path
        from tools.ficha_rosario import extraer
        import oportunidades as o
        url='https://www.rosario.gob.ar/inicio/compras-licitaciones/detalle/38684'
        r=o.normalizar(extraer(Path('tests/fixtures/reales/rosario-detalle-38684.html').read_text(),url)[0])
        self.assertEqual(r['numero_procedimiento'],'64/2026')
        self.assertEqual(r['expediente'],'40641/2026')
        self.assertEqual(r['fecha_publicacion'],'2026-10-30')
        self.assertEqual(r['fecha_apertura'],'2026-11-10')
        self.assertEqual(r['documentos'][0]['url'],'https://apimgw.rosario.gob.ar/licitaciones-api/v1/licitaciones/38684/documentos/102885')
        self.assertEqual(extraer('<h1>Información general</h1>',url),[])
