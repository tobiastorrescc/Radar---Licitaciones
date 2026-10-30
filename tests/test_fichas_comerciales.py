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

class IntegridadClasificacionTests(unittest.TestCase):
    def test_circular_con_tipo_explicito_se_vincula_al_mismo_procedimiento(self):
        import extractores
        texto='CIRCULAR ACLARATORIA N°1 LICITACION 26/26. LLAMADO A LICITACION PUBLICA NACIONAL N°26/26 INDUMENTARIA'
        ps=extractores.procesos(texto)
        self.assertTrue(ps);self.assertTrue(all(p['tipo']=='licitacion publica' for p in ps))
        a=o.normalizar({'titulo':'Licitación Pública 26/2026','organismo':'Municipalidad VGG','provincia':'Santa Fe','objeto':'Indumentaria'})
        b=o.normalizar({'titulo':texto,'numero_procedimiento':'26/2026','tipo_procedimiento':'licitacion','organismo':'Municipalidad VGG','provincia':'Santa Fe'})
        self.assertEqual(o.identidad(a),o.identidad(b));self.assertEqual(b['tipo_documento'],'CIRCULAR_ACLARATORIA')
    def test_primera_deteccion_sin_fecha_no_es_historica_solo_por_fuente_parcial(self):
        import incremental as inc
        p={'https://oficial.gob.ar/':{'inicio':'2026-10-29T10:00:00-03:00','base_completa':False,'ultima_completa':None}}
        r={'fuente':'https://oficial.gob.ar/','numero_procedimiento':'19/2026','fecha_apertura':'2026-11-19'}
        self.assertEqual(inc.tipo_nuevo(r,p,'2026-10-30T12:00:00-03:00'),'NUEVA_DETECCION_FECHA_DESCONOCIDA')
        r['fecha_apertura']='2026-09-01';self.assertEqual(inc.tipo_nuevo(r,p,'2026-10-30T12:00:00-03:00'),'RECUPERACION_LINEA_BASE')
    def test_ficha_reutiliza_revision_visual_por_hash_sin_ocr(self):
        f=fichas.construir({'comprobacion_pliego':{'sha256':'2b0bd43c642b8ecc8691d43b781a8391d70582baebb5e2b06b309df1e5c5304f','url':'https://licitaciones.chajari.gob.ar/licitaciones?state=para_apertura?id=710'}})
        self.assertEqual(len(f['campos']['productos']['valor']),13)

class CamposDocumentalesTests(unittest.TestCase):
    def test_mencion_suelta_de_plazo_no_absorbe_parrafo_siguiente(self):
        d=fichas.extraer('Se evaluará el plazo de entrega.\n\nLa adjudicación quedará sujeta a la normativa.','https://oficial.gob.ar/a.pdf','a')
        self.assertNotIn('plazo_entrega',d)
    def test_campo_futuro_que_cambia_hash_no_reutiliza_cantidades_anteriores(self):
        f=fichas.construir({'comprobacion_pliego':{'sha256':'nuevo','url':'https://licitaciones.chajari.gob.ar/a.pdf'}})
        self.assertEqual(f['campos']['productos']['estado'],'PENDIENTE')

class URLsRosarioTests(unittest.TestCase):
    def test_paginacion_con_mismos_parametros_no_se_repite_por_orden(self):
        import extractores
        a='https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones?recomendada=apertura&tipoRecomendada=5&page=2'
        b='https://www.rosario.gob.ar/inicio/result-busq-compras-licitaciones?page=2&recomendada=apertura&tipoRecomendada=5'
        self.assertEqual(extractores.url_publica(a),extractores.url_publica(b))

class SalidasGrandesTests(unittest.TestCase):
    def test_documento_con_json_grande_no_se_bloquea_por_pipe(self):
        from unittest.mock import patch
        import subprocess,sys
        from tools import comprobar_pliegos as c
        popen=subprocess.Popen
        payload="import json; print(json.dumps({'url':'https://oficial.gob.ar/a.pdf','estado':'DOCUMENTO_ACCESIBLE','datos':'x'*150000}))"
        def factory(args,**kw):return popen([sys.executable,'-c',payload],**kw)
        registro={'clasificacion_registro':'PROCEDIMIENTO','vigencia':'ABIERTA','url':'https://oficial.gob.ar/ficha','fuente':'https://oficial.gob.ar/','documentos':[{'url':'https://oficial.gob.ar/a.pdf','titulo':'Pliego'}]}
        with patch.object(c.subprocess,'Popen',side_effect=factory),patch('builtins.print'):r=c.comprobar([registro],'2026-10-30',[],total=3)
        self.assertEqual(r[0]['estado'],'DOCUMENTO_ACCESIBLE');self.assertEqual(len(r[0]['datos']),150000)

