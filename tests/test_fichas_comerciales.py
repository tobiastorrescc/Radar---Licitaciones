import unittest
import json
from pathlib import Path
import fichas
import pagos
import oportunidades as o

class ComercialTests(unittest.TestCase):
    def test_plazo_emitir_factura_no_es_plazo_pago(self):
        r=pagos.clasificar('Plazo de pago: treinta (30) días desde recepción definitiva. La factura deberá ser emitida dentro de los cinco (5) días de obtenida la recepción definitiva.')
        self.assertEqual(r['plazos_dias'],[30]);self.assertFalse(r['acreditacion_inmediata_comprobada'])
    def test_tabla_y_hito_complementarios_se_unen_solo_mismo_documento_y_pagina(self):
        es=pagos.extraer('Plazo de Pago Cantidad Unidad de Tiempo 30 Días Hábiles Administrativos\n\nEl plazo de pago se contará a partir del día siguiente a la fecha de recepción definitiva.','https://oficial.gob.ar/a.pdf','a',pdf=True)
        r=pagos.consolidar(es);self.assertEqual(r['estado'],'VERIFICADO');self.assertEqual(r['plazos_dias'],[30]);self.assertIn('CONFORMIDAD_RECEPCION',r['hitos_inicio'])
        es[-1]['pagina']=2;self.assertEqual(pagos.consolidar(es)['estado'],'PENDIENTE')
    def test_hitos_factura_y_recepcion_distintos_siguen_pendientes(self):
        es=pagos.extraer('Forma de pago: a 30 días desde presentación de factura.\n\nPlazo de pago: a 30 días desde recepción definitiva.','https://oficial.gob.ar/a.pdf','a',pdf=True)
        self.assertEqual(pagos.consolidar(es)['estado'],'PENDIENTE')
    def test_orden_por_intervalos_incluye_anticipos_y_sin_verificar(self):
        frases=['Pago: anticipo total.','Pago: contado.','Pago: a 5 días.','Pago: a 10 días.','Pago: a 15 días.','Pago: a 30 días.','Pago: a 60 días.','Pago: a 90 días.','No publicado']
        ps=[pagos.consolidar(pagos.extraer(t,'https://o.gob.ar/a.pdf','a')) for t in frases]
        self.assertEqual([pagos.grupo_comercial(p) for p in ps],list(range(9)))
    def test_chajari_solo_mismo_hash_y_cantidades_verificadas(self):
        sha='2b0bd43c642b8ecc8691d43b781a8391d70582baebb5e2b06b309df1e5c5304f'
        d=fichas.extraer('','https://licitaciones.chajari.gob.ar/licitaciones?state=para_apertura?id=710',sha)
        self.assertEqual(len(d['productos']['valor']),13)
        fila=next(r for r in d['productos']['valor'] if r['equipo']=='KOMATSU PC 200' and r['renglon']==3)
        self.assertEqual(fila['cantidad'],4)
        self.assertNotIn('productos',fichas.extraer('','https://otro.gob.ar/a.pdf','otro-hash'))
    def test_no_asume_acreditacion_inmediata_ni_fecha_desconocida(self):
        f=fichas.construir({'objeto':'Repuestos','pago':pagos.consolidar(pagos.extraer('Pago: contado contra entrega.','https://o.gob.ar/a.pdf','a'))})
        self.assertEqual(f['campos']['fecha_publicacion']['estado'],'PENDIENTE')
        self.assertIsNone(f['recuperacion_efectiva_capital']['dias'])
    def test_suspension_no_figura_como_abierta(self):
        r=o.normalizar({'titulo':'Licitación Pública 1/2026','situacion_publicada':'SUSPENDIDA','fecha_apertura':'2026-11-20'},'2026-10-30T12:00:00-03:00')
        self.assertNotEqual(r['vigencia'],'ABIERTA')
