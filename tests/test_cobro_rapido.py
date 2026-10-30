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