class HuellaFichaTests(unittest.TestCase):
    def test_reusar_ocr_no_crea_cambio_pero_otra_cantidad_si(self):
        import copy,incremental as inc
        r={'titulo':'Licitación Pública 1/2026','detalle_documental':{'productos':{'valor':[{'producto':'Cadena','cantidad':2}],'estado':'VERIFICADO','evidencia':{'sha256':'a','url':'https://o.gob.ar/a.pdf','pagina':5,'metodo':'OCR_SELECTIVO'}}}}
        b=copy.deepcopy(r);b['detalle_documental']['productos']['evidencia']['metodo']='OCR_SELECTIVO_CACHE'
        self.assertEqual(inc.huella(r),inc.huella(b))
        b['detalle_documental']['productos']['valor'][0]['cantidad']=4
        self.assertNotEqual(inc.huella(r),inc.huella(b))

class CantidadesTests(unittest.TestCase):
    def test_cantidad_narrativa_con_vinculo_explicito_y_sin_telefonos(self):
        d=fichas.extraer('Adquisición de 600 luminarias leds para alumbrado público. Teléfono 03442 555555.','https://oficial.gob.ar/a.pdf','a')
        self.assertEqual(d['productos']['valor'][0]['cantidad'],600)
        uno=fichas.extraer('Provisión de una (1)contadora de billetes.','https://www.iafas.gov.ar/descargas/17688','a')
        self.assertEqual(uno['productos']['valor'][0]['cantidad'],1)
        self.assertNotIn('productos',fichas.extraer('Presupuesto 6000000. Teléfono 03442 555555.','https://oficial.gob.ar/a.pdf','a'))
    def test_numero_en_letras_contradictorio_no_se_afirma(self):
        d=fichas.extraer('Provisión de una (2) contadora de billetes.','https://oficial.gob.ar/a.pdf','a')
        self.assertNotIn('productos',d)

class CondicionesSinPlazoTests(unittest.TestCase):
    def test_iafas_condicion_verificada_no_equivale_a_contado_ni_a_dias_inventados(self):
        texto='FORMAS de PAGO. El pago al proveedor se realizará en el Dpto. Tesorería del Instituto previa entrega y aceptación de lo que le fuera adjudicado; en cumplimiento de los trámites administrativos corrientes y presentación por parte del adjudicatario de la pertinente factura. En el caso de que se hubiera efectuado la adjudicación en moneda extranjera autorizada, la factura se convertirá a moneda nacional.\n\nEl pago, en caso del servicio mensual de mantenimiento, se realizará mensual a mes vencido.'
        p=pagos.consolidar(pagos.extraer(texto,'https://www.iafas.gov.ar/descargas/17688','b',pdf=True))
        self.assertEqual(p['estado'],'VERIFICADO');self.assertEqual(p['clasificacion'],'DESPUES_CONFORMIDAD_RECEPCION')
        self.assertEqual(p['plazos_dias'],[]);self.assertIn('PRESENTACION_FACTURA',p['hitos_inicio']);self.assertIn('TRAMITES_ADMINISTRATIVOS',p['hitos_inicio'])
        self.assertIn('plazo no indicado',p['etiqueta'])
    def test_oferta_por_pago_contado_no_prueba_condicion_de_cobro(self):
        p=pagos.consolidar(pagos.extraer('Las propuestas deberán consignar: d) Oferta por pago contado.','https://o.gob.ar/a.pdf','a'))
        self.assertEqual(p['estado'],'PENDIENTE')

class ClausulaContinuaTests(unittest.TestCase):
    def test_mismo_articulo_en_paginas_contiguas_completa_plazo_y_condiciones(self):
        texto='ARTÍCULO 15: FORMAS de PAGO. El pago al proveedor se realizará previa entrega y aceptación; en cumplimiento de los trámites administrativos corrientes y presentación por parte del adjudicatario de la pertinente factura.\fEl pago será efectuado dentro de los treinta (30) días corridos de la fecha de recepción de la correspondiente documentación.'
        es=pagos.extraer(texto,'https://www.iafas.gov.ar/descargas/17685','a',pdf=True)
        p=pagos.consolidar(es);self.assertEqual(p['estado'],'VERIFICADO');self.assertEqual(p['plazos_dias'],[30]);self.assertEqual(p['hitos_inicio'],['RECEPCION_DOCUMENTACION_CORRESPONDIENTE'])
        self.assertTrue(p['evidencias'][0]['evidencias_condiciones_previas'])
        es[-1]['clausula']='Articulo 18'
        self.assertEqual(pagos.consolidar(es)['estado'],'PENDIENTE')

class MotivoActualTests(unittest.TestCase):
    def test_conflicto_documental_no_se_oculta_con_error_ocr_anterior(self):
        e=pagos.extraer('Forma de pago: a 30 días.','https://o.gob.ar/a.pdf','a')+pagos.extraer('Forma de pago: a 60 días.','https://o.gob.ar/b.pdf','b')
        r=o.normalizar({'titulo':'Licitación Pública 1/2026','pago_evidencias':e,'pago_motivo_pendiente':'REQUIERE_OCR_O_LECTURA'})
        self.assertEqual(r['pago']['motivo'],'CONDICIONES_DIFERENTES_REQUIEREN_REVISION')
