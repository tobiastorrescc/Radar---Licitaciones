import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import HTTPError,URLError
import pagos
import oportunidades as o
import cache_documentos as cache

URL='https://oficial.gob.ar/pliego.pdf'
SHA='a'*64
class PagosTests(unittest.TestCase):
    def analizar(self,texto):return pagos.consolidar(pagos.extraer(texto,URL,SHA,pdf=True))
    def test_plazos_explicitos_numericos_y_escritos(self):
        for n,palabra in [(7,'siete'),(15,'quince'),(30,'treinta'),(45,'cuarenta y cinco'),(60,'sesenta'),(90,'noventa')]:
            for valor in [str(n),palabra,palabra+' ('+str(n)+')']:
                with self.subTest(plazo=valor):
                    r=self.analizar('FORMA DE PAGO: dentro de '+valor+' días corridos desde la recepción de la factura.')
                    self.assertEqual(r['estado'],'VERIFICADO');self.assertEqual(r['clasificacion'],f'PLAZO_{n}_DIAS');self.assertEqual(r['plazos_dias'],[n])
                    self.assertFalse(r['prioritario']);self.assertEqual(r['unidades_dias'],['corridos'])
    def test_otro_plazo_y_unidad_no_inventada(self):
        r=self.analizar('El pago se realizará a ciento veinte días de recibida la factura.')
        self.assertEqual(r['clasificacion'],'OTRO_PLAZO');self.assertEqual(r['plazos_dias'],[120]);self.assertEqual(r['unidades_dias'],['no indicada'])
    def test_contado_entrega_factura_y_conformidad_son_distintos(self):
        casos=[('Forma de pago: al contado.','CONTADO',True),('El pago será contra entrega de la mercadería.','CONTRA_ENTREGA',True),('Pago contra presentación de factura.','CONTRA_PRESENTACION_FACTURA',False),('Pago contra entrega de factura.','CONTRA_PRESENTACION_FACTURA',False),('El pago se hará después de la conformidad de recepción.','DESPUES_CONFORMIDAD_RECEPCION',False)]
        for texto,categoria,prioritario in casos:
            with self.subTest(texto=texto):
                r=self.analizar(texto);self.assertEqual(r['clasificacion'],categoria);self.assertEqual(r['prioritario'],prioritario)
    def test_plazo_desde_factura_conformada_no_es_contra_entrega(self):
        r=self.analizar('FORMA DE PAGO: treinta (30) días hábiles desde la presentación de la factura conformada, previa conformidad de recepción.')
        self.assertEqual(r['clasificacion'],'PLAZO_30_DIAS');self.assertIn('CONFORMIDAD_RECEPCION',r['hitos_inicio']);self.assertIn('CONFORMIDAD_FACTURA',r['hitos_inicio']);self.assertFalse(r['prioritario'])
    def test_contado_a_treinta_dias_no_tiene_prioridad_inmediata(self):
        r=self.analizar('Forma de pago: contado a 30 días de la recepción de factura.')
        self.assertEqual(r['clasificacion'],'PLAZO_30_DIAS');self.assertFalse(r['prioritario'])
    def test_sin_clausula_negacion_y_remision_no_se_suponen(self):
        for t in ['Plazo de entrega: 7 días. Garantía: 30 días.','No se admite pago al contado.','Forma de pago: según lo establecido en el pliego general.','Pago en efectivo.']:
            with self.subTest(texto=t):self.assertEqual(self.analizar(t)['etiqueta'],'Pendiente de verificar')
    def test_precio_del_pliego_y_garantia_no_son_pago_al_proveedor(self):
        for t in ['Forma de pago del pliego: al contado.','Pago del sellado: al contado.','Forma de pago: valor del pliego al contado.']:
            self.assertEqual(self.analizar(t)['estado'],'PENDIENTE')
    def test_plazo_de_entrega_no_contamina_plazo_de_pago(self):
        r=self.analizar('Forma de pago: 30 días desde factura. Plazo de entrega: 7 días.')
        self.assertEqual(r['plazos_dias'],[30])
    def test_mixto_opciones_y_conflictos_no_prometen_contado(self):
        for texto,categoria in [('Forma de pago: anticipo 20% al contado y saldo a 60 días.','MIXTO'),('Forma de pago: contado o a 30 días.','OPCIONES_PUBLICADAS')]:
            r=self.analizar(texto);self.assertEqual(r['clasificacion'],categoria);self.assertFalse(r['prioritario'])
        a=pagos.extraer('Forma de pago: a 30 días.',URL,SHA)
        b=pagos.extraer('Forma de pago: a 90 días.','https://oficial.gob.ar/otro.pdf','b'*64)
        r=pagos.consolidar(a+b);self.assertEqual(r['estado'],'PENDIENTE');self.assertEqual(len(r['evidencias']),2)
    def test_cita_pagina_documento_y_hash_son_exigidos(self):
        es=pagos.extraer('Introducción\fFORMA DE PAGO: contra entrega de los bienes.',URL,SHA,pdf=True)
        self.assertEqual(es[0]['pagina'],2);self.assertIn('contra entrega',es[0]['cita']);self.assertEqual(es[0]['sha256'],SHA)
        self.assertEqual(pagos.consolidar([{**es[0],'sha256':None}])['estado'],'PENDIENTE')
    def test_venta_pago_del_adjudicatario_no_es_cobro_inmediato(self):
        r=self.analizar('Forma de pago: el adjudicatario deberá abonar al contado a la Municipalidad.')
        self.assertEqual(r['estado'],'VERIFICADO');self.assertEqual(r['direccion'],'OFERTANTE_AL_ORGANISMO');self.assertFalse(r['prioritario'])
    def test_normalizacion_no_verifica_una_frase_del_titulo(self):
        r=o.normalizar({'titulo':'Compra menor 1/2026 Pago contado','url':URL,'fuente':URL})
        self.assertEqual(r['condiciones_pago'],'Pendiente de verificar');self.assertFalse(r['pago_prioritario'])
    def test_todas_las_novedades_sin_filtros_ni_limite_y_columnas(self):
        rs=[]
        for i in range(1200):
            texto='Forma de pago: a 90 días.' if i%2 else 'Sin información de pago'
            r={'titulo':f'Licitación Pública {i}/2026','numero_procedimiento':f'{i}/2026','tipo_procedimiento':'licitacion publica','organismo':'Municipio','fuente':URL,'url':URL,'pago_evidencias':pagos.extraer(texto,URL,SHA)}
            rs.append(r)
        h={};nuevas=o.incorporar(h,rs,'2026-10-27T09:00:00-03:00')
        self.assertEqual(len(nuevas),1200);self.assertEqual(sum(r['pago']['clasificacion']=='PLAZO_90_DIAS' for r in nuevas),600)
        reporte=o.reporte(nuevas,'2026-10-27');self.assertIn('Condiciones de pago',reporte);self.assertIn('Documento de respaldo',reporte);self.assertIn('Pendiente de verificar',reporte)
        self.assertEqual(reporte.count('| Municipio /'),1200)
    def test_orden_contado_y_entrega_antes_que_otros_sin_excluirlos(self):
        rs=[]
        for n,texto in enumerate(['Forma de pago: a 90 días.','Forma de pago: contra entrega.','Forma de pago: al contado.','Sin información']):
            rs.append(o.normalizar({'titulo':str(n),'url':URL,'pago_evidencias':pagos.extraer(texto,URL,SHA)}))
        orden=sorted(rs,key=o.prioridad);self.assertEqual([r['titulo'] for r in orden],['1','2','0','3'])

class CacheTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.entorno=patch.dict('os.environ',{'RADAR_CACHE_DOCUMENTOS':self.temp.name});self.entorno.start();self.addCleanup(self.entorno.stop)
    def test_revalidacion_304_y_cambio_documental(self):
        peticiones=[]
        def transport(url,**kw):
            peticiones.append(kw['headers_extra'])
            if len(peticiones)==2:raise HTTPError(url,304,'Not Modified',{},None)
            return (b'%PDF-version1' if len(peticiones)==1 else b'%PDF-version2'),'application/pdf',url,{'ETag':'uno' if len(peticiones)==1 else 'dos'}
        a=cache.obtener(URL,transport,fresco=0,reloj=lambda:100)
        b=cache.obtener(URL,transport,fresco=0,reloj=lambda:101)
        c=cache.obtener(URL,transport,fresco=0,reloj=lambda:102)
        self.assertEqual(b[3]['cache_estado'],'HTTP_304');self.assertEqual(a[0],b[0]);self.assertNotEqual(a[3]['sha256'],c[3]['sha256']);self.assertEqual(peticiones[1]['If-None-Match'],'uno')
    def test_sin_validadores_reutiliza_y_expira_sin_suponer_cambio(self):
        transport=unittest.mock.Mock(return_value=(b'%PDF-version','application/pdf',URL,{}))
        cache.obtener(URL,transport,reloj=lambda:100)
        r=cache.obtener(URL,transport,reloj=lambda:101)
        self.assertEqual(transport.call_count,1);self.assertEqual(r[3]['cache_estado'],'CACHE_RECIENTE')
        cache.obtener(URL,transport,reloj=lambda:22000);self.assertEqual(transport.call_count,2)
    def test_no_se_reutiliza_html_como_documento(self):
        transport=unittest.mock.Mock(return_value=(b'<html>error</html>','text/html',URL,{}))
        cache.obtener(URL,transport);cache.obtener(URL,transport);self.assertEqual(transport.call_count,2)
    def test_texto_por_hash_no_repite_extraccion(self):
        with patch('documentos.leer',return_value='Forma de pago: a 15 días.') as lector:
            for i in range(2):cache.leer_texto(b'%PDF-nativo','application/pdf',URL)
            self.assertEqual(lector.call_count,1)
            cache.leer_texto(b'%PDF-modificado','application/pdf',URL);self.assertEqual(lector.call_count,2)
    def test_error_de_revalidacion_no_declara_cache_actual(self):
        cache.obtener(URL,lambda *a,**kw:(b'%PDF-datos','application/pdf',URL,{'ETag':'uno'}),reloj=lambda:100)
        with self.assertRaises(URLError):cache.obtener(URL,lambda *a,**kw:(_ for _ in ()).throw(URLError('bloqueado')),fresco=0,reloj=lambda:101)

