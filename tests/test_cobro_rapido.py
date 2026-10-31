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

    def test_pago_servicios_en_parrafo_siguiente_no_es_plazo_firme(self):
        import pagos
        texto='ARTÍCULO 9: FORMA DE PAGO La Municipalidad abonará dentro de los Diez (10) días hábiles desde entrega y presentación de factura. En el caso de la ejecución de servicios contratados, los mismos se prestarán según las necesidades del\n\nservicio. El pago podrá hacerse en forma semanal, quincenal o mensual, contra presentación de factura.\n\nARTÍCULO 10: RECONOCIMIENTO DE COSTOS'
        es=pagos.extraer(texto,'https://haciendalapaz.gob.ar/pliego.pdf')
        self.assertEqual(es[0]['categoria'],'OPCIONES_PUBLICADAS')

    def test_pliego_real_lapaz40_no_es_cobro_rapido(self):
        import pagos
        from pathlib import Path
        es=pagos.extraer(Path('tests/fixtures/reales/lapaz40-pago-ocr.txt').read_text(),'https://haciendalapaz.gob.ar/pliego.pdf',hash_documento='727e8101cc959651319cabd903290384c4f1bed0de23635befb0fa7034890c18',pdf=True)
        p=pagos.consolidar(es)
        self.assertEqual(p['clasificacion'],'OPCIONES_PUBLICADAS')
        self.assertFalse(rapido({'pago':p}))

    def test_lapaz39_tabla_revisada_solo_con_hash_correcto(self):
        import fichas
        sha='65b930bc1f48d394bcbe853a974288d223294cff6326a5d76a7e8917099e14f8'
        r=fichas.extraer('','https://haciendalapaz.gob.ar/archivos/20261030074127-f_pliego.pdf',sha,'REVISION')
        self.assertEqual(len(r['productos']['valor']),9)
        self.assertEqual(r['productos']['evidencia']['pagina'],1)
        self.assertEqual(r['productos']['valor'][1]['cantidad'],115)
        self.assertIn('30 días hábiles',r['plazo_entrega']['valor'])
        self.assertNotIn('productos',fichas.extraer('','https://haciendalapaz.gob.ar/otro.pdf','hash_distinto','REVISION'))
