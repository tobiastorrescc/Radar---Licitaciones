import unittest
from tools.revisar_cobro_rapido import rapido

class CobroRapido(unittest.TestCase):
    def test_solo_evidencia_y_hasta_quince(self):
        self.assertTrue(rapido({'pago':{'estado':'VERIFICADO','clasificacion':'CONTRA_ENTREGA'}}))
        self.assertTrue(rapido({'pago':{'estado':'VERIFICADO','plazos_dias':[15]}}))
        self.assertFalse(rapido({'pago':{'estado':'PENDIENTE','clasificacion':'CONTADO'}}))
        self.assertFalse(rapido({'pago':{'estado':'VERIFICADO','plazos_dias':[5,30]}}))
        self.assertFalse(rapido({'pago':{'estado':'VERIFICADO','plazos_dias':[]}}))