class PrecisionTests(unittest.TestCase):
    def test_factura_conformada_no_inventa_recepcion_conforme(self):
        p=pagos.consolidar(pagos.extraer('Forma de pago: 30 días desde factura conformada.',URL,SHA))
        self.assertIn('CONFORMIDAD_FACTURA',p['hitos_inicio']);self.assertNotIn('CONFORMIDAD_RECEPCION',p['hitos_inicio'])
    def test_costo_del_pliego_no_es_contado_comercial(self):
        for t in ['Valor del pliego: pago al contado.','Pago al contado del pliego.']:
            self.assertEqual(pagos.consolidar(pagos.extraer(t,URL,SHA))['estado'],'PENDIENTE')

    def test_fecha_presentacion_y_recepcion_factura_no_se_confunden(self):
        casos=[('Forma de pago: 30 días de la fecha de factura.','FECHA_O_EMISION_FACTURA','desde fecha/emisión de factura'),('Forma de pago: 30 días desde presentación de factura.','PRESENTACION_FACTURA','desde presentación de factura'),('Forma de pago: 30 días de recibida la factura.','RECEPCION_FACTURA','desde recepción de factura')]
        for t,hito,etiqueta in casos:
            r=pagos.consolidar(pagos.extraer(t,URL,SHA));self.assertIn(hito,r['hitos_inicio']);self.assertIn(etiqueta,r['etiqueta'])
    def test_contra_factura_conformada_no_se_reemplaza_por_presentacion(self):
        r=pagos.consolidar(pagos.extraer('El pago se hará contra factura conformada.',URL,SHA))
        self.assertEqual(r['clasificacion'],'CONTRA_FACTURA_CONFORMADA');self.assertNotIn('PRESENTACION_FACTURA',r['hitos_inicio'])

    def test_articulos_y_garantias_no_crean_pago_contado(self):
        for t in ['Forma de pago de la garantía: al contado.','Pago de las tasas: al contado.','Pago del arancel: al contado.']:
            self.assertEqual(pagos.consolidar(pagos.extraer(t,URL,SHA))['estado'],'PENDIENTE',t)

    def test_reparto_documental_entre_fuentes_sin_tope_de_cantidad(self):
        from tools import comprobar_pliegos as c
        candidatos={};vinculos={}
        for fuente in ['https://a.gob.ar','https://b.gob.ar','https://c.gob.ar']:
            for i in range(700):
                url=fuente+f'/{i}.pdf';candidatos[url]={'estado':'PENDIENTE'};vinculos[url]=[{'fuente':fuente,'vigencia':'DESCONOCIDA','numero_procedimiento':f'{i}/2026'}]
        orden=list(c.ordenar_documentos(candidatos,vinculos,'2026-10-27'))
        self.assertEqual(len(orden),2100);self.assertEqual(len(set(orden)),2100)
        self.assertEqual([u.split('/')[2] for u in orden[:3]],['a.gob.ar','b.gob.ar','c.gob.ar'])

class EvidenciaRealTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.reales=json.loads(Path('tests/fixtures/reales/pagos-65.json').read_text())
    def test_cantidad_y_unidad_aeropuerto_treinta_dias(self):
        e=next(r for r in self.reales if r['numero_procedimiento']=='52/2026')['pago']['evidencias'][0]
        r=pagos.consolidar(pagos.extraer(e['cita'],e['url_documento'],e['sha256']))
        self.assertEqual(r['clasificacion'],'PLAZO_30_DIAS');self.assertIn('CONFORMIDAD_RECEPCION',r['hitos_inicio'])
    def test_reconquista_definicion_general_no_selecciona_contado(self):
        es=next(r for r in self.reales if r['organismo']=='Municipalidad de Reconquista' and r['numero_procedimiento']=='9/2026')['pago']['evidencias']
        r=pagos.consolidar(pagos.extraer(es[0]['cita'],es[0]['url_documento'],es[0]['sha256']))
        self.assertEqual(r['estado'],'PENDIENTE');self.assertFalse(r['prioritario'])
    def test_si_se_selecciona_contado_se_aplica_definicion_explicita_no_cero_dias(self):
        e=next(r for r in self.reales if r['organismo']=='Municipalidad de Reconquista' and r['numero_procedimiento']=='9/2026')['pago']['evidencias'][0]
        texto=e['cita']+'\fFORMA DE PAGO: Contado.'
        r=pagos.consolidar(pagos.extraer(texto,e['url_documento'],e['sha256'],pdf=True))
        self.assertEqual(r['plazos_dias'],[10]);self.assertFalse(r['prioritario']);self.assertTrue(r['evidencias'][0]['definicion_contado'])
    def test_crespo_veinte_dias_y_facturas_en_plural(self):
        e=next(r for r in self.reales if r['organismo']=='Municipalidad de Crespo')['pago']['evidencias'][0]
        r=pagos.consolidar(pagos.extraer(e['cita'],e['url_documento'],e['sha256']))
        self.assertEqual(r['plazos_dias'],[20]);self.assertIn('PRESENTACION_FACTURA',r['hitos_inicio']);self.assertNotIn('VARIACIONES DE COSTOS',r['evidencias'][0]['cita'])
    def test_canon_sin_sujeto_no_identifica_quien_paga(self):
        e=next(r for r in self.reales if r['organismo']=='Municipalidad de Federación')['pago']['evidencias'][0]
        r=pagos.consolidar(pagos.extraer(e['cita'],e['url_documento'],e['sha256']))
        self.assertEqual(r['direccion'],'NO_ESPECIFICADA');self.assertIn('mensual a mes vencido',r['etiqueta'])
    def test_codigo_pdf_cortado_solo_se_completa_con_la_url_del_adjunto(self):
        from tools import comprobar_pliegos as c
        parcial='licitacion privada LPR-2026-2-APPSF-OD'
        destino='licitacion privada LPR-2026-2-APPSF-OD-COM-CON-AIR-ROS'
        url='https://aeropuertorosario.com/LPR-2026-00000002-APPSF-OD-COM-CON-AIR-ROS.pdf'
        self.assertTrue(c.pertenece_a([parcial],destino,url))
        self.assertFalse(c.pertenece_a([parcial],destino))
        self.assertFalse(c.pertenece_a([parcial],destino,url.replace('COM-CON','OF-LEGALES')))

    def test_ater_conformidad_no_es_recepcion_inventada(self):
        e=next(r for r in self.reales if r['organismo']=='ATER')['pago']['evidencias'][0]
        p=pagos.consolidar(pagos.extraer(e['cita'],e['url_documento'],e['sha256']))
        self.assertIn('FECHA_O_EMISION_FACTURA',p['hitos_inicio']);self.assertIn('CONFORMIDAD_NO_ESPECIFICADA',p['hitos_inicio']);self.assertNotIn('CONFORMIDAD_RECEPCION',p['hitos_inicio'])

    def test_dato_omitido_no_contradice_condicion_completa(self):
        a=pagos.extraer('Forma de pago: a 30 días.',URL,SHA)
        b=pagos.extraer('Forma de pago: a 30 días corridos desde presentación de factura.','https://oficial.gob.ar/particular.pdf','b'*64)
        p=pagos.consolidar(a+b)
        self.assertEqual(p['estado'],'VERIFICADO');self.assertIn('PRESENTACION_FACTURA',p['hitos_inicio']);self.assertEqual(len(p['evidencias']),2)
    def test_dias_habiles_y_corridos_no_se_unifican(self):
        a=pagos.extraer('Forma de pago: a 30 días hábiles.',URL,SHA)
        b=pagos.extraer('Forma de pago: a 30 días corridos.','https://oficial.gob.ar/particular.pdf','b'*64)
        self.assertEqual(pagos.consolidar(a+b)['estado'],'PENDIENTE')

    def test_contado_no_oculta_requisito_de_factura(self):
        r=pagos.consolidar(pagos.extraer('Forma de pago: contado contra presentación de factura.',URL,SHA))
        self.assertEqual(r['clasificacion'],'CONTADO');self.assertIn('contra presentación de factura',r['etiqueta'])
    def test_contra_entrega_no_oculta_conformidad(self):
        r=pagos.consolidar(pagos.extraer('Forma de pago: contra entrega, previa conformidad de recepción.',URL,SHA))
        self.assertEqual(r['clasificacion'],'CONTRA_ENTREGA');self.assertIn('exige conformidad de recepción',r['etiqueta'])

class LimitesRealesTests(unittest.TestCase):
    def evidencia(self,inicio):
        datos=json.loads(Path('tests/fixtures/reales/pagos-67.json').read_text())
        return next(e for e in datos['evidencias'] if e['cita'].startswith(inicio))
    def test_constancia_seguro_y_pagos_suss_no_son_cobro_del_proveedor(self):
        e=self.evidencia('los pagos de')
        p=pagos.consolidar(pagos.extraer(e['cita'],e['url_documento'],e['sha256']))
        self.assertEqual(p['estado'],'PENDIENTE')
    def test_formulario_plazo_recepcion_no_es_plazo_pago(self):
        e=self.evidencia('Plazo de Pago')
        es=pagos.extraer(e['cita'],e['url_documento'],e['sha256'])
        self.assertEqual(es[0]['plazos_dias'],[30])
        self.assertEqual(es[0]['unidades_dias'],['corridos'])
        self.assertNotIn('7 Días',es[0]['cita'])

class ReporteCamposPreviosTests(unittest.TestCase):
    def test_pago_no_oculta_presupuesto_ubicacion_hora_y_pliego(self):
        r={'organismo':'Municipio','numero_procedimiento':'1/2026','localidad':'Rosario','provincia':'Santa Fe','presupuesto':'$36.000.000','fecha_apertura':'2026-10-28','fecha_hora_apertura':'2026-10-28T10:00:00-03:00','fecha_publicacion':'2026-10-20','enlace_pliego':URL,'url':URL,'titulo':'Servicio','vigencia':'ABIERTA'}
        reporte=o.reporte([r],'2026-10-27')
        for dato in ['Rosario / Santa Fe','$36.000.000','2026-10-28T10:00:00-03:00','2026-10-20','[Pliego]('+URL+')','Condiciones de pago','Documento de respaldo','Pendiente de verificar']:self.assertIn(dato,reporte)
        r['presupuesto']={'importe':'36000000','moneda':None}
        reporte=o.reporte([r],'2026-10-27')
        self.assertIn('36000000 (moneda no informada)',reporte)
        self.assertNotIn("{'importe':",reporte)
